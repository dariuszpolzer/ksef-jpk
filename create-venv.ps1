param(
    [switch]$Force,
    [switch]$Rebuild,
    [string]$PythonPath = "python"
)

Write-Host "=== Python venv manager ===" -ForegroundColor Cyan

$project = Get-Location
$venvPath = Join-Path $project "venv"
$activatePath = Join-Path $venvPath "Scripts\activate"

Write-Host "Project directory: $project"

# 1. Rebuild: remove venv completely
if ($Rebuild) {
    if (Test-Path $venvPath) {
        Write-Host "Rebuild requested. Removing existing venv..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force $venvPath
    }
}

# 2. Create venv if missing or forced
if (-not (Test-Path $venvPath) -or $Force) {
    if ($Force -and (Test-Path $venvPath)) {
        Write-Host "Force enabled. Removing existing venv..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force $venvPath
    }

    Write-Host "Creating venv using: $PythonPath" -ForegroundColor Green
    & $PythonPath -m venv venv

    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to create venv. Check PythonPath." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "venv already exists. Use -Force or -Rebuild to recreate." -ForegroundColor Yellow
}

# 3. Activate venv
if (Test-Path $activatePath) {
    Write-Host "Activating venv..." -ForegroundColor Green
    & $activatePath
} else {
    Write-Host "ERROR: Activation script not found." -ForegroundColor Red
    exit 1
}

# 4. Create requirements.txt if missing
$reqFile = Join-Path $project "requirements.txt"

if (-not (Test-Path $reqFile)) {
    Write-Host "Generating requirements.txt..." -ForegroundColor Green
    pip freeze > $reqFile
} else {
    Write-Host "requirements.txt already exists." -ForegroundColor Yellow
}

Write-Host "Done. venv is active." -ForegroundColor Cyan
