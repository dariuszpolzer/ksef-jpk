from lxml import etree

def validate_jpk(xml_path: str, xsd_path: str):
    try:
        # Wczytanie XSD
        with open(xsd_path, "rb") as f:
            schema_root = etree.XML(f.read())
        schema = etree.XMLSchema(schema_root)

        # Wczytanie JPK
        with open(xml_path, "rb") as f:
            xml_doc = etree.XML(f.read())

        # Walidacja
        schema.assertValid(xml_doc)
        print("✔ JPK jest poprawny zgodnie z XSD MF")

    except etree.DocumentInvalid as e:
        print("❌ BŁĘDY WALIDACJI JPK:")
        for error in schema.error_log:
            print(f"  • Linia {error.line}: {error.message}")

    except Exception as e:
        print("❌ Błąd walidacji:", e)


# Pozwala uruchomić skrypt bezpośrednio:
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Użycie: python validate_jpk.py <plik.xml> <schemat.xsd>")
        sys.exit(1)

    xml_file = sys.argv[1]
    xsd_file = sys.argv[2]

    validate_jpk(xml_file, xsd_file)
