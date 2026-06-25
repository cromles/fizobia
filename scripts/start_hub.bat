@echo off
chcp 65001 >nul
cd /d "%~dp0.."
title OAM Hub - Port 8787

echo.
echo  ========================================
echo   Veridag The Hub - OAM Gateway
echo  ========================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo [HATA] Python bulunamadi. https://python.org adresinden kurun.
    pause
    exit /b 1
)

echo [1/2] Bagimliliklar kontrol ediliyor...
python -m pip install -q -r requirements.txt
if errorlevel 1 (
    echo [HATA] pip install basarisiz.
    pause
    exit /b 1
)

echo [2/2] Gateway baslatiliyor...
echo.
echo   Tarayici:  http://127.0.0.1:8787/hub
echo   Saglik:    http://127.0.0.1:8787/health
echo.
echo   DURDURMAK ICIN: Ctrl+C
echo   Bu pencereyi KAPATMAYIN.
echo.

python -m app.main
pause
