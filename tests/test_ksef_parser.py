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

  <FaWiersz>
    <P_7>Produkt B</P_7>
    <P_11>200</P_11>
    <P_12>5</P_12>
  </FaWiersz>
</Faktura>
"""


def test_ksef_parser_basic(tmp_path):
    xml_file = tmp_path / "test.xml"
    xml_file.write_text(SAMPLE_XML, encoding="utf-8")

    parser = KSeFParser("6791444505")
    faktura = parser.parse(str(xml_file))

    assert faktura.meta["typ"] == "sprzedaz"
    assert faktura.meta["numer"] == "FV/1/04/2026"

    assert len(faktura.pozycje) == 2

    assert faktura.pozycje[0].stawka == 23
    assert faktura.pozycje[1].stawka == 5

    assert faktura.pozycje[0].netto == 100
    assert faktura.pozycje[1].netto == 200


def test_korekta_stan_przed_only(tmp_path):
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
        <RodzajFaktury>KOR</RodzajFaktury>

        <FaWiersz>
          <P_7>Projekt1</P_7>
          <P_11>1000</P_11>
          <P_12>23</P_12>
          <StanPrzed>1</StanPrzed>
        </FaWiersz>

        <FaWiersz>
          <P_7>Projekt1</P_7>
          <P_11>1000</P_11>
          <P_12>23</P_12>
        </FaWiersz>
      </Fa>
    </Faktura>
    """

    xml_file = tmp_path / "korekta.xml"
    xml_file.write_text(xml, encoding="utf-8")

    parser = KSeFParser("6791444505")
    faktura = parser.parse(str(xml_file))

    assert faktura.meta["is_korekta"] is True

    # tylko StanPrzed
    assert len(faktura.pozycje) == 1

    p = faktura.pozycje[0]

    assert p.netto == -1000.0
    assert p.vat == -230.0
    assert p.stawka == 23

def test_korekta_totals_check_does_not_warn_for_zero_correction(tmp_path):
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
          <P_11>1000</P_11>
          <P_12>23</P_12>
          <StanPrzed>1</StanPrzed>
        </FaWiersz>

        <FaWiersz>
          <P_7>Projekt1</P_7>
          <P_11>1000</P_11>
          <P_12>23</P_12>
        </FaWiersz>
      </Fa>
    </Faktura>
    """

    xml_file = tmp_path / "korekta.xml"
    xml_file.write_text(xml, encoding="utf-8")

    parser = KSeFParser("6791444505")
    faktura = parser.parse(str(xml_file))

    kontrola_sum = faktura.meta["kontrola_sum"]

    assert kontrola_sum["is_korekta"] is True
    assert kontrola_sum["all_ok"] is True
    assert kontrola_sum["mode"] == "kor_skip_header_compare"
