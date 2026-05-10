from ksef2jpk.classifier.gtu_classifier import GTUClassifier


def test_gtu_classifier_uses_default_rules_when_config_missing():
    classifier = GTUClassifier(config_path="missing_gtu_rules.yaml")

    assert classifier.classify("Sprzedaż laptopa") == "GTU_06"
    assert classifier.classify("Usługa doradztwa podatkowego") == "GTU_12"
    assert classifier.classify("Sprzedaż książek papierowych") is None


def test_gtu_classifier_loads_rules_from_yaml(tmp_path):
    config_file = tmp_path / "gtu_rules.yaml"
    config_file.write_text(
        """
GTU_99:
  - specjalny produkt
  - testowy towar

GTU_12:
  - audyt
  - consulting

PROCEDURY:
  MPP:
    - mechanizm podzielonej płatności
""",
        encoding="utf-8",
    )

    classifier = GTUClassifier(config_path=str(config_file))

    assert classifier.classify("Sprzedaż specjalny produkt") == "GTU_99"
    assert classifier.classify("Usługa audyt") == "GTU_12"
    assert classifier.classify("laptop") is None


def test_gtu_classifier_is_case_insensitive(tmp_path):
    config_file = tmp_path / "gtu_rules.yaml"
    config_file.write_text(
        """
GTU_06:
  - laptop
""",
        encoding="utf-8",
    )

    classifier = GTUClassifier(config_path=str(config_file))

    assert classifier.classify("SPRZEDAŻ LAPTOP GAMINGOWY") == "GTU_06"
