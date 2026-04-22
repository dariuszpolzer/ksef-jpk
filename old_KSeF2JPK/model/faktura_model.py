from dataclasses import dataclass, field
from typing import List
from .pozycja import Pozycja

@dataclass
class FakturaModel:
    pozycje: List[Pozycja] = field(default_factory=list)
    meta: dict = field(default_factory=dict)
