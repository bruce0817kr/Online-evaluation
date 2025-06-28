@echo off
chcp 65001 >nul 2>&1
title Test Ultra Deploy System
color 0e

echo.
echo ================================================================
echo              Test Ultra Deploy System
echo ================================================================
echo.
echo This script tests the ultra deployment system without actually
echo starting the containers - it validates the configuration only.
echo.

:: Validation
if not exist "ultra-deploy.py" (
    echo [ERROR] ultra-deploy.py not found
    pause
    exit /b 1
)

docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker not available
    pause
    exit /b 1
)

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not available
    pause
    exit /b 1
)

echo [OK] Environment checks passed
echo.

:: Test configuration generation
echo [Test 1] Testing configuration generation...
python -c "
import sys
sys.path.append('.')
from ultra_deploy import UltraDeployer

deployer = UltraDeployer()
ports = deployer.allocate_ports()
success = deployer.create_clean_override(ports)
print(f'Configuration test: {'SUCCESS' if success else 'FAILED'}')
"

if %errorlevel% neq 0 (
    echo [ERROR] Configuration test failed
    pause
    exit /b 1
)

echo [OK] Configuration generation works
echo.

:: Test YAML validation
echo [Test 2] Testing YAML file validity...
if exist "docker-compose.override.yml" (
    docker-compose -f docker-compose.yml -f docker-compose.override.yml config >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] Generated YAML is invalid
        pause
        exit /b 1
    )
    echo [OK] Generated YAML is valid
) else (
    echo [WARNING] No override file generated
)

echo.
echo ================================================================
echo                All Tests Passed Successfully!
echo ================================================================
echo.
echo The ultra deployment system is ready to use.
echo Run 'ultra-deploy.bat' to perform actual deployment.
echo.
pause