from dataclasses import dataclass
from .kontrahent import Kontrahent

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

