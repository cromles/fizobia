@echo off
chcp 65001 >nul
cd /d "%~dp0.."
title OAM On-Chain Stack

echo.
echo  ========================================
echo   OAM + MetaMask On-Chain Staking
echo ========================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo [HATA] Python bulunamadi.
    pause
    exit /b 1
)

where npx >nul 2>&1
if errorlevel 1 (
    echo [HATA] Node.js / npx bulunamadi.
    pause
    exit /b 1
)

set OAM_HUB_DEMO=false
set OAM_ONCHAIN_ENABLED=true
set OAM_ONCHAIN_REQUIRE_TX=true
set OAM_ONCHAIN_OPERATOR_KEY=0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80

echo [1/3] Bagimliliklar...
python -m pip install -q -r requirements.txt
call npm install

echo [2/3] Hardhat node + deploy (ayri pencerede node acin):
echo   Pencere 1: npx hardhat node
echo   Pencere 2: npm run deploy:local
echo   MetaMask: chain 31337, RPC http://127.0.0.1:8545
echo.

echo [3/3] Gateway baslatiliyor...
python -m app.run_stack
pause
