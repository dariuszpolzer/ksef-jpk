import xml.etree.ElementTree as ET  # nosec B405
from xml.dom import minidom  # nosec B408


class JPKGeneratorPRO:
    NS = {
        "jpk": "http://crd.gov.pl/wzor/2025/12/19/14090/",
        "etd": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/09/13/eD/DefinicjeTypy/",
        "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    }

    def fmt(self, v):
        if v is None:
            return "0"
        try:
            return f"{float(v):.2f}".rstrip("0").rstrip(".")
        except (TypeError, ValueError):
            return "0"

    def is_zeroish(self, v):
        if v is None:
            return True
        try:
            return float(v) == 0.0
        except (TypeError, ValueError):
            return False

    def add_if_nonzero(self, parent, ns, name, value):
        if not self.is_zeroish(value):
            ET.SubElement(parent, f"{{{ns}}}{name}").text = self.fmt(value)

    def add_if_present(self, parent, ns, name, value):
        if value is None:
            return
        if isinstance(value, str) and not value.strip():
            return
        ET.SubElement(parent, f"{{{ns}}}{name}").text = str(value)

    def add_gtu_flag(self, parent, ns, gtu_value):
        """
        GTU w JPK_V7 występuje jako osobny tag, np.:
        <GTU_06>1</GTU_06>
        a nie jako:
        <GTU>GTU_06</GTU>
        """
        if not gtu_value:
            return

        gtu_value = str(gtu_value).strip()
        if not gtu_value:
            return

        ET.SubElement(parent, f"{{{ns}}}{gtu_value}").text = "1"

    def _split_name(self, full_name: str):
        full_name = (full_name or "").strip()
        if not full_name:
            return "", ""
        parts = full_name.split()
        if len(parts) == 1:
            return parts[0], ""
        return parts[0], " ".join(parts[1:])

    def generate(self, jpk_model, output_path):
        ns_jpk = self.NS["jpk"]
        ns_etd = self.NS["etd"]
        ns_xsi = self.NS["xsi"]

        ET.register_namespace("", ns_jpk)
        ET.register_namespace("etd", ns_etd)
        ET.register_namespace("xsi", ns_xsi)

        # ----------------------------------------------------
        # ROOT
        # ----------------------------------------------------
        root = ET.Element(f"{{{ns_jpk}}}JPK", {f"{{{ns_xsi}}}schemaLocation": f"{ns_jpk} {ns_jpk}schemat.xsd"})

        # ----------------------------------------------------
        # 1. NAGŁÓWEK
        # ----------------------------------------------------
        nag = ET.SubElement(root, f"{{{ns_jpk}}}Naglowek")

        ET.SubElement(
            nag,
            f"{{{ns_jpk}}}KodFormularza",
            kodSystemowy="JPK_V7M (3)",
            wersjaSchemy="1-0E",
        ).text = "JPK_VAT"

        ET.SubElement(nag, f"{{{ns_jpk}}}WariantFormularza").text = "3"
        ET.SubElement(nag, f"{{{ns_jpk}}}DataWytworzeniaJPK").text = jpk_model.data_wytworzenia
        ET.SubElement(nag, f"{{{ns_jpk}}}CelZlozenia", poz="P_7").text = "1"
        ET.SubElement(nag, f"{{{ns_jpk}}}KodUrzedu").text = jpk_model.kod_urzedu
        ET.SubElement(nag, f"{{{ns_jpk}}}Rok").text = jpk_model.data_od[:4]
        ET.SubElement(nag, f"{{{ns_jpk}}}Miesiac").text = jpk_model.data_od[5:7]

        # ----------------------------------------------------
        # 2. PODMIOT1 – OSOBA FIZYCZNA
        # ----------------------------------------------------
        pod = ET.SubElement(root, f"{{{ns_jpk}}}Podmiot1", rola="Podatnik")
        osf = ET.SubElement(pod, f"{{{ns_jpk}}}OsobaFizyczna")

        ET.SubElement(osf, f"{{{ns_etd}}}NIP").text = jpk_model.nip
        imie, nazwisko = self._split_name(jpk_model.nazwa)
        ET.SubElement(osf, f"{{{ns_etd}}}ImiePierwsze").text = imie
        ET.SubElement(osf, f"{{{ns_etd}}}Nazwisko").text = nazwisko
        ET.SubElement(osf, f"{{{ns_etd}}}DataUrodzenia").text = jpk_model.data_urodzenia

        ET.SubElement(osf, f"{{{ns_jpk}}}Email").text = jpk_model.email
        ET.SubElement(osf, f"{{{ns_jpk}}}Telefon").text = jpk_model.telefon

        # ----------------------------------------------------
        # 3. DEKLARACJA – VAT-7(23)
        # ----------------------------------------------------
        dek = ET.SubElement(root, f"{{{ns_jpk}}}Deklaracja")

        dek_nag = ET.SubElement(dek, f"{{{ns_jpk}}}Naglowek")
        ET.SubElement(
            dek_nag,
            f"{{{ns_jpk}}}KodFormularzaDekl",
            kodSystemowy="VAT-7 (23)",
            kodPodatku="VAT",
            rodzajZobowiazania="Z",
            wersjaSchemy="1-0E",
        ).text = "VAT-7"
        ET.SubElement(dek_nag, f"{{{ns_jpk}}}WariantFormularzaDekl").text = "23"

        poz = ET.SubElement(dek, f"{{{ns_jpk}}}PozycjeSzczegolowe")

        required_zero_fields = {"P_38", "P_51"}

        for pole in [
            "P_10",
            "P_11",
            "P_12",
            "P_13",
            "P_14",
            "P_15",
            "P_16",
            "P_17",
            "P_18",
            "P_19",
            "P_20",
            "P_21",
            "P_22",
            "P_23",
            "P_24",
            "P_25",
            "P_26",
            "P_27",
            "P_28",
            "P_29",
            "P_30",
            "P_31",
            "P_32",
            "P_33",
            "P_34",
            "P_35",
            "P_36",
            "P_37",
            "P_38",
            "P_39",
            "P_40",
            "P_41",
            "P_42",
            "P_43",
            "P_44",
            "P_45",
            "P_46",
            "P_47",
            "P_48",
            "P_49",
            "P_50",
            "P_51",
            "P_52",
            "P_53",
            "P_54",
            "P_55",
            "P_56",
            "P_57",
            "P_58",
            "P_59",
            "P_60",
            "P_61",
            "P_62",
            "P_63",
            "P_64",
            "P_65",
            "P_66",
            "P_67",
            "P_68",
            "P_69",
            "P_ORDZU",
        ]:
            val = getattr(jpk_model.deklaracja, pole, None)

            if pole == "P_26" and not self.is_zeroish(getattr(jpk_model.deklaracja, "P_25", 0)):
                ET.SubElement(poz, f"{{{ns_jpk}}}{pole}").text = "0"
                continue

            if pole == "P_30" and not self.is_zeroish(getattr(jpk_model.deklaracja, "P_29", 0)):
                ET.SubElement(poz, f"{{{ns_jpk}}}{pole}").text = "0"
                continue

            if pole == "P_32" and not self.is_zeroish(getattr(jpk_model.deklaracja, "P_31", 0)):
                ET.SubElement(poz, f"{{{ns_jpk}}}{pole}").text = "0"
                continue

            if pole in required_zero_fields:
                if val is None:
                    val = 0
                ET.SubElement(poz, f"{{{ns_jpk}}}{pole}").text = self.fmt(val)
                continue

            if isinstance(val, str):
                self.add_if_present(poz, ns_jpk, pole, val)
            else:
                self.add_if_nonzero(poz, ns_jpk, pole, val)

        ET.SubElement(dek, f"{{{ns_jpk}}}Pouczenia").text = "1"

        # ----------------------------------------------------
        # 4. EWIDENCJA
        # ----------------------------------------------------
        has_sprzedaz = bool(jpk_model.sprzedaz_wiersz)
        has_zakup = bool(jpk_model.zakup_wiersz)

        if has_sprzedaz or has_zakup:
            ewid = ET.SubElement(root, f"{{{ns_jpk}}}Ewidencja")
        else:
            ewid = None

        # ----------------------------------------------------
        # SPRZEDAŻ – WIERSZE
        # ----------------------------------------------------
        if ewid is not None and has_sprzedaz:
            for w in jpk_model.sprzedaz_wiersz:
                sw = ET.SubElement(ewid, f"{{{ns_jpk}}}SprzedazWiersz")

                ET.SubElement(sw, f"{{{ns_jpk}}}LpSprzedazy").text = str(w.LpSprzedazy)
                ET.SubElement(sw, f"{{{ns_jpk}}}KodKrajuNadaniaTIN").text = (
                    getattr(w, "KodKrajuNadaniaTIN", "PL") or "PL"
                )
                ET.SubElement(sw, f"{{{ns_jpk}}}NrKontrahenta").text = w.NrKontrahenta
                ET.SubElement(sw, f"{{{ns_jpk}}}NazwaKontrahenta").text = w.NazwaKontrahenta
                ET.SubElement(sw, f"{{{ns_jpk}}}DowodSprzedazy").text = w.DowodSprzedazy
                ET.SubElement(sw, f"{{{ns_jpk}}}DataWystawienia").text = w.DataWystawienia
                ET.SubElement(sw, f"{{{ns_jpk}}}DataSprzedazy").text = w.DataSprzedazy

                if getattr(w, "NrKSeF", ""):
                    ET.SubElement(sw, f"{{{ns_jpk}}}NrKSeF").text = w.NrKSeF
                else:
                    if getattr(w, "OFF", None):
                        ET.SubElement(sw, f"{{{ns_jpk}}}OFF").text = str(w.OFF)
                    elif getattr(w, "BFK", None):
                        ET.SubElement(sw, f"{{{ns_jpk}}}BFK").text = str(w.BFK)
                    elif getattr(w, "DI", None):
                        ET.SubElement(sw, f"{{{ns_jpk}}}DI").text = str(w.DI)
                    else:
                        ET.SubElement(sw, f"{{{ns_jpk}}}OFF").text = "1"

                # GTU tylko w sprzedaży i jako GTU_XX=1
                self.add_gtu_flag(sw, ns_jpk, getattr(w, "GTU", None))

                # procedury / oznaczenia
                # self.add_if_present(sw, ns_jpk, "WDT", getattr(w, "WDT", None))
                # self.add_if_present(sw, ns_jpk, "Eksport", getattr(w, "Eksport", None))
                # self.add_if_present(sw, ns_jpk, "OO", getattr(w, "OO", None))
                # self.add_if_present(sw, ns_jpk, "MPP", getattr(w, "MPP", None))
                self.add_if_present(sw, ns_jpk, "Marza", getattr(w, "Marza", None))
                self.add_if_present(sw, ns_jpk, "SW", getattr(w, "SW", None))
                self.add_if_present(sw, ns_jpk, "EE", getattr(w, "EE", None))
                self.add_if_present(sw, ns_jpk, "TP", getattr(w, "TP", None))

                self.add_if_nonzero(sw, ns_jpk, "K_19", getattr(w, "K_19", 0))
                self.add_if_nonzero(sw, ns_jpk, "K_20", getattr(w, "K_20", 0))
                self.add_if_nonzero(sw, ns_jpk, "K_21", getattr(w, "K_21", 0))
                self.add_if_nonzero(sw, ns_jpk, "K_22", getattr(w, "K_22", 0))
                self.add_if_nonzero(sw, ns_jpk, "K_23", getattr(w, "K_23", 0))
                self.add_if_nonzero(sw, ns_jpk, "K_24", getattr(w, "K_24", 0))
                self.add_if_nonzero(sw, ns_jpk, "K_27", getattr(w, "K_27", 0))

                if getattr(w, "WDT", None) or getattr(w, "Eksport", None):
                    ET.SubElement(sw, f"{{{ns_jpk}}}K_28").text = "0"
                else:
                    self.add_if_nonzero(sw, ns_jpk, "K_28", getattr(w, "K_28", 0))

        # ----------------------------------------------------
        # SPRZEDAŻ CTRL
        # ----------------------------------------------------
        if ewid is not None:
            liczba_wierszy = len(jpk_model.sprzedaz_wiersz)
            podatek_nalezny = 0.0
            for w in jpk_model.sprzedaz_wiersz:
                podatek_nalezny += float(getattr(w, "K_20", 0) or 0)
                podatek_nalezny += float(getattr(w, "K_22", 0) or 0)
                podatek_nalezny += float(getattr(w, "K_24", 0) or 0)
                podatek_nalezny += float(getattr(w, "K_28", 0) or 0)

            sc = ET.SubElement(ewid, f"{{{ns_jpk}}}SprzedazCtrl")
            ET.SubElement(sc, f"{{{ns_jpk}}}LiczbaWierszySprzedazy").text = str(liczba_wierszy)
            ET.SubElement(sc, f"{{{ns_jpk}}}PodatekNalezny").text = self.fmt(podatek_nalezny)

        # ----------------------------------------------------
        # ZAKUP – WIERSZE
        # ----------------------------------------------------
        if ewid is not None and has_zakup:
            for w in jpk_model.zakup_wiersz:
                zw = ET.SubElement(ewid, f"{{{ns_jpk}}}ZakupWiersz")

                ET.SubElement(zw, f"{{{ns_jpk}}}LpZakupu").text = str(w.LpZakupu)
                ET.SubElement(zw, f"{{{ns_jpk}}}KodKrajuNadaniaTIN").text = (
                    getattr(w, "KodKrajuNadaniaTIN", "PL") or "PL"
                )
                ET.SubElement(zw, f"{{{ns_jpk}}}NrDostawcy").text = w.NrDostawcy
                ET.SubElement(zw, f"{{{ns_jpk}}}NazwaDostawcy").text = w.NazwaDostawcy
                ET.SubElement(zw, f"{{{ns_jpk}}}DowodZakupu").text = w.DowodZakupu

                data_zakupu = w.DataZakupu or w.DataWplywu or "2026-01-01"
                ET.SubElement(zw, f"{{{ns_jpk}}}DataZakupu").text = data_zakupu

                data_wplywu = w.DataWplywu or data_zakupu
                ET.SubElement(zw, f"{{{ns_jpk}}}DataWplywu").text = data_wplywu

                if getattr(w, "NrKSeF", ""):
                    ET.SubElement(zw, f"{{{ns_jpk}}}NrKSeF").text = w.NrKSeF
                else:
                    if getattr(w, "OFF", None):
                        ET.SubElement(zw, f"{{{ns_jpk}}}OFF").text = str(w.OFF)
                    elif getattr(w, "BFK", None):
                        ET.SubElement(zw, f"{{{ns_jpk}}}BFK").text = str(w.BFK)
                    elif getattr(w, "DI", None):
                        ET.SubElement(zw, f"{{{ns_jpk}}}DI").text = str(w.DI)
                    else:
                        ET.SubElement(zw, f"{{{ns_jpk}}}OFF").text = "1"

                # UWAGA: GTU nie emitujemy w zakupach
                self.add_if_present(zw, ns_jpk, "IMP", getattr(w, "IMP", None))
                # self.add_if_present(zw, ns_jpk, "MPP", getattr(w, "MPP", None))
                # self.add_if_present(zw, ns_jpk, "OO", getattr(w, "OO", None))
                self.add_if_present(zw, ns_jpk, "VAT_RR", getattr(w, "VAT_RR", None))

                self.add_if_nonzero(zw, ns_jpk, "K_42", getattr(w, "K_42", 0))
                self.add_if_nonzero(zw, ns_jpk, "K_43", getattr(w, "K_43", 0))
                self.add_if_nonzero(zw, ns_jpk, "K_44", getattr(w, "K_44", 0))
                self.add_if_nonzero(zw, ns_jpk, "K_45", getattr(w, "K_45", 0))
                self.add_if_nonzero(zw, ns_jpk, "K_46", getattr(w, "K_46", 0))
                self.add_if_nonzero(zw, ns_jpk, "K_47", getattr(w, "K_47", 0))

        # ----------------------------------------------------
        # ZAKUP CTRL
        # ----------------------------------------------------
        if ewid is not None:
            liczba_zakupow = len(jpk_model.zakup_wiersz)
            podatek_naliczony = 0.0
            for w in jpk_model.zakup_wiersz:
                podatek_naliczony += float(getattr(w, "K_43", 0) or 0)
                podatek_naliczony += float(getattr(w, "K_45", 0) or 0)
                podatek_naliczony += float(getattr(w, "K_47", 0) or 0)

            zc = ET.SubElement(ewid, f"{{{ns_jpk}}}ZakupCtrl")
            ET.SubElement(zc, f"{{{ns_jpk}}}LiczbaWierszyZakupow").text = str(liczba_zakupow)
            ET.SubElement(zc, f"{{{ns_jpk}}}PodatekNaliczony").text = self.fmt(podatek_naliczony)

        # ----------------------------------------------------
        # 5. ZAPIS
        # ----------------------------------------------------
        xml_str = ET.tostring(root, encoding="utf-8")
        pretty = minidom.parseString(xml_str).toprettyxml(  # nosec B318
            indent="  ",
            encoding="utf-8",
        )

        with open(output_path, "wb") as f:
            f.write(pretty)
