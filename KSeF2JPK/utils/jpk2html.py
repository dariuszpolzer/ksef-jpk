import os
import sys
from html import escape

from defusedxml import ElementTree as ET

TAG_COLOR = "#D0D0D0"


def localname(tag):
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


class JPK2HTML:
    def __init__(self, xml_path: str, output_dir: str | None = None):
        self.xml_path = xml_path

        if output_dir is None:
            output_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(xml_path))),
                "HTML",
            )

        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

        base = os.path.splitext(os.path.basename(xml_path))[0]
        self.html_path = os.path.join(self.output_dir, base + ".html")

        self.output_dir = os.path.abspath(output_dir)
        os.makedirs(self.output_dir, exist_ok=True)

        base = os.path.splitext(os.path.basename(xml_path))[0]
        self.html_path = os.path.join(self.output_dir, base + ".html")

    def xml_to_html_tree(self, elem, indent=0):

        pad = "&nbsp;&nbsp;&nbsp;&nbsp;" * indent
        html_parts = []

        name = localname(elem.tag)

        html_parts.append(f'{pad}<span style="color:{TAG_COLOR};">&lt;{escape(name)}</span>')

        if elem.attrib:
            for k, v in elem.attrib.items():
                html_parts.append(f' <span style="font-weight:bold;">{escape(k)}="{escape(v)}"</span>')

        html_parts.append(f'<span style="color:{TAG_COLOR};">&gt;</span>')

        text = (elem.text or "").strip()

        if text:
            html_parts.append(f' <span style="font-weight:bold;">{escape(text)}</span>')

        children = list(elem)

        if children:

            html_parts.append("<br>")

            for child in children:
                html_parts.append(self.xml_to_html_tree(child, indent + 1))

            html_parts.append(f'{pad}<span style="color:{TAG_COLOR};">&lt;/{escape(name)}&gt;</span><br>')

        else:

            html_parts.append(f'<span style="color:{TAG_COLOR};">&lt;/{escape(name)}&gt;</span><br>')

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
