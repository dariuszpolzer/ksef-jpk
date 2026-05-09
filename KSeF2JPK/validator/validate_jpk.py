from pathlib import Path

from lxml import etree


class LocalResolver(etree.Resolver):
    def __init__(self, xsd_dir: Path):
        super().__init__()
        self.xsd_dir = xsd_dir

    def resolve(self, url, pubid, context):
        filename = Path(url).name

        candidates = [
            self.xsd_dir / filename,
            self.xsd_dir / "DefinicjeTypy.xsd",
            self.xsd_dir / "eD" / filename,
            self.xsd_dir / "etd" / filename,
        ]

        for path in candidates:
            if path.exists():
                return self.resolve_filename(str(path), context)

        return None


def validate_jpk(xml_path: str, xsd_path: str):
    xsd_file = Path(xsd_path).resolve()
    xsd_dir = xsd_file.parent

    try:
        parser = etree.XMLParser(resolve_entities=False, no_network=False)
        parser.resolvers.add(LocalResolver(xsd_dir))

        schema_doc = etree.parse(str(xsd_file), parser)
        schema = etree.XMLSchema(schema_doc)

        xml_doc = etree.parse(str(Path(xml_path).resolve()))
        schema.assertValid(xml_doc)

        print("✔ JPK jest poprawny zgodnie z XSD MF")
        return True

    except etree.XMLSchemaParseError as e:
        print("❌ Błąd parsowania XSD:")
        for error in e.error_log:
            print(f"  • Linia {error.line}: {error.message}")
        return False

    except etree.DocumentInvalid as e:
        print("❌ BŁĘDY WALIDACJI JPK:")
        for error in e.error_log:
            print(f"  • Linia {error.line}: {error.message}")
        return False

    except Exception as e:
        print("❌ Błąd walidacji JPK:", e)
        return False


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Użycie: python validate_jpk.py <plik.xml> <schemat.xsd>")
        sys.exit(1)

    ok = validate_jpk(sys.argv[1], sys.argv[2])
    sys.exit(0 if ok else 1)
