from calendar import monthrange
from datetime import datetime
from typing import Any

from ksef2jpk.model.jpk_model import WierszEwidencji


class JPKBuilderPROPlus:
    def __init__(self, rok: int, miesiac: int, podmiot: dict[str, Any]):
        self.rok = rok
        self.miesiac = miesiac
        self.podmiot = podmiot

    def _round_pln(self, value: float) -> int:
        return int(round(float(value or 0)))

    def build(
        self,
        sprzedaz: list[WierszEwidencji],
        zakupy: list[WierszEwidencji],
    ) -> dict[str, Any]:
        pierwszy = f"{self.rok}-{self.miesiac:02d}-01"
        ostatni_dzien = monthrange(self.rok, self.miesiac)[1]
        ostatni = f"{self.rok}-{self.miesiac:02d}-{ostatni_dzien:02d}"

        deklaracja = self.mapuj_deklaracje_PRO_PLUS(sprzedaz, zakupy)
        ewidencja = self.buduj_ewidencje(sprzedaz, zakupy)

        return {
            "Naglowek": {
                "KodFormularza": "JPK_V7M",
                "WariantFormularza": "3",
                "CelZlozenia": "1",
                "DataWytworzeniaJPK": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                "Rok": self.rok,
                "Miesiac": f"{self.miesiac:02d}",
                "KodUrzedu": self.podmiot.get("kod_urzedu", "1214"),
                "DataOd": pierwszy,
                "DataDo": ostatni,
            },
            "Podmiot1": {
                "NIP": self.podmiot["nip"],
                "Nazwa": self.podmiot["nazwa"],
                "PelnaNazwa": self.podmiot["nazwa"],
                "Email": self.podmiot.get("email", "biuro@example.com"),
                "Telefon": self.podmiot.get("telefon", "123456789"),
                "DataUrodzenia": self.podmiot.get("data_urodzenia", "1980-01-01"),
            },
            "Deklaracja": {"PozycjeSzczegolowe": deklaracja},
            "Ewidencja": ewidencja,
        }

    def mapuj_deklaracje_PRO_PLUS(
        self,
        sprzedaz: list[WierszEwidencji],
        zakupy: list[WierszEwidencji],
    ) -> dict[str, int | None]:
        d = {
            "P_10": 0.0,
            "P_11": 0.0,
            "P_12": 0.0,
            "P_13": 0.0,
            "P_14": 0.0,
            "P_15": 0.0,
            "P_16": 0.0,
            "P_17": 0.0,
            "P_18": 0.0,
            "P_19": 0.0,
            "P_20": 0.0,
            "P_21": 0.0,
            "P_22": 0.0,
            "P_23": 0.0,
            "P_24": 0.0,
            "P_25": 0.0,
            "P_26": 0.0,
            "P_27": 0.0,
            "P_28": 0.0,
            "P_29": 0.0,
            "P_30": 0.0,
            "P_31": 0.0,
            "P_32": 0.0,
            "P_33": 0.0,
            "P_34": 0.0,
            "P_35": 0.0,
            "P_36": 0.0,
            "P_37": 0,
            "P_38": 0,
            "P_39": 0,
            "P_40": 0.0,
            "P_41": 0.0,
            "P_42": 0.0,
            "P_43": 0.0,
            "P_44": 0.0,
            "P_45": 0.0,
            "P_46": 0.0,
            "P_47": 0.0,
            "P_48": 0,
            "P_49": 0,
            "P_50": 0,
            "P_51": 0,
            "P_52": 0,
            "P_53": 0,
            "P_54": None,
            "P_55": None,
            "P_56": None,
            "P_57": None,
            "P_58": None,
            "P_59": None,
            "P_60": 0,
            "P_61": None,
            "P_62": 0,
            "P_63": None,
            "P_64": None,
            "P_65": None,
            "P_66": None,
            "P_67": None,
            "P_68": 0,
            "P_69": 0,
            "P_ORDZU": None,
        }

        for w in sprzedaz:
            stawka = w.stawka
            netto = float(w.netto or 0)
            vat = float(w.vat or 0)
            procedury = set(w.procedury or [])

            if stawka == 23:
                d["P_19"] += netto
                d["P_20"] += vat
            elif stawka == 8:
                d["P_21"] += netto
                d["P_22"] += vat
            elif stawka == 5:
                d["P_23"] += netto
                d["P_24"] += vat
            elif stawka == 0 and "WDT" not in procedury and "EXP" not in procedury:
                d["P_27"] += netto

            if "WDT" in procedury:
                d["P_25"] += netto
            if "EXP" in procedury:
                d["P_29"] += netto
            if "OO" in procedury:
                d["P_31"] += netto
            if "OO" not in procedury and (stawka is None or "ZW" in procedury or "NP" in procedury):
                d["P_35"] += netto

        for w in zakupy:
            netto = float(w.netto or 0)
            vat = float(w.vat or 0)
            procedury = set(w.procedury or [])

            if "IMP" in procedury:
                d["P_45"] += netto
            elif vat:
                d["P_42"] += netto
                d["P_43"] += vat

        base_amount_fields = [
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
            "P_40",
            "P_41",
            "P_42",
            "P_43",
            "P_44",
            "P_45",
            "P_46",
            "P_47",
        ]

        for field in base_amount_fields:
            d[field] = self._round_pln(d[field])

        d["P_37"] = d["P_19"] + d["P_21"] + d["P_23"] + d["P_25"] + d["P_27"] + d["P_29"] + d["P_31"]
        d["P_38"] = d["P_20"] + d["P_22"] + d["P_24"]
        d["P_48"] = d["P_43"]
        d["P_51"] = max(d["P_38"] - d["P_48"], 0)

        return d

    def buduj_ewidencje(
        self,
        sprzedaz: list[WierszEwidencji],
        zakupy: list[WierszEwidencji],
    ) -> dict[str, Any]:
        sprzedaz_wiersze = []

        for lp, w in enumerate(sprzedaz, start=1):
            self._validate_sales_row(w)

            row = {
                "LpSprzedazy": lp,
                "NrKontrahenta": w.kontrahent_nip,
                "NazwaKontrahenta": w.kontrahent_nazwa,
                "DowodSprzedazy": w.dokument,
                "DataWystawienia": w.data_wystawienia,
                "DataSprzedazy": w.data_sprzedazy,
            }

            if w.nr_ksef:
                row["NrKSeF"] = w.nr_ksef
            else:
                row["OFF"] = "1"

            row.update(
                {
                    "K_19": w.netto if w.stawka == 23 else 0,
                    "K_20": w.vat if w.stawka == 23 else 0,
                    "K_21": w.netto if w.stawka == 8 else 0,
                    "K_22": w.vat if w.stawka == 8 else 0,
                    "K_23": w.netto if w.stawka == 5 else 0,
                    "K_24": w.vat if w.stawka == 5 else 0,
                    "K_27": w.netto if w.stawka == 0 else 0,
                    "K_28": 0,
                }
            )

            if w.gtu:
                row["GTU"] = w.gtu

            procedury = set(w.procedury or [])
            if "WDT" in procedury:
                row["WDT"] = "1"
            if "EXP" in procedury:
                row["Eksport"] = "1"
            if "OO" in procedury:
                row["OO"] = "1"
            if "MPP" in procedury:
                row["MPP"] = "1"
            if "MARZA" in procedury:
                row["Marza"] = "1"
            if "SW" in procedury:
                row["SW"] = "1"
            if "EE" in procedury:
                row["EE"] = "1"
            if "TP" in procedury:
                row["TP"] = "1"

            sprzedaz_wiersze.append(row)

        zakup_wiersze = []

        for lp, w in enumerate(zakupy, start=1):
            self._validate_purchase_row(w)

            row = {
                "LpZakupu": lp,
                "NrDostawcy": w.kontrahent_nip,
                "NazwaDostawcy": w.kontrahent_nazwa,
                "DowodZakupu": w.dokument,
                "DataZakupu": w.data_wystawienia,
                "DataWplywu": w.data_wplywu or w.data_wystawienia,
            }

            if w.nr_ksef:
                row["NrKSeF"] = w.nr_ksef
            else:
                row["OFF"] = "1"

            procedury = set(w.procedury or [])

            is_imp = "IMP" in procedury

            row.update(
                {
                    "K_42": 0 if is_imp else (w.netto if w.vat else 0),
                    "K_43": 0 if is_imp else (w.vat if w.vat else 0),
                    "K_44": 0,
                    "K_45": w.netto if is_imp else 0,
                    "K_46": w.vat if is_imp else 0,
                    "K_47": 0,
                }
            )
            if "IMP" in procedury:
                row["IMP"] = "1"
            if "MPP" in procedury:
                row["MPP"] = "1"
            if "OO" in procedury:
                row["OO"] = "1"
            if "VAT_RR" in procedury:
                row["VAT_RR"] = "1"

            zakup_wiersze.append(row)

        sprzedaz_ctrl = {
            "LiczbaWierszySprzedazy": len(sprzedaz_wiersze),
            "PodatekNalezny": round(
                sum(
                    float(w.get("K_20", 0))
                    + float(w.get("K_22", 0))
                    + float(w.get("K_24", 0))
                    + float(w.get("K_28", 0))
                    for w in sprzedaz_wiersze
                ),
                2,
            ),
        }

        zakup_ctrl = {
            "LiczbaWierszyZakupow": len(zakup_wiersze),
            "PodatekNaliczony": round(
                sum(
                    float(w.get("K_43", 0))
                    + float(w.get("K_45", 0))
                    + float(w.get("K_46", 0))
                    + float(w.get("K_47", 0))
                    for w in zakup_wiersze
                ),
                2,
            ),
        }

        return {
            "SprzedazWiersz": sprzedaz_wiersze,
            "SprzedazCtrl": sprzedaz_ctrl,
            "ZakupWiersz": zakup_wiersze,
            "ZakupCtrl": zakup_ctrl,
        }

    def _validate_sales_row(self, w: WierszEwidencji) -> None:
        if not (w.kontrahent_nip or "").strip():
            raise ValueError(f"Brak NrKontrahenta dla dokumentu sprzedaży: {w.dokument}")
        if not (w.kontrahent_nazwa or "").strip():
            raise ValueError(f"Brak NazwaKontrahenta dla dokumentu sprzedaży: {w.dokument}")
        if not (w.data_wystawienia or "").strip():
            raise ValueError(f"Brak DataWystawienia dla dokumentu sprzedaży: {w.dokument}")
        if not (w.data_sprzedazy or "").strip():
            raise ValueError(f"Brak DataSprzedazy dla dokumentu sprzedaży: {w.dokument}")

    def _validate_purchase_row(self, w: WierszEwidencji) -> None:
        if not (w.kontrahent_nip or "").strip():
            raise ValueError(f"Brak NrDostawcy dla dokumentu zakupu: {w.dokument}")
        if not (w.kontrahent_nazwa or "").strip():
            raise ValueError(f"Brak NazwaDostawcy dla dokumentu zakupu: {w.dokument}")
        if not (w.data_wystawienia or "").strip():
            raise ValueError(f"Brak DataZakupu/DataWystawienia dla dokumentu zakupu: {w.dokument}")
