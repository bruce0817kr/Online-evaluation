@echo off
chcp 65001 >nul
title Environment Test
echo.
echo ================================================================
echo                Environment Test
echo ================================================================
echo.

echo [TEST 1] Checking Code Page...
echo Current code page: %ERRORLEVEL%
echo.

echo [TEST 2] Checking Python...
python --version
if %errorlevel% neq 0 (
    echo [ERROR] Python not found
) else (
    echo [OK] Python found
)
echo.

echo [TEST 3] Checking Docker...
docker --version
if %errorlevel% neq 0 (
    echo [ERROR] Docker not found
) else (
    echo [OK] Docker found
)
echo.

echo [TEST 4] Checking Universal Port Manager...
python -c "import sys; sys.path.append('.'); from universal_port_manager import cli; print('UPM module found')"
if %errorlevel% neq 0 (
    echo [ERROR] Universal Port Manager module not found
) else (
    echo [OK] Universal Port Manager module found
)
echo.

echo [TEST 5] Checking current directory...
echo Current directory: %CD%
dir /b | findstr "docker-compose.yml"
if %errorlevel% neq 0 (
    echo [ERROR] docker-compose.yml not found in current directory
) else (
    echo [OK] docker-compose.yml found
)
echo.

echo [TEST 6] Quick Port Manager Test...
python -m universal_port_manager.cli doctor
echo.

echo ================================================================
echo                Environment Test Complete
echo ================================================================
echo.
echo If all tests pass, you can try running:
echo   one-click-deploy.bat    (Full deployment)
echo   simple-deploy.bat       (Simple deployment)
echo   python quick-deploy.py  (Cross-platform)
echo.

pause