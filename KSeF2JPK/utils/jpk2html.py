import os
import sys
import xml.etree.ElementTree as ET
from html import escape


TAG_COLOR = "#D0D0D0"


def localname(tag):
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


class JPK2HTML:

    def __init__(self, xml_path: str):
        self.xml_path = xml_path

        self.output_dir = r"C:\Users\dpolz\Documents\JPK\HTML"
        os.makedirs(self.output_dir, exist_ok=True)

        base = os.path.splitext(os.path.basename(xml_path))[0]
        self.html_path = os.path.join(self.output_dir, base + ".html")


    def xml_to_html_tree(self, elem, indent=0):

        pad = "&nbsp;&nbsp;&nbsp;&nbsp;" * indent
        html_parts = []

        name = localname(elem.tag)

        html_parts.append(
            f'{pad}<span style="color:{TAG_COLOR};">&lt;{escape(name)}</span>'
        )

        if elem.attrib:
            for k, v in elem.attrib.items():
                html_parts.append(
                    f' <span style="font-weight:bold;">{escape(k)}="{escape(v)}"</span>'
                )

        html_parts.append(
            f'<span style="color:{TAG_COLOR};">&gt;</span>'
        )

        text = (elem.text or "").strip()

        if text:
            html_parts.append(
                f' <span style="font-weight:bold;">{escape(text)}</span>'
            )

        children = list(elem)

        if children:

            html_parts.append("<br>")

            for child in children:
                html_parts.append(
                    self.xml_to_html_tree(child, indent + 1)
                )

            html_parts.append(
                f'{pad}<span style="color:{TAG_COLOR};">&lt;/{escape(name)}&gt;</span><br>'
            )

        else:

            html_parts.append(
                f'<span style="color:{TAG_COLOR};">&lt;/{escape(name)}&gt;</span><br>'
            )

        return "".join(html_parts)


    def convert(self):

        if not os.path.isfile(self.xml_path):
            raise FileNotFoundError(f"Plik nie istnieje: {self.xml_path}")

        try:
            tree = ET.parse(self.xml_path)

        except ET.ParseError as e:
            raise ValueError(f"Błąd parsowania XML: {e}")

        root = tree.getroot()

        body_html = self.xml_to_html_tree(root)

        html_doc = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Podgląd JPK</title>

<style>

body {{
    font-family: Consolas, monospace;
    font-size: 10pt;
    margin: 20px;
}}

@media print {{
    body {{
        margin: 10mm;
    }}
}}

</style>

</head>

<body>

<h2>Podgląd JPK</h2>

<div>
{body_html}
</div>

</body>
</html>
"""

        with open(self.html_path, "w", encoding="utf-8") as f:
            f.write(html_doc)

        return self.html_path


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Użycie: python jpk2html.py <plik.xml>")
        sys.exit(1)

    xml_file = sys.argv[1]

    converter = JPK2HTML(xml_file)

    out = converter.convert()

    print("Gotowe! Utworzono plik HTML:")
    print(out)