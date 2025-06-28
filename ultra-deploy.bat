@echo off
chcp 65001 >nul 2>&1
title Ultra Deploy - Zero Errors Guaranteed
color 0f

echo.
echo ================================================================
echo              Ultra Deploy - Zero Errors Guaranteed
echo ================================================================
echo.
echo This deployment system eliminates:
echo   - UTF-8 BOM issues
echo   - Korean text encoding problems
echo   - Docker Compose version warnings
echo   - YAML formatting errors
echo.

:: Environment validation
echo [Validation] Checking environment...

if not exist "docker-compose.yml" (
    echo [ERROR] Not in project directory
    echo Make sure you are in the Online-evaluation folder
    pause
    exit /b 1
)

if not exist "ultra-deploy.py" (
    echo [ERROR] ultra-deploy.py not found
    pause
    exit /b 1
)

docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker not found or not running
    echo Please start Docker Desktop and try again
    pause
    exit /b 1
)

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

echo [OK] All checks passed
echo.

:: Clean any problematic files
echo [Cleanup] Removing problematic files...
if exist "docker-compose.override.yml" del /f /q "docker-compose.override.yml" >nul 2>&1
echo [OK] Cleanup completed
echo.

:: Execute ultra deployment
echo [Deploy] Starting ultra deployment...
echo.

python ultra-deploy.py

echo.
echo ================================================================
echo                    Deployment Process Complete
echo ================================================================
echo.
echo If deployment succeeded, your services should now be running.
echo If there were any issues, check the output above for details.
echo.
pause