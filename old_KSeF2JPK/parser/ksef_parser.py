import xml.etree.ElementTree as ET
from model.faktura_model import FakturaModel
from model.pozycja import Pozycja
from KSeF2JPK.model.kontrahent import Kontrahent
from KSeF2JPK.utils.math_tools import safe_float

NS = {"k": "http://crd.gov.pl/wzor/2025/06/25/13775/"}


class KSeFParser:

    def parse(self, xml_path: str) -> FakturaModel:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        model = FakturaModel()

        # ============================================================
        #   USTAL TYP FAKTURY (sprzedaż / zakup)
        # ============================================================
        moj_nip = "6791444505"  # Twój NIP z konfiguracji

        nip_podmiot1 = self._get(root, ".//k:Podmiot1/k:DaneIdentyfikacyjne/k:NIP")
        nip_podmiot2 = self._get(root, ".//k:Podmiot2/k:DaneIdentyfikacyjne/k:NIP")

        if nip_podmiot1 == moj_nip:
            typ_faktury = "sprzedaz"
            kontrahent_nip = nip_podmiot2
            kontrahent_nazwa = self._get(root, ".//k:Podmiot2/k:DaneIdentyfikacyjne/k:Nazwa")
            kontrahent_kraj = self._get(root, ".//k:Podmiot2/k:Adres/k:KodKraju")
        else:
            typ_faktury = "zakup"
            kontrahent_nip = nip_podmiot1
            kontrahent_nazwa = self._get(root, ".//k:Podmiot1/k:DaneIdentyfikacyjne/k:Nazwa")
            kontrahent_kraj = self._get(root, ".//k:Podmiot1/k:Adres/k:KodKraju")

        kontrahent = Kontrahent(
            nip=kontrahent_nip,
            nazwa=kontrahent_nazwa,
            kraj=kontrahent_kraj
        )

        # ============================================================
        #   DANE FAKTURY
        # ============================================================
        data_wyst = self._get(root, ".//k:Fa/k:P_1")
        data_sprz = self._get(root, ".//k:Fa/k:P_6")
        dokument = self._get(root, ".//k:Fa/k:P_2")

        # ============================================================
        #   POZYCJE
        # ============================================================
        for w in root.findall(".//k:FaWiersz", NS):

            nazwa_poz = self._get(w, "k:P_7")
            netto = safe_float(self._get(w, "k:P_11"))
            vat_rate = self._get(w, "k:P_12")
            vat = netto * (safe_float(vat_rate) / 100)

            p = Pozycja(
                nazwa=nazwa_poz,
                typ=typ_faktury,
                netto=netto,
                vat=vat,
                stawka=vat_rate,
                dokument=dokument,
                data_wystawienia=data_wyst,
                data_sprzedazy=data_sprz,
                kontrahent=kontrahent,
            )

            model.pozycje.append(p)

        # ============================================================
        #   META
        # ============================================================
        model.meta["waluta"] = self._get(root, ".//k:Fa/k:KodWaluty")
        model.meta["data_wytworzenia"] = self._get(root, ".//k:Naglowek/k:DataWytworzeniaFa")
        model.meta["data_wystawienia"] = data_wyst
        model.meta["data_sprzedazy"] = data_sprz

        return model

    def _get(self, root, path: str) -> str:
        el = root.find(path, NS)
        return el.text.strip() if el is not None and el.text else ""
