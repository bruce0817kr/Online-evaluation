@echo off
chcp 65001 >nul
title Fixed Deploy - Docker Issues Resolved
color 0a

echo.
echo ================================================================
echo              Fixed Deploy - Docker Issues Resolved
echo ================================================================
echo.
echo This script uses the fixed deployment that bypasses Dockerfile
echo path issues by using base Docker images instead of custom builds.
echo.

:: Quick checks
if not exist "docker-compose.yml" (
    echo [ERROR] Not in project directory
    pause
    exit /b 1
)

if not exist "fixed-deploy.py" (
    echo [ERROR] fixed-deploy.py not found
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
echo Starting fixed deployment...
echo.

python fixed-deploy.py

echo.
echo Fixed deployment script finished.
pause