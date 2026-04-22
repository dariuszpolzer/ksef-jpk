from KSeF2JPK.model.faktura_model import FakturaModel
from KSeF2JPK.model.jpk_model import JPKModel
from KSeF2JPK.utils.math_tools import round2

class JPKMapper:

    def map(self, faktura: FakturaModel) -> JPKModel:
        """
        Przekształca FakturaModel w JPKModel.
        Wersja startowa – sumowanie po stawkach VAT.
        """
        jpk = JPKModel()

        # --- SUMOWANIE SPRZEDAŻY ---
        self._sumuj_sprzedaz(faktura, jpk)

        # --- SUMOWANIE ZAKUPU ---
        self._sumuj_zakup(faktura, jpk)

        # --- LICZBA WIERSZY ---
        jpk.liczba_wierszy_sprzedazy = len([p for p in faktura.pozycje if p.typ == "sprzedaz"])
        jpk.liczba_wierszy_zakupu = len([p for p in faktura.pozycje if p.typ == "zakup"])

        # --- PODATEK NALEŻNY / NALICZONY ---
        jpk.podatek_nalezny = round2(sum(jpk.k.get(k, 0) for k in ["K_19", "K_20", "K_21"]))
        jpk.podatek_naliczony = round2(sum(jpk.k.get(k, 0) for k in ["K_43", "K_44", "K_45"]))

        return jpk


    # ============================================================
    #   SUMOWANIE SPRZEDAŻY → K_10–K_36
    # ============================================================
    def _sumuj_sprzedaz(self, faktura: FakturaModel, jpk: JPKModel):

        for p in faktura.pozycje:
            if p.typ != "sprzedaz":
                continue

            stawka = p.stawka

            # --- 23% ---
            if stawka == "23":
                jpk.k["K_19"] = jpk.k.get("K_19", 0) + p.vat
                jpk.k["K_20"] = jpk.k.get("K_20", 0) + p.netto

            # --- 8% ---
            elif stawka == "8":
                jpk.k["K_21"] = jpk.k.get("K_21", 0) + p.vat
                jpk.k["K_22"] = jpk.k.get("K_22", 0) + p.netto

            # --- 5% ---
            elif stawka == "5":
                jpk.k["K_23"] = jpk.k.get("K_23", 0) + p.vat
                jpk.k["K_24"] = jpk.k.get("K_24", 0) + p.netto

            # --- 0% ---
            elif stawka == "0":
                jpk.k["K_31"] = jpk.k.get("K_31", 0) + p.netto

            # --- ZW / NP / OO ---
            elif stawka in ["ZW", "NP", "OO"]:
                jpk.k["K_33"] = jpk.k.get("K_33", 0) + p.netto

        # Zaokrąglenia
        for k in jpk.k:
            jpk.k[k] = round2(jpk.k[k])


    # ============================================================
    #   SUMOWANIE ZAKUPU → K_40–K_47
    # ============================================================
    def _sumuj_zakup(self, faktura: FakturaModel, jpk: JPKModel):

        for p in faktura.pozycje:
            if p.typ != "zakup":
                continue

            stawka = p.stawka

            # --- 23% ---
            if stawka == "23":
                jpk.k["K_43"] = jpk.k.get("K_43", 0) + p.vat
                jpk.k["K_44"] = jpk.k.get("K_44", 0) + p.netto

            # --- 8% ---
            elif stawka == "8":
                jpk.k["K_45"] = jpk.k.get("K_45", 0) + p.vat
                jpk.k["K_46"] = jpk.k.get("K_46", 0) + p.netto

            # --- 5% ---
            elif stawka == "5":
                jpk.k["K_47"] = jpk.k.get("K_47", 0) + p.vat

        # Zaokrąglenia
        for k in jpk.k:
            jpk.k[k] = round2(jpk.k[k])
