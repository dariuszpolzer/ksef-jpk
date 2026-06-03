import json

import pytest

from ksef2jpk.utils.batch_loader import get_invoices_dir, load_batch_manifest, validate_batch_manifest_contract


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


def test_batch_manifest_contract_accepts_current_shape():
    manifest = {
        "schema_version": 1,
        "tool": {"name": "ksef-sync"},
        "period": {"label": "2026-05"},
        "inputs": {},
        "outputs": {},
        "checks": {},
        "hashes": {},
        "status": "prepared",
        "storage": {"invoices_dir": "invoices"},
    }

    assert validate_batch_manifest_contract(manifest) == []


def test_batch_manifest_contract_warns_for_legacy_manifest():
    manifest = {"storage": {"invoices_dir": "invoices"}}

    assert validate_batch_manifest_contract(manifest) == ["Legacy manifest bez schema_version."]


def test_load_batch_manifest_rejects_incomplete_current_contract(tmp_path):
    batch_dir = tmp_path / "batch"
    batch_dir.mkdir()
    (batch_dir / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "storage": {"invoices_dir": "invoices"},
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="Niepełny kontrakt"):
        load_batch_manifest(batch_dir)
