@echo off
chcp 65001 >nul 2>&1
title Instant Fix - Frontend 문제 해결
color 0c

echo.
echo ================================================================
echo              Instant Fix - Frontend 문제 해결
echo ================================================================
echo.
echo Frontend 컨테이너가 계속 재시작되는 문제를 해결합니다.
echo.
echo 해결 방법:
echo   ✓ npm install 문제 수정
echo   ✓ package.json 문제 해결
echo   ✓ 안정적인 Frontend 설정
echo   ✓ 기존 포트 재사용
echo.

:: 환경 확인
if not exist "docker-compose.yml" (
    echo [ERROR] 프로젝트 디렉토리가 아닙니다
    pause
    exit /b 1
)

docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker를 찾을 수 없습니다
    pause
    exit /b 1
)

echo [OK] 환경 확인 완료
echo.

:: 기존 문제있는 컨테이너 먼저 중지
echo [정리] 문제있는 컨테이너 중지 중...
docker-compose -f docker-compose.quick.yml -p quick down >nul 2>&1
echo [OK] 정리 완료
echo.

:: Instant Fix 실행
echo [수정] Frontend 문제 해결 중...
echo.

python instant-fix.py

echo.
echo ================================================================
echo                    Instant Fix 완료
echo ================================================================
echo.
echo Backend는 즉시 사용 가능하고, Frontend는 3-5분 후 준비됩니다.
echo Frontend가 준비되면 자동으로 브라우저에서 열릴 것입니다.
echo.
pause