import os
import glob
from datetime import datetime, timedelta

from KSeF2JPK.parser.ksef_parser import KSeFParser
from KSeF2JPK.mapper.jpk_mapper import JPKMapperPRO
from KSeF2JPK.builder.jpk_builder import JPKBuilderPROPlus
from KSeF2JPK.generator.jpk_generator import JPKGeneratorPRO
from KSeF2JPK.adapter.jpk_adapter import dict_to_jpk_model
from KSeF2JPK.validator.validate_jpk import validate_jpk

PROD_DIR = "prod_data"

def poprzedni_miesiac():
    dzis = datetime.today()
    pierwszy = dzis.replace(day=1)
    ostatni = pierwszy - timedelta(days=1)
    return ostatni.strftime("%Y-%m")

pop_mies = poprzedni_miesiac()
print(f"Filtruję faktury z miesiąca: {pop_mies}")

parser = KSeFParser()
paths = glob.glob(os.path.join(PROD_DIR, "*.xml"))

wszystkie = [parser.parse(p) for p in paths]

faktury = []
for f in wszystkie:
    typ = f.meta.get("typ")
    if typ == "sprzedaz":
        if f.meta.get("data_sprzedazy", "").startswith(pop_mies):
            faktury.append(f)
    elif typ == "zakup":
        data = f.meta.get("data_wplywu") or f.meta.get("data_wystawienia", "")
        if data.startswith(pop_mies):
            faktury.append(f)

print(f"Znaleziono {len(faktury)} faktur produkcyjnych.")

mapper = JPKMapperPRO()
models = [mapper.map(f) for f in faktury]

rok, mies = pop_mies.split("-")
builder = JPKBuilderPROPlus(
    rok=int(rok),
    miesiac=int(mies),
    podmiot={"nip": "6791444505", "nazwa": "DARIUSZ POLZER"}
)

jpk_dict = builder.build_from_models(models)
jpk = dict_to_jpk_model(jpk_dict)

generator = JPKGeneratorPRO()
generator.generate(jpk, "wynik_prod_jpk.xml")

print("Wygenerowano: wynik_prod_jpk.xml")

validate_jpk(
    "wynik_prod_jpk.xml",
    r"validator/xsd/JPK_V7M_3.xsd"
)
