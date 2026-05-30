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


def make_fa3_xml(seller_nip="6791444505", buyer_nip="5270005984", invoice_type="VAT"):
    correction = ""
    if invoice_type == "KOR":
        correction = """
        <RodzajFaktury>KOR</RodzajFaktury>
        <DaneFaKorygowanej>
          <NrFaKorygowanej>FV/1/2026</NrFaKorygowanej>
          <DataFaKorygowanej>2026-04-01</DataFaKorygowanej>
        </DaneFaKorygowanej>
"""

    stan_przed = "<StanPrzed>1</StanPrzed>" if invoice_type == "KOR" else ""

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Faktura xmlns="http://crd.gov.pl/wzor/2025/06/25/13775/">
  <Podmiot1>
    <DaneIdentyfikacyjne>
      <NIP>{seller_nip}</NIP>
      <Nazwa>FA3 Seller</Nazwa>
    </DaneIdentyfikacyjne>
  </Podmiot1>
  <Podmiot2>
    <DaneIdentyfikacyjne>
      <NIP>{buyer_nip}</NIP>
      <Nazwa>FA3 Buyer</Nazwa>
    </DaneIdentyfikacyjne>
  </Podmiot2>
  <Fa>
    <P_1>2026-04-01</P_1>
    <P_2>FA3/{invoice_type}/1/2026</P_2>
    <P_6>2026-04-01</P_6>
    <P_13_1>100</P_13_1>
    <P_14_1>23</P_14_1>
    <P_15>123</P_15>
    {correction}
    <FaWiersz>
      <P_7>Usługa FA3</P_7>
      <P_11>100</P_11>
      <P_12>23</P_12>
      {stan_przed}
    </FaWiersz>
  </Fa>
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


def test_parser_accepts_fa3_sales_fixture(tmp_path):
    xml_file = tmp_path / "fa3_sales.xml"
    xml_file.write_text(make_fa3_xml(), encoding="utf-8")

    faktura = KSeFParser("6791444505").parse(str(xml_file))

    assert faktura.meta["typ"] == "sprzedaz"
    assert faktura.meta["numer"] == "FA3/VAT/1/2026"
    assert faktura.pozycje[0].netto == 100
    assert faktura.meta["walidacja_wejscia"]["ok"] is True


def test_parser_accepts_fa3_purchase_fixture(tmp_path):
    xml_file = tmp_path / "fa3_purchase.xml"
    xml_file.write_text(make_fa3_xml(seller_nip="5270005984", buyer_nip="6791444505"), encoding="utf-8")

    faktura = KSeFParser("6791444505").parse(str(xml_file))

    assert faktura.meta["typ"] == "zakup"
    assert faktura.meta["nip_sprzedawcy"] == "5270005984"
    assert faktura.pozycje[0].typ == "zakup"


def test_parser_accepts_fa3_correction_fixture(tmp_path):
    xml_file = tmp_path / "fa3_correction.xml"
    xml_file.write_text(make_fa3_xml(invoice_type="KOR"), encoding="utf-8")

    faktura = KSeFParser("6791444505").parse(str(xml_file))

    assert faktura.meta["is_korekta"] is True
    assert faktura.meta["nr_fa_korygowanej"] == "FV/1/2026"
    assert faktura.pozycje[0].netto == -100


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


def test_parser_detects_mpp(tmp_path):
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <Faktura xmlns="http://crd.gov.pl/wzor/2025/06/25/13775/">

      <Podmiot1>
        <DaneIdentyfikacyjne>
          <NIP>6791444505</NIP>
          <Nazwa>Seller</Nazwa>
        </DaneIdentyfikacyjne>
      </Podmiot1>

      <Podmiot2>
        <DaneIdentyfikacyjne>
          <NIP>1234567890</NIP>
          <Nazwa>Buyer</Nazwa>
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
          <P_7>Usługa</P_7>
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

    assert len(faktura.pozycje) == 1

    p = faktura.pozycje[0]

    assert "MPP" in (p.procedury or [])


def test_parser_handles_oo_procedure(tmp_path):
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <Faktura xmlns="http://crd.gov.pl/wzor/2025/06/25/13775/">

      <Podmiot1>
        <DaneIdentyfikacyjne>
          <NIP>6791444505</NIP>
          <Nazwa>Seller</Nazwa>
        </DaneIdentyfikacyjne>
      </Podmiot1>

      <Podmiot2>
        <DaneIdentyfikacyjne>
          <NIP>1234567890</NIP>
          <Nazwa>Buyer</Nazwa>
        </DaneIdentyfikacyjne>
      </Podmiot2>

      <Fa>
        <P_1>2026-03-24</P_1>
        <P_2>FV/OO/1</P_2>
        <P_6>2026-03-24</P_6>

        <FaWiersz>
          <P_7>Usługa OO</P_7>
          <P_11>5000</P_11>
          <P_12>OO</P_12>
        </FaWiersz>

      </Fa>
    </Faktura>
    """

    xml_file = tmp_path / "oo.xml"
    xml_file.write_text(xml, encoding="utf-8")

    parser = KSeFParser("6791444505")
    faktura = parser.parse(str(xml_file))

    assert len(faktura.pozycje) == 1

    p = faktura.pozycje[0]

    assert p.netto == 5000.0
    assert p.vat == 0.0
    assert p.stawka is None
    assert "OO" in (p.procedury or [])


def test_parser_detects_wdt(tmp_path):
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <Faktura xmlns="http://crd.gov.pl/wzor/2025/06/25/13775/">
      <Podmiot1>
        <DaneIdentyfikacyjne>
          <NIP>6791444505</NIP>
          <Nazwa>Test Seller</Nazwa>
        </DaneIdentyfikacyjne>
        <Adres>
          <KodKraju>PL</KodKraju>
        </Adres>
      </Podmiot1>

      <Podmiot2>
        <DaneIdentyfikacyjne>
          <NIP>DE123456789</NIP>
          <Nazwa>EU Buyer</Nazwa>
        </DaneIdentyfikacyjne>
        <Adres>
          <KodKraju>DE</KodKraju>
        </Adres>
      </Podmiot2>

      <Fa>
        <P_1>2026-04-01</P_1>
        <P_2>WDT/1/2026</P_2>
        <P_6>2026-04-01</P_6>

        <FaWiersz>
          <P_7>Export service</P_7>
          <P_11>10000</P_11>
          <P_12>0</P_12>
        </FaWiersz>
      </Fa>
    </Faktura>
    """

    xml_file = tmp_path / "wdt.xml"
    xml_file.write_text(xml, encoding="utf-8")

    parser = KSeFParser("6791444505")
    faktura = parser.parse(str(xml_file))

    assert len(faktura.pozycje) == 1

    p = faktura.pozycje[0]

    assert p.stawka == 0.0
    assert "WDT" in (p.procedury or [])


def test_parser_detects_export_exp(tmp_path):
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <Faktura xmlns="http://crd.gov.pl/wzor/2025/06/25/13775/">
      <Podmiot1>
        <DaneIdentyfikacyjne>
          <NIP>6791444505</NIP>
          <Nazwa>Test Seller</Nazwa>
        </DaneIdentyfikacyjne>
        <Adres>
          <KodKraju>PL</KodKraju>
        </Adres>
      </Podmiot1>

      <Podmiot2>
        <DaneIdentyfikacyjne>
          <NIP>GB123456789</NIP>
          <Nazwa>UK Buyer</Nazwa>
        </DaneIdentyfikacyjne>
        <Adres>
          <KodKraju>GB</KodKraju>
        </Adres>
      </Podmiot2>

      <Fa>
        <P_1>2026-04-01</P_1>
        <P_2>EXP/1/2026</P_2>
        <P_6>2026-04-01</P_6>

        <FaWiersz>
          <P_7>Export goods</P_7>
          <P_11>10000</P_11>
          <P_12>0</P_12>
        </FaWiersz>
      </Fa>
    </Faktura>
    """

    xml_file = tmp_path / "exp.xml"
    xml_file.write_text(xml, encoding="utf-8")

    parser = KSeFParser("6791444505")
    faktura = parser.parse(str(xml_file))

    assert len(faktura.pozycje) == 1

    p = faktura.pozycje[0]

    assert p.stawka == 0.0
    assert "EXP" in (p.procedury or [])
    assert "WDT" not in (p.procedury or [])


def test_parser_detects_gtu_06(tmp_path):
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <Faktura xmlns="http://crd.gov.pl/wzor/2025/06/25/13775/">
      <Podmiot1>
        <DaneIdentyfikacyjne>
          <NIP>6791444505</NIP>
          <Nazwa>Seller</Nazwa>
        </DaneIdentyfikacyjne>
      </Podmiot1>

      <Podmiot2>
        <DaneIdentyfikacyjne>
          <NIP>5250001001</NIP>
          <Nazwa>Buyer</Nazwa>
        </DaneIdentyfikacyjne>
      </Podmiot2>

      <Fa>
        <P_1>2026-04-01</P_1>
        <P_2>FV/GTU/1</P_2>
        <P_6>2026-04-01</P_6>

        <FaWiersz>
          <P_7>Sprzedaż laptop gamingowy</P_7>
          <P_11>10000</P_11>
          <P_12>23</P_12>
        </FaWiersz>
      </Fa>
    </Faktura>
    """

    xml_file = tmp_path / "gtu.xml"
    xml_file.write_text(xml, encoding="utf-8")

    parser = KSeFParser("6791444505")
    faktura = parser.parse(str(xml_file))

    assert len(faktura.pozycje) == 1

    p = faktura.pozycje[0]

    assert p.gtu == "GTU_06"
