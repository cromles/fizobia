# Veridag The Hub - OAM Gateway baslat
Set-Location (Split-Path $PSScriptRoot -Parent)

Write-Host ""
Write-Host "  Veridag The Hub - OAM Gateway" -ForegroundColor Cyan
Write-Host ""

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "[HATA] Python bulunamadi." -ForegroundColor Red
    exit 1
}

Write-Host "[1/2] Bagimliliklar..."
python -m pip install -q -r requirements.txt

Write-Host "[2/2] Gateway baslatiliyor..."
Write-Host ""
Write-Host "  http://127.0.0.1:8787/hub" -ForegroundColor Green
Write-Host "  Ctrl+C ile durdurun. Bu terminali acik birakin." -ForegroundColor Yellow
Write-Host ""

python -m app.main
