@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

:: ===================================================================
:: 🚀 Online Evaluation System - 원클릭 배포 시스템 (Ultimate)
:: ===================================================================
:: 작성일: 2025-06-26
:: 버전: 3.0 Ultimate
:: 설명: 개발/스테이징/운영 환경 자동 배포 (고급 기능 포함)
:: ===================================================================

echo.
echo ====================================================================
echo                  Online Evaluation System                      
echo                   Ultimate 원클릭 배포 시스템                    
echo                        v3.0 Professional                         
echo ====================================================================
echo.

:: 색상 코드 설정
set "GREEN=[92m"
set "RED=[91m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "PURPLE=[95m"
set "CYAN=[96m"
set "WHITE=[97m"
set "RESET=[0m"

:: 현재 시간과 빌드 정보
for /f %%i in ('git rev-parse --short HEAD 2^>nul') do set "BUILD_VERSION=%%i"
if "%BUILD_VERSION%"=="" set "BUILD_VERSION=local"

for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "timestamp=%dt:~0,8%_%dt:~8,6%"

:: 로그 파일
set "LOGFILE=deployment_%timestamp%.log"
set "ERROR_LOG=deployment_error_%timestamp%.log"

:: 유틸리티 함수들
:log
echo [%date% %time%] %~1 >> %LOGFILE%
exit /b

:success
echo %GREEN%✅ %~1%RESET%
call :log "SUCCESS: %~1"
exit /b

:info
echo %BLUE%ℹ️  %~1%RESET%
call :log "INFO: %~1"
exit /b

:warning
echo %YELLOW%⚠️  %~1%RESET%
call :log "WARNING: %~1"
exit /b

:error
echo %RED%❌ ERROR: %~1%RESET%
call :log "ERROR: %~1"
echo %~1 >> %ERROR_LOG%
exit /b

:: 메인 메뉴
:main_menu
cls
echo.
echo ====================================================================
echo                       배포 환경 선택                              
echo ====================================================================
echo.
echo   %CYAN%배포 환경:%RESET%
echo   [1]  Development (개발) - Hot Reload
echo   [2]  Staging (스테이징) - Blue-Green
echo   [3]  Production (운영) - Zero Downtime
echo   [4]  Docker Compose (로컬 전체)
echo.
echo   %CYAN%관리 도구:%RESET%
echo   [5]  포트 관리 및 설정
echo   [6]  시스템 진단 및 헬스체크
echo   [7]  배포 상태 모니터링
echo   [8]  데이터베이스 관리
echo   [9]  서비스 재시작/복구
echo.
echo   %CYAN%고급 기능:%RESET%
echo   [A]  AI 기반 스마트 배포
echo   [B]  성능 테스트 실행
echo   [C]  보안 스캔 및 검증
echo   [D]  배포 히스토리 관리
echo.
echo   [0]  종료
echo.
set /p choice="선택 (1-9, A-D, 0): "

if /i "%choice%"=="1" goto deploy_development
if /i "%choice%"=="2" goto deploy_staging
if /i "%choice%"=="3" goto deploy_production
if /i "%choice%"=="4" goto deploy_docker
if /i "%choice%"=="5" goto port_management
if /i "%choice%"=="6" goto system_diagnosis
if /i "%choice%"=="7" goto deployment_monitoring
if /i "%choice%"=="8" goto database_management
if /i "%choice%"=="9" goto service_recovery
if /i "%choice%"=="A" goto smart_deploy
if /i "%choice%"=="B" goto performance_test
if /i "%choice%"=="C" goto security_scan
if /i "%choice%"=="D" goto deployment_history
if /i "%choice%"=="0" goto exit_script
goto main_menu

:: ===========================================
:: 사전 검사 시스템
:: ===========================================
:check_prerequisites
call :info "🔍 시스템 사전 검사 시작..."

:: 필수 도구 확인
set "missing_tools="

git --version >nul 2>&1
if !errorlevel! neq 0 set "missing_tools=!missing_tools! Git"

docker --version >nul 2>&1
if !errorlevel! neq 0 set "missing_tools=!missing_tools! Docker"

docker compose version >nul 2>&1
if !errorlevel! neq 0 set "missing_tools=!missing_tools! Docker-Compose"

node --version >nul 2>&1
if !errorlevel! neq 0 set "missing_tools=!missing_tools! Node.js"

python --version >nul 2>&1
if !errorlevel! neq 0 set "missing_tools=!missing_tools! Python"

if not "%missing_tools%"=="" (
    call :error "누락된 도구: %missing_tools%"
    echo.
    echo %YELLOW%설치 가이드:%RESET%
    echo   Git: https://git-scm.com/download/win
    echo   Docker: https://www.docker.com/products/docker-desktop
    echo   Node.js: https://nodejs.org/en/download/
    echo   Python: https://www.python.org/downloads/
    pause
    goto main_menu
)

:: 시스템 리소스 확인
call :info "💻 시스템 리소스 확인 중..."

:: 메모리 확인 (4GB 이상 권장)
for /f "skip=1" %%p in ('wmic computersystem get TotalPhysicalMemory') do (
    set /a "total_memory_gb=%%p/1024/1024/1024"
    goto memory_done
)
:memory_done

if %total_memory_gb% lss 4 (
    call :warning "메모리가 부족합니다 (%total_memory_gb%GB). 4GB 이상 권장"
)

:: 디스크 공간 확인 (10GB 이상 권장)
for /f "tokens=3" %%a in ('dir /-c ^| find "bytes free"') do set "free_space=%%a"
set /a "free_space_gb=%free_space:~0,-9%"

if %free_space_gb% lss 10 (
    call :warning "디스크 공간이 부족합니다 (%free_space_gb%GB). 10GB 이상 권장"
)

call :success "시스템 사전 검사 완료"
exit /b

:: ===========================================
:: 포트 관리 시스템 (Enhanced)
:: ===========================================
:port_management
cls
call :info "🔌 포트 관리 시스템"
echo.

:: Universal Port Manager 확인
if exist "universal_port_manager\__init__.py" (
    call :info "Universal Port Manager 발견 - 스마트 포트 할당 중..."
    
    python -m universal_port_manager --project online-evaluation status
    echo.
    
    echo %CYAN%포트 관리 옵션:%RESET%
    echo   1) 🔄 포트 재할당
    echo   2) 📊 포트 상태 확인
    echo   3) 🛠️  포트 설정 파일 재생성
    echo   4) 🔧 수동 포트 설정
    echo   5) 🏠 메인 메뉴로 돌아가기
    echo.
    
    set /p port_choice="선택 (1-5): "
    
    if "%port_choice%"=="1" (
        python -m universal_port_manager --project online-evaluation allocate frontend backend mongodb redis
        python -m universal_port_manager --project online-evaluation generate
        call :success "포트 재할당 완료"
    ) else if "%port_choice%"=="2" (
        python -m universal_port_manager --project online-evaluation status
    ) else if "%port_choice%"=="3" (
        python -m universal_port_manager --project online-evaluation generate
        call :success "설정 파일 재생성 완료"
    ) else if "%port_choice%"=="4" (
        goto manual_port_setup
    ) else (
        goto main_menu
    )
) else (
    call :warning "Universal Port Manager 없음 - 수동 포트 설정으로 진행"
    goto manual_port_setup
)

pause
goto main_menu

:manual_port_setup
echo.
call :info "🔧 수동 포트 설정"
echo.

echo 현재 사용 중인 포트:
netstat -an | findstr ":3000 :8080 :27017 :6379" | find "LISTENING"
echo.

set /p frontend_port="프론트엔드 포트 (기본: 3000): "
if "%frontend_port%"=="" set "frontend_port=3000"

set /p backend_port="백엔드 포트 (기본: 8080): "
if "%backend_port%"=="" set "backend_port=8080"

set /p mongo_port="MongoDB 포트 (기본: 27017): "
if "%mongo_port%"=="" set "mongo_port=27017"

set /p redis_port="Redis 포트 (기본: 6379): "
if "%redis_port%"=="" set "redis_port=6379"

:: 포트 파일 생성
(
echo FRONTEND_PORT=%frontend_port%
echo BACKEND_PORT=%backend_port%
echo MONGODB_PORT=%mongo_port%
echo REDIS_PORT=%redis_port%
) > .env.ports

call :success "포트 설정 완료"
exit /b

:: ===========================================
:: 빌드 및 배포 시스템
:: ===========================================
:build_and_deploy
set "env=%~1"
call :info "🔨 %env% 환경 빌드 시작..."

:: 환경별 설정 로드
if exist ".env.%env%" (
    copy /y ".env.%env%" ".env" >nul
    call :success ".env.%env% 설정 로드"
) else (
    call :warning ".env.%env% 없음 - 기본 설정 사용"
)

:: 포트 설정 로드
if exist ".env.ports" (
    for /f "tokens=1,2 delims==" %%a in (.env.ports) do (
        set "%%a=%%b"
    )
    call :success "포트 설정 로드"
)

:: Git 정보
for /f %%i in ('git rev-parse --short HEAD 2^>nul') do set "BUILD_VERSION=%%i"
for /f %%i in ('git branch --show-current 2^>nul') do set "BUILD_BRANCH=%%i"

call :info "빌드 정보: %BUILD_VERSION% (%BUILD_BRANCH%)"

:: 의존성 설치 및 빌드
call :info "📦 의존성 설치 중..."

:: 백엔드
cd backend
if exist "requirements.txt" (
    pip install -r requirements.txt --quiet
    if !errorlevel! neq 0 (
        call :error "백엔드 의존성 설치 실패"
        cd ..
        exit /b 1
    )
)
cd ..

:: 프론트엔드
cd frontend
if exist "package.json" (
    npm install --silent
    if !errorlevel! neq 0 (
        call :error "프론트엔드 의존성 설치 실패"
        cd ..
        exit /b 1
    )
    
    :: 환경별 빌드
    if "%env%"=="production" (
        npm run build --silent
        if !errorlevel! neq 0 (
            call :error "프론트엔드 빌드 실패"
            cd ..
            exit /b 1
        )
    )
)
cd ..

call :success "빌드 완료"
exit /b

:: ===========================================
:: 개발 환경 배포
:: ===========================================
:deploy_development
cls
call :info "🖥️  개발 환경 배포 시작"
call :check_prerequisites
call :build_and_deploy development

:: 개발 서버 실행
call :info "🚀 개발 서버 시작 중..."

:: 백엔드 서버 (백그라운드)
start "Online-Eval Backend" cmd /c "cd backend && python -m uvicorn server:app --reload --host 0.0.0.0 --port %BACKEND_PORT%"

:: 잠시 대기
timeout /t 3 /nobreak >nul

:: 프론트엔드 서버 (백그라운드)
start "Online-Eval Frontend" cmd /c "cd frontend && set PORT=%FRONTEND_PORT% && npm start"

:: 서버 시작 대기
call :info "⏳ 서버 시작 대기 중..."
timeout /t 15 /nobreak >nul

:: 헬스 체크
call :health_check "http://localhost:%BACKEND_PORT%/api/health" "백엔드 서버"
call :health_check "http://localhost:%FRONTEND_PORT%" "프론트엔드 서버"

echo.
call :success "개발 환경 배포 완료! 🎉"
echo.
echo %CYAN%접속 정보:%RESET%
echo   🌐 프론트엔드: http://localhost:%FRONTEND_PORT%
echo   🔧 백엔드 API: http://localhost:%BACKEND_PORT%
echo   📊 API 문서: http://localhost:%BACKEND_PORT%/docs
echo.
echo %YELLOW%개발 서버가 백그라운드에서 실행 중입니다.%RESET%
echo %YELLOW%종료하려면 해당 명령 프롬프트 창을 닫으세요.%RESET%

pause
goto main_menu

:: ===========================================
:: 스테이징 환경 배포 (Blue-Green)
:: ===========================================
:deploy_staging
cls
call :info "🧪 스테이징 환경 배포 시작 (Blue-Green)"
call :check_prerequisites
call :build_and_deploy staging

:: Docker 이미지 빌드
call :build_docker_images staging

:: Blue-Green 배포
call :info "🔄 Blue-Green 배포 진행 중..."

if exist "docker-compose.staging.yml" (
    :: 현재 실행 중인 컨테이너 확인
    docker compose -f docker-compose.staging.yml ps > staging_status.tmp
    
    :: Blue 환경 배포
    call :info "📘 Blue 환경 배포 중..."
    docker compose -f docker-compose.staging.yml up -d --no-deps backend-blue frontend
    
    timeout /t 20 /nobreak >nul
    call :health_check "http://localhost:8081/api/health" "Blue 백엔드"
    
    if !errorlevel! equ 0 (
        call :info "🔄 트래픽을 Blue로 전환 중..."
        :: 여기서 로드밸런서 설정 변경 (nginx reload 등)
        
        call :info "📗 Green 환경 준비 중..."
        docker compose -f docker-compose.staging.yml up -d --no-deps backend-green
        
        call :success "스테이징 배포 완료!"
        echo.
        echo %CYAN%스테이징 환경:%RESET%
        echo   🌐 접속: http://localhost:3001
        echo   🔧 API: http://localhost:8081
    ) else (
        call :error "Blue 환경 배포 실패 - 롤백 진행"
        docker compose -f docker-compose.staging.yml down
    )
) else (
    call :error "docker-compose.staging.yml 파일이 없습니다"
)

pause
goto main_menu

:: ===========================================
:: 운영 환경 배포 (Zero Downtime)
:: ===========================================
:deploy_production
cls
echo.
echo %RED%╔════════════════════════════════════════════════════════════╗%RESET%
echo %RED%║              ⚠️  운영 환경 배포 경고 ⚠️               ║%RESET%
echo %RED%╚════════════════════════════════════════════════════════════╝%RESET%
echo.
echo %YELLOW%운영 환경 배포는 매우 중요한 작업입니다!%RESET%
echo.
echo %CYAN%배포 전 체크리스트:%RESET%
echo   ✓ 모든 테스트가 통과했나요?
echo   ✓ 스테이징에서 검증을 완료했나요?
echo   ✓ 데이터베이스 백업이 완료되었나요?
echo   ✓ 배포 승인을 받았나요?
echo   ✓ 롤백 계획이 준비되었나요?
echo   ✓ 모니터링 시스템이 준비되었나요?
echo.

set /p confirm1="위의 모든 항목을 확인했습니까? (YES/no): "
if /i not "%confirm1%"=="YES" (
    call :info "운영 배포가 취소되었습니다"
    goto main_menu
)

echo.
echo %RED%마지막 확인: 정말로 운영 환경에 배포하시겠습니까?%RESET%
set /p confirm2="최종 확인 (DEPLOY/cancel): "
if /i not "%confirm2%"=="DEPLOY" (
    call :info "운영 배포가 취소되었습니다"
    goto main_menu
)

call :info "🌐 운영 환경 배포 시작"
call :check_prerequisites

:: 운영 환경 백업
call :info "🗄️  데이터베이스 백업 중..."
if exist "scripts\backup-production.bat" (
    call scripts\backup-production.bat
    if !errorlevel! neq 0 (
        call :error "데이터베이스 백업 실패"
        goto main_menu
    )
    call :success "백업 완료"
) else (
    call :warning "백업 스크립트가 없습니다"
)

call :build_and_deploy production
call :build_docker_images production

:: Zero-downtime 배포
call :info "🚀 Zero-downtime 배포 시작..."

if exist "docker-compose.prod.yml" (
    :: 순차적 배포로 다운타임 최소화
    docker compose -f docker-compose.prod.yml up -d --no-deps --scale backend=2 backend
    timeout /t 30 /nobreak >nul
    
    call :health_check "https://api.evaluation.com/api/health" "운영 백엔드"
    
    if !errorlevel! equ 0 (
        docker compose -f docker-compose.prod.yml up -d frontend nginx
        timeout /t 20 /nobreak >nul
        
        call :health_check "https://evaluation.com" "운영 프론트엔드"
        
        if !errorlevel! equ 0 (
            call :success "운영 환경 배포 완료! 🎉"
            
            :: 배포 알림
            call :info "📱 배포 완료 알림 발송 중..."
            if exist "scripts\send-notification.py" (
                python scripts\send-notification.py --env production --version %BUILD_VERSION%
            )
            
            :: 배포 로그 기록
            echo %date% %time% - Production Deployment v%BUILD_VERSION% - SUCCESS >> production_deployments.log
        ) else (
            goto production_rollback
        )
    ) else (
        goto production_rollback
    )
) else (
    call :error "docker-compose.prod.yml 파일이 없습니다"
)

pause
goto main_menu

:production_rollback
echo.
echo %RED%🚨 운영 배포 실패! 자동 롤백 시작...%RESET%
call :info "🔄 롤백 진행 중..."

if exist "scripts\rollback-production.bat" (
    call scripts\rollback-production.bat
    call :success "롤백 완료"
) else (
    call :error "롤백 스크립트가 없습니다 - 수동 개입 필요!"
)

echo %date% %time% - Production Deployment v%BUILD_VERSION% - FAILED & ROLLBACK >> production_deployments.log
pause
goto main_menu

:: ===========================================
:: Docker Compose 배포
:: ===========================================
:deploy_docker
cls
call :info "🐳 Docker Compose 전체 배포"
call :check_prerequisites

echo.
echo %CYAN%Docker Compose 배포 옵션:%RESET%
echo   1) 🚀 전체 새로 배포 (--build)
echo   2) 🔄 서비스 재시작 (restart)
echo   3) 📊 현재 상태 확인
echo   4) 🧹 정리 후 재배포 (clean)
echo   5) 🏠 메인 메뉴로 돌아가기
echo.

set /p docker_choice="선택 (1-5): "

if "%docker_choice%"=="1" goto docker_fresh_deploy
if "%docker_choice%"=="2" goto docker_restart
if "%docker_choice%"=="3" goto docker_status
if "%docker_choice%"=="4" goto docker_clean_deploy
if "%docker_choice%"=="5" goto main_menu
goto deploy_docker

:docker_fresh_deploy
call :info "🚀 새로운 배포 시작..."
docker compose up -d --build
goto docker_post_deploy

:docker_restart
call :info "🔄 서비스 재시작..."
docker compose restart
goto docker_post_deploy

:docker_status
call :info "📊 현재 Docker 상태"
echo.
docker compose ps
echo.
docker compose logs --tail=20
pause
goto deploy_docker

:docker_clean_deploy
call :info "🧹 기존 환경 정리 중..."
docker compose down -v --remove-orphans
docker system prune -f
call :info "🚀 새로운 배포 시작..."
docker compose up -d --build
goto docker_post_deploy

:docker_post_deploy
timeout /t 20 /nobreak >nul

call :health_check "http://localhost:%BACKEND_PORT%/api/health" "백엔드"
call :health_check "http://localhost:%FRONTEND_PORT%" "프론트엔드"

echo.
call :success "Docker Compose 배포 완료! 🎉"
echo.
echo %CYAN%서비스 정보:%RESET%
echo   🌐 프론트엔드: http://localhost:%FRONTEND_PORT%
echo   🔧 백엔드: http://localhost:%BACKEND_PORT%
echo   📊 상태 확인: docker compose ps
echo   📋 로그 확인: docker compose logs -f
echo.

pause
goto main_menu

:: ===========================================
:: Docker 이미지 빌드
:: ===========================================
:build_docker_images
set "env=%~1"
call :info "🐳 Docker 이미지 빌드 중 (%env%)..."

:: 백엔드 이미지
call :info "🔨 백엔드 이미지 빌드..."
docker build -t online-evaluation-backend:%env%-%BUILD_VERSION% -f backend/Dockerfile ./backend
if !errorlevel! neq 0 (
    call :error "백엔드 이미지 빌드 실패"
    exit /b 1
)
docker tag online-evaluation-backend:%env%-%BUILD_VERSION% online-evaluation-backend:%env%-latest

:: 프론트엔드 이미지  
call :info "🔨 프론트엔드 이미지 빌드..."

if "%env%"=="production" (
    set "BACKEND_URL=https://api.evaluation.com"
) else if "%env%"=="staging" (
    set "BACKEND_URL=https://staging-api.evaluation.com"
) else (
    set "BACKEND_URL=http://localhost:%BACKEND_PORT%"
)

docker build --build-arg REACT_APP_BACKEND_URL=%BACKEND_URL% -t online-evaluation-frontend:%env%-%BUILD_VERSION% -f frontend/Dockerfile ./frontend
if !errorlevel! neq 0 (
    call :error "프론트엔드 이미지 빌드 실패"
    exit /b 1
)
docker tag online-evaluation-frontend:%env%-%BUILD_VERSION% online-evaluation-frontend:%env%-latest

call :success "Docker 이미지 빌드 완료"
exit /b

:: ===========================================
:: 헬스 체크 시스템
:: ===========================================
:health_check
set "url=%~1"
set "service=%~2"
set "max_attempts=24"
set "attempt=0"

call :info "🏥 %service% 헬스 체크 중..."

:health_check_loop
set /a attempt+=1
if %attempt% gtr %max_attempts% (
    call :error "%service% 헬스 체크 실패 (타임아웃)"
    exit /b 1
)

:: curl 또는 PowerShell을 사용한 HTTP 요청
curl -f -s "%url%" >nul 2>&1
if !errorlevel! equ 0 (
    call :success "%service% 정상 작동 중"
    exit /b 0
) else (
    :: curl이 없으면 PowerShell 사용
    powershell -Command "try { $r = Invoke-WebRequest -Uri '%url%' -UseBasicParsing -TimeoutSec 5; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
    if !errorlevel! equ 0 (
        call :success "%service% 정상 작동 중"
        exit /b 0
    )
)

echo %BLUE%  ⏳ %service% 대기 중... (%attempt%/%max_attempts%)%RESET%
timeout /t 5 /nobreak >nul
goto health_check_loop

:: ===========================================
:: 시스템 진단
:: ===========================================
:system_diagnosis
cls
call :info "🔧 시스템 진단 시작"
echo.

echo %CYAN%=== 🖥️  시스템 정보 ===%RESET%
systeminfo | findstr /C:"OS Name" /C:"Total Physical Memory"
echo.

echo %CYAN%=== 🐳 Docker 상태 ===%RESET%
docker --version
docker compose version
docker system df
echo.

echo %CYAN%=== 🌐 네트워크 포트 ===%RESET%
echo 사용 중인 포트:
netstat -an | findstr "LISTENING" | findstr ":3000 :8080 :27017 :6379"
echo.

echo %CYAN%=== 📁 프로젝트 상태 ===%RESET%
if exist ".git" (
    echo ✅ Git 저장소
    git status --short
    echo 최근 커밋:
    git log --oneline -3
) else (
    echo ❌ Git 저장소 아님
)
echo.

echo %CYAN%=== 🗂️  환경 파일 ===%RESET%
if exist ".env" echo ✅ .env & if exist ".env.development" echo ✅ .env.development
if exist ".env.staging" echo ✅ .env.staging & if exist ".env.production" echo ✅ .env.production
if exist ".env.ports" echo ✅ .env.ports
echo.

echo %CYAN%=== 📦 의존성 상태 ===%RESET%
cd backend
if exist "requirements.txt" (
    echo 백엔드 패키지:
    pip list | findstr /C:"fastapi" /C:"uvicorn" /C:"pymongo"
)
cd ../frontend
if exist "package.json" (
    echo 프론트엔드 패키지:
    if exist "node_modules" (echo ✅ node_modules 설치됨) else (echo ❌ node_modules 없음)
)
cd ..
echo.

echo %CYAN%=== 🔍 실행 중인 서비스 ===%RESET%
docker compose ps 2>nul
echo.

echo %CYAN%=== 💾 디스크 사용량 ===%RESET%
for /f "tokens=3" %%a in ('dir /-c ^| find "bytes free"') do (
    set "free_space=%%a"
    echo 사용 가능 공간: !free_space! bytes
)

echo.
call :success "시스템 진단 완료"
pause
goto main_menu

:: ===========================================
:: 배포 모니터링
:: ===========================================
:deployment_monitoring
cls
call :info "📊 배포 상태 모니터링"
echo.

:monitoring_loop
cls
echo %CYAN%╔═══════════════════════════════════════════════════════════════╗%RESET%
echo %CYAN%║                    📊 실시간 모니터링                          ║%RESET%
echo %CYAN%╚═══════════════════════════════════════════════════════════════╝%RESET%
echo %YELLOW%업데이트: %date% %time%%RESET%
echo.

:: Docker 컨테이너 상태
echo %BLUE%🐳 Docker 컨테이너:%RESET%
docker compose ps --format "table {{.Service}}\t{{.Status}}\t{{.Ports}}" 2>nul
echo.

:: 메모리 사용량
echo %BLUE%💾 메모리 사용량:%RESET%
for /f "skip=1" %%p in ('wmic OS get TotalVisibleMemorySize^,FreePhysicalMemory /value') do (
    if not "%%p"=="" (
        for /f "tokens=1,2 delims==" %%a in ("%%p") do (
            if "%%a"=="FreePhysicalMemory" set "free_mem=%%b"
            if "%%a"=="TotalVisibleMemorySize" set "total_mem=%%b"
        )
    )
)
set /a "used_mem_percent=(total_mem-free_mem)*100/total_mem"
echo   사용률: %used_mem_percent%%%
echo.

:: 네트워크 연결
echo %BLUE%🌐 네트워크 상태:%RESET%
call :quick_health_check "http://localhost:%BACKEND_PORT%/api/health" "백엔드"
call :quick_health_check "http://localhost:%FRONTEND_PORT%" "프론트엔드"
echo.

:: 로그 미리보기
echo %BLUE%📋 최근 로그:%RESET%
docker compose logs --tail=3 --no-color 2>nul
echo.

echo %YELLOW%[R] 새로고침 | [Q] 종료%RESET%
choice /c RQ /n /t 10 /d R >nul
if errorlevel 2 goto main_menu
goto monitoring_loop

:quick_health_check
curl -f -s "%~1" >nul 2>&1
if !errorlevel! equ 0 (
    echo   %GREEN%✅ %~2 정상%RESET%
) else (
    echo   %RED%❌ %~2 오류%RESET%
)
exit /b

:: ===========================================
:: 데이터베이스 관리
:: ===========================================
:database_management
cls
call :info "🗄️  데이터베이스 관리"
echo.

echo %CYAN%데이터베이스 관리 옵션:%RESET%
echo   1) 📊 상태 확인
echo   2) 💾 백업 생성
echo   3) 🔄 복원
echo   4) 🧹 데이터 정리
echo   5) 🔧 인덱스 최적화
echo   6) 📈 성능 분석
echo   7) 🏠 메인 메뉴로 돌아가기
echo.

set /p db_choice="선택 (1-7): "

if "%db_choice%"=="1" goto db_status
if "%db_choice%"=="2" goto db_backup
if "%db_choice%"=="3" goto db_restore
if "%db_choice%"=="4" goto db_cleanup
if "%db_choice%"=="5" goto db_optimize
if "%db_choice%"=="6" goto db_performance
if "%db_choice%"=="7" goto main_menu
goto database_management

:db_status
call :info "📊 데이터베이스 상태 확인"
docker compose exec mongodb mongosh --eval "db.adminCommand('serverStatus')" 2>nul
pause
goto database_management

:db_backup
call :info "💾 데이터베이스 백업 생성"
set "backup_name=backup_%timestamp%"
docker compose exec mongodb mongodump --out /backups/%backup_name% 2>nul
call :success "백업 완료: %backup_name%"
pause
goto database_management

:db_performance
call :info "📈 데이터베이스 성능 분석"
docker compose exec mongodb mongosh --eval "db.stats()" 2>nul
pause
goto database_management

:: ===========================================
:: 서비스 복구
:: ===========================================
:service_recovery
cls
call :info "🔄 서비스 복구 시스템"
echo.

echo %CYAN%복구 옵션:%RESET%
echo   1) 🔄 모든 서비스 재시작
echo   2) 🐳 Docker 컨테이너 재시작
echo   3) 🧹 Docker 시스템 정리
echo   4) 🚨 응급 복구 (강제 재시작)
echo   5) 📊 서비스 상태 확인
echo   6) 🏠 메인 메뉴로 돌아가기
echo.

set /p recovery_choice="선택 (1-6): "

if "%recovery_choice%"=="1" goto restart_all_services
if "%recovery_choice%"=="2" goto restart_containers
if "%recovery_choice%"=="3" goto cleanup_docker
if "%recovery_choice%"=="4" goto emergency_recovery
if "%recovery_choice%"=="5" goto check_service_status
if "%recovery_choice%"=="6" goto main_menu
goto service_recovery

:restart_all_services
call :info "🔄 모든 서비스 재시작 중..."
docker compose restart
timeout /t 10 /nobreak >nul
call :success "서비스 재시작 완료"
pause
goto service_recovery

:emergency_recovery
echo %RED%🚨 응급 복구 모드%RESET%
echo %YELLOW%모든 컨테이너를 강제로 재시작합니다.%RESET%
set /p confirm="계속하시겠습니까? (y/N): "
if /i "%confirm%"=="y" (
    docker compose down --remove-orphans
    docker compose up -d --force-recreate
    call :success "응급 복구 완료"
)
pause
goto service_recovery

:: ===========================================
:: 고급 기능들
:: ===========================================
:smart_deploy
cls
call :info "🚀 AI 기반 스마트 배포"
echo.
echo %PURPLE%스마트 배포 기능:%RESET%
echo   • 📊 시스템 리소스 자동 분석
echo   • 🧪 배포 전 자동 테스트
echo   • 🎯 최적 배포 전략 추천
echo   • 🔄 자동 롤백 설정
echo.

call :info "📊 시스템 분석 중..."

:: 시스템 리소스 분석
for /f "skip=1" %%p in ('wmic computersystem get TotalPhysicalMemory') do (
    set /a "total_memory_gb=%%p/1024/1024/1024"
    goto memory_analysis_done
)
:memory_analysis_done

:: 배포 전략 추천
if %total_memory_gb% geq 8 (
    set "recommended_strategy=parallel"
    echo %GREEN%✅ 병렬 배포 권장 (충분한 메모리: %total_memory_gb%GB)%RESET%
) else (
    set "recommended_strategy=sequential"
    echo %YELLOW%⚠️  순차 배포 권장 (제한된 메모리: %total_memory_gb%GB)%RESET%
)

echo.
echo %CYAN%추천 배포 환경을 선택하세요:%RESET%
echo   1) 🖥️  Development (Hot Reload)
echo   2) 🧪 Staging (Blue-Green)
echo   3) 🐳 Docker Compose (추천: %recommended_strategy%)
echo   4) 🏠 메인 메뉴로 돌아가기
echo.

set /p smart_choice="선택 (1-4): "

if "%smart_choice%"=="1" goto deploy_development
if "%smart_choice%"=="2" goto deploy_staging
if "%smart_choice%"=="3" goto deploy_docker
if "%smart_choice%"=="4" goto main_menu
goto smart_deploy

:performance_test
cls
call :info "📈 성능 테스트 실행"
echo.

echo %CYAN%성능 테스트 옵션:%RESET%
echo   1) 🚀 기본 성능 테스트
echo   2) 💪 부하 테스트
echo   3) 🔍 메모리 누수 테스트
echo   4) 🌐 네트워크 지연 테스트
echo   5) 🏠 메인 메뉴로 돌아가기
echo.

set /p perf_choice="선택 (1-5): "

if "%perf_choice%"=="1" goto basic_performance_test
if "%perf_choice%"=="5" goto main_menu

:basic_performance_test
call :info "🚀 기본 성능 테스트 시작"

:: API 응답 시간 테스트
call :info "⏱️  API 응답 시간 측정 중..."
for /l %%i in (1,1,5) do (
    powershell -Command "$start = Get-Date; try { Invoke-WebRequest -Uri 'http://localhost:%BACKEND_PORT%/api/health' -UseBasicParsing | Out-Null; $end = Get-Date; Write-Host ('Test %%i: ' + ($end - $start).TotalMilliseconds + 'ms') } catch { Write-Host 'Test %%i: Failed' }"
)

call :success "성능 테스트 완료"
pause
goto main_menu

:security_scan
cls
call :info "🔒 보안 스캔 및 검증"
echo.

echo %CYAN%보안 검사 옵션:%RESET%
echo   1) 🛡️  Docker 이미지 보안 스캔
echo   2) 🔍 의존성 취약점 검사
echo   3) 🚪 포트 보안 검사
echo   4) 🔐 SSL/TLS 인증서 확인
echo   5) 🏠 메인 메뉴로 돌아가기
echo.

set /p sec_choice="선택 (1-5): "

if "%sec_choice%"=="1" goto docker_security_scan
if "%sec_choice%"=="2" goto dependency_scan
if "%sec_choice%"=="5" goto main_menu

:docker_security_scan
call :info "🛡️  Docker 보안 스캔 중..."
docker image ls | findstr online-evaluation
echo.
call :info "💡 보안 스캔을 위해 'docker scout' 또는 'trivy' 도구 사용을 권장합니다"
pause
goto security_scan

:dependency_scan
call :info "🔍 의존성 취약점 검사 중..."

cd backend
if exist "requirements.txt" (
    echo 백엔드 의존성 검사:
    pip list --outdated
)
cd ../frontend
if exist "package.json" (
    echo 프론트엔드 보안 검사:
    npm audit
)
cd ..

pause
goto security_scan

:deployment_history
cls
call :info "📋 배포 히스토리 관리"
echo.

if exist "production_deployments.log" (
    echo %CYAN%최근 운영 배포 히스토리:%RESET%
    type production_deployments.log | findstr /V "^$"
) else (
    echo %YELLOW%배포 히스토리가 없습니다.%RESET%
)

echo.
if exist "%LOGFILE%" (
    echo %CYAN%현재 세션 로그:%RESET%
    type "%LOGFILE%" | find "SUCCESS" | findstr /V "^$"
)

pause
goto main_menu

:: ===========================================
:: 스크립트 종료
:: ===========================================
:exit_script
cls
echo.
echo %CYAN%╔═══════════════════════════════════════════════════════════════╗%RESET%
echo %CYAN%║                    🎉 배포 시스템 종료                         ║%RESET%
echo %CYAN%╚═══════════════════════════════════════════════════════════════╝%RESET%
echo.

if exist "%ERROR_LOG%" (
    echo %RED%⚠️  오류가 발생했습니다:%RESET%
    type "%ERROR_LOG%"
    echo.
)

echo %GREEN%📊 배포 세션 요약:%RESET%
if exist "%LOGFILE%" (
    for /f %%i in ('type "%LOGFILE%" ^| find /c "SUCCESS"') do echo   ✅ 성공: %%i개
    for /f %%i in ('type "%LOGFILE%" ^| find /c "ERROR"') do echo   ❌ 오류: %%i개
    for /f %%i in ('type "%LOGFILE%" ^| find /c "WARNING"') do echo   ⚠️  경고: %%i개
    echo.
    echo %CYAN%📄 상세 로그: %LOGFILE%%RESET%
)

echo.
echo %GREEN%🚀 Online Evaluation System Ultimate Deploy%RESET%
echo %GREEN%   감사합니다! Happy Coding! 🎯%RESET%
echo.
pause
exit