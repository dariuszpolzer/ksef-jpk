import glob
import json
from dataclasses import dataclass, field
from pathlib import Path

from ksef2jpk.utils.batch_loader import get_invoices_dir, resolve_batch_dir
from ksef2jpk.utils.invoice_xml import classify_ksef_invoice_xml


@dataclass
class ValidationReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    info: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def is_candidate_input_xml(path: str | Path) -> bool:
    name = Path(path).name.lower()

    excluded_prefixes = (
        "jpk_",
        "wynik_",
        "output_",
    )

    excluded_exact = {
        "wynik_test_jpk.xml",
    }

    if name in excluded_exact:
        return False

    if name.startswith(excluded_prefixes):
        return False

    return classify_ksef_invoice_xml(path)["ok"]


def build_skipped_invoice_report(paths: list[str | Path]) -> list[dict]:
    skipped = []
    for path in paths:
        path = Path(path)
        name = path.name.lower()
        reason = ""

        if name in {"wynik_test_jpk.xml"}:
            reason = "excluded output XML filename"
        elif name.startswith(("jpk_", "wynik_", "output_")):
            reason = "excluded output XML prefix"
        else:
            reason = classify_ksef_invoice_xml(path)["reason"]

        skipped.append({"filename": path.name, "path": str(path), "reason": reason})

    return skipped


def validate_config(config: dict) -> ValidationReport:
    report = ValidationReport()

    for key in ("xsd_path", "xml_dir", "podmiot"):
        if not config.get(key):
            report.errors.append(f"Brak wymaganego pola config: {key}")

    podmiot = config.get("podmiot") or {}
    for key in ("nip", "nazwa", "kod_urzedu"):
        if not podmiot.get(key):
            report.errors.append(f"Brak wymaganego pola config: podmiot.{key}")

    xsd_path = config.get("xsd_path")
    if xsd_path and not Path(xsd_path).exists():
        report.errors.append(f"Nie istnieje plik XSD: {xsd_path}")

    if config.get("batch_dir") and config.get("input_dir"):
        report.warnings.append("Ustawiono batch_dir i input_dir; batch_dir ma pierwszeństwo.")

    if not config.get("batch_dir") and not config.get("input_dir"):
        report.errors.append("Brak źródła faktur: ustaw batch_dir albo input_dir.")

    for key in ("xml_dir", "html_dir"):
        if config.get(key):
            report.info.append(f"{key}: {config[key]}")

    return report


def validate_input_source(config: dict) -> ValidationReport:
    report = ValidationReport()

    try:
        if config.get("batch_dir"):
            batch_dir = resolve_batch_dir(config["batch_dir"])
            invoices_dir = get_invoices_dir(batch_dir)
            manifest_path = batch_dir / "manifest.json"
            report.info.append(f"Batch: {batch_dir}")
            report.info.append(f"Katalog faktur: {invoices_dir}")

            if not manifest_path.exists():
                report.errors.append(f"Brak manifest.json w batchu: {batch_dir}")
            else:
                with manifest_path.open(encoding="utf-8") as f:
                    manifest = json.load(f)
                invoice_count = manifest.get("batch", {}).get("invoice_count")
                if invoice_count is not None:
                    report.info.append(f"Faktur w manifeście: {invoice_count}")
        else:
            invoices_dir = Path(config["input_dir"])
            report.info.append(f"Katalog faktur: {invoices_dir}")

        if not invoices_dir.exists():
            report.errors.append(f"Nie istnieje katalog faktur: {invoices_dir}")
            return report

        all_xml = sorted(glob.glob(str(invoices_dir / "*.xml")))
        input_xml = [path for path in all_xml if is_candidate_input_xml(path)]
        skipped_xml = [path for path in all_xml if not is_candidate_input_xml(path)]
        report.info.append(f"Plików XML wejściowych: {len(input_xml)}")
        report.info.append(f"Plików XML pominiętych: {len(skipped_xml)}")

        for item in build_skipped_invoice_report(skipped_xml):
            report.warnings.append(f"Pominięto XML {item['filename']}: {item['reason']}")

        if not input_xml:
            report.errors.append(f"Brak wejściowych faktur XML w katalogu: {invoices_dir}")
    except Exception as error:
        report.errors.append(str(error))

    return report


def validate_runtime_config(config: dict) -> ValidationReport:
    report = ValidationReport()

    config_report = validate_config(config)
    report.errors.extend(config_report.errors)
    report.warnings.extend(config_report.warnings)
    report.info.extend(config_report.info)

    if not config_report.errors:
        input_report = validate_input_source(config)
        report.errors.extend(input_report.errors)
        report.warnings.extend(input_report.warnings)
        report.info.extend(input_report.info)

    return report
