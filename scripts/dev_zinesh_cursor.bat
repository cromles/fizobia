@echo off
chcp 65001 >nul
cd /d "%~dp0.."
title Zinesh + Hub — Cursor Dev

set OAM_HUB_DEMO=false
set OAM_PUBLIC_BASE_URL=http://127.0.0.1:8787
set OAM_CORS_ORIGINS=http://127.0.0.1:3000,http://localhost:3000,https://zinesh.com

echo.
echo  Zinesh site:  http://127.0.0.1:3000
echo  Hub API:      http://127.0.0.1:8787/hub/sdk/config
echo.
echo  Cursor workspace: fizobia-zinesh.code-workspace
echo.

start "OAM Hub" cmd /k "python -m app.run_stack"
timeout /t 4 /nobreak >nul
start "Zinesh Web" cmd /k "cd zinesh-web && python -m http.server 3000"
echo Iki pencere acildi. Tarayicida http://127.0.0.1:3000 acin.
pause
