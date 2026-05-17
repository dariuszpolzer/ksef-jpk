import re

OUTPUT_NAME = "ksef2jpk_project_for_ai.txt"
MAX_TEXT_FILE_SIZE = 1_000_000
EXTRA_IGNORE_FILES = {
    "project_for_ai.txt",
    "ksef_send_project_for_ai.txt",
    OUTPUT_NAME,
}
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

PIPELINE_ARCHITECTURE_CONTEXT = """# PIPELINE ARCHITECTURE

High level processing flow:

1. Import faktur
   Sources:
   - XML KSeF
   - PDF
   - OCR
   - manual corrections

2. Parsing layer
   Components:
   - xml_parser
   - pdf extraction
   - OCR normalization
   - invoice normalization

3. Domain mapping
   Raw source data mapped into:
   - FakturaModel
   - Pozycja
   - Kontrahent

4. Classification stage
   Includes:
   - GTU classification
   - procedure detection
   - correction detection
   - invoice type detection

5. Validation stage
   Includes:
   - schema validation
   - business validation
   - VAT consistency checks
   - totals verification
   - duplicate detection

6. Aggregation stage
   Produces:
   - sales registers
   - purchase registers
   - VAT summaries
   - JPK aggregates

7. Export stage
   Outputs:
   - JPK XML
   - CSV reports
   - HTML previews
   - validation reports
   - audit/debug artifacts

8. Quality and audit layer
   Includes:
   - logging
   - snapshot generation
   - debug exports
   - validation diagnostics
   - QA reports
"""

SYSTEM_INVARIANTS = """# SYSTEM INVARIANTS

Critical rules that must never be violated:

1. Monetary precision
- always use Decimal
- never use float for VAT or totals

2. XML handling
- preserve original namespaces
- preserve ordering where required by JPK schema

3. Validation
- validation errors must never silently disappear
- every validation issue must be traceable

4. Auditability
- every generated JPK must be reproducible
- source invoices must be traceable

5. Corrections
- correction invoices must preserve linkage
- original invoice references are mandatory

6. Data lineage
- normalized models must retain raw source references

7. Export integrity
- exported totals must equal aggregated totals
"""

MODULE_RESPONSIBILITIES = """# MODULE RESPONSIBILITIES

app.parsers
- source parsing only
- no business logic

app.domain
- canonical business entities
- normalized invoice representation

app.classification
- GTU and tax procedure detection

app.validation
- business validation
- schema validation
- consistency checks

app.export
- JPK generation
- XML serialization
- CSV/HTML exports

app.audit
- snapshots
- diagnostics
- traceability
"""

AI_PITFALLS_CONTEXT = """# COMMON AI PITFALLS

Common mistakes to avoid:

1. Do not use float for money calculations.

2. Do not bypass validation layers.

3. Do not mutate normalized domain objects during export.

4. Do not mix parsing logic with business rules.

5. Do not hardcode VAT rates.

6. Do not silently ignore invalid invoices.

7. Do not remove logging/debug information without replacement.

8. Do not generate fake fallback values for missing tax data.
"""

SECRET_SENSITIVE_CONTEXT = """# SECRET / SENSITIVE DATA WARNINGS

- Projekt przetwarza dane podatkowe i księgowe:
  - NIP
  - nazwy kontrahentów
  - numery faktur
  - NrKSeF
  - kwoty netto/VAT/brutto

- config.json oraz ksef2jpk/config.json są traktowane jako potencjalnie wrażliwe.

- Dane z faktur KSeF nie powinny być publikowane bez anonimizacji.

- Przed udostępnieniem snapshotu należy maskować:
  - NIP podatnika
  - NIP kontrahentów
  - nazwy kontrahentów
  - numery faktur
  - NrKSeF
  - adresy e-mail
  - numery telefonów

- Wygenerowane:
  - JPK XML
  - HTML preview
  - CSV quality reports
  mogą zawierać dane wrażliwe.

- test_data oraz prod_data są domyślnie pomijane.
"""

MODULE_SUMMARY_CONTEXT = """# MODULE SUMMARY — ADDITIONAL CONTEXT

config/gtu_rules.yaml
- YAML rules for GTU and procedure keyword classification
- Used by GTUClassifier as configurable business rule source

config_example.json
- Example runtime configuration
- Defines input/output directories, JPK period, XSD path and taxpayer identity structure

ISSUES_BACKLOG.md
- Technical and domain backlog
- Priority grouping P1–P4

ksef2jpk/utils/dedup.py
- Invoice deduplication helper
- Uses NrKSeF and invoice number fallback logic

check.ps1
- Local quality gate helper
- Runs pytest, ruff, black check and bandit

fix.ps1
- Local autofix helper
- Runs black and ruff --fix
"""

DOMAIN_OBJECTS_CONTEXT = """# DOMAIN OBJECTS — ADDITIONAL CONTEXT

Business/domain concepts:
- FakturaModel
- Pozycja
- Kontrahent
- WierszEwidencji
- JPKModel
- DeklaracjaVAT7
- SprzedazWiersz
- ZakupWiersz
- SprzedazCtrl
- ZakupCtrl

Important metadata fields:
- typ
- numer
- nr_ksef
- nr_ksef_source
- data_wystawienia
- data_sprzedazy
- data_wplywu
- nip_sprzedawcy
- nip_nabywcy
- is_korekta
- rodzaj_faktury
- procedury
- gtu
- kontrola_sum
- walidacja_wejscia
"""

FILE_METADATA_CONTEXT = """# FILE METADATA — INTERPRETATION

- mtime reflects local filesystem modification time.
- sha256 may be used for change tracking between snapshots.
- Empty __init__.py files are intentional package markers.
- Skipped XSD files are excluded to reduce snapshot size.
- Skipped XML files are treated as business/input data.
- config.json is excluded as sensitive runtime configuration.
- test_data and prod_data are intentionally excluded from AI snapshots.
"""
SYSTEM_INVARIANTS = """# SYSTEM INVARIANTS

Critical rules that must not be violated:

1. Monetary values
- VAT, netto, brutto and declaration totals must be calculated deterministically.
- Prefer Decimal for money calculations.
- Do not introduce float-based financial logic in new code.
- Rounding must be explicit and consistent with JPK/VAT rules.

2. XML safety
- Input XML must be parsed with defusedxml.
- Do not replace safe XML parsing with unsafe xml.etree parsing for KSeF inputs.
- Generated XML must remain XSD-valid.

3. JPK schema compliance
- Generated JPK_V7M must validate against the configured XSD.
- Namespace handling must not be changed casually.
- Optional JPK fields should be emitted only when allowed and required by schema/business logic.

4. Data lineage
- Every JPK row must be traceable back to a source invoice.
- NrKSeF, invoice number and source filename must be preserved where available.
- Deduplication must not remove invoices without a clear stable key.

5. Period filtering
- Sales invoices are filtered by sale date, with issue date fallback.
- Purchase invoices are filtered by receipt date, with issue date fallback.
- Date filtering rules must remain explicit and test-covered.

6. Corrections
- KOR invoices must not be silently ignored.
- Correction metadata must be preserved.
- Correction accounting logic must be tested before production use.

7. Validation
- Validation warnings must not disappear silently.
- Input validation, totals validation and XSD validation must remain visible in reports.
- Invalid or suspicious invoices should be reported, not hidden.

8. Sensitive data
- config.json, production invoices, generated JPK, HTML previews and CSV reports are sensitive.
- Snapshots must exclude production data and runtime secrets.
- NIP, NrKSeF, invoice numbers and counterparty names require care before external sharing.

9. Local-only behavior
- The project must remain local/offline unless explicitly changed.
- No outbound network communication should be introduced without clear justification.
"""

MODULE_RESPONSIBILITIES = """# MODULE RESPONSIBILITIES

ksef2jpk/main.py
- CLI entrypoint and pipeline orchestration.
- Loads configuration.
- Resolves input source.
- Coordinates parsing, classification, mapping, building, generation, validation and reports.
- Should not contain detailed tax mapping rules long-term.

ksef2jpk/parser/ksef_parser.py
- Parses KSeF XML into FakturaModel.
- Extracts invoice metadata, counterparties, positions, dates, NrKSeF and correction data.
- Performs basic input validation and totals checks.
- Should not generate JPK XML.
- Should not decide final declaration totals.

ksef2jpk/classifier/jpk_flags.py
- Detects candidate JPK flags and procedures.
- Handles MPP, WDT, EXP, OO, TP, SW, EE and GTU heuristics.
- Should stay conservative and avoid overconfident guesses.

ksef2jpk/classifier/gtu_classifier.py
- Loads GTU keyword rules from YAML.
- Provides configurable GTU classification.
- Should not perform VAT declaration mapping.

ksef2jpk/mapper/jpk_mapper.py
- Converts FakturaModel into WierszEwidencji rows.
- Groups invoice positions by VAT rate.
- Propagates GTU, procedures, dates, correction metadata and NrKSeF.
- Should not generate XML.
- Should not perform XSD validation.

ksef2jpk/builder/jpk_builder.py
- Builds JPK dictionary structure from sales and purchase evidence rows.
- Calculates declaration fields and control totals.
- Applies JPK-specific aggregation rules.
- Should be the main place for declaration arithmetic.

ksef2jpk/adapter/jpk_adapter.py
- Converts dictionary structure into typed JPK model objects.
- Should remain a conversion layer only.
- Should not contain business classification logic.

ksef2jpk/generator/jpk_generator.py
- Serializes JPKModel to XML.
- Handles namespaces, tags, optional fields and XML formatting.
- Should not recalculate business totals.
- Should not mutate source invoice models.

ksef2jpk/validator/validate_jpk.py
- Validates generated JPK XML against local XSD.
- Handles local schema resolution.
- Should not modify generated XML.

ksef2jpk/model/*
- Contains domain and JPK data structures.
- Should remain simple, predictable and typed where possible.

ksef2jpk/utils/*
- Contains small reusable helpers.
- Should not become a dumping ground for business logic.

tools/ai_snapshot/*
- Generates AI-readable project snapshots.
- Must avoid including secrets, production data, generated JPK files and binary documents.
- Should remain independent from tax/business pipeline execution.
"""

COMMON_AI_PITFALLS = """# COMMON AI PITFALLS

Common mistakes to avoid when modifying this project:

1. Do not use float for new money calculations.
- Existing float usage should be treated as technical debt.
- New financial logic should prefer Decimal.

2. Do not bypass validation.
- Parser warnings, totals checks and XSD validation are part of the safety model.

3. Do not hardcode taxpayer data.
- NIP, company name, tax office code, email and phone must come from config.

4. Do not emit GTU in purchase rows.
- GTU applies to sales evidence, not purchase evidence.

5. Do not assume every 0% sale is WDT or export.
- 0% VAT requires context.

6. Do not assume every foreign counterparty means WDT, EXP or IMP.
- Cross-border classification requires business/tax review.

7. Do not treat MPP as certain based only on amount.
- Amount-based MPP detection is only a candidate signal.

8. Do not remove NrKSeF fallback logic.
- Some invoices may require filename-based NrKSeF extraction.

9. Do not silently skip KOR invoices.
- Corrections must be detected, reported and eventually accounted for correctly.

10. Do not change XML namespaces without XSD regression tests.

11. Do not generate fake fallback dates for real business data.
- Missing dates should be reported.
- Fallbacks must be explicit and justified.

12. Do not mix layers.
- Parser parses.
- Mapper maps.
- Builder aggregates.
- Generator serializes.
- Validator validates.

13. Do not include production XML, config.json, generated JPK, reports or previews in AI snapshots.

14. Do not trust README blindly if snapshot status says otherwise.
- README may lag behind implementation.
"""
CRITICAL_BUSINESS_RULES = """# CRITICAL BUSINESS RULES

1. Invoice direction
- If taxpayer NIP is seller NIP, invoice is sales.
- If taxpayer NIP is buyer NIP, invoice is purchase.
- If neither matches, invoice type is unknown and must not be blindly mapped.

2. JPK period filtering
- Sales should use sale date.
- Purchase should use receipt date.
- Issue date may be used only as fallback.
- Invoices outside the selected month should be skipped when date filtering is enabled.

3. NrKSeF
- Prefer NrKSeF from XML.
- If missing, extract NrKSeF from filename when possible.
- Preserve source information: XML, filename or missing.
- NrKSeF is important for traceability and deduplication.

4. Deduplication
- Prefer NrKSeF as document identity.
- Fallback to invoice metadata only when NrKSeF is unavailable.
- Duplicate skipping must be reported.

5. VAT evidence rows
- One invoice may create multiple evidence rows.
- Positions should be grouped by VAT rate.
- Sales and purchase rows must be separated.
- Unknown invoice types should not be silently included.

6. GTU
- GTU should be assigned conservatively.
- Conflicting GTU values should not be guessed.
- Manual overrides should take precedence over heuristics.
- GTU should be emitted as GTU_XX tags in sales rows.

7. Procedures
- Procedures such as MPP, WDT, EXP, OO, IMP, TP, SW, EE require conservative handling.
- Heuristic detections should be visible in reports/debug data.
- Business/tax review is required for production certainty.

8. Corrections
- KOR invoices require special handling.
- Correction references should be preserved:
  - original invoice number
  - original invoice date
  - correction reason
- Correction values must be mapped according to tested accounting logic.

9. Declaration totals
- Declaration fields must be derived from mapped evidence rows.
- Control totals must agree with evidence rows.
- Rounding must be explicit and test-covered.

10. XML generation
- Generated XML must match JPK_V7M variant and namespace requirements.
- Required zero fields must be emitted where schema/business rules require them.
- Optional zero fields should not be emitted unless required.

11. Reports
- Quality reports must show:
  - missing NrKSeF
  - GTU/procedure detection
  - validation warnings
  - totals mismatch
  - corrections
  - skipped duplicates
  - skipped date-filtered invoices

12. Production readiness
- This project is suitable for controlled/internal use.
- Tax correctness, especially GTU/procedures/corrections/cross-border scenarios, requires deterministic review before production submission.
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
    ".lock",
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
    "uv.lock",
    "README.md",
    ".gitignore",
    ".gitattributes",
    "check.ps1",
    "fix.ps1",
    "ksef2jpk/main.py",
]


SECRET_PATTERNS = [
    (
        "possible_api_key",
        re.compile(r"(?i)\b(api[_-]?key|secret[_-]?key|token|password)\b\s*[:=]\s*['\"][^'\"]{8,}['\"]"),
    ),
    ("possible_private_key", re.compile(r"-----BEGIN (RSA |OPENSSH |EC )?PRIVATE KEY-----")),
    ("possible_jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")),
    ("possible_iban_pl", re.compile(r"\bPL\d{26}\b|\b\d{26}\b")),
    ("possible_polish_nip", re.compile(r"\b\d{10}\b")),
]
