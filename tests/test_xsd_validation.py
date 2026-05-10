from pathlib import Path

from ksef2jpk.adapter.jpk_adapter import dict_to_jpk_model
from ksef2jpk.builder.jpk_builder import JPKBuilderPROPlus
from ksef2jpk.generator.jpk_generator import JPKGeneratorPRO
from ksef2jpk.model.jpk_model import WierszEwidencji
from ksef2jpk.validator.validate_jpk import validate_jpk


def test_generated_jpk_passes_xsd_validation(tmp_path):
    xsd_path = Path("validator/JPK_V7M_3.xsd")

    if not xsd_path.exists():
        xsd_path = Path("ksef2jpk/validator/JPK_V7M_3.xsd")

    assert xsd_path.exists(), f"Brak XSD: {xsd_path}"

    sprzedaz = [
        WierszEwidencji(
            typ="sprzedaz",
            kontrahent_nip="1234567890",
            kontrahent_nazwa="Test Buyer",
            nr_ksef="",
            dokument="FV/1/2026",
            data_wystawienia="2026-04-01",
            data_sprzedazy="2026-04-01",
            netto=1000,
            vat=230,
            stawka=23,
            procedury=[],
        )
    ]

    builder = JPKBuilderPROPlus(
        rok=2026,
        miesiac=4,
        podmiot={
            "nip": "6791444505",
            "nazwa": "Dariusz Polzer",
            "kod_urzedu": "1214",
            "email": "test@example.com",
            "telefon": "123456789",
            "data_urodzenia": "1980-01-01",
        },
    )

    jpk_dict = builder.build(sprzedaz, [])
    jpk_model = dict_to_jpk_model(jpk_dict)

    output_xml = tmp_path / "jpk.xml"

    generator = JPKGeneratorPRO()
    generator.generate(jpk_model, str(output_xml))

    assert output_xml.exists()

    assert validate_jpk(str(output_xml), str(xsd_path)) is True


def test_generated_jpk_with_kor_oo_imp_passes_xsd_validation(tmp_path):
    xsd_path = Path("validator/JPK_V7M_3.xsd")

    if not xsd_path.exists():
        xsd_path = Path("ksef2jpk/validator/JPK_V7M_3.xsd")

    assert xsd_path.exists(), f"Brak XSD: {xsd_path}"

    sprzedaz = [
        WierszEwidencji(
            typ="sprzedaz",
            kontrahent_nip="1234567890",
            kontrahent_nazwa="Test Buyer",
            nr_ksef="",
            dokument="KOR/1/2026",
            data_wystawienia="2026-04-05",
            data_sprzedazy="2026-04-05",
            netto=-1000,
            vat=-230,
            stawka=23,
            procedury=[],
            is_korekta=True,
        ),
        WierszEwidencji(
            typ="sprzedaz",
            kontrahent_nip="1234567890",
            kontrahent_nazwa="Test Buyer",
            nr_ksef="",
            dokument="OO/1/2026",
            data_wystawienia="2026-04-06",
            data_sprzedazy="2026-04-06",
            netto=5000,
            vat=0,
            stawka=None,
            procedury=["OO"],
        ),
    ]

    zakupy = [
        WierszEwidencji(
            typ="zakup",
            kontrahent_nip="DE123456789",
            kontrahent_nazwa="EU Supplier",
            nr_ksef="",
            dokument="IMP/1/2026",
            data_wystawienia="2026-04-10",
            data_sprzedazy="2026-04-10",
            data_wplywu="2026-04-11",
            netto=10000,
            vat=2300,
            stawka=23,
            procedury=["IMP"],
        )
    ]

    builder = JPKBuilderPROPlus(
        rok=2026,
        miesiac=4,
        podmiot={
            "nip": "6791444505",
            "nazwa": "Dariusz Polzer",
            "kod_urzedu": "1214",
            "email": "test@example.com",
            "telefon": "123456789",
            "data_urodzenia": "1980-01-01",
        },
    )

    jpk_dict = builder.build(sprzedaz, zakupy)
    jpk_model = dict_to_jpk_model(jpk_dict)

    output_xml = tmp_path / "jpk_kor_oo_imp.xml"

    generator = JPKGeneratorPRO()
    generator.generate(jpk_model, str(output_xml))

    assert output_xml.exists()
    assert validate_jpk(str(output_xml), str(xsd_path)) is True

def test_generated_jpk_with_wdt_passes_xsd_validation(tmp_path):
    xsd_path = Path("validator/JPK_V7M_3.xsd")

    if not xsd_path.exists():
        xsd_path = Path("ksef2jpk/validator/JPK_V7M_3.xsd")

    assert xsd_path.exists()

    sprzedaz = [
        WierszEwidencji(
            typ="sprzedaz",
            kontrahent_nip="DE123456789",
            kontrahent_nazwa="EU Buyer",
            nr_ksef="",
            dokument="WDT/1/2026",
            data_wystawienia="2026-04-01",
            data_sprzedazy="2026-04-01",
            netto=10000,
            vat=0,
            stawka=0,
            procedury=["WDT"],
        )
    ]

    builder = JPKBuilderPROPlus(
        rok=2026,
        miesiac=4,
        podmiot={
            "nip": "6791444505",
            "nazwa": "Dariusz Polzer",
            "kod_urzedu": "1214",
            "email": "test@example.com",
            "telefon": "123456789",
            "data_urodzenia": "1980-01-01",
        },
    )

    jpk_dict = builder.build(sprzedaz, [])
    deklaracja = jpk_dict["Deklaracja"]["PozycjeSzczegolowe"]

    assert deklaracja["P_25"] == 10000

    row = jpk_dict["Ewidencja"]["SprzedazWiersz"][0]
    assert row["WDT"] == "1"

    jpk_model = dict_to_jpk_model(jpk_dict)

    output_xml = tmp_path / "jpk_wdt.xml"

    generator = JPKGeneratorPRO()
    generator.generate(jpk_model, str(output_xml))

    assert validate_jpk(str(output_xml), str(xsd_path)) is True
