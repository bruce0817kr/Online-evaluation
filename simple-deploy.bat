@echo off
chcp 65001 >nul
title Simple Deploy
color 0a

echo.
echo ================================================================
echo              Simple One-Click Deploy
echo ================================================================
echo.

:: Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.7+ and try again
    pause
    exit /b 1
)

echo [OK] Python found

:: Check if Docker is available
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not installed or not in PATH
    echo Please install Docker Desktop and try again
    pause
    exit /b 1
)

echo [OK] Docker found

:: Try to start Universal Port Manager
echo.
echo [Step 1] Running Python deployment script...
echo This may take a few minutes...
echo.

python quick-deploy.py

if %errorlevel% equ 0 (
    echo.
    echo ================================================================
    echo              Deployment Successful!
    echo ================================================================
    echo.
    echo Your online evaluation system should now be running.
    echo Check your web browser for the application.
    echo.
) else (
    echo.
    echo ================================================================
    echo              Deployment Failed!
    echo ================================================================
    echo.
    echo Please check the error messages above.
    echo Try running: python quick-deploy.py
    echo.
)

pause
exit /b %errorlevel%