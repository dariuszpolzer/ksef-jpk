from dataclasses import dataclass, field


@dataclass
class Kontrahent:
    nip: str
    nazwa: str
    kraj: str = "PL"


@dataclass
class Pozycja:
    nazwa: str
    netto: float
    vat: float
    typ: str
    kontrahent: Kontrahent
    stawka: float | None = None
    gtu: str | None = None
    procedury: list[str] | None = None
    gtu_manual: str | None = None
    procedury_manual: list[str] | None = None


@dataclass
class FakturaModel:
    pozycje: list[Pozycja] = field(default_factory=list)
    meta: dict = field(default_factory=dict)
    nr_ksef: str = ""
