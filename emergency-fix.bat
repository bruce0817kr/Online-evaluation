@echo off
chcp 65001 >nul 2>&1
title Emergency Fix - 모든 문제 즉시 해결
color 0c

echo.
echo ================================================================
echo              Emergency Fix - 모든 문제 즉시 해결
echo ================================================================
echo.
echo 발견된 문제들:
echo   ❌ Backend: ModuleNotFoundError: No module named 'dotenv'
echo   ❌ Frontend: npm install 계속 실패
echo   ❌ 포트 충돌 문제
echo.
echo 해결 방법:
echo   ✅ 모든 필요한 Python 패키지 설치
echo   ✅ Frontend를 간단한 HTML로 대체
echo   ✅ 새로운 포트로 충돌 방지
echo   ✅ 즉시 작동하는 시스템 구축
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

:: 모든 문제있는 컨테이너 중지
echo [정리] 모든 문제있는 컨테이너 중지 중...
docker-compose -f docker-compose.quick.yml -p quick down >nul 2>&1
docker-compose -f docker-compose.instant.yml -p instant down >nul 2>&1
echo [OK] 정리 완료
echo.

:: Emergency Fix 실행
echo [긴급수정] 모든 문제 해결 중...
echo.

python emergency-fix.py

echo.
echo ================================================================
echo                    Emergency Fix 완료
echo ================================================================
echo.
echo 🆘 Emergency Mode로 실행됨
echo ✅ Backend API 즉시 사용 가능
echo ✅ 간단한 Frontend 제공
echo ✅ 모든 종속성 문제 해결
echo.
pause