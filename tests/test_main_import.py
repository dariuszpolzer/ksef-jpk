import importlib


def test_main_module_import_has_no_runtime_side_effects():
    module = importlib.import_module("ksef2jpk.main")

    assert hasattr(module, "main")
