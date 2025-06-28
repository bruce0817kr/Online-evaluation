@echo off
chcp 65001 >nul 2>&1
title Quick Start - 빠른 배포 + 포트 매니저
color 0a

echo.
echo ================================================================
echo              Quick Start - 빠른 배포 + 포트 매니저
echo ================================================================
echo.
echo 특징:
echo   ✓ 빌드 시간 없음 (pre-built 이미지 사용)
echo   ✓ Universal Port Manager 통합
echo   ✓ 포트 충돌 자동 회피
echo   ✓ npm 캐시 최적화로 빠른 시작
echo.

:: 환경 검증
echo [검증] 환경 확인 중...

if not exist "docker-compose.yml" (
    echo [ERROR] 프로젝트 디렉토리가 아닙니다
    echo Online-evaluation 폴더에서 실행해주세요
    pause
    exit /b 1
)

docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker를 찾을 수 없습니다
    echo Docker Desktop을 설치하고 실행해주세요
    pause
    exit /b 1
)

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python을 찾을 수 없습니다
    echo Python 3.8+ 설치가 필요합니다
    pause
    exit /b 1
)

echo [OK] 모든 환경 검증 완료
echo.

:: 이전 설정 정리
echo [정리] 이전 설정 정리 중...
if exist "docker-compose.quick.yml" del /f /q "docker-compose.quick.yml" >nul 2>&1
echo [OK] 정리 완료
echo.

:: Quick Start 실행
echo [시작] Quick Start 배포 실행...
echo.

python quick-start.py

echo.
echo ================================================================
echo                    Quick Start 완료
echo ================================================================
echo.
echo 배포가 성공했다면 브라우저에서 애플리케이션이 열렸을 것입니다.
echo 문제가 있다면 위의 출력 내용을 확인해주세요.
echo.
echo 포트 정보는 ports.json 파일에 저장되어 있습니다.
echo.
pause