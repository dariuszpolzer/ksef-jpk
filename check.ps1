# ============================================
# CHECK.PS1 — testy + lint + format + security
# ============================================

$ErrorActionPreference = "Stop"

$src = "ksef2jpk"
$tests = "tests"

if (-not (Test-Path $src)) {
    Write-Host "Źródło nie istnieje: $src" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $tests)) {
    Write-Host "Katalog testów nie istnieje: $tests" -ForegroundColor Red
    exit 1
}

Write-Host "=== PYTEST ===" -ForegroundColor Cyan
python -m pytest -v
if ($LASTEXITCODE -ne 0) {
    Write-Host "`nPYTEST FAILED ❌" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "`n=== RUFF ===" -ForegroundColor Cyan
python -m ruff check $src $tests
if ($LASTEXITCODE -ne 0) {
    Write-Host "`nRUFF FAILED ❌" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "`n=== BLACK (check) ===" -ForegroundColor Cyan
python -m black --check $src $tests
if ($LASTEXITCODE -ne 0) {
    Write-Host "`nBLACK FAILED ❌" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "`n=== BANDIT ===" -ForegroundColor Cyan
python -m bandit -r $src
if ($LASTEXITCODE -ne 0) {
    Write-Host "`nBANDIT FAILED ❌" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "`n============================================" -ForegroundColor Green
Write-Host "Wszystkie testy zakończone sukcesem ✔️" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green

exit 0