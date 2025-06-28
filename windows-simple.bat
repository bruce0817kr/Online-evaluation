@echo off
chcp 65001 >nul
title Windows Simple Deploy
color 0a

echo.
echo ================================================================
echo              Windows Simple Deploy
echo ================================================================
echo.

:: Check if we're in the right directory
if not exist "docker-compose.yml" (
    echo [ERROR] docker-compose.yml not found
    echo Please run this from the project root directory
    pause
    exit /b 1
)

echo [OK] Project directory confirmed

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found
    pause
    exit /b 1
)
echo [OK] Python found

:: Check Docker
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker not found
    pause
    exit /b 1
)
echo [OK] Docker found

:: Run Windows-specific deployment
echo.
echo [INFO] Starting Windows deployment script...
echo This will use a simplified approach that bypasses encoding issues.
echo.

python windows-deploy.py

echo.
echo [INFO] Deployment script completed
echo Check the output above for any errors
echo.

pause