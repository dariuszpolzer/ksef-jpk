from ksef2jpk.utils.ksef_number import (
    extract_ksef_number_from_filename,
    is_valid_ksef_number,
)


def test_valid_ksef_number():
    value = "6791444505-20260401-755BEE800001-B8"
    assert is_valid_ksef_number(value)


def test_extract_ksef_number_from_filename():
    filename = "6791444505-20260401-755BEE800001-B8.xml"
    assert extract_ksef_number_from_filename(filename) == ("6791444505-20260401-755BEE800001-B8")


def test_invalid_ksef_number():
    assert not is_valid_ksef_number("abc.xml")
