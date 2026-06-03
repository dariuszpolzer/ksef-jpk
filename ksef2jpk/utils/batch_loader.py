import json
from pathlib import Path

REQUIRED_MANIFEST_CONTRACT_FIELDS = {
    "schema_version",
    "tool",
    "period",
    "inputs",
    "outputs",
    "checks",
    "hashes",
    "status",
}


def find_latest_batch(batches_root: Path) -> Path:
    batches = [d for d in batches_root.iterdir() if d.is_dir()]
    if not batches:
        raise RuntimeError(f"Brak batchy w katalogu: {batches_root}")
    return sorted(batches)[-1]


def load_batch_manifest(batch_dir: Path) -> dict:
    manifest_path = batch_dir / "manifest.json"
    if not manifest_path.exists():
        raise RuntimeError(f"Brak manifest.json w {batch_dir}")

    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    validate_batch_manifest_contract(manifest)
    return manifest


def validate_batch_manifest_contract(manifest: dict) -> list[str]:
    if not isinstance(manifest, dict):
        raise RuntimeError("manifest.json musi być obiektem JSON.")

    if "schema_version" not in manifest:
        return ["Legacy manifest bez schema_version."]

    missing = sorted(REQUIRED_MANIFEST_CONTRACT_FIELDS - set(manifest))
    if missing:
        raise RuntimeError(f"Niepełny kontrakt manifest.json, brak pól: {', '.join(missing)}")

    if not isinstance(manifest["schema_version"], int) or manifest["schema_version"] < 1:
        raise RuntimeError("schema_version w manifest.json musi być liczbą całkowitą >= 1.")

    for field in ("tool", "period", "inputs", "outputs", "checks", "hashes"):
        if not isinstance(manifest[field], dict):
            raise RuntimeError(f"Pole manifest.json {field} musi być obiektem.")

    if not isinstance(manifest["status"], str) or not manifest["status"].strip():
        raise RuntimeError("Pole manifest.json status musi być niepustym tekstem.")

    return []


def resolve_batch_dir(path: str | Path) -> Path:
    path = Path(path)

    if (path / "manifest.json").exists():
        return path

    return find_latest_batch(path)


def get_invoices_dir(batch_path: str | Path) -> Path:
    batch_dir = resolve_batch_dir(batch_path)
    manifest = load_batch_manifest(batch_dir)

    invoices_rel = manifest["storage"]["invoices_dir"]
    return batch_dir / invoices_rel
