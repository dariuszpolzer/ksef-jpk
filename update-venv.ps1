$ErrorActionPreference = "Stop"

Write-Host "=== UV SYNC START ===" -ForegroundColor Cyan

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "Nie znaleziono uv. Zainstaluj uv: https://docs.astral.sh/uv/" -ForegroundColor Red
    exit 1
}

uv sync --extra dev

if ($LASTEXITCODE -ne 0) {
    Write-Host "`nUV SYNC FAILED" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "`n--- Paczki w środowisku uv ---" -ForegroundColor Yellow
uv pip list

Write-Host "`n=== UV SYNC DONE ===" -ForegroundColor Green
