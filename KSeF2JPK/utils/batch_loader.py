import json
from pathlib import Path


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
        return json.load(f)


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
