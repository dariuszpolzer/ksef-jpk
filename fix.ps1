# ============================================
# FIX.PS1 — automatyczne poprawki
# ============================================

$ErrorActionPreference = "Stop"

Write-Host "=== BLACK ===" -ForegroundColor Cyan
python -m black ksef2jpk tests

Write-Host "`n=== RUFF FIX ===" -ForegroundColor Cyan
python -m ruff check ksef2jpk tests --fix

Write-Host "`nGotowe ✔️" -ForegroundColor Green