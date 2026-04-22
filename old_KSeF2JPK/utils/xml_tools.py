import xml.etree.ElementTree as ET

def load_xml(path: str):
    return ET.parse(path)

def pretty_print(xml_path: str):
    # opcjonalnie: integracja z Twoim prettyprint
    pass
