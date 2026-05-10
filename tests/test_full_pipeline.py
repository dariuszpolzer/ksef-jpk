from ksef2jpk.builder.jpk_builder import JPKBuilderPROPlus
from ksef2jpk.generator.jpk_generator import JPKGeneratorPRO
from ksef2jpk.mapper.jpk_mapper import JPKMapperPRO
from ksef2jpk.parser.ksef_parser import KSeFParser

SAMPLE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Faktura xmlns="http://ksef.mf.gov.pl/schema">
  <Fa>
    <P_1>2026-04-01</P_1>
    <P_2>FV/1/04/2026</P_2>
    <P_6>2026-04-01</P_6>
  </Fa>

  <Podmiot1>
    <DaneIdentyfikacyjne>
      <NIP>6791444505</NIP>
      <Nazwa>Test Seller</Nazwa>
    </DaneIdentyfikacyjne>
  </Podmiot1>

  <Podmiot2>
    <DaneIdentyfikacyjne>
      <NIP>1234567890</NIP>
      <Nazwa>Test Buyer</Nazwa>
    </DaneIdentyfikacyjne>
  </Podmiot2>

  <FaWiersz>
    <P_7>Produkt A</P_7>
    <P_11>100</P_11>
    <P_12>23</P_12>
  </FaWiersz>
</Faktura>
"""


def test_full_pipeline(tmp_path):

    xml_file = tmp_path / "invoice.xml"
    xml_file.write_text(SAMPLE_XML, encoding="utf-8")

    parser = KSeFParser("6791444505")
    faktura = parser.parse(str(xml_file))

    mapper = JPKMapperPRO()
    rows = mapper.map(faktura)

    builder = JPKBuilderPROPlus(
        rok=2026,
        miesiac=4,
        podmiot={
            "nip": "6791444505",
            "nazwa": "Dariusz Polzer",
            "kod_urzedu": "1214",
        },
    )

    jpk_dict = builder.build(rows, [])

    class DummyModel:
        pass

    model = DummyModel()
    model.data_wytworzenia = "2026-04-30T10:00:00"
    model.kod_urzedu = "1214"
    model.data_od = "2026-04-01"
    model.nip = "6791444505"
    model.nazwa = "Dariusz Polzer"
    model.data_urodzenia = "1980-01-01"
    model.email = "test@example.com"
    model.telefon = "123456789"

    model.deklaracja = type("Dek", (), jpk_dict["Deklaracja"]["PozycjeSzczegolowe"])
    model.sprzedaz_wiersz = []
    model.zakup_wiersz = []

    generator = JPKGeneratorPRO()

    out = tmp_path / "jpk.xml"
    generator.generate(model, str(out))

    assert out.exists()


def test_full_pipeline_korekta_to_zero(tmp_path):
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <Faktura xmlns="http://crd.gov.pl/wzor/2025/06/25/13775/">
      <Podmiot1>
        <DaneIdentyfikacyjne>
          <NIP>6791444505</NIP>
          <Nazwa>Test Seller</Nazwa>
        </DaneIdentyfikacyjne>
      </Podmiot1>

      <Podmiot2>
        <DaneIdentyfikacyjne>
          <NIP>1234567890</NIP>
          <Nazwa>Test Buyer</Nazwa>
        </DaneIdentyfikacyjne>
      </Podmiot2>

      <Fa>
        <P_1>2026-03-24</P_1>
        <P_2>PE003K/2026</P_2>
        <P_6>2026-03-24</P_6>
        <P_15>0</P_15>
        <RodzajFaktury>KOR</RodzajFaktury>

        <FaWiersz>
          <P_7>Projekt1</P_7>
          <P_11>11000</P_11>
          <P_12>23</P_12>
          <StanPrzed>1</StanPrzed>
        </FaWiersz>

        <FaWiersz>
          <P_7>Projekt1</P_7>
          <P_11>11000</P_11>
          <P_12>23</P_12>
        </FaWiersz>

        <FaWiersz>
          <P_7>Projekt2</P_7>
          <P_11>4500</P_11>
          <P_12>23</P_12>
          <StanPrzed>1</StanPrzed>
        </FaWiersz>

        <FaWiersz>
          <P_7>Projekt2</P_7>
          <P_11>4500</P_11>
          <P_12>23</P_12>
        </FaWiersz>
      </Fa>
    </Faktura>
    """

    xml_file = tmp_path / "korekta.xml"
    xml_file.write_text(xml, encoding="utf-8")

    parser = KSeFParser("6791444505")
    faktura = parser.parse(str(xml_file))

    mapper = JPKMapperPRO()
    rows = mapper.map(faktura)

    assert len(rows) == 1
    assert rows[0].typ == "sprzedaz"
    assert rows[0].netto == -15500.0
    assert rows[0].vat == -3565.0
    assert rows[0].stawka == 23.0
    assert rows[0].is_korekta is True

    builder = JPKBuilderPROPlus(
        rok=2026,
        miesiac=3,
        podmiot={
            "nip": "6791444505",
            "nazwa": "Dariusz Polzer",
            "kod_urzedu": "1214",
        },
    )

    jpk = builder.build(rows, [])

    deklaracja = jpk["Deklaracja"]["PozycjeSzczegolowe"]
    ewidencja = jpk["Ewidencja"]

    assert deklaracja["P_19"] == -15500
    assert deklaracja["P_20"] == -3565
    assert deklaracja["P_37"] == -15500
    assert deklaracja["P_38"] == -3565

    sprzedaz_wiersz = ewidencja["SprzedazWiersz"][0]

    assert sprzedaz_wiersz["K_19"] == -15500.0
    assert sprzedaz_wiersz["K_20"] == -3565.0
    assert ewidencja["SprzedazCtrl"]["LiczbaWierszySprzedazy"] == 1
    assert ewidencja["SprzedazCtrl"]["PodatekNalezny"] == -3565.0


def test_mpp_is_detected_but_not_emitted_in_jpk_xml(tmp_path):
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <Faktura xmlns="http://crd.gov.pl/wzor/2025/06/25/13775/">
      <Podmiot1>
        <DaneIdentyfikacyjne>
          <NIP>6791444505</NIP>
          <Nazwa>Test Seller</Nazwa>
        </DaneIdentyfikacyjne>
      </Podmiot1>

      <Podmiot2>
        <DaneIdentyfikacyjne>
          <NIP>1234567890</NIP>
          <Nazwa>Test Buyer</Nazwa>
        </DaneIdentyfikacyjne>
      </Podmiot2>

      <Fa>
        <P_1>2026-03-24</P_1>
        <P_2>FV/MPP/1</P_2>
        <P_6>2026-03-24</P_6>

        <Adnotacje>
          <MPP>1</MPP>
        </Adnotacje>

        <FaWiersz>
          <P_7>Usługa MPP</P_7>
          <P_11>20000</P_11>
          <P_12>23</P_12>
        </FaWiersz>
      </Fa>
    </Faktura>
    """

    xml_file = tmp_path / "mpp.xml"
    xml_file.write_text(xml, encoding="utf-8")

    parser = KSeFParser("6791444505")
    faktura = parser.parse(str(xml_file))

    assert faktura.meta["mpp"] is True
    assert "MPP" in faktura.meta["procedury"]

    mapper = JPKMapperPRO()
    rows = mapper.map(faktura)

    assert len(rows) == 1
    assert "MPP" in rows[0].procedury

    builder = JPKBuilderPROPlus(
        rok=2026,
        miesiac=3,
        podmiot={
            "nip": "6791444505",
            "nazwa": "Dariusz Polzer",
            "kod_urzedu": "1214",
        },
    )

    jpk_dict = builder.build(rows, [])

    from ksef2jpk.adapter.jpk_adapter import dict_to_jpk_model

    jpk_model = dict_to_jpk_model(jpk_dict)

    output_xml = tmp_path / "jpk_mpp.xml"
    generator = JPKGeneratorPRO()
    generator.generate(jpk_model, str(output_xml))

    xml_out = output_xml.read_text(encoding="utf-8")

    assert "<MPP>" not in xml_out
    assert "</MPP>" not in xml_out
