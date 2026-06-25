@echo off
chcp 65001 >nul
cd /d "%~dp0.."
title OAM Canli Stack - Port 8787

echo.
echo  ========================================
echo   OAM Canli Entegrasyon (GERCEK MOD)
echo ========================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo [HATA] Python bulunamadi.
    pause
    exit /b 1
)

set OAM_HUB_DEMO=false
set OAM_HUB_LIVE_INTERVAL=30

echo [1/2] Bagimliliklar...
python -m pip install -q -r requirements.txt

echo [2/2] Gateway + 3 ajan baslatiliyor...
echo.
echo   The Hub:  http://127.0.0.1:8787/hub
echo   Surum:    http://127.0.0.1:8787/hub/version  (demo_mode: false)
echo.
echo   Bu pencereyi KAPATMAYIN.
echo.

python -m app.run_stack
pause
