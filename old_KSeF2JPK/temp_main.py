
# import sys
# import os

# # dodaj katalog nadrzędny (Documents)
# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# sys.path.append(BASE_DIR)

# from parser.ksef_parser import KSeFParser
# from mapper.jpk_mapper import JPKMapper
# from generator.jpk_generator import JPKGenerator
# from model.jpk_model import JPKModel

# def main():
    # ksef_xml = "przyklad_faktury.xml"   # tu ścieżka do Twojego pliku KSeF
    # jpk_xml = "wynik_jpk.xml"

    # # 1) KSeF → FakturaModel
    # parser = KSeFParser()
    # faktura = parser.parse(ksef_xml)

    # # 2) FakturaModel → JPKModel
    # mapper = JPKMapper()
    # jpk = mapper.map(faktura)

    # # meta na sztywno na test
    # jpk.meta = {
        # "rok": 2026,
        # "miesiac": 4,
        # "kod_urzedu": "1234",
        # "przestrzenie_nazw": {}  # na razie puste
    # }

    # # 3) JPKModel → XML
    # generator = JPKGenerator()
    # generator.generate_xml(jpk, jpk_xml)

    # print("Gotowe. Wygenerowano:", jpk_xml)

# if __name__ == "__main__":
    # main()



import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from KSeF2JPK.parser.ksef_parser import KSeFParser
from KSeF2JPK.mapper.jpk_mapper import JPKMapper
from KSeF2JPK.generator.jpk_generator import JPKGenerator
from KSeF2JPK.model.jpk_model import JPKModel

def main():
    ksef_xml = "przyklad_faktury.xml"
    jpk_xml = "wynik_jpk.xml"

    parser = KSeFParser()
    faktura = parser.parse(ksef_xml)

    mapper = JPKMapper()
    jpk = mapper.map(faktura)

    jpk.meta = {
        "rok": 2026,
        "miesiac": 4,
        "kod_urzedu": "1234",
        "przestrzenie_nazw": {}
    }

    generator = JPKGenerator()
    generator.generate_xml(jpk, jpk_xml)

    print("Gotowe. Wygenerowano:", jpk_xml)

if __name__ == "__main__":
    main()