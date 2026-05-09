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
