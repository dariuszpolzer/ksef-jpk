import argparse
import csv
import glob
import json
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

from ksef2jpk.adapter.jpk_adapter import dict_to_jpk_model
from ksef2jpk.builder.jpk_builder import JPKBuilderPROPlus
from ksef2jpk.classifier.jpk_flags import JPKFlagsClassifier
from ksef2jpk.generator.jpk_generator import JPKGeneratorPRO
from ksef2jpk.mapper.jpk_mapper import JPKMapperPRO
from ksef2jpk.parser.ksef_parser import KSeFParser
from ksef2jpk.utils.batch_loader import get_invoices_dir
from ksef2jpk.utils.dedup import get_document_dedup_key
from ksef2jpk.utils.jpk2html import JPK2HTML
from ksef2jpk.utils.policz_xml_w_katalogu import policz_xml_w_katalogu
from ksef2jpk.utils.string_tools import safe_filename
from ksef2jpk.validation import (
    build_skipped_invoice_report,
    is_candidate_input_xml,
    validate_runtime_config,
)
from ksef2jpk.validator.validate_jpk import validate_jpk

# ------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "config.json"))


def load_config(config_path: str) -> dict:
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Brak pliku konfiguracyjnego: {config_path}")

    with open(config_path, encoding="utf-8") as f:
        return json.load(f)


def configure_console_encoding() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="KSeF2JPK - generator JPK z faktur KSeF")

    parser.add_argument(
        "command",
        nargs="?",
        choices=["build", "validate"],
        default="build",
        help="Komenda: build generuje JPK, validate sprawdza konfigurację i źródło faktur.",
    )
    parser.add_argument("--year", type=int, help="Rok JPK, np. 2026")
    parser.add_argument("--month", type=int, help="Miesiąc JPK, np. 4")
    parser.add_argument("--input-dir", help="Katalog z fakturami XML")
    parser.add_argument("--batch-dir", help="Katalog batch z ksef-sync")
    parser.add_argument("--config", help="Ścieżka do config.json")
    parser.add_argument("--no-date-filter", action="store_true", help="Wyłącz filtr daty")

    return parser.parse_args(argv)


def build_runtime_config(args):
    config_path = os.path.abspath(args.config) if args.config else DEFAULT_CONFIG_PATH
    config = load_config(config_path)

    if args.input_dir:
        config["input_dir"] = args.input_dir
        config["batch_dir"] = None

    if args.batch_dir:
        config["batch_dir"] = args.batch_dir
        config["input_dir"] = None

    return config_path, config


def resolve_input_source(config: dict):
    """
    Obsługuje dwa tryby:
    1. batch_dir z ksef-sync
    2. klasyczne input_dir
    """
    if config.get("batch_dir"):
        batch_root = Path(config["batch_dir"])
        input_dir = get_invoices_dir(batch_root)

        batch_dir = input_dir.parent
        manifest_path = batch_dir / "manifest.json"

        manifest = None
        if manifest_path.exists():
            with open(manifest_path, encoding="utf-8") as f:
                manifest = json.load(f)

        return str(input_dir), batch_dir, manifest

    if config.get("input_dir"):
        return config["input_dir"], None, None

    raise RuntimeError("Brak input_dir albo batch_dir w config.json")


# ------------------------------------------------------------
# HELPER: WYDRUK SEKCJI
# ------------------------------------------------------------


def print_section(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


# ------------------------------------------------------------
# HELPER: ZAKRES OKRESU JPK
# ------------------------------------------------------------


def get_period_bounds(year: int, month: int):
    from calendar import monthrange

    start = datetime(year, month, 1)
    end = datetime(year, month, monthrange(year, month)[1])
    return start, end


def parse_iso_date(date_txt: str):
    if not date_txt:
        return None
    try:
        return datetime.fromisoformat(date_txt[:10])
    except ValueError:
        return None


def get_filter_date_for_invoice(faktura):
    """
    Data używana do kwalifikacji do okresu JPK.
    - sprzedaż: data_sprzedazy, fallback data_wystawienia
    - zakup: data_wplywu, fallback data_wystawienia
    """
    typ = faktura.meta.get("typ")

    if typ == "sprzedaz":
        return faktura.meta.get("data_sprzedazy") or faktura.meta.get("data_wystawienia")

    if typ == "zakup":
        return faktura.meta.get("data_wplywu") or faktura.meta.get("data_wystawienia")

    return faktura.meta.get("data_wystawienia")


def invoice_in_period(faktura, start_dt: datetime, end_dt: datetime) -> bool:
    date_txt = get_filter_date_for_invoice(faktura)
    dt = parse_iso_date(date_txt)
    if dt is None:
        return False
    return start_dt <= dt <= end_dt


def init_quality_stats() -> dict:
    return {
        "nr_ksef_xml": 0,
        "nr_ksef_filename": 0,
        "nr_ksef_missing": 0,
        "with_gtu": 0,
        "with_procedury": 0,
        "sum_warning": 0,
        "korekty": 0,
        "input_xml_skipped": 0,
        "input_validation_warning": 0,
        "duplicates_skipped": 0,
    }


def update_quality_stats(stats: dict, faktura) -> None:
    nr_ksef_source = faktura.meta.get("nr_ksef_source", "none")

    if nr_ksef_source == "xml":
        stats["nr_ksef_xml"] += 1
    elif nr_ksef_source == "filename":
        stats["nr_ksef_filename"] += 1
    else:
        stats["nr_ksef_missing"] += 1

    if faktura.meta.get("gtu"):
        stats["with_gtu"] += 1

    if faktura.meta.get("procedury"):
        stats["with_procedury"] += 1

    kontrola_sum = faktura.meta.get("kontrola_sum", {})
    if kontrola_sum and not kontrola_sum.get("all_ok", True):
        stats["sum_warning"] += 1

    if faktura.meta.get("is_korekta"):
        stats["korekty"] += 1

    walidacja = faktura.meta.get("walidacja_wejscia", {})
    if walidacja and not walidacja.get("ok", True):
        stats["input_validation_warning"] += 1


def write_quality_csv(output_path, parsed_records, mapped_rows):
    """
    Raport jakości danych po parsowaniu i mapowaniu.
    parsed_records = []

    parsed_records.append(
        {
            "filename": filename,
            "faktura": faktura,
        }
    )

    mapped_rows: lista WierszEwidencji
    """

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows_by_document = {}
    for row in mapped_rows:
        rows_by_document.setdefault(row.dokument, []).append(row)

    fieldnames = [
        "filename",
        "numer",
        "nr_ksef",
        "typ",
        "data_wystawienia",
        "data_sprzedazy",
        "kontrahent_nip",
        "kontrahent_nazwa",
        "netto",
        "vat",
        "gtu",
        "procedury",
        "is_korekta",
        "kontrola_sum_ok",
        "walidacja_ok",
        "ostrzezenia",
    ]

    with output_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()

        for record in parsed_records:
            filename = record["filename"]
            faktura = record["faktura"]
            meta = faktura.meta or {}

            numer = meta.get("numer") or faktura.nr_ksef or "BRAK"
            related_rows = rows_by_document.get(numer, [])

            kontrola_sum = meta.get("kontrola_sum", {})
            walidacja = meta.get("walidacja_wejscia", {})

            if related_rows:
                netto = sum(float(r.netto or 0) for r in related_rows)
                vat = sum(float(r.vat or 0) for r in related_rows)
                gtu = sorted({r.gtu for r in related_rows if r.gtu})
                procedury = sorted({proc for r in related_rows for proc in (r.procedury or []) if proc})
            else:
                netto = meta.get("netto_razem", 0)
                vat = meta.get("vat_razem", 0)
                gtu = []
                procedury = meta.get("procedury", [])

            if meta.get("typ") == "sprzedaz":
                kontrahent_nip = meta.get("nip_nabywcy", "")
                kontrahent_nazwa = meta.get("nazwa_nabywcy", "")
            elif meta.get("typ") == "zakup":
                kontrahent_nip = meta.get("nip_sprzedawcy", "")
                kontrahent_nazwa = meta.get("nazwa_sprzedawcy", "")
            else:
                kontrahent_nip = ""
                kontrahent_nazwa = ""

            writer.writerow(
                {
                    "filename": filename,
                    "numer": meta.get("numer", ""),
                    "nr_ksef": faktura.nr_ksef or meta.get("nr_ksef", ""),
                    "typ": meta.get("typ", ""),
                    "data_wystawienia": meta.get("data_wystawienia", ""),
                    "data_sprzedazy": meta.get("data_sprzedazy", ""),
                    "kontrahent_nip": kontrahent_nip,
                    "kontrahent_nazwa": kontrahent_nazwa,
                    "netto": round(float(netto or 0), 2),
                    "vat": round(float(vat or 0), 2),
                    "gtu": ",".join(gtu),
                    "procedury": ",".join(procedury),
                    "is_korekta": bool(meta.get("is_korekta")),
                    "kontrola_sum_ok": kontrola_sum.get("all_ok", ""),
                    "walidacja_ok": walidacja.get("ok", ""),
                    "ostrzezenia": " | ".join(walidacja.get("warnings", [])),
                }
            )

    print(f"[OK] Raport jakości CSV: {output_path}")


# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------


def print_validation_report(report) -> None:
    print("\nWALIDACJA KSEF2JPK")

    for item in report.info:
        print(f"OK {item}")

    for warning in report.warnings:
        print(f"WARN {warning}")

    for error in report.errors:
        print(f"ERROR {error}")

    if report.ok:
        print("\n=== VALIDATION OK ===")
    else:
        print("\n=== VALIDATION FAILED ===")


def run_validate(args) -> int:
    _, config = build_runtime_config(args)
    report = validate_runtime_config(config)
    print_validation_report(report)
    return 0 if report.ok else 2


def run_build(args) -> int:
    _, config = build_runtime_config(args)
    validation_report = validate_runtime_config(config)
    if not validation_report.ok:
        print_validation_report(validation_report)
        return 2

    xsd_path = config["xsd_path"]
    xml_dir = config["xml_dir"]
    podmiot = config["podmiot"]
    html_dir = config.get("html_dir", os.path.join(os.path.dirname(xml_dir), "html"))

    os.makedirs(xml_dir, exist_ok=True)
    os.makedirs(html_dir, exist_ok=True)

    input_dir, batch_dir, batch_manifest = resolve_input_source(config)

    print("Katalog faktur wejściowych:", input_dir)

    if batch_dir:
        print("Batch:", batch_dir)

    if batch_manifest:
        batch_info = batch_manifest.get("batch", {})
        print("Batch ID:", batch_info.get("batch_id"))
        print("Faktur w manifeście:", batch_info.get("invoice_count"))

    now = datetime.now()

    jpk_rok = args.year or config.get("jpk_rok") or now.year
    jpk_miesiac = args.month or config.get("jpk_miesiac") or now.month

    if not 1 <= int(jpk_miesiac) <= 12:
        raise ValueError(f"Nieprawidłowy miesiąc: {jpk_miesiac}")

    enable_date_filter = config.get("enable_date_filter", True)

    if args.no_date_filter:
        enable_date_filter = False

    numer = policz_xml_w_katalogu(xml_dir) + 1

    output_pattern = config.get("output_file_pattern", "JPK_{podatnik}_{miesiac}_{rok}.xml")
    podatnik_safe = safe_filename(podmiot["nazwa"]).upper()
    output_filename = output_pattern.format(rok=jpk_rok, miesiac=f"{jpk_miesiac:02d}", podatnik=podatnik_safe)
    output_xml = os.path.join(xml_dir, output_filename)

    parser = KSeFParser(podmiot["nip"])
    classifier = JPKFlagsClassifier()
    mapper = JPKMapperPRO()

    all_paths = sorted(glob.glob(os.path.join(input_dir, "*.xml")))
    paths = [p for p in all_paths if is_candidate_input_xml(p)]
    skipped_non_input = [p for p in all_paths if not is_candidate_input_xml(p)]
    skipped_invoice_report = build_skipped_invoice_report(skipped_non_input)

    if batch_manifest:
        manifest_count = batch_manifest.get("batch", {}).get("invoice_count")
        if manifest_count is not None and manifest_count != len(paths):
            print(f"[WARN] Różnica manifest/XML: " f"manifest={manifest_count}, XML={len(paths)}")

    if not paths:
        print(f"[ERROR] Nie znaleziono plików XML w katalogu: {input_dir}")
        return 2

    quality_stats = init_quality_stats()
    quality_stats["input_xml_skipped"] = len(skipped_non_input)

    if skipped_invoice_report:
        report_path = Path(xml_dir) / f"skipped_invoices_{jpk_miesiac:02d}_{jpk_rok}.json"
        report_path.write_text(
            json.dumps(skipped_invoice_report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"[INFO] Raport pominiętych XML: {report_path}")

    period_start, period_end = get_period_bounds(jpk_rok, jpk_miesiac)

    # -----------------------------------------------------------------
    # 1. PARSOWANIE + KLASYFIKACJA + OPCJONALNY FILTR DATY
    # -----------------------------------------------------------------
    print_section("1. PARSOWANIE FAKTUR")

    faktury = []
    parsed_records = []
    parse_errors = []
    skipped_by_date = []
    detected_corrections = []
    seen_documents = set()
    for path in paths:
        filename = os.path.basename(path)

        try:
            faktura = parser.parse(path)
            faktura = classifier.apply_to_invoice(faktura)

            update_quality_stats(quality_stats, faktura)

            # ---------------------------------------------------------
            # KOREKTY – sygnał diagnostyczny; dalej przechodzą przez pipeline.
            # ---------------------------------------------------------
            if faktura.meta.get("is_korekta"):
                detected_corrections.append(
                    {
                        "filename": filename,
                        "numer": faktura.meta.get("numer"),
                        "rodzaj_faktury": faktura.meta.get("rodzaj_faktury"),
                        "przyczyna_korekty": faktura.meta.get("przyczyna_korekty"),
                        "nr_fa_korygowanej": faktura.meta.get("nr_fa_korygowanej"),
                        "data_fa_korygowanej": faktura.meta.get("data_fa_korygowanej"),
                        "nr_ksef": faktura.nr_ksef,
                    }
                )

                print(
                    f"[KOREKTA] {filename} | "
                    f"numer={faktura.meta.get('numer')!r} | "
                    f"korygowana={faktura.meta.get('nr_fa_korygowanej')!r} | "
                    f"powód={faktura.meta.get('przyczyna_korekty')!r}"
                )

            if enable_date_filter:
                if not invoice_in_period(faktura, period_start, period_end):
                    skip_date = get_filter_date_for_invoice(faktura)
                    skipped_by_date.append((filename, skip_date, faktura.meta.get("typ")))

                    print(
                        f"[POMINIĘTO] {filename} | " f"typ={faktura.meta.get('typ')!r} | " f"data_filtra={skip_date!r}"
                    )
                    continue
            # dedup_key = faktura.nr_ksef or faktura.meta.get("nr_ksef") or faktura.meta.get("numer")
            dedup_key = get_document_dedup_key(faktura)
            if dedup_key in seen_documents:
                print(f"[POMINIĘTO DUPLIKAT] {filename} | " f"klucz={dedup_key!r}")
                quality_stats["duplicates_skipped"] += 1
                continue

            seen_documents.add(dedup_key)
            faktury.append(faktura)

            parsed_records.append(
                {
                    "filename": filename,
                    "faktura": faktura,
                }
            )
            kontrola_sum = faktura.meta.get("kontrola_sum", {})
            print(
                f"[OK] {filename} | "
                f"typ={faktura.meta.get('typ')!r} | "
                f"nr_ksef={faktura.nr_ksef!r} | "
                f"nip_sprzedawcy={faktura.meta.get('nip_sprzedawcy')!r} | "
                f"nip_nabywcy={faktura.meta.get('nip_nabywcy')!r} | "
                f"data_wystawienia={faktura.meta.get('data_wystawienia')!r} | "
                f"data_filtra={get_filter_date_for_invoice(faktura)!r} | "
                f"pozycji={len(faktura.pozycje or [])} | "
                f"procedury={faktura.meta.get('procedury', [])!r} | "
                f"gtu={faktura.meta.get('gtu')!r} | "
                f"kontrola_sum={kontrola_sum.get('all_ok')!r}"
            )

        except Exception as e:
            parse_errors.append((filename, str(e)))
            print(f"[BŁĄD] {filename} | parser/classifier: {e}")
            traceback.print_exc()

    print(f"\nZaładowano poprawnie {len(faktury)} z {len(paths)} faktur wejściowych.")

    if enable_date_filter:
        print(f"Filtr okresu JPK: WŁĄCZONY " f"({period_start.date()} -> {period_end.date()})")
        print(f"Pominięto po dacie: {len(skipped_by_date)}")
    else:
        print("Filtr okresu JPK: WYŁĄCZONY")

    print(f"Wykryte korekty: {len(detected_corrections)}")

    if parse_errors:
        print_section("BŁĘDY PARSOWANIA")
        for filename, err in parse_errors:
            print(f"- {filename}: {err}")

    if detected_corrections:
        print_section("WYKRYTE KOREKTY")
        for item in detected_corrections:
            print(
                f"- {item['filename']} | "
                f"numer={item['numer']!r} | "
                f"rodzaj={item['rodzaj_faktury']!r} | "
                f"korygowana={item['nr_fa_korygowanej']!r} | "
                f"data_korygowanej={item['data_fa_korygowanej']!r} | "
                f"powód={item['przyczyna_korekty']!r}"
            )

    if not faktury:
        print("\n[ERROR] Brak poprawnie sparsowanych faktur po filtracji. Kończę.")
        return 2
    # policz faktury wg typu
    faktury_sprzedaz = [f for f in faktury if f.meta.get("typ") == "sprzedaz"]
    faktury_zakup = [f for f in faktury if f.meta.get("typ") == "zakup"]
    faktury_inne = [f for f in faktury if f.meta.get("typ") not in ("sprzedaz", "zakup")]

    # -----------------------------------------------------------------
    # 2. MAPOWANIE
    # -----------------------------------------------------------------
    print_section("2. MAPOWANIE DO WIERSZY EWIDENCJI")

    wiersze = []
    map_errors = []

    for i, faktura in enumerate(faktury, start=1):
        try:
            mapped_rows = mapper.map(faktura)
            wiersze.extend(mapped_rows)

            for j, w in enumerate(mapped_rows, start=1):
                print(
                    f"[OK] #{i}.{j} | "
                    f"typ={w.typ!r} | "
                    f"korekta={w.is_korekta!r} | "
                    f"nip={w.kontrahent_nip!r} | "
                    f"nazwa={w.kontrahent_nazwa!r} | "
                    f"netto={w.netto} | "
                    f"vat={w.vat} | "
                    f"stawka={w.stawka!r} | "
                    f"nr_ksef={w.nr_ksef!r} | "
                    f"dokument={w.dokument!r} | "
                    f"gtu={w.gtu!r} | "
                    f"procedury={w.procedury!r}"
                )

        except Exception as e:
            doc = faktura.meta.get("numer") or faktura.nr_ksef or "BRAK"
            map_errors.append((doc, str(e)))
            print(f"[BŁĄD] dokument={doc!r} | mapper: {e}")
            traceback.print_exc()

    if map_errors:
        print_section("BŁĘDY MAPOWANIA")
        for doc, err in map_errors:
            print(f"- {doc}: {err}")

    quality_csv_path = Path.home() / "Documents" / "JPK" / "REPORTS" / f"quality_report_{jpk_miesiac:02d}_{jpk_rok}.csv"

    write_quality_csv(
        quality_csv_path,
        parsed_records,
        wiersze,
    )

    if not wiersze:
        print("\n[ERROR] Brak poprawnie zmapowanych wierszy. Kończę.")
        return 2
    # -----------------------------------------------------------------
    # 3. PODZIAŁ NA SPRZEDAŻ / ZAKUP
    # -----------------------------------------------------------------
    print_section("3. PODZIAŁ NA SPRZEDAŻ / ZAKUP")

    sprzedaz_we = [w for w in wiersze if w.typ == "sprzedaz"]
    zakupy_we = [w for w in wiersze if w.typ == "zakup"]
    inne_we = [w for w in wiersze if w.typ not in ("sprzedaz", "zakup")]

    print(f"Sprzedaż: {len(sprzedaz_we)}")
    print(f"Zakup:    {len(zakupy_we)}")
    print(f"Inne:     {len(inne_we)}")

    if inne_we:
        print("\n[WARN] Wykryto wiersze z nieobsługiwanym typem:")
        for w in inne_we:
            print(f"- dokument={w.dokument!r}, typ={w.typ!r}, " f"nip={w.kontrahent_nip!r}, nr_ksef={w.nr_ksef!r}")

    # -----------------------------------------------------------------
    # 4. BUDOWA JPK
    # -----------------------------------------------------------------
    print_section("4. BUDOWA JPK")

    builder = JPKBuilderPROPlus(rok=jpk_rok, miesiac=jpk_miesiac, podmiot=podmiot)

    try:
        jpk_dict = builder.build(sprzedaz_we, zakupy_we)
        print("[OK] Zbudowano strukturę JPK.")
    except Exception as e:
        print(f"[ERROR] Błąd podczas budowy JPK: {e}")
        traceback.print_exc()
        return 2

    # -----------------------------------------------------------------
    # 5. ADAPTACJA I GENEROWANIE XML
    # -----------------------------------------------------------------
    print_section("5. ADAPTACJA I GENEROWANIE XML")

    try:
        jpk_model = dict_to_jpk_model(jpk_dict)
        generator = JPKGeneratorPRO()
        generator.generate(jpk_model, output_xml)
        print(f"[OK] Wygenerowano: {output_xml}")
    except Exception as e:
        print(f"[ERROR] Błąd podczas generowania XML: {e}")
        traceback.print_exc()
        return 2

    # -----------------------------------------------------------------
    # 6. WALIDACJA XSD
    # -----------------------------------------------------------------
    print_section("6. WALIDACJA XSD")

    try:
        validate_jpk(output_xml, xsd_path)
    except Exception as e:
        print(f"[ERROR] Błąd podczas walidacji JPK: {e}")
        traceback.print_exc()
        return 2

    # -----------------------------------------------------------------
    # 7. KONWERSJA DO HTML
    # -----------------------------------------------------------------
    converter = JPK2HTML(output_xml, html_dir)
    html_file = converter.convert()

    # -----------------------------------------------------------------
    # 8. PODSUMOWANIE I RAPORT JAKOŚCI
    # -----------------------------------------------------------------
    print_section("8. PODSUMOWANIE")

    print(f"Plik XML w katalogu:            {numer}")
    print(f"Miesiąc:                        {jpk_miesiac}")
    print(f"Rok:                            {jpk_rok}")

    if batch_dir:
        print(f"Batch źródłowy:                 {batch_dir}")

    if batch_manifest:
        batch_info = batch_manifest.get("batch", {})
        print(f"Batch ID:                       {batch_info.get('batch_id')}")
        print(f"Faktur wg manifestu:            {batch_info.get('invoice_count')}")

    print(f"Liczba plików wejściowych:      {len(paths)}")
    print(f"Poprawnie sparsowane faktury:   {len(faktury)}")
    print(f"Poprawnie zmapowane wiersze:    {len(wiersze)}")
    print(f"Faktury sprzedażowe:            {len(faktury_sprzedaz)}")
    print(f"Faktury zakupowe:               {len(faktury_zakup)}")
    print(f"Faktury inne:                   {len(faktury_inne)}")

    print(f"Wiersze sprzedaży:              {len(sprzedaz_we)}")
    print(f"Wiersze zakupu:                 {len(zakupy_we)}")

    if enable_date_filter:
        print(f"Pominięte po dacie:             {len(skipped_by_date)}")

    print(f"Wykryte korekty:                {len(detected_corrections)}")
    print(f"XML-e pominięte jako nie-wejściowe: {quality_stats['input_xml_skipped']}")

    print("")
    print("---- RAPORT JAKOŚCI DANYCH ----")

    print(f"NrKSeF z XML:                   {quality_stats['nr_ksef_xml']}")
    print(f"NrKSeF z nazwy pliku:           {quality_stats['nr_ksef_filename']}")
    print(f"Bez NrKSeF:                     {quality_stats['nr_ksef_missing']}")

    print(f"Faktury z GTU:                  {quality_stats['with_gtu']}")
    print(f"Faktury z procedurami:          {quality_stats['with_procedury']}")
    print(f"Ostrzeżenia kontroli sum:       {quality_stats['sum_warning']}")
    print(f"Wykryte korekty:                {quality_stats['korekty']}")
    print(f"Pominięte duplikaty:            {quality_stats['duplicates_skipped']}")

    print("")
    print(f"Plik wynikowy:                  {output_xml}")
    print(f"Podgląd HTML zapisany jako:     {html_file}")
    return 0


def main(argv=None) -> int:
    configure_console_encoding()
    args = parse_args(argv)

    if args.command == "validate":
        return run_validate(args)

    return run_build(args)


if __name__ == "__main__":
    sys.exit(main())
