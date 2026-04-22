from dataclasses import dataclass, field


# ============================================================
#   SPRZEDAŻ
# ============================================================

@dataclass
class SprzedazWiersz:
    KodKrajuNadaniaTIN: str = ""
    NrKontrahenta: str = ""
    NazwaKontrahenta: str = ""
    DataWystawienia: str = ""
    DataSprzedazy: str = ""
    K_10: float = 0.0
    K_11: float = 0.0
    GTU: list = field(default_factory=list)


@dataclass
class SprzedazCtrl:
    LiczbaWierszySprzedazy: int = 0
    PodatekNalezny: float = 0.0


# ============================================================
#   ZAKUP
# ============================================================

@dataclass
class ZakupWiersz:
    KodKrajuNadaniaTIN: str = ""
    NrDostawcy: str = ""
    NazwaDostawcy: str = ""
    DataZakupu: str = ""
    DataWplywu: str = ""
    K_40: float = 0.0
    K_41: float = 0.0


@dataclass
class ZakupCtrl:
    LiczbaWierszyZakupow: int = 0
    PodatekNaliczony: float = 0.0


# ============================================================
#   MODEL JPK
# ============================================================

@dataclass
class JPKModel:
    sprzedaz_wiersz: list = field(default_factory=list)
    sprzedaz_ctrl: SprzedazCtrl = None

    zakup_wiersz: list = field(default_factory=list)
    zakup_ctrl: ZakupCtrl = None

    meta: dict = field(default_factory=dict)



# from dataclasses import dataclass, field
# from typing import List

# @dataclass
# class SprzedazWiersz:
    # NrKontrahenta: str = ""
    # DataWystawienia: str = ""
    # DataSprzedazy: str = ""
    # K_10: float = 0.0
    # K_11: float = 0.0
    # GTU: list = field(default_factory=list)

# @dataclass
# class SprzedazCtrl:
    # LiczbaWierszySprzedazy: int = 0
    # PodatekNalezny: float = 0.0

# @dataclass
# class JPKModel:
    # meta: dict = field(default_factory=dict)
    # sprzedaz_wiersz: List[SprzedazWiersz] = field(default_factory=list)
    # sprzedaz_ctrl: SprzedazCtrl = None
