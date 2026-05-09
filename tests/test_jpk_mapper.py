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
