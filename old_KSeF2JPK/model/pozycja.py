from dataclasses import dataclass, field

@dataclass
class Pozycja:
    nazwa: str
    typ: str
    netto: float
    vat: float
    stawka: str
    dokument: str = ""
    data_wystawienia: str = ""
    data_sprzedazy: str = ""
    kontrahent: object = None
    gtu: list = field(default_factory=list)
