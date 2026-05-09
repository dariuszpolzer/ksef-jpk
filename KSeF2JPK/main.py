import argparse
import glob
import json
import os
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
from ksef2jpk.utils.jpk2html import JPK2HTML
from ksef2jpk.utils.policz_xml_w_katalogu import policz_xml_w_katalogu
from ksef2jpk.utils.string_tools import safe_filename
from ksef2jpk.validator.validate_jpk import validate_jpk

# ------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "config.json"))


def load_config(config_path: str) -> dict:
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Brak pliku konfiguracyjnego: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_args():
    parser = argparse.ArgumentParser(description="KSeF2JPK - generator JPK z faktur KSeF")

    parser.add_argument("--year", type=int, help="Rok JPK, np. 2026")
    parser.add_argument("--month", type=int, help="Miesiąc JPK, np. 4")
    parser.add_argument("--input-dir", help="Katalog z fakturami XML")
    parser.add_argument("--batch-dir", help="Katalog batch z ksef-sync")
    parser.add_argument("--config", help="Ścieżka do config.json")
    parser.add_argument("--no-date-filter", action="store_true", help="Wyłącz filtr daty")

    return parser.parse_args()


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
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)

        return str(input_dir), batch_dir, manifest

    if config.get("input_dir"):
        return config["input_dir"], None, None

    raise RuntimeError("Brak input_dir albo batch_dir w config.json")


ARGS = parse_args()

CONFIG_PATH = os.path.abspath(ARGS.config) if ARGS.config else DEFAULT_CONFIG_PATH
CONFIG = load_config(CONFIG_PATH)
XSD_PATH = CONFIG["xsd_path"]
XML_DIR = CONFIG["xml_dir"]
PODMIOT = CONFIG["podmiot"]
HTML_DIR = CONFIG.get("html_dir", os.path.join(os.path.dirname(XML_DIR), "html"))

os.makedirs(XML_DIR, exist_ok=True)
os.makedirs(HTML_DIR, exist_ok=True)

if ARGS.input_dir:
    CONFIG["input_dir"] = ARGS.input_dir
    CONFIG["batch_dir"] = None

if ARGS.batch_dir:
    CONFIG["batch_dir"] = ARGS.batch_dir
    CONFIG["input_dir"] = None

INPUT_DIR, BATCH_DIR, BATCH_MANIFEST = resolve_input_source(CONFIG)

print("Katalog faktur wejściowych:", INPUT_DIR)

if BATCH_DIR:
    print("Batch:", BATCH_DIR)

if BATCH_MANIFEST:
    batch_info = BATCH_MANIFEST.get("batch", {})
    print("Batch ID:", batch_info.get("batch_id"))
    print("Faktur w manifeście:", batch_info.get("invoice_count"))


now = datetime.now()

JPK_ROK = ARGS.year or CONFIG.get("jpk_rok") or now.year
JPK_MIESIAC = ARGS.month or CONFIG.get("jpk_miesiac") or now.month

if not 1 <= int(JPK_MIESIAC) <= 12:
    raise ValueError(f"Nieprawidłowy miesiąc: {JPK_MIESIAC}")

ENABLE_DATE_FILTER = CONFIG.get("enable_date_filter", True)

if ARGS.no_date_filter:
    ENABLE_DATE_FILTER = False

numer = policz_xml_w_katalogu(XML_DIR) + 1

output_pattern = CONFIG.get("output_file_pattern", "JPK_{podatnik}_{miesiac}_{rok}.xml")

nazwa = CONFIG["podmiot"]["nazwa"]
podatnik_safe = safe_filename(nazwa).upper()

output_filename = output_pattern.format(rok=JPK_ROK, miesiac=f"{JPK_MIESIAC:02d}", podatnik=podatnik_safe)

OUTPUT_XML = os.path.join(XML_DIR, output_filename)


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


def is_candidate_input_xml(path: str) -> bool:
    """
    Filtruje tylko pliki, które chcemy traktować jako wejściowe faktury KSeF.
    Odrzuca wygenerowane JPK i pomocnicze XML-e.
    """
    name = os.path.basename(path).lower()

    excluded_prefixes = (
        "jpk_",
        "wynik_",
        "output_",
    )

    excluded_exact = {
        "wynik_test_jpk.xml",
    }

    if name in excluded_exact:
        return False

    if name.startswith(excluded_prefixes):
        return False

    return True


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


# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------


def main():
    parser = KSeFParser(PODMIOT["nip"])
    classifier = JPKFlagsClassifier()
    mapper = JPKMapperPRO()

    all_paths = sorted(glob.glob(os.path.join(INPUT_DIR, "*.xml")))
    paths = [p for p in all_paths if is_candidate_input_xml(p)]
    skipped_non_input = [p for p in all_paths if not is_candidate_input_xml(p)]

    if BATCH_MANIFEST:
        manifest_count = BATCH_MANIFEST.get("batch", {}).get("invoice_count")
        if manifest_count is not None and manifest_count != len(paths):
            print(f"⚠️ Różnica manifest/XML: " f"manifest={manifest_count}, XML={len(paths)}")

    if not paths:
        print(f"❌ Nie znaleziono plików XML w katalogu: {INPUT_DIR}")
        return

    quality_stats = init_quality_stats()
    quality_stats["input_xml_skipped"] = len(skipped_non_input)

    period_start, period_end = get_period_bounds(JPK_ROK, JPK_MIESIAC)

    # -----------------------------------------------------------------
    # 1. PARSOWANIE + KLASYFIKACJA + OPCJONALNY FILTR DATY
    # -----------------------------------------------------------------
    print_section("1. PARSOWANIE FAKTUR")

    faktury = []
    parse_errors = []
    skipped_by_date = []
    skipped_corrections = []

    for path in paths:
        filename = os.path.basename(path)

        try:
            faktura = parser.parse(path)
            faktura = classifier.apply_to_invoice(faktura)

            update_quality_stats(quality_stats, faktura)

            # ---------------------------------------------------------
            # KOREKTY – tylko sygnał, bez wpuszczania do JPK
            # ---------------------------------------------------------
            if faktura.meta.get("is_korekta"):
                skipped_corrections.append(
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

            if ENABLE_DATE_FILTER:
                if not invoice_in_period(faktura, period_start, period_end):
                    skip_date = get_filter_date_for_invoice(faktura)
                    skipped_by_date.append((filename, skip_date, faktura.meta.get("typ")))

                    print(
                        f"[POMINIĘTO] {filename} | " f"typ={faktura.meta.get('typ')!r} | " f"data_filtra={skip_date!r}"
                    )
                    continue

            faktury.append(faktura)

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

    if ENABLE_DATE_FILTER:
        print(f"Filtr okresu JPK: WŁĄCZONY " f"({period_start.date()} -> {period_end.date()})")
        print(f"Pominięto po dacie: {len(skipped_by_date)}")
    else:
        print("Filtr okresu JPK: WYŁĄCZONY")

    print(f"Korekty uwzględnione: {len(skipped_corrections)}")

    if parse_errors:
        print_section("BŁĘDY PARSOWANIA")
        for filename, err in parse_errors:
            print(f"• {filename}: {err}")

    if skipped_corrections:
        print_section("POMINIĘTE KOREKTY")
        for item in skipped_corrections:
            print(
                f"• {item['filename']} | "
                f"numer={item['numer']!r} | "
                f"rodzaj={item['rodzaj_faktury']!r} | "
                f"korygowana={item['nr_fa_korygowanej']!r} | "
                f"data_korygowanej={item['data_fa_korygowanej']!r} | "
                f"powód={item['przyczyna_korekty']!r}"
            )

    if not faktury:
        print("\n❌ Brak poprawnie sparsowanych faktur po filtracji. Kończę.")
        return
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
            print(f"• {doc}: {err}")

    if not wiersze:
        print("\n❌ Brak poprawnie zmapowanych wierszy. Kończę.")
        return

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
        print("\n⚠️ Wykryto wiersze z nieobsługiwanym typem:")
        for w in inne_we:
            print(f"• dokument={w.dokument!r}, typ={w.typ!r}, " f"nip={w.kontrahent_nip!r}, nr_ksef={w.nr_ksef!r}")

    # -----------------------------------------------------------------
    # 4. BUDOWA JPK
    # -----------------------------------------------------------------
    print_section("4. BUDOWA JPK")

    builder = JPKBuilderPROPlus(rok=JPK_ROK, miesiac=JPK_MIESIAC, podmiot=PODMIOT)

    try:
        jpk_dict = builder.build(sprzedaz_we, zakupy_we)
        print("[OK] Zbudowano strukturę JPK.")
    except Exception as e:
        print(f"❌ Błąd podczas budowy JPK: {e}")
        traceback.print_exc()
        return

    # -----------------------------------------------------------------
    # 5. ADAPTACJA I GENEROWANIE XML
    # -----------------------------------------------------------------
    print_section("5. ADAPTACJA I GENEROWANIE XML")

    try:
        jpk_model = dict_to_jpk_model(jpk_dict)
        generator = JPKGeneratorPRO()
        generator.generate(jpk_model, OUTPUT_XML)
        print(f"[OK] Wygenerowano: {OUTPUT_XML}")
    except Exception as e:
        print(f"❌ Błąd podczas generowania XML: {e}")
        traceback.print_exc()
        return

    # -----------------------------------------------------------------
    # 6. WALIDACJA XSD
    # -----------------------------------------------------------------
    print_section("6. WALIDACJA XSD")

    try:
        validate_jpk(OUTPUT_XML, XSD_PATH)
    except Exception as e:
        print(f"❌ Błąd podczas walidacji JPK: {e}")
        traceback.print_exc()

    # -----------------------------------------------------------------
    # 7. KONWERSJA DO HTML
    # -----------------------------------------------------------------
    converter = JPK2HTML(OUTPUT_XML, HTML_DIR)
    html_file = converter.convert()

    # -----------------------------------------------------------------
    # 8. PODSUMOWANIE I RAPORT JAKOŚCI
    # -----------------------------------------------------------------
    print_section("8. PODSUMOWANIE")

    print(f"Plik XML w katalogu:            {numer}")
    print(f"Miesiąc:                        {JPK_MIESIAC}")
    print(f"Rok:                            {JPK_ROK}")

    if BATCH_DIR:
        print(f"Batch źródłowy:                 {BATCH_DIR}")

    if BATCH_MANIFEST:
        batch_info = BATCH_MANIFEST.get("batch", {})
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

    if ENABLE_DATE_FILTER:
        print(f"Pominięte po dacie:             {len(skipped_by_date)}")

    print(f"Pominięte korekty:              {len(skipped_corrections)}")
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

    print("")
    print(f"Plik wynikowy:                  {OUTPUT_XML}")
    print(f"Podgląd HTML zapisany jako:     {html_file}")


if __name__ == "__main__":
    main()
