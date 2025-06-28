@echo off
chcp 65001 >nul
title Online Evaluation System - One Click Deploy
color 0b
echo.
echo  ========================================================
echo    Online Evaluation System One-Click Deploy
echo  ========================================================
echo.

:: Variable Settings
set PROJECT_NAME=online-evaluation
set BACKEND_SERVICE=backend
set FRONTEND_SERVICE=frontend
set SERVICES=frontend backend mongodb redis nginx
set MAX_WAIT_TIME=120
set CHECK_INTERVAL=5

:: Check Administrator Rights
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Administrator privileges required.
    echo     Please run this script as administrator.
    pause
    exit /b 1
)

echo  [OK] Administrator privileges confirmed
echo.

:: Step 1: System Diagnosis
echo  [Step 1/7] System diagnosis...
python -m universal_port_manager.cli doctor --quiet
if %errorlevel% neq 0 (
    echo  [ERROR] System diagnosis failed
    goto :error_exit
)
echo  [OK] System diagnosis completed
echo.

:: Step 2: Port Scan
echo  [Step 2/7] Scanning port usage...
python -m universal_port_manager.cli scan --range 3000-9000 --format json > port_scan_result.json
if %errorlevel% neq 0 (
    echo  [ERROR] Port scan failed
    goto :error_exit
)
echo  [OK] Port scan completed
echo.

:: Step 3: Port Allocation
echo  [Step 3/7] Allocating service ports...
python -m universal_port_manager.cli --project %PROJECT_NAME% allocate %SERVICES%
if %errorlevel% neq 0 (
    echo  [ERROR] Port allocation failed
    goto :error_exit
)
echo  [OK] Port allocation completed
echo.

:: Step 4: Generate Configuration Files
echo  [Step 4/7] Generating configuration files...
python -m universal_port_manager.cli --project %PROJECT_NAME% generate
if %errorlevel% neq 0 (
    echo  [ERROR] Configuration file generation failed
    goto :error_exit
)
echo  [OK] Configuration files generated
echo.

:: Read allocated port information
if exist ports.json (
    echo  [INFO] Allocated port information:
    type ports.json | findstr "port"
    echo.
)

:: Step 5: Docker Container Execution
echo  [Step 5/7] Starting Docker containers...

:: Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo  [WARNING] Docker is not running. Starting Docker Desktop...
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    
    echo  [WAIT] Waiting for Docker Desktop to start...
    timeout /t 30 /nobreak >nul
    
    :: Re-check Docker
    set DOCKER_WAIT=0
    :check_docker
    docker info >nul 2>&1
    if %errorlevel% equ 0 goto :docker_ready
    
    set /a DOCKER_WAIT+=5
    if %DOCKER_WAIT% geq 60 (
        echo  [ERROR] Docker Desktop failed to start (60s timeout)
        goto :error_exit
    )
    
    echo  [WAIT] Waiting for Docker... (%DOCKER_WAIT%/60s)
    timeout /t 5 /nobreak >nul
    goto :check_docker
)

:docker_ready
echo  [OK] Docker is running

:: Clean up existing containers
echo  [INFO] Cleaning up existing containers...
docker-compose -p %PROJECT_NAME% down --remove-orphans 2>nul
docker system prune -f >nul 2>&1

:: Start services with Docker Compose
if exist docker-compose.yml (
    echo  [INFO] Starting services with Docker Compose...
    docker-compose -p %PROJECT_NAME% up --build -d
    if %errorlevel% neq 0 (
        echo  [ERROR] Docker Compose execution failed
        goto :error_exit
    )
) else (
    echo  [ERROR] docker-compose.yml file not found
    goto :error_exit
)

echo  [OK] Docker containers started
echo.

:: Step 6: Service Status Check
echo  [Step 6/7] Checking service readiness...

::Enable delayed expansion for variables
setlocal EnableDelayedExpansion

:: Extract port information from JSON
set FRONTEND_PORT=3001
set BACKEND_PORT=8001

if exist ports.json (
    for /f "tokens=2 delims=:" %%a in ('type ports.json ^| findstr "frontend" ^| findstr "port"') do (
        set FRONTEND_PORT=%%a
        set FRONTEND_PORT=!FRONTEND_PORT: =!
        set FRONTEND_PORT=!FRONTEND_PORT:,=!
    )

    for /f "tokens=2 delims=:" %%a in ('type ports.json ^| findstr "backend" ^| findstr "port"') do (
        set BACKEND_PORT=%%a
        set BACKEND_PORT=!BACKEND_PORT: =!
        set BACKEND_PORT=!BACKEND_PORT:,=!
    )
)

:: Use default ports if extraction failed
if not defined FRONTEND_PORT set FRONTEND_PORT=3001
if not defined BACKEND_PORT set BACKEND_PORT=8001

echo  [INFO] Frontend port: %FRONTEND_PORT%
echo  [INFO] Backend port: %BACKEND_PORT%
echo.

:: Check service readiness
set WAIT_TIME=0
:check_services
echo  [WAIT] Checking service readiness... (%WAIT_TIME%/%MAX_WAIT_TIME%s)

:: Backend health check
curl -s -o nul -w "%%{http_code}" http://localhost:%BACKEND_PORT%/health 2>nul | findstr "200" >nul
set BACKEND_READY=%errorlevel%

:: Frontend check (simple connection check)
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:%FRONTEND_PORT%' -TimeoutSec 3 -UseBasicParsing; exit 0 } catch { exit 1 }" >nul 2>&1
set FRONTEND_READY=%errorlevel%

if %BACKEND_READY% equ 0 if %FRONTEND_READY% equ 0 (
    echo  [OK] All services ready!
    goto :services_ready
)

set /a WAIT_TIME+=%CHECK_INTERVAL%
if %WAIT_TIME% geq %MAX_WAIT_TIME% (
    echo  [WARNING] Service readiness timeout (%MAX_WAIT_TIME%s)
    echo     Will try opening web pages anyway...
    goto :services_ready
)

timeout /t %CHECK_INTERVAL% /nobreak >nul
goto :check_services

:services_ready
echo.

:: Step 7: Open Web Pages
echo  [Step 7/7] Opening web pages...

:: Open frontend page in default browser
echo  [INFO] Opening web page: http://localhost:%FRONTEND_PORT%
start "" http://localhost:%FRONTEND_PORT%

:: Optionally open backend API docs
timeout /t 2 /nobreak >nul
echo  [INFO] Opening API docs: http://localhost:%BACKEND_PORT%/docs
start "" http://localhost:%BACKEND_PORT%/docs

echo.
echo  ========================================================
echo    One-Click Deploy Completed Successfully!
echo  ========================================================
echo.
echo  [SERVICE ACCESS INFO]
echo     Frontend: http://localhost:%FRONTEND_PORT%
echo     Backend API: http://localhost:%BACKEND_PORT%
echo     API Docs: http://localhost:%BACKEND_PORT%/docs
echo.
echo  [MANAGEMENT COMMANDS]
echo     Service status: docker-compose -p %PROJECT_NAME% ps
echo     View logs: docker-compose -p %PROJECT_NAME% logs -f
echo     Stop services: docker-compose -p %PROJECT_NAME% down
echo.
echo  [TROUBLESHOOTING]
echo     If there are issues, check logs:
echo     docker-compose -p %PROJECT_NAME% logs --tail=50
echo.

pause
goto :end

:error_exit
echo.
echo  ========================================================
echo    Deploy Error Occurred!
echo  ========================================================
echo.
echo  [DEBUGGING INFO]
echo.

:: Collect debugging information
echo  [INFO] Current port status:
python -m universal_port_manager.cli --project %PROJECT_NAME% status 2>nul

echo.
echo  [INFO] Docker status:
docker-compose -p %PROJECT_NAME% ps 2>nul

echo.
echo  [INFO] Recent logs (last 10 lines):
docker-compose -p %PROJECT_NAME% logs --tail=10 2>nul

echo.
echo  [MANUAL RECOVERY COMMANDS]
echo     1. Re-allocate ports: python -m universal_port_manager.cli --project %PROJECT_NAME% allocate %SERVICES%
echo     2. Restart services: docker-compose -p %PROJECT_NAME% up --build -d
echo     3. Check logs: docker-compose -p %PROJECT_NAME% logs -f
echo.

pause
exit /b 1

:end
exit /b 0