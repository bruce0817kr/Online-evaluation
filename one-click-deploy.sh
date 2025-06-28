#!/bin/bash

# ===================================================================
# 🚀 Online Evaluation System - 원클릭 배포 시스템 (Linux/macOS)
# ===================================================================
# 작성일: 2025-06-26
# 버전: 3.0 Ultimate
# 설명: 개발/스테이징/운영 환경 자동 배포 (고급 기능 포함)
# ===================================================================

set -euo pipefail

# 색상 코드 설정
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# 빌드 정보
BUILD_VERSION=$(git rev-parse --short HEAD 2>/dev/null || echo "local")
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# 로그 파일
LOGFILE="deployment_${TIMESTAMP}.log"
ERROR_LOG="deployment_error_${TIMESTAMP}.log"

# 설정 변수
PROJECT_NAME="online-evaluation"
SERVICES="frontend backend mongodb redis"
MAX_WAIT_TIME=120
CHECK_INTERVAL=5

# 로깅 함수
log_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_step() {
    echo -e "${PURPLE}📋 $1${NC}"
}

# 오류 처리 함수
error_exit() {
    echo
    echo -e "${RED}========================================================"
    echo -e "❌ 배포 중 오류가 발생했습니다!"
    echo -e "========================================================${NC}"
    echo
    
    log_info "🔧 문제 해결을 위한 디버깅 정보:"
    echo
    
    # 디버깅 정보 수집
    log_info "📊 현재 포트 상태:"
    python3 -m universal_port_manager.cli --project $PROJECT_NAME status 2>/dev/null || true
    
    echo
    log_info "🐳 Docker 상태:"
    docker-compose -p $PROJECT_NAME ps 2>/dev/null || true
    
    echo
    log_info "📝 최근 로그 (마지막 10줄):"
    docker-compose -p $PROJECT_NAME logs --tail=10 2>/dev/null || true
    
    echo
    log_info "💡 수동 복구 명령어:"
    echo "  1. 포트 재할당: python3 -m universal_port_manager.cli --project $PROJECT_NAME allocate $SERVICES"
    echo "  2. 서비스 재시작: docker-compose -p $PROJECT_NAME up --build -d"
    echo "  3. 로그 확인: docker-compose -p $PROJECT_NAME logs -f"
    echo
    
    exit 1
}

# 시그널 처리 (Ctrl+C 등)
trap error_exit ERR

# 메인 함수
main() {
    clear
    echo
    echo -e "${BLUE}========================================================"
    echo -e "🚀 온라인 평가 시스템 원클릭 배포 시작"
    echo -e "========================================================${NC}"
    echo
    
    # 권한 확인 (sudo 필요한 경우)
    if [[ $EUID -eq 0 ]]; then
        log_warning "루트 권한으로 실행되고 있습니다."
    fi
    
    # Python 확인
    if ! command -v python3 &> /dev/null; then
        log_error "Python3가 설치되지 않았습니다."
        exit 1
    fi
    
    log_success "Python3 확인 완료"
    echo
    
    # 단계 1: 시스템 진단
    log_step "단계 1/7: 시스템 진단 중..."
    if ! python3 -m universal_port_manager.cli doctor --quiet; then
        log_error "시스템 진단 실패"
        error_exit
    fi
    log_success "시스템 진단 완료"
    echo
    
    # 단계 2: 현재 포트 사용 현황 스캔
    log_step "단계 2/7: 포트 사용 현황 스캔 중..."
    if ! python3 -m universal_port_manager.cli scan --range 3000-9000 --format json > port_scan_result.json; then
        log_error "포트 스캔 실패"
        error_exit
    fi
    log_success "포트 스캔 완료"
    echo
    
    # 단계 3: 포트 할당
    log_step "단계 3/7: 서비스 포트 할당 중..."
    if ! python3 -m universal_port_manager.cli --project $PROJECT_NAME allocate $SERVICES; then
        log_error "포트 할당 실패"
        error_exit
    fi
    log_success "포트 할당 완료"
    echo
    
    # 단계 4: 설정 파일 생성
    log_step "단계 4/7: 설정 파일 생성 중..."
    if ! python3 -m universal_port_manager.cli --project $PROJECT_NAME generate; then
        log_error "설정 파일 생성 실패"
        error_exit
    fi
    log_success "설정 파일 생성 완료"
    echo
    
    # 할당된 포트 정보 표시
    if [[ -f "ports.json" ]]; then
        log_info "📊 할당된 포트 정보:"
        cat ports.json | grep -E "port|service" | head -10
        echo
    fi
    
    # 단계 5: Docker 컨테이너 실행
    log_step "단계 5/7: Docker 컨테이너 실행 중..."
    
    # Docker 확인
    if ! command -v docker &> /dev/null; then
        log_error "Docker가 설치되지 않았습니다."
        error_exit
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker 데몬이 실행되지 않았습니다. Docker를 시작해주세요."
        error_exit
    fi
    
    log_success "Docker 실행 확인 완료"
    
    # 기존 컨테이너 정리
    log_info "🧹 기존 컨테이너 정리 중..."
    docker-compose -p $PROJECT_NAME down --remove-orphans 2>/dev/null || true
    docker system prune -f &>/dev/null || true
    
    # Docker Compose로 서비스 실행
    if [[ -f "docker-compose.yml" ]]; then
        log_info "🐳 Docker Compose로 서비스 시작 중..."
        if ! docker-compose -p $PROJECT_NAME up --build -d; then
            log_error "Docker Compose 실행 실패"
            error_exit
        fi
    else
        log_error "docker-compose.yml 파일을 찾을 수 없습니다."
        error_exit
    fi
    
    log_success "Docker 컨테이너 실행 완료"
    echo
    
    # 단계 6: 서비스 상태 확인 및 대기
    log_step "단계 6/7: 서비스 준비 상태 확인 중..."
    
    # 포트 정보 추출
    FRONTEND_PORT=$(cat ports.json 2>/dev/null | grep -A3 "frontend" | grep "port" | grep -o '[0-9]\+' | head -1)
    BACKEND_PORT=$(cat ports.json 2>/dev/null | grep -A3 "backend" | grep "port" | grep -o '[0-9]\+' | head -1)
    
    # 기본값 설정
    FRONTEND_PORT=${FRONTEND_PORT:-3001}
    BACKEND_PORT=${BACKEND_PORT:-8001}
    
    log_info "🔍 프론트엔드 포트: $FRONTEND_PORT"
    log_info "🔍 백엔드 포트: $BACKEND_PORT"
    echo
    
    # 서비스 준비 상태 확인
    WAIT_TIME=0
    while [[ $WAIT_TIME -lt $MAX_WAIT_TIME ]]; do
        log_info "⏳ 서비스 준비 확인 중... ($WAIT_TIME/$MAX_WAIT_TIME초)"
        
        # 백엔드 헬스체크
        BACKEND_READY=false
        if curl -s -o /dev/null -w "%{http_code}" "http://localhost:$BACKEND_PORT/health" 2>/dev/null | grep -q "200"; then
            BACKEND_READY=true
        fi
        
        # 프론트엔드 확인
        FRONTEND_READY=false
        if curl -s -o /dev/null "http://localhost:$FRONTEND_PORT" 2>/dev/null; then
            FRONTEND_READY=true
        fi
        
        if [[ "$BACKEND_READY" == "true" && "$FRONTEND_READY" == "true" ]]; then
            log_success "모든 서비스 준비 완료!"
            break
        fi
        
        WAIT_TIME=$((WAIT_TIME + CHECK_INTERVAL))
        sleep $CHECK_INTERVAL
    done
    
    if [[ $WAIT_TIME -ge $MAX_WAIT_TIME ]]; then
        log_warning "서비스 준비 시간 초과 ($MAX_WAIT_TIME초)"
        log_warning "그래도 웹페이지를 열어보겠습니다..."
    fi
    
    echo
    
    # 단계 7: 웹페이지 오픈
    log_step "단계 7/7: 웹페이지 오픈 중..."
    
    # 운영체제별 브라우저 열기
    if command -v xdg-open &> /dev/null; then
        # Linux
        log_info "🌐 웹페이지 열기: http://localhost:$FRONTEND_PORT"
        xdg-open "http://localhost:$FRONTEND_PORT" &
        sleep 2
        log_info "📚 API 문서 열기: http://localhost:$BACKEND_PORT/docs"
        xdg-open "http://localhost:$BACKEND_PORT/docs" &
    elif command -v open &> /dev/null; then
        # macOS
        log_info "🌐 웹페이지 열기: http://localhost:$FRONTEND_PORT"
        open "http://localhost:$FRONTEND_PORT"
        sleep 2
        log_info "📚 API 문서 열기: http://localhost:$BACKEND_PORT/docs"
        open "http://localhost:$BACKEND_PORT/docs"
    else
        log_warning "브라우저를 자동으로 열 수 없습니다."
        log_info "수동으로 브라우저에서 다음 주소를 열어주세요:"
        log_info "  프론트엔드: http://localhost:$FRONTEND_PORT"
        log_info "  API 문서: http://localhost:$BACKEND_PORT/docs"
    fi
    
    echo
    echo -e "${GREEN}========================================================"
    echo -e "🎉 원클릭 배포 완료!"
    echo -e "========================================================${NC}"
    echo
    log_info "📱 서비스 접속 정보:"
    echo "    프론트엔드: http://localhost:$FRONTEND_PORT"
    echo "    백엔드 API: http://localhost:$BACKEND_PORT"
    echo "    API 문서:   http://localhost:$BACKEND_PORT/docs"
    echo
    log_info "🛠️ 관리 명령어:"
    echo "    서비스 상태: docker-compose -p $PROJECT_NAME ps"
    echo "    로그 확인:   docker-compose -p $PROJECT_NAME logs -f"
    echo "    서비스 중지: docker-compose -p $PROJECT_NAME down"
    echo
    log_info "💡 문제가 있다면 로그를 확인하세요:"
    echo "    docker-compose -p $PROJECT_NAME logs --tail=50"
    echo
    
    read -p "아무 키나 누르세요..."
}

# 스크립트 실행
main "$@"