from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass
class JPKFlags:
    mpp: bool = False
    wdt: bool = False
    eksport: bool = False
    tp: bool = False
    sw: bool = False
    ee: bool = False
    oo: bool = False
    gtu: str | None = None


class JPKFlagsClassifier:
    """
    Prosta warstwa klasyfikacji procedur/oznaczeń JPK.

    Założenia:
    - nie zgadujemy agresywnie rzeczy, których nie da się wiarygodnie
      wyprowadzić z samej faktury,
    - preferujemy reguły konserwatywne,
    - łatwo dodać kolejne reguły lub ręczne nadpisania.

    Uwaga:
    - MPP, TP, WDT, Eksport, SW, EE, OO bardzo często wymagają danych
      biznesowych spoza samego XML. Tutaj wykrywamy tylko kandydatów
      lub oczywiste przypadki.
    """

    # Prosty słownik słów kluczowych -> GTU
    # To jest wersja startowa. Docelowo można to przenieść do JSON.
    GTU_KEYWORDS = {
        "GTU_01": [
            "alkohol", "wino", "piwo", "wódka", "whisky", "napój alkoholowy"
        ],
        "GTU_02": [
            "paliwo", "benzyna", "olej napędowy", "gaz", "smar"
        ],
        "GTU_03": [
            "olej opałowy", "olej smarowy"
        ],
        "GTU_06": [
            "telefon", "smartfon", "laptop", "komputer", "tablet",
            "dysk", "ssd", "hub usb", "monitor", "drukarka", "elektronika"
        ],
        "GTU_07": [
            "pojazd", "samochód", "auto", "motocykl", "części samochodowe"
        ],
        "GTU_08": [
            "metal szlachetny", "złoto", "srebro", "platyna"
        ],
        "GTU_09": [
            "lek", "wyrób medyczny", "medyczny", "farmaceutyczny"
        ],
        "GTU_10": [
            "budynek", "lokal", "nieruchomość", "grunt", "działka"
        ],
        "GTU_11": [
            "emisja", "uprawnienia do emisji"
        ],
        "GTU_12": [
            "doradztwo", "księgowość", "rachunkowość", "prawne",
            "marketing", "reklama", "szkolenie", "transport", "spedycja",
            "magazynowanie", "telekomunikacyjne", "telekomunikacja",
            "internet", "wifi", "ochrona internetu"
        ],
        "GTU_13": [
            "transport", "spedycja", "gospodarka magazynowa"
        ],
    }

    # Słowa-klucze do prostego wsparcia procedur
    MPP_KEYWORDS = [
        "mechanizm podzielonej płatności",
        "split payment",
        "mpp",
    ]

    WDT_KEYWORDS = [
        "wdt",
        "wewnątrzwspólnotowa dostawa",
    ]

    EKSPORT_KEYWORDS = [
        "eksport",
        "export",
    ]

    SW_KEYWORDS = [
        "sprzedaż wysyłkowa",
        "sw",
    ]

    EE_KEYWORDS = [
        "świadczenie usług telekomunikacyjnych",
        "świadczenie usług nadawczych",
        "świadczenie usług elektronicznych",
        "ee",
    ]

    OO_KEYWORDS = [
        "odwrotne obciążenie",
        "reverse charge",
        "oo",
    ]

    def classify_invoice(self, faktura) -> JPKFlags:
        flags = JPKFlags()

        text_blob = self._build_text_blob(faktura)
        total_brutto = self._total_brutto(faktura)
        kontrahent_nip = self._get_counterparty_nip(faktura)
        is_foreign = self._is_probably_foreign_counterparty(kontrahent_nip)

        # GTU
        flags.gtu = self._detect_gtu(text_blob)

        # MPP:
        # Ostrożnie: z samej faktury nie da się tego rozstrzygnąć idealnie.
        # Tu: sygnał z tekstu albo wysoka kwota brutto jako kandydat.
        flags.mpp = self._detect_mpp(text_blob, total_brutto)

        # WDT / eksport
        flags.wdt = self._detect_wdt(text_blob, is_foreign)
        flags.eksport = self._detect_eksport(text_blob, is_foreign)

        # TP
        # Z samej faktury zwykle nie da się tego rozstrzygnąć.
        # Zostawiamy False, ale można nadpisać z zewnętrznej bazy kontrahentów.
        flags.tp = False

        # SW / EE
        flags.sw = self._contains_any(text_blob, self.SW_KEYWORDS)
        flags.ee = self._contains_any(text_blob, self.EE_KEYWORDS)

        # OO
        flags.oo = self._detect_oo(faktura, text_blob)

        return flags

    def apply_to_invoice(self, faktura):
        """
        Zapisuje wynik klasyfikacji do faktura.meta, żeby mapper mógł go użyć.
        """
        flags = self.classify_invoice(faktura)

        procedury = []

        if flags.mpp:
            procedury.append("MPP")
        if flags.wdt:
            procedury.append("WDT")
        if flags.eksport:
            procedury.append("EXP")
        if flags.tp:
            procedury.append("TP")
        if flags.sw:
            procedury.append("SW")
        if flags.ee:
            procedury.append("EE")
        if flags.oo:
            procedury.append("OO")

        faktura.meta["gtu"] = flags.gtu
        faktura.meta["procedury"] = procedury
        faktura.meta["flags_debug"] = {
            "mpp": flags.mpp,
            "wdt": flags.wdt,
            "eksport": flags.eksport,
            "tp": flags.tp,
            "sw": flags.sw,
            "ee": flags.ee,
            "oo": flags.oo,
            "gtu": flags.gtu,
        }

        return faktura

    def _build_text_blob(self, faktura) -> str:
        parts: list[str] = []

        for key in (
            "numer",
            "nazwa_sprzedawcy",
            "nazwa_nabywcy",
            "data_wystawienia",
            "data_sprzedazy",
        ):
            val = faktura.meta.get(key)
            if val:
                parts.append(str(val))

        for p in faktura.pozycje or []:
            if getattr(p, "nazwa", None):
                parts.append(str(p.nazwa))

        return " | ".join(parts).lower()

    def _contains_any(self, text: str, keywords: Iterable[str]) -> bool:
        return any(kw.lower() in text for kw in keywords)

    def _detect_gtu(self, text_blob: str) -> str | None:
        matches: list[str] = []

        for gtu_code, keywords in self.GTU_KEYWORDS.items():
            if self._contains_any(text_blob, keywords):
                matches.append(gtu_code)

        if len(matches) == 1:
            return matches[0]

        # Jeśli pasuje wiele, na razie nie zgadujemy.
        return None

    def _total_brutto(self, faktura) -> float:
        netto = sum((p.netto or 0) for p in (faktura.pozycje or []))
        vat = sum((p.vat or 0) for p in (faktura.pozycje or []))
        return round(netto + vat, 2)

    def _get_counterparty_nip(self, faktura) -> str:
        typ = faktura.meta.get("typ")
        if typ == "sprzedaz":
            return (faktura.meta.get("nip_nabywcy") or "").strip()
        if typ == "zakup":
            return (faktura.meta.get("nip_sprzedawcy") or "").strip()
        return ""

    def _is_probably_foreign_counterparty(self, nip: str) -> bool:
        """
        Bardzo ostrożny heurystyczny test.
        Jeśli nie wygląda jak zwykły polski 10-cyfrowy NIP, traktujemy
        jako potencjalnie zagraniczny identyfikator.
        """
        nip_clean = "".join(ch for ch in nip if ch.isalnum())
        return not (nip_clean.isdigit() and len(nip_clean) == 10)

    def _detect_mpp(self, text_blob: str, total_brutto: float) -> bool:
        # Sygnał z opisu
        if self._contains_any(text_blob, self.MPP_KEYWORDS):
            return True

        # Bardzo ostrożny kandydat:
        # sama kwota > 15000 nie przesądza obowiązkowego MPP,
        # ale może być przydatna jako startowa reguła robocza.
        if total_brutto > 15000:
            return True

        return False

    def _detect_wdt(self, text_blob: str, is_foreign: bool) -> bool:
        if self._contains_any(text_blob, self.WDT_KEYWORDS):
            return True

        # Startowy heurystyczny kandydat:
        # zagraniczny kontrahent + frazy sugerujące dostawę UE
        if is_foreign and ("wewnątrzwspólnot" in text_blob or "unia europejska" in text_blob):
            return True

        return False

    def _detect_eksport(self, text_blob: str, is_foreign: bool) -> bool:
        if self._contains_any(text_blob, self.EKSPORT_KEYWORDS):
            return True

        # Ostrożny heurystyczny kandydat
        if is_foreign and "eksport" in text_blob:
            return True

        return False

    def _detect_oo(self, faktura, text_blob: str) -> bool:
        if self._contains_any(text_blob, self.OO_KEYWORDS):
            return True

        for p in faktura.pozycje or []:
            for proc in (p.procedury or []):
                if str(proc).upper() == "OO":
                    return True

        return False