@echo off
chcp 65001 >nul
title Manual Deploy Guide
color 0b

echo.
echo ================================================================
echo              Manual Deployment Guide
echo ================================================================
echo.
echo This script will guide you through manual deployment steps
echo if the automatic deployment fails.
echo.

:menu
echo Choose an option:
echo.
echo 1. Check environment
echo 2. Clean up existing containers
echo 3. Start containers with default ports
echo 4. Check container status
echo 5. View container logs
echo 6. Stop all containers
echo 7. Exit
echo.
set /p choice="Enter your choice (1-7): "

if "%choice%"=="1" goto check_env
if "%choice%"=="2" goto cleanup
if "%choice%"=="3" goto start_containers
if "%choice%"=="4" goto check_status
if "%choice%"=="5" goto view_logs
if "%choice%"=="6" goto stop_containers
if "%choice%"=="7" goto exit
goto menu

:check_env
echo.
echo [Step 1] Environment Check
echo ========================
echo.
echo Checking Python...
python --version
echo.
echo Checking Docker...
docker --version
echo.
echo Checking Docker daemon...
docker info | findstr "Server Version"
echo.
echo Checking current directory...
dir | findstr "docker-compose.yml"
echo.
pause
goto menu

:cleanup
echo.
echo [Step 2] Cleanup
echo ===============
echo.
echo Stopping existing containers...
docker-compose -p online-evaluation down --remove-orphans
echo.
echo Removing unused Docker resources...
docker system prune -f
echo.
echo Cleanup completed
pause
goto menu

:start_containers
echo.
echo [Step 3] Start Containers
echo ========================
echo.
echo Creating simple override file...
echo version: '3.8' > docker-compose.override.yml
echo. >> docker-compose.override.yml
echo services: >> docker-compose.override.yml
echo   frontend: >> docker-compose.override.yml
echo     ports: >> docker-compose.override.yml
echo       - "3001:3000" >> docker-compose.override.yml
echo   backend: >> docker-compose.override.yml
echo     ports: >> docker-compose.override.yml
echo       - "8001:8000" >> docker-compose.override.yml
echo   mongodb: >> docker-compose.override.yml
echo     ports: >> docker-compose.override.yml
echo       - "27018:27017" >> docker-compose.override.yml
echo   redis: >> docker-compose.override.yml
echo     ports: >> docker-compose.override.yml
echo       - "6381:6379" >> docker-compose.override.yml
echo.
echo Starting containers...
docker-compose -p online-evaluation up --build -d
echo.
echo Containers started. Default ports:
echo   Frontend: http://localhost:3001
echo   Backend: http://localhost:8001
echo   API Docs: http://localhost:8001/docs
echo.
echo Opening web pages...
start http://localhost:3001
timeout /t 3 /nobreak >nul
start http://localhost:8001/docs
echo.
pause
goto menu

:check_status
echo.
echo [Step 4] Container Status
echo ========================
echo.
docker-compose -p online-evaluation ps
echo.
pause
goto menu

:view_logs
echo.
echo [Step 5] Container Logs
echo ======================
echo.
echo Choose which logs to view:
echo 1. All services
echo 2. Frontend only
echo 3. Backend only
echo 4. MongoDB only
echo.
set /p log_choice="Enter choice (1-4): "

if "%log_choice%"=="1" docker-compose -p online-evaluation logs --tail=20
if "%log_choice%"=="2" docker-compose -p online-evaluation logs --tail=20 frontend
if "%log_choice%"=="3" docker-compose -p online-evaluation logs --tail=20 backend
if "%log_choice%"=="4" docker-compose -p online-evaluation logs --tail=20 mongodb
echo.
pause
goto menu

:stop_containers
echo.
echo [Step 6] Stop Containers
echo =======================
echo.
docker-compose -p online-evaluation down
echo.
echo All containers stopped
pause
goto menu

:exit
echo.
echo Goodbye!
exit /b 0