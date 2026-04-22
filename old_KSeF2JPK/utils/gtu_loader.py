import xml.etree.ElementTree as ET

CONFIG_PATH = r"C:\Users\dpolz\Documents\projekty_config.xml"


def load_gtu_rules():
    """
    Wczytuje reguły GTU z projekt_config.xml.
    Zwraca listę słowników: [{"nazwa": "...", "gtu": "GTU_12"}, ...]
    """
    tree = ET.parse(CONFIG_PATH)
    root = tree.getroot()

    konf = root.find(".//Konfiguracja[@nazwa='JPK']")
    if konf is None:
        return []

    gtu_node = konf.find("GTUReguly")
    if gtu_node is None:
        return []

    rules = []
    for reg in gtu_node.findall("Regula"):
        nazwa = reg.get("nazwa", "").strip().lower()
        gtu = reg.get("gtu", "").strip()
        if nazwa and gtu:
            rules.append({"nazwa": nazwa, "gtu": gtu})

    return rules
