@echo off
chcp 65001 >nul
title Quick Fix Deploy
color 0c

echo.
echo ================================================================
echo              Quick Fix Deploy
echo ================================================================
echo.
echo This script bypasses the Universal Port Manager CLI issues
echo and deploys the system using a direct approach.
echo.

:: Quick checks
if not exist "docker-compose.yml" (
    echo [ERROR] Not in project directory
    pause
    exit /b 1
)

docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker not found
    pause
    exit /b 1
)

echo [OK] Environment checks passed
echo.
echo Starting bypass deployment...
echo.

python bypass-deploy.py

echo.
echo Deployment script finished.
pause