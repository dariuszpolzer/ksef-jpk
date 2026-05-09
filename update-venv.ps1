param(
    [string]$VenvPath = ".\venv",
    [string]$Requirements = ".\requirements.txt"
)

Write-Host "=== UPDATE VENV START ===" -ForegroundColor Cyan

# 1. Sprawdzenie istnienia venv
if (-not (Test-Path "$VenvPath\Scripts\Activate.ps1")) {
    Write-Host "Brak środowiska venv w: $VenvPath" -ForegroundColor Red
    exit 1
}

# 2. Aktywacja venv
Write-Host "Aktywuję venv..." -ForegroundColor Cyan
& "$VenvPath\Scripts\Activate.ps1"

# 3. Raport przed aktualizacją
Write-Host "`n--- Paczki przed aktualizacją ---" -ForegroundColor Yellow
pip list

# 4. Aktualizacja wg requirements.txt (jeśli istnieje)
if (Test-Path $Requirements) {
    Write-Host "`nAktualizuję paczki z $Requirements..." -ForegroundColor Cyan
    pip install --upgrade -r $Requirements
}
else {
    Write-Host "`nBrak pliku requirements.txt — pomijam ten krok." -ForegroundColor DarkYellow
}

# 5. Pobranie listy przestarzałych paczek (pip 26.x kompatybilne)
Write-Host "`nSprawdzam przestarzałe paczki..." -ForegroundColor Cyan
$outdated = pip list --outdated --format=json | ConvertFrom-Json

if ($outdated.Count -eq 0) {
    Write-Host "Brak przestarzałych paczek — środowisko jest aktualne." -ForegroundColor Green
}
else {
    Write-Host "`n--- Aktualizuję przestarzałe paczki ---" -ForegroundColor Yellow
    foreach ($pkg in $outdated) {
        Write-Host "Aktualizuję $($pkg.name)..." -ForegroundColor Cyan
        pip install --upgrade $pkg.name
    }
}

# 6. Raport końcowy
Write-Host "`n--- Paczki po aktualizacji ---" -ForegroundColor Yellow
pip list

Write-Host "`n=== UPDATE VENV DONE ===" -ForegroundColor Green
