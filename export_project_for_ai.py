import argparse
import ast
import hashlib
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pathspec

OUTPUT_NAME = "ksef2jpk_project_for_ai.txt"

MAX_TEXT_FILE_SIZE = 1_000_000
MAX_NONPY_FILE_SIZE = 300_000

CHUNK_SIZE_LINES = 900


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
Preparing Polish VAT/JPK reporting data based on KSeF invoice XML files for small business.

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
- CSV quality report
- monthly HTML dashboard
- archived monthly reporting package

Type:
CLI / local automation tool.

Main entrypoint:
ksef2jpk/main.py

Typical run:
python -m ksef2jpk.main --year 2026 --month 4

Status:
Personal/local business tool in active development.

Important safety assumption:
This project does not send invoices to KSeF. It only reads KSeF XML files and generates JPK_V7M.
"""


CURRENT_STATUS = """# CURRENT STATUS

## Completed

### Monthly orchestration
- PowerShell monthly orchestrator implemented
- End-to-end automation:
  - ksef-sync
  - validation/tests
  - JPK generation
  - HTML preview
  - CSV quality reports
  - monthly HTML report
- Dry-run support implemented
- Artifact archiving implemented

---

### Data quality reporting
- CSV quality report implemented
- HTML quality dashboard implemented
- Reporting includes:
  - GTU
  - procedures
  - validation warnings
  - totals consistency
  - correction detection

---

### Deduplication
- Duplicate invoice detection implemented
- NrKSeF-based deduplication implemented
- Duplicate skipping statistics implemented

---

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
- StanPrzed handling implemented
- KOR values normalized to negative JPK values
- KOR included in JPK pipeline
- KOR totals validation adjusted to avoid false warnings
- Parser and end-to-end KOR tests implemented
- Broader correction scenarios still require validation

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
- XSD validation regression tests implemented
- KOR, MPP, OO, IMP, WDT, EXP tests implemented
- Deduplication tests implemented
- GTU classifier tests implemented

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
- YAML-based GTU rules implemented
- Manual GTU/procedure override implemented
- Default GTU fallback rules implemented
- Requires deterministic business review for production tax correctness

---

### XML resilience
- Pipeline-level exception handling implemented
- Parser still requires stronger malformed XML handling

---

### Validation
- Basic structural validation implemented
- Business/domain validation still incomplete

---

### Input validation subsystem
- NIP validation implemented
- ISO date validation implemented
- Required field warnings implemented
- Validation warnings exposed in quality reports

---

### Reverse charge / import services
- OO detection implemented
- IMP handling implemented in purchase evidence/declaration model
- WDT and EXP classification implemented
- Advanced cross-border VAT scenarios still require tax review

---

## Next Priority Targets

### P1 — Critical
1. Broader correction accounting scenarios
2. Domain validation engine
3. Reverse charge / import services hardening
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

- KOR support currently covers tested correction-to-zero cases; broader correction types still require validation
- GTU classification may generate false positives
- MPP heuristic may be too aggressive
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
| Corrections support | Partial |
| GTU accuracy | Experimental |
| Integration tests | Growing |
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
- deduplication
- mapping invoices to JPK evidence rows
- building JPK declaration and evidence structure
- adapting dictionaries to JPK model classes
- generating JPK_V7M XML
- validating XML against XSD
- generating HTML preview
- CSV quality reporting
- monthly reporting dashboard
- console quality report

Core files:
- ksef2jpk/main.py
- ksef2jpk/parser/ksef_parser.py
- ksef2jpk/classifier/jpk_flags.py
- ksef2jpk/classifier/gtu_classifier.py
- ksef2jpk/mapper/jpk_mapper.py
- ksef2jpk/builder/jpk_builder.py
- ksef2jpk/adapter/jpk_adapter.py
- ksef2jpk/generator/jpk_generator.py
- ksef2jpk/validator/validate_jpk.py
- ksef2jpk/utils/dedup.py
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
ksef2jpk/classifier/jpk_flags.py and gtu_classifier.py
    ↓
GTU/procedure candidates
    ↓
date filter for selected JPK year/month
    ↓
deduplication
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
    ↓
quality CSV report
    ↓
monthly HTML dashboard
    ↓
archived reporting package
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


TEXT_FILENAMES = {
    ".gitignore",
    ".gitattributes",
    ".env.example",
    "Dockerfile",
    "Containerfile",
    "Makefile",
    "docker-compose.yml",
    "docker-compose.yaml",
}


PRIORITY_FILES = [
    "pyproject.toml",
    "requirements.txt",
    "README.md",
    "pytest.ini",
    ".gitignore",
    ".gitattributes",
    "check.ps1",
    "fix.ps1",
    "ksef2jpk/main.py",
]


SECRET_PATTERNS = [
    ("possible_api_key", re.compile(r"(?i)\b(api[_-]?key|secret[_-]?key|token|password)\b\s*[:=]\s*['\"][^'\"]{8,}['\"]")),
    ("possible_private_key", re.compile(r"-----BEGIN (RSA |OPENSSH |EC )?PRIVATE KEY-----")),
    ("possible_jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")),
    ("possible_iban_pl", re.compile(r"\bPL\d{26}\b|\b\d{26}\b")),
    ("possible_polish_nip", re.compile(r"\b\d{10}\b")),
]


@dataclass(frozen=True)
class ImportRef:
    module: str
    level: int = 0
    name: str | None = None


@dataclass
class ModuleSummary:
    path: Path
    classes: list[str]
    functions: list[str]
    imports: list[str]
    line_count: int


def rel_posix(path: Path) -> str:
    return path.as_posix()


def read_text_safe(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def load_gitignore(root: Path):
    gitignore = root / ".gitignore"
    if not gitignore.exists():
        return None

    patterns = read_text_safe(gitignore).splitlines()
    return pathspec.PathSpec.from_lines("gitwildmatch", patterns)


def is_probably_binary(path: Path) -> bool:
    try:
        chunk = path.read_bytes()[:2048]
    except OSError:
        return True

    return b"\0" in chunk


def is_text_file(path: Path) -> bool:
    if path.name in TEXT_FILENAMES:
        return True

    if path.suffix.lower() in TEXT_EXTENSIONS:
        return True

    return not is_probably_binary(path)


def is_ignored_by_gitignore(rel: Path, spec) -> bool:
    if spec is None:
        return False

    return spec.match_file(rel_posix(rel))


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()

    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 128), b""):
            h.update(chunk)

    return h.hexdigest()


def get_file_limit(path: Path) -> int:
    if path.suffix.lower() == ".py":
        return MAX_TEXT_FILE_SIZE
    return MAX_NONPY_FILE_SIZE


def should_skip_file(path: Path, rel: Path, spec, output_path: Path) -> tuple[bool, str | None]:
    try:
        if path.resolve() == output_path.resolve():
            return True, "output file"
    except OSError:
        return True, "unreadable"

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

    limit = get_file_limit(path)
    if size > limit:
        return True, f"too large: {size} bytes > {limit} bytes"

    if not is_text_file(path):
        return True, "binary file"

    return False, None


def collect_files(root: Path, spec, output_path: Path, include_exporter: bool):
    files: list[Path] = []
    skipped_files: list[tuple[Path, str | None]] = []
    skipped_dirs: set[str] = set()

    exporter_path = Path(__file__).resolve()

    def walk(directory: Path):
        try:
            children = sorted(directory.iterdir(), key=lambda p: p.name.lower())
        except OSError:
            skipped_dirs.add(rel_posix(directory.relative_to(root)) + "/")
            return

        for path in children:
            try:
                rel = path.relative_to(root)
                rel_str = rel_posix(rel)
            except ValueError:
                continue

            try:
                is_dir = path.is_dir()
                is_file = path.is_file()
            except OSError:
                skipped_files.append((rel, "unreadable"))
                continue

            if is_dir:
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

            if not is_file:
                continue

            try:
                if not include_exporter and path.resolve() == exporter_path:
                    skipped_files.append((rel, "exporter script"))
                    continue
            except OSError:
                skipped_files.append((rel, "unreadable"))
                continue

            skip, reason = should_skip_file(path, rel, spec, output_path)
            if skip:
                skipped_files.append((rel, reason))
                continue

            files.append(rel)

    walk(root)

    return sort_files(files), sorted(skipped_dirs), sorted(skipped_files, key=lambda x: rel_posix(x[0]))


def sort_files(files: list[Path]) -> list[Path]:
    priority_index = {name: idx for idx, name in enumerate(PRIORITY_FILES)}

    def key(path: Path):
        rel = rel_posix(path)
        return (
            0 if rel in priority_index else 1,
            priority_index.get(rel, 9999),
            rel.lower(),
        )

    return sorted(files, key=key)


def module_name_from_path(file: Path) -> str:
    if file.name == "__init__.py":
        return file.parent.as_posix().replace("/", ".")
    return file.with_suffix("").as_posix().replace("/", ".")


def package_name_from_path(file: Path) -> str:
    parent = file.parent.as_posix().replace("/", ".")
    return "" if parent == "." else parent


def resolve_relative_import(file: Path, node: ast.ImportFrom) -> str | None:
    package = package_name_from_path(file)
    if not package and node.level > 0:
        return node.module

    parts = package.split(".") if package else []

    if node.level > 0:
        keep = max(len(parts) - node.level + 1, 0)
        base_parts = parts[:keep]
    else:
        base_parts = []

    if node.module:
        base_parts.append(node.module)

    result = ".".join(part for part in base_parts if part)
    return result or None


def parse_import_refs(file_path: Path, rel_path: Path | None = None) -> list[ImportRef]:
    try:
        source = read_text_safe(file_path)
        tree = ast.parse(source)
    except Exception:
        return []

    imports: list[ImportRef] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(ImportRef(module=alias.name, level=0))

        elif isinstance(node, ast.ImportFrom):
            if node.level > 0 and rel_path is not None:
                module = resolve_relative_import(rel_path, node)
            else:
                module = node.module

            if module:
                imports.append(ImportRef(module=module, level=node.level))

    return imports


def resolve_import_to_file(imported_module: str, module_map: dict[str, Path]) -> Path | None:
    current = imported_module

    while current:
        if current in module_map:
            return module_map[current]

        if "." not in current:
            break

        current = current.rsplit(".", 1)[0]

    return None


def build_dependency_map(root: Path, files: list[Path]) -> dict[Path, list[Path]]:
    module_map: dict[str, Path] = {}
    deps: dict[Path, list[Path]] = {}

    for file in files:
        if file.suffix != ".py":
            continue

        module = module_name_from_path(file)
        if module:
            module_map[module] = file

        if file.name == "__init__.py":
            package_name = file.parent.as_posix().replace("/", ".")
            if package_name != ".":
                module_map[package_name] = file

    for file in files:
        if file.suffix != ".py":
            continue

        found: set[Path] = set()

        for import_ref in parse_import_refs(root / file, file):
            module_path = resolve_import_to_file(import_ref.module, module_map)
            if module_path and module_path != file:
                found.add(module_path)

        deps[file] = sorted(found, key=rel_posix)

    return deps


def render_dependencies(deps: dict[Path, list[Path]]) -> str:
    lines = ["# MODULE DEPENDENCIES", ""]
    has_any = False

    for file, imports in sorted(deps.items(), key=lambda item: rel_posix(item[0])):
        visible_imports = [imported_file for imported_file in imports if imported_file.name != "__init__.py"]

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


def parse_module_summary(root: Path, file: Path) -> ModuleSummary | None:
    if file.suffix != ".py":
        return None

    full_path = root / file

    try:
        source = read_text_safe(full_path)
        tree = ast.parse(source)
    except Exception:
        return None

    classes: list[str] = []
    functions: list[str] = []

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            classes.append(node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node.name)

    imports = [ref.module for ref in parse_import_refs(full_path, file)]

    return ModuleSummary(
        path=file,
        classes=classes,
        functions=functions,
        imports=imports,
        line_count=len(source.splitlines()),
    )


def render_module_summaries(root: Path, files: list[Path]) -> str:
    lines = ["# MODULE SUMMARY", ""]
    summaries = [parse_module_summary(root, file) for file in files]
    summaries = [summary for summary in summaries if summary is not None]

    if not summaries:
        lines.append("No Python module summaries available.")
        return "\n".join(lines)

    for summary in summaries:
        lines.append(rel_posix(summary.path))
        lines.append(f"- lines: {summary.line_count}")
        lines.append(f"- classes: {', '.join(summary.classes) if summary.classes else '-'}")
        lines.append(f"- functions: {', '.join(summary.functions) if summary.functions else '-'}")
        lines.append(f"- imports: {', '.join(summary.imports) if summary.imports else '-'}")
        lines.append("")

    return "\n".join(lines)


def render_domain_objects(root: Path, files: list[Path]) -> str:
    lines = ["# DOMAIN OBJECTS / PUBLIC SYMBOLS", ""]
    found_any = False

    for file in files:
        if file.suffix != ".py":
            continue

        try:
            source = read_text_safe(root / file)
            tree = ast.parse(source)
        except Exception:
            continue

        symbols: list[str] = []

        for node in tree.body:
            if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
                symbols.append(f"class {node.name}")
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
                symbols.append(f"def {node.name}()")

        if symbols:
            found_any = True
            lines.append(rel_posix(file))
            for symbol in symbols:
                lines.append(f"- {symbol}")
            lines.append("")

    if not found_any:
        lines.append("No public symbols detected.")

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
        return len(read_text_safe(path).splitlines())
    except OSError:
        return 0


def file_metadata(root: Path, file: Path) -> dict[str, str | int | float]:
    full_path = root / file
    stat = full_path.stat()

    return {
        "path": rel_posix(file),
        "size": stat.st_size,
        "mtime": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
        "sha256": file_sha256(full_path),
        "lines": count_lines(full_path),
    }


def render_file_metadata(root: Path, files: list[Path]) -> str:
    lines = ["# FILE METADATA", ""]

    for file in files:
        try:
            meta = file_metadata(root, file)
        except OSError:
            lines.append(f"- {rel_posix(file)} — metadata unavailable")
            continue

        lines.append(f"- {meta['path']}")
        lines.append(f"  size: {meta['size']}")
        lines.append(f"  lines: {meta['lines']}")
        lines.append(f"  mtime: {meta['mtime']}")
        lines.append(f"  sha256: {meta['sha256']}")

    return "\n".join(lines)


def scan_text_for_secrets(text: str) -> list[str]:
    hits: list[str] = []

    for name, pattern in SECRET_PATTERNS:
        if pattern.search(text):
            hits.append(name)

    return sorted(set(hits))


def scan_files_for_secret_warnings(root: Path, files: list[Path]) -> dict[Path, list[str]]:
    warnings: dict[Path, list[str]] = {}

    for file in files:
        try:
            text = read_text_safe(root / file)
        except OSError:
            continue

        hits = scan_text_for_secrets(text)
        if hits:
            warnings[file] = hits

    return warnings


def render_secret_warnings(secret_warnings: dict[Path, list[str]]) -> str:
    lines = ["# SECRET / SENSITIVE DATA WARNINGS", ""]

    if not secret_warnings:
        lines.append("No obvious secret patterns detected in included files.")
        return "\n".join(lines)

    lines.append("Potential sensitive patterns detected. Review before sharing externally.")
    lines.append("")

    for file, warnings in sorted(secret_warnings.items(), key=lambda item: rel_posix(item[0])):
        lines.append(f"- {rel_posix(file)}: {', '.join(warnings)}")

    return "\n".join(lines)


def render_tooling_context(root: Path) -> str:
    lines = ["# BUILD / TOOLING CONTEXT", ""]

    for filename in ["pyproject.toml", "requirements.txt", "pytest.ini", ".bandit", "check.ps1", "fix.ps1"]:
        path = root / filename
        if path.exists() and path.is_file():
            try:
                lines.append(f"## {filename}")
                lines.append("")
                content = read_text_safe(path).strip()
                if content:
                    lines.append(content)
                else:
                    lines.append("[EMPTY FILE]")
                lines.append("")
            except OSError:
                lines.append(f"## {filename}")
                lines.append("[Could not read file]")
                lines.append("")

    return "\n".join(lines)


def write_file_content(out, root: Path, rel: Path):
    full_path = root / rel
    rel_name = rel_posix(rel)

    out.write(f"\n\n===== FILE START: {rel_name} =====\n\n")

    try:
        content = read_text_safe(full_path)
    except OSError as error:
        out.write(f"[Could not read file: {error}]\n")
        out.write(f"\n===== FILE END: {rel_name} =====\n")
        return

    if not content.strip():
        out.write("[EMPTY FILE]\n")
        out.write(f"\n===== FILE END: {rel_name} =====\n")
        return

    lines = content.splitlines(keepends=True)

    if len(lines) <= CHUNK_SIZE_LINES:
        out.write(content)
        if not content.endswith("\n"):
            out.write("\n")
        out.write(f"\n===== FILE END: {rel_name} =====\n")
        return

    chunks = [lines[i : i + CHUNK_SIZE_LINES] for i in range(0, len(lines), CHUNK_SIZE_LINES)]

    for idx, chunk in enumerate(chunks, start=1):
        out.write(f"===== FILE CHUNK {idx}/{len(chunks)}: {rel_name} =====\n\n")
        out.write("".join(chunk))
        if chunk and not chunk[-1].endswith("\n"):
            out.write("\n")
        out.write("\n")

    out.write(f"===== FILE END: {rel_name} =====\n")


def write_snapshot(
    root: Path,
    output_path: Path,
    files: list[Path],
    skipped_dirs: list[str],
    skipped_files: list[tuple[Path, str | None]],
):
    total_lines = sum(count_lines(root / file) for file in files)
    deps = build_dependency_map(root, files)
    secret_warnings = scan_files_for_secret_warnings(root, files)

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

        out.write(render_tooling_context(root))
        out.write("\n\n")

        out.write(render_secret_warnings(secret_warnings))
        out.write("\n\n")

        out.write(render_dependencies(deps))
        out.write("\n\n")

        out.write(render_module_summaries(root, files))
        out.write("\n\n")

        out.write(render_domain_objects(root, files))
        out.write("\n\n")

        out.write(render_file_metadata(root, files))
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
            write_file_content(out, root, rel)


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