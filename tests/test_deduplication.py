from ksef2jpk.model.faktura_model import FakturaModel
from ksef2jpk.utils.dedup import get_document_dedup_key


def test_get_document_dedup_key_prefers_nr_ksef():
    faktura = FakturaModel(
        nr_ksef="KSEF-123",
        meta={
            "nr_ksef": "META-KSEF",
            "numer": "FV/1/2026",
        },
        pozycje=[],
    )

    assert get_document_dedup_key(faktura) == "KSEF-123"


def test_get_document_dedup_key_falls_back_to_meta_nr_ksef():
    faktura = FakturaModel(
        nr_ksef="",
        meta={
            "nr_ksef": "META-KSEF",
            "numer": "FV/1/2026",
        },
        pozycje=[],
    )

    assert get_document_dedup_key(faktura) == "META-KSEF"


def test_get_document_dedup_key_falls_back_to_invoice_number():
    faktura = FakturaModel(
        nr_ksef="",
        meta={
            "nr_ksef": "",
            "numer": "FV/1/2026",
        },
        pozycje=[],
    )

    assert get_document_dedup_key(faktura) == "FV/1/2026"
