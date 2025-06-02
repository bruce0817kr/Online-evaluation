@echo off
setlocal EnableDelayedExpansion

REM 온라인 평가 시스템 빌드 및 배포 스크립트 (Windows)
REM 사용법: build-and-deploy.bat [production|development] [명령어]

set ENVIRONMENT=%1
if "%ENVIRONMENT%"=="" set ENVIRONMENT=development

set COMMAND=%2
if "%COMMAND%"=="" set COMMAND=full

set PROJECT_NAME=online-evaluation

echo ===============================================
echo 온라인 평가 시스템 빌드 및 배포 스크립트
echo ===============================================
echo 환경: %ENVIRONMENT%
echo 명령어: %COMMAND%
echo 프로젝트: %PROJECT_NAME%
echo ===============================================

REM 사전 검사
:check_requirements
echo [INFO] 시스템 요구사항 확인 중...

docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker가 설치되지 않았습니다.
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Compose가 설치되지 않았습니다.
    pause
    exit /b 1
)

if not exist ".env.%ENVIRONMENT%" (
    echo [ERROR] .env.%ENVIRONMENT% 파일이 없습니다.
    pause
    exit /b 1
)

echo [INFO] 시스템 요구사항 확인 완료

REM 환경변수 파일 복사
copy ".env.%ENVIRONMENT%" .env >nul

if "%COMMAND%"=="build" goto build_images
if "%COMMAND%"=="deploy" goto deploy_containers
if "%COMMAND%"=="restart" goto restart_services
if "%COMMAND%"=="stop" goto stop_services
if "%COMMAND%"=="backup" goto create_backup
if "%COMMAND%"=="logs" goto show_logs
if "%COMMAND%"=="full" goto full_deployment
goto show_help

:build_images
echo [INFO] Docker 이미지 빌드 중...
docker-compose build --no-cache
if errorlevel 1 (
    echo [ERROR] 이미지 빌드 실패
    pause
    exit /b 1
)
echo [INFO] Docker 이미지 빌드 완료
if "%COMMAND%"=="build" goto end
goto deploy_containers

:deploy_containers
echo [INFO] 컨테이너 배포 중...

REM 기존 컨테이너 중지
docker-compose down

REM 새 컨테이너 시작
docker-compose up -d
if errorlevel 1 (
    echo [ERROR] 컨테이너 시작 실패
    pause
    exit /b 1
)

REM 헬스 체크
echo [INFO] 서비스 헬스 체크 중...
timeout /t 15 /nobreak >nul

REM 서비스 상태 확인
curl -f http://localhost:8080/health >nul 2>&1
if errorlevel 1 (
    echo [WARN] 백엔드 서비스 헬스 체크 실패 (서비스가 시작 중일 수 있습니다)
) else (
    echo [INFO] 백엔드 서비스 정상
)

curl -f http://localhost:3000 >nul 2>&1
if errorlevel 1 (
    echo [WARN] 프론트엔드 서비스 헬스 체크 실패 (서비스가 시작 중일 수 있습니다)
) else (
    echo [INFO] 프론트엔드 서비스 정상
)

echo [INFO] 컨테이너 배포 완료
goto check_services

:restart_services
echo [INFO] 서비스 재시작 중...
docker-compose restart
goto check_services

:stop_services
echo [INFO] 서비스 중지 중...
docker-compose down
goto end

:create_backup
echo [INFO] 데이터 백업 생성 중...
set BACKUP_DIR=backups\%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set BACKUP_DIR=%BACKUP_DIR: =0%
mkdir "%BACKUP_DIR%" 2>nul

REM MongoDB 백업
for /f "tokens=*" %%i in ('docker-compose ps -q mongodb') do set MONGODB_CONTAINER=%%i
docker exec %MONGODB_CONTAINER% mongodump --out /tmp/backup
docker cp %MONGODB_CONTAINER%:/tmp/backup "%BACKUP_DIR%\mongodb"

REM 설정 파일 백업
xcopy scripts "%BACKUP_DIR%\scripts\" /E /I >nul
copy .env "%BACKUP_DIR%\" >nul
copy docker-compose.yml "%BACKUP_DIR%\" >nul

echo [INFO] 백업 생성 완료: %BACKUP_DIR%
goto end

:show_logs
docker-compose logs -f
goto end

:full_deployment
call :build_images
call :deploy_containers
goto check_services

:check_services
echo.
echo ===============================================
echo 서비스 상태 확인
echo ===============================================
docker-compose ps

echo.
echo ===============================================
echo 서비스 접속 정보
echo ===============================================
echo 프론트엔드: http://localhost:3000
echo 백엔드 API: http://localhost:8080
echo MongoDB: mongodb://localhost:27017
echo Redis: redis://localhost:6379
echo.
echo ===============================================
echo 로그 확인 명령어
echo ===============================================
echo 전체 로그: docker-compose logs -f
echo 백엔드 로그: docker-compose logs -f backend
echo 프론트엔드 로그: docker-compose logs -f frontend
echo.
echo 배포 완료! 위 URL로 접속하여 시스템을 확인하세요.
goto end

:show_help
echo.
echo 온라인 평가 시스템 관리 스크립트 (Windows)
echo.
echo 사용법: %0 [환경] [명령어]
echo.
echo 환경:
echo   development (기본값) - 개발 환경
echo   production          - 프로덕션 환경
echo.
echo 명령어:
echo   build     - Docker 이미지 빌드
echo   deploy    - 컨테이너 배포 및 실행
echo   restart   - 서비스 재시작
echo   stop      - 서비스 중지
echo   backup    - 데이터 백업
echo   logs      - 실시간 로그 확인
echo   full      - 빌드 + 배포 (기본값, 전체 과정)
echo.
echo 예시:
echo   %0 production full    # 프로덕션 환경으로 전체 배포
echo   %0 development build  # 개발 환경으로 이미지 빌드
echo   %0 development deploy # 개발 환경으로 배포

:end
echo.
echo 스크립트 실행 완료.
pause
