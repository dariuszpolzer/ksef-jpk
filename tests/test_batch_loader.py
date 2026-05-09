import json

from ksef2jpk.utils.batch_loader import get_invoices_dir


def test_get_invoices_dir(tmp_path):
    batch_dir = tmp_path / "20260501T092813Z"
    batch_dir.mkdir()

    manifest = {
        "storage": {
            "invoices_dir": "invoices",
        }
    }

    (batch_dir / "manifest.json").write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )

    assert get_invoices_dir(batch_dir) == batch_dir / "invoices"
