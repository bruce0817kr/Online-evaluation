@echo off
REM ELK Stack 배포 및 관리 스크립트 (Windows)
REM Online Evaluation System - ELK Stack Management

setlocal enabledelayedexpansion

REM 색상 코드 정의 (Windows Terminal 지원)
set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "NC=[0m"

goto main

:log_info
echo %BLUE%[INFO]%NC% %~1
goto :eof

:log_success
echo %GREEN%[SUCCESS]%NC% %~1
goto :eof

:log_warning
echo %YELLOW%[WARNING]%NC% %~1
goto :eof

:log_error
echo %RED%[ERROR]%NC% %~1
goto :eof

:check_elk_status
call :log_info "ELK 스택 상태 확인 중..."

REM Elasticsearch 상태 확인
curl -f -s http://localhost:9200/_cluster/health >nul 2>&1
if %errorlevel% equ 0 (
    call :log_success "Elasticsearch: 정상 작동"
) else (
    call :log_error "Elasticsearch: 연결 실패"
    exit /b 1
)

REM Logstash 상태 확인
curl -f -s http://localhost:9600 >nul 2>&1
if %errorlevel% equ 0 (
    call :log_success "Logstash: 정상 작동"
) else (
    call :log_error "Logstash: 연결 실패"
    exit /b 1
)

REM Kibana 상태 확인
curl -f -s http://localhost:5601/api/status >nul 2>&1
if %errorlevel% equ 0 (
    call :log_success "Kibana: 정상 작동"
) else (
    call :log_error "Kibana: 연결 실패"
    exit /b 1
)

call :log_success "모든 ELK 컴포넌트가 정상적으로 작동 중입니다!"
goto :eof

:start_elk
call :log_info "ELK 스택 시작 중..."

REM logging 프로파일로 ELK 스택 시작
docker-compose --profile logging up -d

call :log_info "ELK 서비스 시작 대기 중..."
timeout /t 30 /nobreak >nul

REM 초기화 스크립트 실행
call :log_info "Elasticsearch 초기화 실행 중..."
docker-compose --profile logging-init up elasticsearch-setup-dev

call :log_info "Kibana 대시보드 설정 중..."
docker-compose --profile logging-init up kibana-setup-dev

call :log_success "ELK 스택이 성공적으로 시작되었습니다!"

REM 상태 확인
timeout /t 10 /nobreak >nul
call :check_elk_status
goto :eof

:stop_elk
call :log_info "ELK 스택 중지 중..."

docker-compose --profile logging --profile logging-init down

call :log_success "ELK 스택이 중지되었습니다."
goto :eof

:restart_elk
call :log_info "ELK 스택 재시작 중..."

call :stop_elk
timeout /t 5 /nobreak >nul
call :start_elk
goto :eof

:view_logs
set "service=%~1"

if "%service%"=="" (
    call :log_info "모든 ELK 서비스 로그 확인..."
    docker-compose logs -f elasticsearch-dev logstash-dev kibana-dev filebeat-dev
) else (
    call :log_info "%service% 로그 확인..."
    docker-compose logs -f "%service%"
)
goto :eof

:cleanup_indices
set "days=%~1"
if "%days%"=="" set "days=30"

call :log_info "%days% 일 이상 된 인덱스 정리 중..."

REM PowerShell을 사용하여 날짜 계산 및 인덱스 목록 조회
powershell -Command "$cutoffDate = (Get-Date).AddDays(-%days%).ToString('yyyy-MM-dd'); $indices = curl -s 'http://localhost:9200/_cat/indices/app-logs-*?h=index,creation.date.string' | ForEach-Object { $parts = $_ -split '\s+'; if ($parts[1] -lt $cutoffDate) { $parts[0] } }; if ($indices) { Write-Host 'Old indices found:'; $indices | ForEach-Object { Write-Host $_ } } else { Write-Host 'No indices to cleanup.' }"

call :log_warning "계속하려면 아무 키나 누르고, 취소하려면 Ctrl+C를 누르세요."
pause >nul

REM 실제 삭제는 PowerShell로 수행
powershell -Command "$cutoffDate = (Get-Date).AddDays(-%days%).ToString('yyyy-MM-dd'); $indices = curl -s 'http://localhost:9200/_cat/indices/app-logs-*?h=index,creation.date.string' | ForEach-Object { $parts = $_ -split '\s+'; if ($parts[1] -lt $cutoffDate) { $parts[0] } }; $indices | ForEach-Object { Write-Host 'Deleting index:' $_; curl -X DELETE \"http://localhost:9200/$_\" }"

call :log_success "인덱스 정리 완료!"
goto :eof

:backup_elk
set "backup_dir=elk_backup_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%"
set "backup_dir=%backup_dir: =0%"

call :log_info "ELK 설정 백업 생성 중: %backup_dir%"

mkdir "%backup_dir%" 2>nul

REM 설정 파일 백업
xcopy /E /I /Q logging "%backup_dir%\logging\"

REM Elasticsearch 매핑 및 설정 백업
curl -s "http://localhost:9200/_cluster/settings" > "%backup_dir%\cluster_settings.json"
curl -s "http://localhost:9200/_template" > "%backup_dir%\index_templates.json"
curl -s "http://localhost:9200/_ilm/policy" > "%backup_dir%\ilm_policies.json"

REM 압축 (PowerShell 사용)
powershell -Command "Compress-Archive -Path '%backup_dir%' -DestinationPath '%backup_dir%.zip'"
rmdir /S /Q "%backup_dir%"

call :log_success "백업이 생성되었습니다: %backup_dir%.zip"
goto :eof

:monitor_performance
call :log_info "ELK 성능 모니터링 시작..."

if exist "logging\elk_performance_monitor.py" (
    python logging\elk_performance_monitor.py %*
) else (
    call :log_error "성능 모니터링 스크립트를 찾을 수 없습니다."
    exit /b 1
)
goto :eof

:check_indices
call :log_info "인덱스 상태 확인 중..."

echo.
echo 📊 인덱스 상태:
curl -s "http://localhost:9200/_cat/indices/app-logs-*?v&s=index"

echo.
echo 💾 인덱스 크기:
curl -s "http://localhost:9200/_cat/indices/app-logs-*?v&h=index,store.size,docs.count&s=store.size:desc"

echo.
echo 🏥 클러스터 상태:
curl -s "http://localhost:9200/_cluster/health?pretty"
goto :eof

:show_help
echo ELK Stack 관리 스크립트 (Windows)
echo.
echo 사용법: %~nx0 [COMMAND] [OPTIONS]
echo.
echo Commands:
echo   start                 ELK 스택 시작
echo   stop                  ELK 스택 중지
echo   restart               ELK 스택 재시작
echo   status                ELK 스택 상태 확인
echo   logs [service]        로그 확인 (서비스명 선택사항)
echo   cleanup [days]        오래된 인덱스 정리 (기본: 30일)
echo   backup                설정 백업 생성
echo   monitor [--watch]     성능 모니터링
echo   indices               인덱스 상태 확인
echo   help                  이 도움말 출력
echo.
echo Examples:
echo   %~nx0 start              # ELK 스택 시작
echo   %~nx0 logs elasticsearch-dev # Elasticsearch 로그 확인
echo   %~nx0 cleanup 7          # 7일 이상 된 인덱스 삭제
echo   %~nx0 monitor --watch    # 지속적인 성능 모니터링
goto :eof

:main
set "command=%~1"
if "%command%"=="" set "command=help"

if "%command%"=="start" (
    call :start_elk
) else if "%command%"=="stop" (
    call :stop_elk
) else if "%command%"=="restart" (
    call :restart_elk
) else if "%command%"=="status" (
    call :check_elk_status
) else if "%command%"=="logs" (
    call :view_logs "%~2"
) else if "%command%"=="cleanup" (
    call :cleanup_indices "%~2"
) else if "%command%"=="backup" (
    call :backup_elk
) else if "%command%"=="monitor" (
    shift
    call :monitor_performance %*
) else if "%command%"=="indices" (
    call :check_indices
) else if "%command%"=="help" (
    call :show_help
) else if "%command%"=="--help" (
    call :show_help
) else if "%command%"=="-h" (
    call :show_help
) else (
    call :log_error "알 수 없는 명령어: %command%"
    echo.
    call :show_help
    exit /b 1
)

goto :eof
