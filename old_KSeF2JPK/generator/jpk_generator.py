import xml.etree.ElementTree as ET
from KSeF2JPK.model.jpk_model import JPKModel
from KSeF2JPK.utils.namespace_loader import load_namespaces

CONFIG_PATH = r"C:\Users\dpolz\Documents\projekty_config.xml"


class JPKGenerator:

    # =====================================================================
    #   ŁADOWANIE KONFIGURACJI
    # =====================================================================
    def _load_config_into_meta(self, jpk: JPKModel):
        tree = ET.parse(CONFIG_PATH)
        root = tree.getroot()

        konf = root.find(".//Konfiguracja[@nazwa='JPK']")
        if konf is None:
            raise Exception("Brak sekcji Konfiguracja nazwa='JPK' w pliku konfiguracyjnym.")

        # --- Nagłówek JPK ---
        nag = konf.find("Naglowek")
        if nag is not None:
            jpk.meta["kod_formularza"] = nag.findtext("KodFormularza", default="JPK_V7M")
            jpk.meta["wariant"] = nag.findtext("WariantFormularza", default="3")
            jpk.meta["kod_urzedu"] = nag.findtext("KodUrzedu", default="1234")

        # --- Dane podatnika ---
        dane = konf.find("DaneIdentyfikacyjne")
        if dane is not None:
            jpk.meta["nip_podatnika"] = dane.findtext("NIP", "")
            jpk.meta["nazwa_podatnika"] = dane.findtext("PelnaNazwa", "")

        # --- Namespace’y ---
        ns = konf.find("PrzestrzenieNazw")
        if ns is not None:
            wartosci = ns.find("WARTOSC")
            atrybuty = ns.find("ATRYBUT")

            ns_dict = {}
            if wartosci is not None and atrybuty is not None:
                wart = [el.text.strip() if el.text else "" for el in wartosci]
                atr = [el.text.strip() if el.text else "" for el in atrybuty]
                for key, val in zip(atr, wart):
                    if key and val:
                        ns_dict[key] = val

            jpk.meta["przestrzenie_nazw"] = ns_dict

    # =====================================================================
    #   GENEROWANIE JPK
    # =====================================================================
    def generate_xml(self, jpk: JPKModel, output_path: str):

        # 1) Wczytaj konfigurację
        self._load_config_into_meta(jpk)

        # 2) Namespace’y
        attrs = load_namespaces(jpk.meta.get("przestrzenie_nazw", {}))
        root = ET.Element("JPK", attrs)

        # ============================================================
        #   NAGŁÓWEK
        # ============================================================
        naglowek = ET.SubElement(root, "Naglowek")

        kod_form = ET.SubElement(naglowek, "KodFormularza")
        kod_form.text = "JPK_V7M"
        kod_form.set("kodSystemowy", "JPK_V7M (3)")
        kod_form.set("wersjaSchemy", "1-0")

        ET.SubElement(naglowek, "WariantFormularza").text = str(jpk.meta.get("wariant", "3"))
        ET.SubElement(naglowek, "CelZlozenia").text = "0"

        ET.SubElement(naglowek, "Rok").text = "2026"
        ET.SubElement(naglowek, "Miesiac").text = "4"
        ET.SubElement(naglowek, "KodUrzedu").text = str(jpk.meta.get("kod_urzedu"))

        # ============================================================
        #   DEKLARACJA (minimalna)
        # ============================================================
        deklaracja = ET.SubElement(root, "Deklaracja")
        ET.SubElement(deklaracja, "NaglowekDeklaracji")
        ET.SubElement(deklaracja, "PozycjeSzczegolowe")

        # ============================================================
        #   EWIDENCJA
        # ============================================================
        ewid = ET.SubElement(root, "Ewidencja")

        self._add_sprzedaz(ewid, jpk)
        self._add_zakup(ewid, jpk)

        # ============================================================
        #   ZAPIS
        # ============================================================
        tree = ET.ElementTree(root)
        tree.write(output_path, encoding="utf-8", xml_declaration=True)

    # =====================================================================
    #   SPRZEDAŻ
    # =====================================================================
    def _add_sprzedaz(self, ewid, jpk: JPKModel):

        for w in jpk.sprzedaz_wiersz:
            sw = ET.SubElement(ewid, "SprzedazWiersz")

            ET.SubElement(sw, "KodKrajuNadaniaTIN").text = w.KodKrajuNadaniaTIN
            ET.SubElement(sw, "NrKontrahenta").text = w.NrKontrahenta
            ET.SubElement(sw, "NazwaKontrahenta").text = w.NazwaKontrahenta

            ET.SubElement(sw, "DataWystawienia").text = w.DataWystawienia
            ET.SubElement(sw, "DataSprzedazy").text = w.DataSprzedazy

            ET.SubElement(sw, "K_10").text = str(w.K_10)
            ET.SubElement(sw, "K_11").text = str(w.K_11)

            # GTU
            for g in getattr(w, "GTU", []):
                ET.SubElement(sw, g).text = "1"

        # kontrola sprzedaży
        if jpk.sprzedaz_ctrl:
            ctrl = ET.SubElement(ewid, "SprzedazCtrl")
            ET.SubElement(ctrl, "LiczbaWierszySprzedazy").text = str(jpk.sprzedaz_ctrl.LiczbaWierszySprzedazy)
            ET.SubElement(ctrl, "PodatekNalezny").text = str(jpk.sprzedaz_ctrl.PodatekNalezny)

    # =====================================================================
    #   ZAKUP
    # =====================================================================
    def _add_zakup(self, ewid, jpk: JPKModel):

        for w in jpk.zakup_wiersz:
            zw = ET.SubElement(ewid, "ZakupWiersz")

            ET.SubElement(zw, "KodKrajuNadaniaTIN").text = w.KodKrajuNadaniaTIN
            ET.SubElement(zw, "NrDostawcy").text = w.NrDostawcy
            ET.SubElement(zw, "NazwaDostawcy").text = w.NazwaDostawcy

            ET.SubElement(zw, "DataZakupu").text = w.DataZakupu
            ET.SubElement(zw, "DataWplywu").text = w.DataWplywu

            ET.SubElement(zw, "K_40").text = str(w.K_40)
            ET.SubElement(zw, "K_41").text = str(w.K_41)

        # kontrola zakupów
        if jpk.zakup_ctrl:
            ctrl = ET.SubElement(ewid, "ZakupCtrl")
            ET.SubElement(ctrl, "LiczbaWierszyZakupow").text = str(jpk.zakup_ctrl.LiczbaWierszyZakupow)
            ET.SubElement(ctrl, "PodatekNaliczony").text = str(jpk.zakup_ctrl.PodatekNaliczony)
