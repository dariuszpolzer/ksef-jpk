import json
import shutil
import subprocess
import sys
from pathlib import Path


def write_config(tmp_path, input_dir):
    repo_root = Path(__file__).resolve().parents[1]
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "input_dir": str(input_dir),
                "xsd_path": str(repo_root / "validator" / "JPK_V7M_3.xsd"),
                "xml_dir": str(tmp_path / "xml"),
                "html_dir": str(tmp_path / "html"),
                "enable_date_filter": True,
                "podmiot": {
                    "nip": "6791444505",
                    "nazwa": "Test Podatnik",
                    "kod_urzedu": "1214",
                    "email": "test@example.com",
                    "telefon": "123456789",
                    "data_urodzenia": "1980-01-01",
                },
            }
        ),
        encoding="utf-8",
    )
    return config_path


def test_cli_validate_reports_valid_input_source(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    shutil.copyfile(
        repo_root / "test_data" / "6791444505-20260401-755BEE800001-B8.xml",
        input_dir / "invoice.xml",
    )
    config_path = write_config(tmp_path, input_dir)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ksef2jpk.main",
            "validate",
            "--config",
            str(config_path),
        ],
        cwd=repo_root,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "WALIDACJA KSEF2JPK" in result.stdout
    assert "=== VALIDATION OK ===" in result.stdout


def test_cli_build_returns_error_when_no_input_xml(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    config_path = write_config(tmp_path, input_dir)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ksef2jpk.main",
            "build",
            "--year",
            "2026",
            "--month",
            "4",
            "--config",
            str(config_path),
        ],
        cwd=repo_root,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert "Brak wejściowych faktur XML" in result.stdout


def test_cli_legacy_build_without_command_is_supported(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    config_path = write_config(tmp_path, input_dir)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ksef2jpk.main",
            "--year",
            "2026",
            "--month",
            "4",
            "--config",
            str(config_path),
        ],
        cwd=repo_root,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert "Brak wejściowych faktur XML" in result.stdout
