from ksef2jpk.utils.string_tools import safe_filename


def test_safe_filename_removes_polish_chars():
    assert safe_filename("Dariusz Pólżer sp. z o.o.") == "Dariusz_Polzer_sp_z_oo"


def test_safe_filename_empty():
    assert safe_filename("") == "unknown"
