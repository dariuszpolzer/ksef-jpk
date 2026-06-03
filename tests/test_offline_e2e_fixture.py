from pathlib import Path

from ksef2jpk.adapter.jpk_adapter import dict_to_jpk_model
from ksef2jpk.builder.jpk_builder import JPKBuilderPROPlus
from ksef2jpk.generator.jpk_generator import JPKGeneratorPRO
from ksef2jpk.mapper.jpk_mapper import JPKMapperPRO
from ksef2jpk.parser.ksef_parser import KSeFParser
from ksef2jpk.validator.validate_jpk import validate_jpk


def test_offline_e2e_fixture_generates_valid_jpk(tmp_path):
    fixture_dir = Path("test_data/offline_e2e")
    xsd_path = Path("validator/JPK_V7M_3.xsd")

    assert fixture_dir.exists()
    assert xsd_path.exists()

    parser = KSeFParser("6791444505")
    mapper = JPKMapperPRO()
    all_rows = []

    for xml_path in sorted(fixture_dir.glob("*.xml")):
        faktura = parser.parse(str(xml_path))
        all_rows.extend(mapper.map(faktura))

    sales_rows = [row for row in all_rows if row.typ == "sprzedaz"]
    purchase_rows = [row for row in all_rows if row.typ == "zakup"]

    assert len(sales_rows) == 2
    assert len(purchase_rows) == 1
    assert any(row.is_korekta for row in sales_rows)

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

    jpk_dict = builder.build(sales_rows, purchase_rows)
    declaration = jpk_dict["Deklaracja"]["PozycjeSzczegolowe"]

    assert declaration["P_19"] == 700
    assert declaration["P_20"] == 161
    assert declaration["P_42"] == 200
    assert declaration["P_43"] == 46

    output_xml = tmp_path / "offline_e2e_jpk.xml"
    JPKGeneratorPRO().generate(dict_to_jpk_model(jpk_dict), str(output_xml))

    assert output_xml.exists()
    assert validate_jpk(str(output_xml), str(xsd_path)) is True
