import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from KSeF2JPK.parser.ksef_parser import KSeFParser
from KSeF2JPK.mapper.jpk_mapper import JPKMapper
from KSeF2JPK.generator.jpk_generator import JPKGenerator
from KSeF2JPK.model.jpk_model import JPKModel
def main():
    if len(sys.argv) < 3:
        print("ERR: Missing arguments")
        return

    xml_ksef = sys.argv[1]
    output_jpk = sys.argv[2]

    parser = KSeFParser()
    mapper = JPKMapper()
    generator = JPKGenerator()

    faktura = parser.parse(xml_ksef)
    jpk = mapper.map(faktura)
    generator.generate_xml(jpk, output_jpk)

    print("OK")

if __name__ == "__main__":
    main()
