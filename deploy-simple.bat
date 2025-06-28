@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

:: ===================================================================
:: Online Evaluation System - 간단 배포 (Windows)
:: ===================================================================

echo.
echo ====================================================================
echo                  Online Evaluation System                      
echo                     간단 원클릭 배포 시스템                    
echo                        v1.0 Simple                         
echo ====================================================================
echo.

:: 현재 시간
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "timestamp=%dt:~0,8%_%dt:~8,6%"

echo [INFO] 배포를 시작합니다... (%timestamp%)
echo.

:: Python 확인
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python이 설치되지 않았습니다.
    echo [INFO] https://python.org 에서 Python을 다운로드하세요.
    pause
    exit /b 1
)
echo [OK] Python 확인 완료

:: Docker 확인
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Docker가 설치되지 않았습니다.
    echo [INFO] https://docker.com 에서 Docker Desktop을 다운로드하세요.
    echo [INFO] Docker 없이 계속 진행합니다...
) else (
    echo [OK] Docker 확인 완료
)

:: Node.js 확인
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Node.js가 설치되지 않았습니다.
    echo [INFO] https://nodejs.org 에서 Node.js를 다운로드하세요.
) else (
    echo [OK] Node.js 확인 완료
)

echo.
echo 배포 방법을 선택하세요:
echo [1] 개발 환경 (로컬)
echo [2] Docker 환경 (권장)
echo [0] 취소
echo.
set /p deploy_choice="선택 (1-2, 0): "

if "%deploy_choice%"=="1" goto local_deploy
if "%deploy_choice%"=="2" goto docker_deploy
if "%deploy_choice%"=="0" goto exit_script
goto invalid_choice

:local_deploy
echo.
echo [INFO] 로컬 개발 환경으로 배포합니다...
echo.

:: 환경 파일 생성
if not exist ".env" (
    echo [INFO] .env 파일을 생성합니다...
    (
        echo NODE_ENV=development
        echo BACKEND_PORT=8080
        echo PORT=3000
        echo REACT_APP_BACKEND_URL=http://localhost:8080
        echo MONGO_URL=mongodb://admin:password123@localhost:27017/online_evaluation
        echo JWT_SECRET=dev-secret-key
        echo CORS_ORIGINS=http://localhost:3000
        echo UPLOAD_DIR=./uploads
    ) > .env
    echo [OK] .env 파일이 생성되었습니다
)

:: 백엔드 의존성 설치
echo [INFO] 백엔드 의존성을 설치합니다...
cd backend
if exist "requirements.txt" (
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] 백엔드 의존성 설치 실패
        pause
        exit /b 1
    )
    echo [OK] 백엔드 의존성 설치 완료
)

:: 백엔드 서버 시작
echo [INFO] 백엔드 서버를 시작합니다...
start "Backend Server" cmd /k "python -m uvicorn server:app --reload --port 8080"
cd ..

:: 프론트엔드 의존성 설치
echo [INFO] 프론트엔드 의존성을 설치합니다...
cd frontend
if exist "package.json" (
    npm install
    if %errorlevel% neq 0 (
        echo [ERROR] 프론트엔드 의존성 설치 실패
        pause
        exit /b 1
    )
    echo [OK] 프론트엔드 의존성 설치 완료
)

:: 프론트엔드 서버 시작
echo [INFO] 프론트엔드 서버를 시작합니다...
start "Frontend Server" cmd /k "npm start"
cd ..

echo.
echo [SUCCESS] 로컬 개발 환경 배포가 완료되었습니다!
echo.
echo 서비스 정보:
echo   프론트엔드: http://localhost:3000
echo   백엔드 API: http://localhost:8080
echo   API 문서:   http://localhost:8080/docs
echo.
echo 잠시 후 브라우저가 자동으로 열립니다...
timeout /t 5 /nobreak > nul
start http://localhost:3000
goto end_script

:docker_deploy
echo.
echo [INFO] Docker 환경으로 배포합니다...
echo.

:: Docker 실행 확인
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker가 실행되지 않았습니다.
    echo [INFO] Docker Desktop을 시작하고 다시 시도하세요.
    pause
    exit /b 1
)

:: 기존 컨테이너 정리
echo [INFO] 기존 컨테이너를 정리합니다...
docker-compose down --remove-orphans >nul 2>&1

:: Docker Compose 확인
if not exist "docker-compose.yml" (
    echo [ERROR] docker-compose.yml 파일을 찾을 수 없습니다.
    pause
    exit /b 1
)

:: 서비스 시작
echo [INFO] Docker 서비스를 시작합니다...
docker-compose up --build -d
if %errorlevel% neq 0 (
    echo [ERROR] Docker 서비스 시작 실패
    echo [INFO] 로그를 확인하세요: docker-compose logs
    pause
    exit /b 1
)

:: 서비스 준비 대기
echo [INFO] 서비스가 준비될 때까지 기다립니다...
timeout /t 30 /nobreak > nul

:: 서비스 상태 확인
echo [INFO] 서비스 상태를 확인합니다...
docker-compose ps

echo.
echo [SUCCESS] Docker 환경 배포가 완료되었습니다!
echo.
echo 서비스 정보:
echo   프론트엔드: http://localhost:3000
echo   백엔드 API: http://localhost:8080
echo   API 문서:   http://localhost:8080/docs
echo.
echo 관리 명령어:
echo   상태 확인: docker-compose ps
echo   로그 확인: docker-compose logs -f
echo   서비스 중지: docker-compose down
echo.
echo 잠시 후 브라우저가 자동으로 열립니다...
timeout /t 5 /nobreak > nul
start http://localhost:3000
goto end_script

:invalid_choice
echo [ERROR] 잘못된 선택입니다.
pause
exit /b 1

:exit_script
echo [INFO] 배포가 취소되었습니다.
goto end_script

:end_script
echo.
echo 배포 스크립트를 종료합니다.
pause
exit /b 0