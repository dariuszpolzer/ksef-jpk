# import xml.etree.ElementTree as ET

# def load_namespaces(config):
    # """
    # config = {
        # "WARTOSC": ["ns1", "ns2", ...],
        # "ATRYBUT": ["atr1", "atr2", ...]
    # }
    # """

    # namespaces = {}
    # attributes = {}

    # wart = config.get("WARTOSC", [])
    # atr = config.get("ATRYBUT", [])

    # # budujemy mapę atrybut → wartość
    # for a, v in zip(atr, wart):
        # if a and v:
            # attributes[a] = v

    # # rejestrujemy namespace’y w ElementTree
    # for a, v in attributes.items():
        # if a.startswith("xmlns"):
            # # xmlns:etd → etd
            # if ":" in a:
                # prefix = a.split(":")[1]
            # else:
                # prefix = ""
            # ET.register_namespace(prefix, v)

    # return attributes
def load_namespaces(ns_dict: dict) -> dict:
    """
    Zamienia słownik:
        {"xmlns": "...", "xmlns:xsi": "...", "xsi:schemaLocation": "..."}
    na atrybuty elementu root JPK.
    """
    attrs = {}

    for key, val in ns_dict.items():
        if key and val:
            attrs[key] = val

    return attrs
