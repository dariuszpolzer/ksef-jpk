from pathlib import Path

import yaml


class GTUClassifier:
    DEFAULT_RULES = {
        "GTU_06": [
            "telefon",
            "smartfon",
            "laptop",
            "komputer",
            "tablet",
        ],
        "GTU_07": [
            "samochód",
            "pojazd",
            "motocykl",
        ],
        "GTU_12": [
            "doradztwo",
            "doradztwa",
            "consulting",
            "księgowość",
            "marketing",
            "reklama",
            "programistyczne",
            "ebook",
            "licencja",
            "saas",
        ],
    }

    def __init__(self, config_path: str = "config/gtu_rules.yaml"):
        self.rules = self._load_rules(config_path)

    def _load_rules(self, config_path: str):
        path = Path(config_path)

        if not path.exists():
            return self.DEFAULT_RULES

        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        rules = {}

        for key, value in data.items():
            if key == "PROCEDURY":
                continue

            if isinstance(value, list):
                rules[key] = [str(v).lower() for v in value]

        return rules or self.DEFAULT_RULES

    def classify(self, text: str):
        txt = (text or "").lower()

        for gtu, keywords in self.rules.items():
            if any(keyword in txt for keyword in keywords):
                return gtu

        return None
