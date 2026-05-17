from ksef2jpk.mapper.jpk_mapper import JPKMapperPRO
from ksef2jpk.model.faktura_model import FakturaModel, Kontrahent, Pozycja


def test_mapper_groups_by_vat_rate_for_sales():
    kontrahent = Kontrahent(nip="1234567890", nazwa="Test Buyer")

    faktura = FakturaModel(
        nr_ksef="6791444505-20260401-755BEE800001-B8",
        meta={
            "typ": "sprzedaz",
            "numer": "FV/1/04/2026",
            "nip_nabywcy": "1234567890",
            "nazwa_nabywcy": "Test Buyer",
            "data_wystawienia": "2026-04-01",
            "data_sprzedazy": "2026-04-01",
            "gtu": "GTU_12",
            "procedury": ["MPP"],
        },
        pozycje=[
            Pozycja("Usługa A", 100.00, 23.00, "sprzedaz", kontrahent, 23.0),
            Pozycja("Usługa B", 200.00, 46.00, "sprzedaz", kontrahent, 23.0),
            Pozycja("Towar C", 50.00, 2.50, "sprzedaz", kontrahent, 5.0),
        ],
    )

    rows = JPKMapperPRO().map(faktura)

    assert len(rows) == 2

    row_23 = rows[0]
    row_5 = rows[1]

    assert row_23.stawka == 23.0
    assert row_23.netto == 300.00
    assert row_23.vat == 69.00
    assert row_23.gtu == "GTU_12"
    assert row_23.procedury == ["MPP"]

    assert row_5.stawka == 5.0
    assert row_5.netto == 50.00
    assert row_5.vat == 2.50


def test_mapper_uses_manual_gtu_override():
    kontrahent = Kontrahent(nip="1234567890", nazwa="Test Buyer")

    faktura = FakturaModel(
        nr_ksef="6791444505-20260401-755BEE800001-B8",
        meta={
            "typ": "sprzedaz",
            "numer": "FV/GTU/OVERRIDE",
            "nip_nabywcy": "1234567890",
            "nazwa_nabywcy": "Test Buyer",
            "data_wystawienia": "2026-04-01",
            "data_sprzedazy": "2026-04-01",
        },
        pozycje=[
            Pozycja(
                nazwa="Laptop",
                netto=1000,
                vat=230,
                typ="sprzedaz",
                kontrahent=kontrahent,
                stawka=23,
                gtu="GTU_06",
                gtu_manual="GTU_12",
            )
        ],
    )

    rows = JPKMapperPRO().map(faktura)

    assert len(rows) == 1
    assert rows[0].gtu == "GTU_12"


def test_mapper_uses_manual_procedure_override():
    kontrahent = Kontrahent(nip="1234567890", nazwa="Test Buyer")

    faktura = FakturaModel(
        nr_ksef="6791444505-20260401-755BEE800001-B8",
        meta={
            "typ": "sprzedaz",
            "numer": "FV/PROC/OVERRIDE",
            "nip_nabywcy": "1234567890",
            "nazwa_nabywcy": "Test Buyer",
            "data_wystawienia": "2026-04-01",
            "data_sprzedazy": "2026-04-01",
        },
        pozycje=[
            Pozycja(
                nazwa="Usługa",
                netto=1000,
                vat=230,
                typ="sprzedaz",
                kontrahent=kontrahent,
                stawka=23,
                procedury=["MPP"],
                procedury_manual=["TP"],
            )
        ],
    )

    rows = JPKMapperPRO().map(faktura)

    assert len(rows) == 1
    assert rows[0].procedury == ["TP"]


def test_mapper_preserves_counterparty_country():
    kontrahent = Kontrahent(nip="DE123456789", nazwa="EU Buyer", kraj="DE")

    faktura = FakturaModel(
        nr_ksef="6791444505-20260401-755BEE800001-B8",
        meta={
            "typ": "sprzedaz",
            "numer": "FV/WDT/1",
            "nip_nabywcy": "DE123456789",
            "nazwa_nabywcy": "EU Buyer",
            "kraj_nabywcy": "DE",
            "data_wystawienia": "2026-04-01",
            "data_sprzedazy": "2026-04-01",
        },
        pozycje=[
            Pozycja(
                nazwa="Towar WDT",
                netto=1000,
                vat=0,
                typ="sprzedaz",
                kontrahent=kontrahent,
                stawka=0,
                procedury=["WDT"],
            )
        ],
    )

    rows = JPKMapperPRO().map(faktura)

    assert len(rows) == 1
    assert rows[0].kontrahent_kraj == "DE"
