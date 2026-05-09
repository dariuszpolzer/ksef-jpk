import argparse
import ast
import sys
from datetime import datetime
from pathlib import Path

import pathspec

OUTPUT_NAME = "ksef2jpk_project_for_ai.txt"
MAX_FILE_SIZE = 300_000  # 300 KB


AI_INSTRUCTIONS = """# INSTRUKCJE DLA AI

To jest snapshot projektu Python ksef2jpk.

Projekt służy do generowania pliku JPK_V7M XML na podstawie faktur XML pobranych z KSeF.

Przeanalizuj projekt jako całość, nie jako pojedyncze niezależne pliki.

Ważne:
- Najpierw zrozum strukturę projektu i przepływ danych.
- Respektuj znaczniki FILE START / FILE END.
- Przy sugestiach podawaj dokładne ścieżki plików.
- Szczególnie sprawdzaj poprawność mapowania KSeF XML -> JPK_V7M.
- Szczególnie sprawdzaj ryzyko błędnego zakwalifikowania sprzedaży/zakupu.
- Szczególnie sprawdzaj korekty, daty okresu JPK, NrKSeF, GTU, procedury i sumy VAT.
- Szczególnie sprawdzaj zgodność generatora XML z XSD JPK_V7M.
- Nie zakładaj istnienia plików, których nie ma na liście.
- Nie przepisuj całego projektu, jeśli nie zostaniesz o to poproszony.
- Jeśli zauważysz możliwe sekrety, NIP-y, dane kontrahentów lub dane prywatne, ostrzeż mnie.
"""


PROJECT_CONTEXT = """# PROJECT CONTEXT

Project name:
ksef2jpk

Purpose:
Local Python CLI tool for generating JPK_V7M XML from invoice XML files downloaded from KSeF.

Business purpose:
Preparing Polish VAT/JPK reporting data based on KSeF invoice XML files for "small buissnes".

Inputs:
- KSeF invoice XML files
- local config.json
- JPK_V7M XSD schema
- optional batch directory from ksef-sync

Outputs:
- generated JPK_V7M XML file
- HTML preview of generated JPK
- console quality report
- validation result against XSD

Type:
CLI / local automation tool.

Main entrypoint:
ksef2jpk/main.py

Typical run:
py -3.11 -m ksef2jpk.main --year 2026 --month 4

Status:
Personal/local business tool in active development.

Important safety assumption:
This project does not send invoices to KSeF. It only reads KSeF XML files and generates JPK_V7M.
"""


CURRENT_STATUS = """# CURRENT STATUS

## Completed

### Core architecture
- Modular pipeline architecture implemented
- Clear separation:
  - parser
  - classifier
  - mapper
  - builder
  - adapter
  - generator
  - validator
- CLI entrypoint implemented
- Batch integration with ksef-sync implemented

---

### KSeF XML parsing
- Namespace-aware XML parsing
- Safe XML parsing using defusedxml
- Detection of:
  - sales invoices
  - purchase invoices
- Fallback extraction of NrKSeF from filename
- Parsing of:
  - invoice dates
  - counterparties
  - invoice positions
  - VAT rates
  - correction metadata
- Decimal-safe amount handling
- Support for multiple XML path variants

---

### VAT mapping
- Grouping invoice positions by VAT rate
- Multiple VAT rows per invoice supported
- Separate sales/purchase evidence rows
- Mapping to:
  - K_19–K_28
  - K_42–K_47
- GTU propagation to evidence rows
- Procedure propagation to evidence rows

---

### JPK declaration builder
- VAT declaration aggregation implemented
- Support for:
  - 23%
  - 8%
  - 5%
  - 0%
  - ZW/NP
- Automatic calculation of:
  - P_37
  - P_38
  - P_48
  - P_51
- PLN rounding rules implemented

---

### XML generation
- Namespace-correct XML generation
- Conditional XML tag rendering
- GTU emitted as GTU_XX tags
- Sales and purchase control sections implemented
- Pretty XML output generation

---

### Validation
- XSD validation implemented
- Local XSD resolver implemented
- Validation result reporting implemented

---

### Data quality controls
- Invoice totals verification implemented:
  - netto
  - VAT
  - brutto
- Quality statistics implemented
- Detection/reporting of:
  - missing NrKSeF
  - GTU usage
  - procedures
  - corrections
  - totals mismatch

---

### Corrections handling
- Detection of KOR invoices implemented
- Correction metadata parsing implemented
- Corrections reporting implemented
- Corrections exclusion from JPK currently implemented intentionally

---

### Batch processing
- Support for ksef-sync batch structure
- manifest.json support
- Latest batch auto-detection
- Invoice directory auto-resolution

---

### HTML preview
- XML → HTML preview conversion implemented
- Safe HTML escaping implemented

---

### Testing
- Parser tests implemented
- Mapper tests implemented
- Builder tests implemented
- Full pipeline smoke test implemented
- Batch loader tests implemented
- Utility tests implemented

---

### Security
- defusedxml used
- No outbound network communication
- No dynamic code execution
- Bandit clean
- Basic XML attack mitigation implemented

---

## Partially Completed

### GTU and procedure classification
- Initial heuristic engine implemented
- MPP/WDT/EXP/OO/GTU candidates supported
- Requires deterministic business rules

---

### XML resilience
- Pipeline-level exception handling implemented
- Parser still requires stronger malformed XML handling

---

### Validation
- Basic structural validation implemented
- Business/domain validation still incomplete

---

## In Progress

### KOR correction support
- Detection implemented
- Full accounting logic not implemented yet

---

### Input validation subsystem
Planned:
- NIP validation
- date validation
- required fields validation
- VAT consistency validation

---

### Reverse charge / import services
Partial placeholders exist:
- IMP
- OO
- K_45–K_47

Business logic still incomplete.

---

## Next Priority Targets

### P1 — Critical
1. Full correction accounting (KOR)
2. Input validation engine
3. Reverse charge / import services
4. GTU/procedure hardening

---

### P2 — Stability
5. Structured audit logging
6. Severity/error model
7. Better malformed XML recovery
8. Real integration test suite

---

### P3 — Architecture
9. Typed domain models
10. Pipeline refactor
11. Enums/constants layer
12. Rule engine extraction

---

## Known Architectural Risks

- Corrections currently excluded from JPK
- GTU classification may generate false positives
- MPP heuristic is too aggressive
- Company entities not yet handled separately from OsobaFizyczna
- Excessive dict usage in builder layer
- main.py becoming orchestration-heavy

---

## Current Maturity Assessment

| Area | Status |
|---|---|
| XML parsing | Stable MVP |
| VAT mapping | Stable MVP |
| XML generation | Stable MVP |
| XSD validation | Stable MVP |
| Tax correctness | Partial |
| Corrections support | Incomplete |
| GTU accuracy | Experimental |
| Integration tests | Limited |
| Production readiness | Controlled/internal use only |

"""











PROJECT_ARCHITECTURE = """# PROJECT ARCHITECTURE

Entry point:
- ksef2jpk/main.py
- ksef2jpk/__main__.py

Main domains:
- configuration loading
- input source resolution
- batch loading from ksef-sync
- KSeF XML invoice parsing
- sales/purchase classification
- GTU and procedure classification
- invoice period filtering
- correction detection/reporting
- mapping invoices to JPK evidence rows
- building JPK declaration and evidence structure
- adapting dictionaries to JPK model classes
- generating JPK_V7M XML
- validating XML against XSD
- generating HTML preview
- console quality report

Core files:
- ksef2jpk/main.py
- ksef2jpk/parser/ksef_parser.py
- ksef2jpk/classifier/jpk_flags.py
- ksef2jpk/mapper/jpk_mapper.py
- ksef2jpk/builder/jpk_builder.py
- ksef2jpk/adapter/jpk_adapter.py
- ksef2jpk/generator/jpk_generator.py
- ksef2jpk/validator/validate_jpk.py
"""


DATA_FLOW = """# DATA FLOW

KSeF invoice XML files
    ↓
input_dir OR latest/specified ksef-sync batch invoices directory
    ↓
ksef2jpk/parser/ksef_parser.py
    ↓
FakturaModel
    ↓
ksef2jpk/classifier/jpk_flags.py
    ↓
GTU/procedure candidates
    ↓
date filter for selected JPK year/month
    ↓
correction detection/reporting
    ↓
ksef2jpk/mapper/jpk_mapper.py
    ↓
WierszEwidencji rows
    ↓
sales/purchase split
    ↓
ksef2jpk/builder/jpk_builder.py
    ↓
JPK dictionary structure
    ↓
ksef2jpk/adapter/jpk_adapter.py
    ↓
JPKModel
    ↓
ksef2jpk/generator/jpk_generator.py
    ↓
JPK_V7M XML
    ↓
ksef2jpk/validator/validate_jpk.py
    ↓
XSD validation result
    ↓
ksef2jpk/utils/jpk2html.py
    ↓
HTML preview
"""


ALWAYS_IGNORE_DIRS = {
    ".git",
    ".idea",
    ".vscode",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "test_data",
    "prod_data",
    "old_test_data",
    "output",
    "outputs",
    "dist",
    "build",
}


SECRET_FILES = {
    ".env",
    ".env.local",
    ".env.production",
    "config.json",
    "id_rsa",
    "id_rsa.pub",
    "ksef_public_key.pem",
    "token.json",
    "public_keys.json",
    "session_lock.json",
}


EXTRA_IGNORE_FILES = {
    "git_init.txt",
    "Nowy Python File.py",
    "project_for_ai.txt",
    "ksef_send_project_for_ai.txt",
    OUTPUT_NAME,
}


TEXT_EXTENSIONS = {
    ".py",
    ".md",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".html",
    ".css",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".sql",
    ".sh",
    ".bat",
    ".ps1",
    ".dockerfile",
}


def rel_posix(path: Path) -> str:
    return path.as_posix()


def load_gitignore(root: Path):
    gitignore = root / ".gitignore"
    if not gitignore.exists():
        return None

    patterns = gitignore.read_text(encoding="utf-8", errors="ignore").splitlines()
    return pathspec.PathSpec.from_lines("gitwildmatch", patterns)


def is_probably_binary(path: Path) -> bool:
    try:
        chunk = path.read_bytes()[:2048]
    except OSError:
        return True

    return b"\0" in chunk


def is_text_file(path: Path) -> bool:
    if path.name in {".gitignore", ".env.example"}:
        return True

    if path.suffix.lower() in TEXT_EXTENSIONS:
        return True

    return not is_probably_binary(path)


def is_ignored_by_gitignore(rel: Path, spec) -> bool:
    if spec is None:
        return False

    return spec.match_file(rel_posix(rel))


def should_skip_file(path: Path, rel: Path, spec, output_path: Path) -> tuple[bool, str | None]:
    if path.resolve() == output_path.resolve():
        return True, "output file"

    suffix = path.suffix.lower()

    if suffix == ".xsd":
        return True, "schema file"

    if suffix == ".xml":
        return True, "invoice/xml data file"

    if path.name in SECRET_FILES:
        return True, "secret/sensitive file"

    if path.name in EXTRA_IGNORE_FILES:
        return True, "extra ignored file"

    if is_ignored_by_gitignore(rel, spec):
        return True, ".gitignore"

    try:
        size = path.stat().st_size
    except OSError:
        return True, "unreadable"

    if size > MAX_FILE_SIZE:
        return True, f"too large: {size} bytes"

    if not is_text_file(path):
        return True, "binary file"

    return False, None


def collect_files(root: Path, spec, output_path: Path, include_exporter: bool):
    files: list[Path] = []
    skipped_files: list[tuple[Path, str | None]] = []
    skipped_dirs: set[str] = set()

    exporter_path = Path(__file__).resolve()

    def walk(directory: Path):
        for path in sorted(directory.iterdir(), key=lambda p: p.name.lower()):
            rel = path.relative_to(root)
            rel_str = rel_posix(rel)

            if path.is_dir():
                if (
                    path.name in ALWAYS_IGNORE_DIRS
                    or path.name.endswith(".egg-info")
                    or path.name in {"__pypackages__"}
                ):
                    skipped_dirs.add(rel_str + "/")
                    continue

                if is_ignored_by_gitignore(rel, spec):
                    skipped_dirs.add(rel_str + "/")
                    continue

                walk(path)
                continue

            if not path.is_file():
                continue

            if not include_exporter and path.resolve() == exporter_path:
                skipped_files.append((rel, "exporter script"))
                continue

            skip, reason = should_skip_file(path, rel, spec, output_path)
            if skip:
                skipped_files.append((rel, reason))
                continue

            files.append(rel)

    walk(root)

    return sorted(files, key=rel_posix), sorted(skipped_dirs), sorted(skipped_files)


def parse_imports(file_path: Path) -> list[str]:
    try:
        source = file_path.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(source)
    except Exception:
        return []

    imports: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)

        elif isinstance(node, ast.ImportFrom):
            if node.level > 0:
                continue

            if node.module:
                imports.append(node.module)

    return imports


def build_dependency_map(root: Path, files: list[Path]) -> dict[Path, list[Path]]:
    module_map: dict[str, Path] = {}
    deps: dict[Path, list[Path]] = {}

    for file in files:
        if file.suffix != ".py":
            continue

        module_name = file.with_suffix("").as_posix().replace("/", ".")
        module_map[module_name] = file

        if file.name == "__init__.py":
            package_name = file.parent.as_posix().replace("/", ".")
            if package_name != ".":
                module_map[package_name] = file

    for file in files:
        if file.suffix != ".py":
            continue

        found: set[Path] = set()

        for imported_module in parse_imports(root / file):
            for module_name, module_path in module_map.items():
                if imported_module == module_name or imported_module.startswith(module_name + "."):
                    if module_path != file:
                        found.add(module_path)

        deps[file] = sorted(found, key=rel_posix)

    return deps


def render_dependencies(deps: dict[Path, list[Path]]) -> str:
    lines = ["# MODULE DEPENDENCIES", ""]
    has_any = False

    for file, imports in sorted(deps.items(), key=lambda item: rel_posix(item[0])):
        visible_imports = [
            imported_file for imported_file in imports if imported_file.name != "__init__.py"
        ]

        if not visible_imports:
            continue

        has_any = True
        lines.append(rel_posix(file))

        for imported_file in visible_imports:
            lines.append(f"  └── {rel_posix(imported_file)}")

        lines.append("")

    if not has_any:
        lines.append("No internal Python module dependencies detected.")

    return "\n".join(lines)


def make_tree(files: list[Path]) -> str:
    lines = ["."]
    dirs: set[Path] = set()

    for file in files:
        for parent in file.parents:
            if str(parent) != ".":
                dirs.add(parent)

    all_paths = sorted(dirs | set(files), key=lambda p: rel_posix(p).lower())

    for path in all_paths:
        depth = len(path.parts) - 1
        prefix = "│   " * depth + "├── "
        suffix = "/" if path in dirs else ""
        lines.append(f"{prefix}{path.name}{suffix}")

    return "\n".join(lines)


def count_lines(path: Path) -> int:
    try:
        return len(path.read_text(encoding="utf-8", errors="ignore").splitlines())
    except OSError:
        return 0


def write_snapshot(
    root: Path,
    output_path: Path,
    files: list[Path],
    skipped_dirs: list[str],
    skipped_files: list[tuple[Path, str | None]],
):
    total_lines = sum(count_lines(root / file) for file in files)
    deps = build_dependency_map(root, files)

    with output_path.open("w", encoding="utf-8") as out:
        out.write("# PROJECT SNAPSHOT FOR AI\n\n")
        out.write(f"Generated: {datetime.now().isoformat(timespec='seconds')}\n")
        out.write(f"Root: {root.name}\n")
        out.write(f"Files included: {len(files)}\n")
        out.write(f"Directories skipped: {len(skipped_dirs)}\n")
        out.write(f"Files skipped: {len(skipped_files)}\n")
        out.write(f"Total skipped paths: {len(skipped_dirs) + len(skipped_files)}\n")
        out.write(f"Total lines: {total_lines}\n\n")

        out.write(AI_INSTRUCTIONS)
        out.write("\n\n")

        out.write(CURRENT_STATUS)
        out.write("\n\n")

        out.write(PROJECT_CONTEXT)
        out.write("\n\n")
        out.write(PROJECT_ARCHITECTURE)
        out.write("\n\n")
        out.write(DATA_FLOW)
        out.write("\n\n")
        out.write(render_dependencies(deps))
        out.write("\n\n")

        out.write("# PROJECT TREE\n\n")
        out.write(make_tree(files))
        out.write("\n\n")

        out.write("# INCLUDED FILES\n\n")
        for file in files:
            out.write(f"- {rel_posix(file)}\n")
        out.write("\n")

        if skipped_dirs or skipped_files:
            out.write("# SKIPPED PATHS\n\n")

            for directory in skipped_dirs:
                out.write(f"- {directory} — ignored directory\n")

            for file, reason in skipped_files:
                out.write(f"- {rel_posix(file)} — {reason}\n")

            out.write("\n")

        out.write("# FILE CONTENTS\n")

        for rel in files:
            full_path = root / rel
            rel_name = rel_posix(rel)

            out.write(f"\n\n===== FILE START: {rel_name} =====\n\n")

            try:
                content = full_path.read_text(encoding="utf-8", errors="ignore")
            except OSError as error:
                out.write(f"[Could not read file: {error}]\n")
                out.write(f"\n===== FILE END: {rel_name} =====\n")
                continue

            if content.strip():
                out.write(content)

                if not content.endswith("\n"):
                    out.write("\n")
            else:
                out.write("[EMPTY FILE]\n")

            out.write(f"\n===== FILE END: {rel_name} =====\n")


def main():
    parser = argparse.ArgumentParser(description="Export project snapshot for AI analysis.")

    parser.add_argument(
        "--root",
        default=".",
        help="Project root directory. Default: current directory.",
    )

    parser.add_argument(
        "--include-exporter",
        action="store_true",
        help="Include this export script in the snapshot.",
    )

    parser.add_argument(
        "--output",
        default=OUTPUT_NAME,
        help=f"Output file name. Default: {OUTPUT_NAME}",
    )

    args = parser.parse_args()

    root = Path(args.root).resolve()

    if not root.exists():
        print(f"Root nie istnieje: {root}")
        sys.exit(1)

    output_path = root / args.output
    spec = load_gitignore(root)

    files, skipped_dirs, skipped_files = collect_files(
        root=root,
        spec=spec,
        output_path=output_path,
        include_exporter=args.include_exporter,
    )

    write_snapshot(root, output_path, files, skipped_dirs, skipped_files)

    print(f"Snapshot zapisany do: {output_path}")
    print(f"Plików dodanych: {len(files)}")
    print(f"Katalogów pominiętych: {len(skipped_dirs)}")
    print(f"Plików pominiętych: {len(skipped_files)}")
    print(f"Łącznie pominiętych ścieżek: {len(skipped_dirs) + len(skipped_files)}")


if __name__ == "__main__":
    main()
