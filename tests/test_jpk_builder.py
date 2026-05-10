from ksef2jpk.builder.jpk_builder import JPKBuilderPROPlus
from ksef2jpk.model.jpk_model import WierszEwidencji


def test_jpk_builder_declaration_values():
    sprzedaz = [
        WierszEwidencji(
            typ="sprzedaz",
            kontrahent_nip="1234567890",
            kontrahent_nazwa="Test Buyer",
            nr_ksef="TEST-KSEF-1",
            dokument="FV/1/04/2026",
            data_wystawienia="2026-04-01",
            data_sprzedazy="2026-04-01",
            netto=100,
            vat=23,
            stawka=23,
        ),
        WierszEwidencji(
            typ="sprzedaz",
            kontrahent_nip="1234567890",
            kontrahent_nazwa="Test Buyer",
            nr_ksef="TEST-KSEF-2",
            dokument="FV/2/04/2026",
            data_wystawienia="2026-04-02",
            data_sprzedazy="2026-04-02",
            netto=200,
            vat=10,
            stawka=5,
        ),
    ]

    zakupy = []

    builder = JPKBuilderPROPlus(
        rok=2026,
        miesiac=4,
        podmiot={
            "nip": "6791444505",
            "nazwa": "Dariusz Polzer",
            "kod_urzedu": "1214",
        },
    )

    jpk = builder.build(sprzedaz, zakupy)

    deklaracja = jpk["Deklaracja"]["PozycjeSzczegolowe"]

    assert deklaracja["P_19"] == 100
    assert deklaracja["P_20"] == 23
    assert deklaracja["P_23"] == 200
    assert deklaracja["P_24"] == 10
    assert deklaracja["P_37"] == 300
    assert deklaracja["P_38"] == 33


def test_builder_marks_oo_sales_procedure():
    sprzedaz = [
        WierszEwidencji(
            typ="sprzedaz",
            kontrahent_nip="1234567890",
            kontrahent_nazwa="Test Buyer",
            nr_ksef="TEST-KSEF-OO",
            dokument="FV/OO/1",
            data_wystawienia="2026-04-01",
            data_sprzedazy="2026-04-01",
            netto=5000,
            vat=0,
            stawka=None,
            procedury=["OO"],
        )
    ]

    builder = JPKBuilderPROPlus(
        rok=2026,
        miesiac=4,
        podmiot={
            "nip": "6791444505",
            "nazwa": "Dariusz Polzer",
            "kod_urzedu": "1214",
        },
    )

    jpk = builder.build(sprzedaz, [])

    row = jpk["Ewidencja"]["SprzedazWiersz"][0]
    deklaracja = jpk["Deklaracja"]["PozycjeSzczegolowe"]

    assert row["OO"] == "1"
    assert deklaracja["P_31"] == 5000


def test_builder_maps_imp_purchase_to_k45_k46():
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
        },
    )

    jpk = builder.build([], zakupy)

    row = jpk["Ewidencja"]["ZakupWiersz"][0]
    deklaracja = jpk["Deklaracja"]["PozycjeSzczegolowe"]

    assert row["IMP"] == "1"

    assert row["K_42"] == 0
    assert row["K_43"] == 0

    assert row["K_45"] == 10000
    assert row["K_46"] == 2300

    assert deklaracja["P_45"] == 10000
    assert deklaracja["P_46"] == 0
