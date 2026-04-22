import os
import sys
import glob
import traceback
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from KSeF2JPK.parser.ksef_parser import KSeFParser
from KSeF2JPK.classifier.jpk_flags import JPKFlagsClassifier
from KSeF2JPK.mapper.jpk_mapper import JPKMapperPRO
from KSeF2JPK.builder.jpk_builder import JPKBuilderPROPlus
from KSeF2JPK.generator.jpk_generator import JPKGeneratorPRO
from KSeF2JPK.validator.validate_jpk import validate_jpk
from KSeF2JPK.adapter.jpk_adapter import dict_to_jpk_model
from KSeF2JPK.utils.policz_xml_w_katalogu import policz_xml_w_katalogu
from KSeF2JPK.utils.jpk2html import JPK2HTML

# ------------------------------------------------------------
# KONFIGURACJA
# ------------------------------------------------------------

INPUT_DIR = r"C:\Users\dpolz\Documents\KSeF2JPK\test_data"
#OUTPUT_XML = r"C:\Users\dpolz\Documents\KSeF2JPK\wynik_jpk.xml"
XSD_PATH = r"C:\Users\dpolz\Documents\KSeF2JPK\KSeF2JPK\validator\xsd\JPK_V7M_3.xsd"
XML_DIR = r"C:\Users\dpolz\Documents\JPK\XML"

PODMIOT = {
    "nip": "6791444505",
    "nazwa": "DARIUSZ POLZER",
    "kod_urzedu": "1210",
    "email": "dpolzer@post.pl",
    "telefon": "509467620",
    "data_urodzenia": "1957-12-06",
}


rok = datetime.now().year
miesiac= datetime.now().month
numer = policz_xml_w_katalogu(XML_DIR)+1

OUTPUT_XML = os.path.join( XML_DIR, f"JPK_Dariusz_Polzer_{numer}_{rok}.xml")

JPK_ROK = rok
JPK_MIESIAC = miesiac

# Łatwe wyłączanie filtra do testów
ENABLE_DATE_FILTER = True


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
        return (
            faktura.meta.get("data_sprzedazy")
            or faktura.meta.get("data_wystawienia")
        )

    if typ == "zakup":
        return (
            faktura.meta.get("data_wplywu")
            or faktura.meta.get("data_wystawienia")
        )

    return faktura.meta.get("data_wystawienia")


def invoice_in_period(faktura, start_dt: datetime, end_dt: datetime) -> bool:
    date_txt = get_filter_date_for_invoice(faktura)
    dt = parse_iso_date(date_txt)
    if dt is None:
        return False
    return start_dt <= dt <= end_dt


# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------

def main():
    parser = KSeFParser()
    classifier = JPKFlagsClassifier()
    mapper = JPKMapperPRO()

    paths = sorted(glob.glob(os.path.join(INPUT_DIR, "*.xml")))

    if not paths:
        print(f"❌ Nie znaleziono plików XML w katalogu: {INPUT_DIR}")
        return

    period_start, period_end = get_period_bounds(JPK_ROK, JPK_MIESIAC)

    # -----------------------------------------------------------------
    # 1. PARSOWANIE + KLASYFIKACJA + OPCJONALNY FILTR DATY
    # -----------------------------------------------------------------
    print_section("1. PARSOWANIE FAKTUR")
    faktury = []
    parse_errors = []
    skipped_by_date = []

    for path in paths:
        filename = os.path.basename(path)

        try:
            faktura = parser.parse(path)
            faktura = classifier.apply_to_invoice(faktura)

            if ENABLE_DATE_FILTER:
                if not invoice_in_period(faktura, period_start, period_end):
                    skip_date = get_filter_date_for_invoice(faktura)
                    skipped_by_date.append((filename, skip_date, faktura.meta.get("typ")))
                    print(
                        f"[POMINIĘTO] {filename} | "
                        f"typ={faktura.meta.get('typ')!r} | "
                        f"data_filtra={skip_date!r}"
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
        print(
            f"Filtr okresu JPK: WŁĄCZONY "
            f"({period_start.date()} -> {period_end.date()})"
        )
        print(f"Pominięto po dacie: {len(skipped_by_date)}")
    else:
        print("Filtr okresu JPK: WYŁĄCZONY")

    if parse_errors:
        print_section("BŁĘDY PARSOWANIA")
        for filename, err in parse_errors:
            print(f"• {filename}: {err}")

    if not faktury:
        print("\n❌ Brak poprawnie sparsowanych faktur po filtracji. Kończę.")
        return

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
            print(
                f"• dokument={w.dokument!r}, typ={w.typ!r}, "
                f"nip={w.kontrahent_nip!r}, nr_ksef={w.nr_ksef!r}"
            )

    # -----------------------------------------------------------------
    # 4. BUDOWA JPK
    # -----------------------------------------------------------------
    print_section("4. BUDOWA JPK")
    builder = JPKBuilderPROPlus(
        rok=JPK_ROK,
        miesiac=JPK_MIESIAC,
        podmiot=PODMIOT
    )

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

    converter = JPK2HTML(OUTPUT_XML)
    html_file = converter.convert()


    # -----------------------------------------------------------------
    # 8. PODSUMOWANIE
    # -----------------------------------------------------------------
    print(f"Plik XML w katalogu:            {numer}")
    print(f"Miesiąc:                        {JPK_MIESIAC}")
    print(f"Rok:                            {JPK_ROK}")   
    print(f"Liczba plików wejściowych:      {len(paths)}")
    print(f"Poprawnie sparsowane faktury:   {len(faktury)}")
    print(f"Poprawnie zmapowane wiersze:    {len(wiersze)}")
    print(f"Wiersze sprzedaży:              {len(sprzedaz_we)}")
    print(f"Wiersze zakupu:                 {len(zakupy_we)}")
    if ENABLE_DATE_FILTER:
        print(f"Pominięte po dacie:             {len(skipped_by_date)}")
    print(f"Plik wynikowy:                  {OUTPUT_XML}")
    print(f"Podgląd HTML zapisany jako:     {html_file}")

if __name__ == "__main__":
    main()
