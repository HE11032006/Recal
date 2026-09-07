$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot\..

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    py -3.11 -m venv .venv
}

.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev,agent,search]"

if (-not (Test-Path ".env")) {
    Copy-Item .env.example .env
    Write-Host ".env créé depuis .env.example. Vérifiez sa configuration avant de lancer l’API."
}

Write-Host "Environnement backend prêt. Activation interactive : .\.venv\Scripts\Activate.ps1"
