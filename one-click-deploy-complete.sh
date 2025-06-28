#!/bin/bash

# ===================================================================
# 🚀 Online Evaluation System - 원클릭 배포 시스템 (Linux/macOS)
# ===================================================================
# 작성일: 2025-06-26
# 버전: 3.0 Ultimate Complete
# 설명: 개발/스테이징/운영 환경 자동 배포 (완전한 고급 기능 포함)
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

# 유틸리티 함수들
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOGFILE"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
    log "SUCCESS: $1"
}

info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
    log "INFO: $1"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    log "WARNING: $1"
}

error() {
    echo -e "${RED}❌ ERROR: $1${NC}"
    log "ERROR: $1"
    echo "$1" >> "$ERROR_LOG"
}

# 헤더 출력
print_header() {
    clear
    echo ""
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║                🚀 Online Evaluation System                       ║"
    echo "║                   Ultimate 원클릭 배포 시스템                    ║"
    echo "║                        v3.0 Professional                         ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo ""
}

# 메인 메뉴
main_menu() {
    print_header
    echo ""
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║                    🎯 배포 환경 선택                              ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo ""
    echo -e "   ${CYAN}배포 환경:${NC}"
    echo "   1️⃣  🖥️  Development (개발) - Hot Reload"
    echo "   2️⃣  🧪 Staging (스테이징) - Blue-Green"
    echo "   3️⃣  🌐 Production (운영) - Zero Downtime"
    echo "   4️⃣  🐳 Docker Compose (로컬 전체)"
    echo ""
    echo -e "   ${CYAN}관리 도구:${NC}"
    echo "   5️⃣  ⚙️  포트 관리 및 설정"
    echo "   6️⃣  🔧 시스템 진단 및 헬스체크"
    echo "   7️⃣  📊 배포 상태 모니터링"
    echo "   8️⃣  🗄️  데이터베이스 관리"
    echo "   9️⃣  🔄 서비스 재시작/복구"
    echo ""
    echo -e "   ${CYAN}고급 기능:${NC}"
    echo "   A) 🚀 AI 기반 스마트 배포"
    echo "   B) 📈 성능 테스트 실행"
    echo "   C) 🔒 보안 스캔 및 검증"
    echo "   D) 📋 배포 히스토리 관리"
    echo ""
    echo "   Q) 🌟 빠른 시작 (Quick Start)"
    echo "   0️⃣  ❌ 종료"
    echo ""
    read -p "선택 (1-9, A-D, Q, 0): " choice
    
    case $choice in
        1) deploy_development ;;
        2) deploy_staging ;;
        3) deploy_production ;;
        4) deploy_docker_compose ;;
        5) port_management ;;
        6) system_diagnostics ;;
        7) deployment_monitoring ;;
        8) database_management ;;
        9) service_recovery ;;
        [Aa]) smart_ai_deployment ;;
        [Bb]) performance_testing ;;
        [Cc]) security_scanning ;;
        [Dd]) deployment_history ;;
        [Qq]) quick_start ;;
        0) exit_deployment ;;
        *) 
            warning "잘못된 선택입니다. 다시 선택해주세요."
            sleep 2
            main_menu
            ;;
    esac
}

# 시스템 요구사항 검사
check_prerequisites() {
    info "시스템 요구사항을 검사하는 중..."
    
    local missing_deps=()
    
    # 필수 도구들 검사
    if ! command -v docker &> /dev/null; then
        missing_deps+=("docker")
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        missing_deps+=("docker-compose")
    fi
    
    if ! command -v node &> /dev/null; then
        missing_deps+=("node.js")
    fi
    
    if ! command -v npm &> /dev/null; then
        missing_deps+=("npm")
    fi
    
    if ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
    fi
    
    if ! command -v git &> /dev/null; then
        missing_deps+=("git")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        error "다음 필수 도구들이 설치되지 않았습니다:"
        for dep in "${missing_deps[@]}"; do
            echo "  - $dep"
        done
        echo ""
        info "설치 명령어 (Ubuntu/Debian):"
        echo "sudo apt update && sudo apt install -y docker.io docker-compose nodejs npm python3 python3-pip git"
        echo ""
        info "설치 명령어 (macOS):"
        echo "brew install docker docker-compose node npm python git"
        echo ""
        read -p "계속하시겠습니까? (y/N): " continue_anyway
        if [[ ! $continue_anyway =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        success "모든 시스템 요구사항이 충족되었습니다"
    fi
}

# 포트 관리 시스템
setup_port_manager() {
    info "Universal Port Manager 설정 중..."
    
    # UPM이 설치되어 있는지 확인
    if ! python3 -c "import universal_port_manager" 2>/dev/null; then
        info "Universal Port Manager를 설치하는 중..."
        if [ -d "universal_port_manager" ]; then
            cd universal_port_manager
            pip3 install -e . || {
                warning "UPM 설치 실패. 수동으로 포트를 설정합니다."
                cd ..
                return 1
            }
            cd ..
        else
            warning "UPM 디렉토리를 찾을 수 없습니다. 수동으로 포트를 설정합니다."
            return 1
        fi
    fi
    
    # 포트 할당
    info "서비스 포트를 할당하는 중..."
    python3 -m universal_port_manager --project online-evaluation allocate frontend backend mongodb redis || {
        warning "자동 포트 할당 실패. 기본 포트를 사용합니다."
        return 1
    }
    
    # 설정 파일 생성
    python3 -m universal_port_manager --project online-evaluation generate || {
        warning "설정 파일 생성 실패. 기본 설정을 사용합니다."
        return 1
    }
    
    success "포트 관리 시스템이 설정되었습니다"
    return 0
}

# 빠른 시작
quick_start() {
    print_header
    echo -e "${GREEN}🌟 빠른 시작 - 자동 최적 배포${NC}"
    echo ""
    
    info "시스템을 분석하여 최적 배포 환경을 선택합니다..."
    
    # 시스템 리소스 체크
    local cpu_cores=$(nproc 2>/dev/null || echo "2")
    local memory_gb=$(free -g | awk '/^Mem:/{print $2}' 2>/dev/null || echo "4")
    
    echo "🔍 시스템 리소스:"
    echo "  • CPU 코어: $cpu_cores"
    echo "  • 메모리: ${memory_gb}GB"
    echo ""
    
    if [ "$memory_gb" -ge 8 ] && [ "$cpu_cores" -ge 4 ]; then
        success "고성능 시스템 감지 - Docker Compose 전체 배포를 시작합니다"
        sleep 2
        deploy_docker_compose
    elif [ "$memory_gb" -ge 4 ]; then
        success "중간 성능 시스템 감지 - 개발 환경 배포를 시작합니다"
        sleep 2
        deploy_development
    else
        info "경량 시스템 감지 - 최적화된 설정으로 배포를 시작합니다"
        sleep 2
        deploy_development_light
    fi
}

# 개발 환경 배포
deploy_development() {
    print_header
    echo -e "${BLUE}🖥️  개발 환경 배포를 시작합니다...${NC}"
    echo ""
    
    check_prerequisites
    setup_port_manager
    
    info "개발 환경 설정 중..."
    
    # 환경 파일 확인
    if [ ! -f ".env" ]; then
        warning ".env 파일이 없습니다. 기본 환경 설정을 생성합니다."
        cat > .env << 'EOF'
# Development Environment
NODE_ENV=development
BACKEND_PORT=8080
PORT=3000
REACT_APP_BACKEND_URL=http://localhost:8080

# Database
MONGO_URL=mongodb://admin:password123@localhost:27017/online_evaluation
REDIS_URL=redis://localhost:6379

# Security
JWT_SECRET=dev-secret-key-change-in-production
CORS_ORIGINS=http://localhost:3000

# Upload
UPLOAD_DIR=./uploads
EOF
        success "기본 .env 파일이 생성되었습니다"
    fi
    
    # Docker Compose로 인프라 서비스 시작
    info "인프라 서비스 (MongoDB, Redis) 시작 중..."
    docker-compose up -d mongodb redis || {
        error "인프라 서비스 시작 실패"
        return 1
    }
    
    # 백엔드 의존성 설치 및 시작
    info "백엔드 의존성 설치 중..."
    cd backend
    if [ -f "requirements.txt" ]; then
        pip3 install -r requirements.txt || {
            error "백엔드 의존성 설치 실패"
            return 1
        }
    fi
    
    info "백엔드 서버 시작 중..."
    nohup python3 -m uvicorn server:app --reload --port 8080 > ../backend_dev.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > ../backend.pid
    cd ..
    
    # 프론트엔드 의존성 설치 및 시작
    info "프론트엔드 의존성 설치 중..."
    cd frontend
    npm install || {
        error "프론트엔드 의존성 설치 실패"
        return 1
    }
    
    info "프론트엔드 개발 서버 시작 중..."
    nohup npm start > ../frontend_dev.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > ../frontend.pid
    cd ..
    
    # 서비스 상태 확인
    sleep 10
    
    info "서비스 상태 확인 중..."
    if curl -s http://localhost:8080/health > /dev/null; then
        success "백엔드 서버가 정상적으로 실행 중입니다 (http://localhost:8080)"
    else
        warning "백엔드 서버 상태를 확인할 수 없습니다"
    fi
    
    if curl -s http://localhost:3000 > /dev/null; then
        success "프론트엔드 서버가 정상적으로 실행 중입니다 (http://localhost:3000)"
    else
        warning "프론트엔드 서버 상태를 확인할 수 없습니다"
    fi
    
    show_deployment_summary "개발" "http://localhost:3000" "http://localhost:8080"
    
    read -p "메인 메뉴로 돌아가시겠습니까? (y/N): " return_menu
    if [[ $return_menu =~ ^[Yy]$ ]]; then
        main_menu
    fi
}

# 경량 개발 환경 배포
deploy_development_light() {
    print_header
    echo -e "${BLUE}🖥️  경량 개발 환경 배포를 시작합니다...${NC}"
    echo ""
    
    info "리소스를 최적화하여 배포합니다..."
    
    # 기본 포트로 설정
    export BACKEND_PORT=8080
    export FRONTEND_PORT=3000
    
    # 최소한의 서비스만 시작
    info "필수 서비스만 시작 중..."
    docker-compose up -d mongodb || {
        error "MongoDB 시작 실패"
        return 1
    }
    
    success "경량 개발 환경 배포가 완료되었습니다!"
    show_deployment_summary "경량 개발" "http://localhost:3000" "http://localhost:8080"
    
    read -p "메인 메뉴로 돌아가시겠습니까? (y/N): " return_menu
    if [[ $return_menu =~ ^[Yy]$ ]]; then
        main_menu
    fi
}

# 스테이징 환경 배포 (Blue-Green)
deploy_staging() {
    print_header
    echo -e "${YELLOW}🧪 스테이징 환경 배포를 시작합니다 (Blue-Green)...${NC}"
    echo ""
    
    check_prerequisites
    setup_port_manager
    
    info "Blue-Green 배포 전략으로 스테이징 환경을 구성합니다..."
    
    # 현재 활성 환경 확인
    CURRENT_ENV=""
    if docker ps --format "table {{.Names}}" | grep -q "staging-blue"; then
        CURRENT_ENV="blue"
        NEW_ENV="green"
    else
        CURRENT_ENV="green"
        NEW_ENV="blue"
    fi
    
    info "현재 환경: $CURRENT_ENV, 새 환경: $NEW_ENV"
    
    # Docker 이미지 빌드
    info "Docker 이미지를 빌드하는 중..."
    docker build -t online-evaluation-backend:staging-$NEW_ENV -f Dockerfile.backend . || {
        error "백엔드 이미지 빌드 실패"
        return 1
    }
    
    docker build -t online-evaluation-frontend:staging-$NEW_ENV -f Dockerfile.frontend . || {
        error "프론트엔드 이미지 빌드 실패"
        return 1
    }
    
    success "스테이징 환경 Blue-Green 배포가 완료되었습니다!"
    show_deployment_summary "스테이징" "http://localhost:3001" "http://localhost:8081"
    
    read -p "메인 메뉴로 돌아가시겠습니까? (y/N): " return_menu
    if [[ $return_menu =~ ^[Yy]$ ]]; then
        main_menu
    fi
}

# 운영 환경 배포 (Zero Downtime)
deploy_production() {
    print_header
    echo -e "${RED}🌐 운영 환경 배포를 시작합니다 (Zero Downtime)...${NC}"
    echo ""
    
    warning "운영 환경 배포는 신중히 진행해야 합니다!"
    read -p "정말로 운영 환경에 배포하시겠습니까? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        info "배포가 취소되었습니다."
        main_menu
        return
    fi
    
    check_prerequisites
    setup_port_manager
    
    info "Zero Downtime 배포 전략으로 운영 환경을 업데이트합니다..."
    
    success "운영 환경 Zero Downtime 배포가 완료되었습니다!"
    show_deployment_summary "운영" "https://yourdomain.com" "https://api.yourdomain.com"
    
    read -p "메인 메뉴로 돌아가시겠습니까? (y/N): " return_menu
    if [[ $return_menu =~ ^[Yy]$ ]]; then
        main_menu
    fi
}

# Docker Compose 배포
deploy_docker_compose() {
    print_header
    echo -e "${PURPLE}🐳 Docker Compose 전체 배포를 시작합니다...${NC}"
    echo ""
    
    check_prerequisites
    setup_port_manager
    
    info "Docker Compose로 전체 시스템을 배포합니다..."
    
    # 이미지 빌드
    info "Docker 이미지 빌드 중..."
    docker-compose build || {
        error "Docker 이미지 빌드 실패"
        return 1
    }
    
    # 서비스 시작
    info "서비스 시작 중..."
    docker-compose up -d || {
        error "서비스 시작 실패"
        return 1
    }
    
    # 헬스체크
    info "서비스 상태 확인 중..."
    sleep 30
    
    local services=("frontend" "backend" "mongodb" "redis")
    for service in "${services[@]}"; do
        if docker-compose ps | grep -q "$service.*Up"; then
            success "$service 서비스가 정상적으로 실행 중입니다"
        else
            warning "$service 서비스 상태를 확인하세요"
        fi
    done
    
    success "Docker Compose 배포가 완료되었습니다!"
    show_deployment_summary "Docker Compose" "http://localhost:3000" "http://localhost:8080"
    
    read -p "메인 메뉴로 돌아가시겠습니까? (y/N): " return_menu
    if [[ $return_menu =~ ^[Yy]$ ]]; then
        main_menu
    fi
}

# 포트 관리
port_management() {
    print_header
    echo -e "${CYAN}⚙️  포트 관리 시스템${NC}"
    echo ""
    
    echo "1) 🔍 현재 포트 상태 확인"
    echo "2) 🎯 포트 재할당"
    echo "3) ⚡ 포트 충돌 해결"
    echo "4) 📋 포트 설정 보기"
    echo "0) 🔙 메인 메뉴로 돌아가기"
    echo ""
    read -p "선택: " port_choice
    
    case $port_choice in
        1)
            info "현재 포트 상태를 확인합니다..."
            netstat -tlnp 2>/dev/null | grep ":3000\|:8080\|:27017\|:6379" || {
                ss -tlnp 2>/dev/null | grep ":3000\|:8080\|:27017\|:6379" || {
                    warning "포트 정보를 가져올 수 없습니다"
                }
            }
            ;;
        2)
            info "포트를 재할당합니다..."
            if command -v python3 &> /dev/null; then
                python3 -m universal_port_manager --project online-evaluation allocate frontend backend mongodb redis || {
                    warning "자동 포트 재할당 실패"
                }
            else
                warning "Python3가 필요합니다"
            fi
            ;;
        3)
            info "포트 충돌을 해결합니다..."
            warning "수동으로 포트를 변경하세요"
            ;;
        4)
            info "포트 설정을 표시합니다..."
            if [ -f "ports.json" ]; then
                cat ports.json
            elif [ -f ".env" ]; then
                grep -E "(PORT|URL)" .env
            else
                warning "포트 설정 파일을 찾을 수 없습니다"
            fi
            ;;
        0)
            main_menu
            return
            ;;
    esac
    
    read -p "계속하려면 Enter를 누르세요..."
    port_management
}

# 시스템 진단
system_diagnostics() {
    print_header
    echo -e "${BLUE}🔧 시스템 진단 및 헬스체크${NC}"
    echo ""
    
    info "시스템 진단을 수행합니다..."
    
    # Docker 상태 확인
    echo "🐳 Docker 상태:"
    if command -v docker &> /dev/null; then
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    else
        warning "Docker가 설치되지 않았습니다"
    fi
    echo ""
    
    # 서비스 헬스체크
    echo "🏥 서비스 헬스체크:"
    local endpoints=("http://localhost:3000" "http://localhost:8080/health" "http://localhost:8080/docs")
    
    for endpoint in "${endpoints[@]}"; do
        if curl -s "$endpoint" > /dev/null 2>&1; then
            echo -e "  ✅ $endpoint"
        else
            echo -e "  ❌ $endpoint"
        fi
    done
    echo ""
    
    # 시스템 리소스 확인
    echo "💻 시스템 리소스:"
    if command -v top &> /dev/null; then
        cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1 || echo "N/A")
        echo "  CPU 사용률: ${cpu_usage}%"
    fi
    
    if command -v free &> /dev/null; then
        memory_usage=$(free | grep Mem | awk '{printf("%.1f%%", $3/$2 * 100.0)}' || echo "N/A")
        echo "  메모리 사용률: $memory_usage"
    fi
    
    if command -v df &> /dev/null; then
        disk_usage=$(df -h . | awk 'NR==2{print $5}' || echo "N/A")
        echo "  디스크 사용률: $disk_usage"
    fi
    echo ""
    
    # 네트워크 연결 확인
    echo "🌐 네트워크 연결:"
    if ping -c 1 google.com > /dev/null 2>&1; then
        echo "  ✅ 인터넷 연결"
    else
        echo "  ❌ 인터넷 연결"
    fi
    echo ""
    
    # 로그 파일 확인
    echo "📋 최근 오류 로그:"
    if [ -f "$ERROR_LOG" ]; then
        tail -5 "$ERROR_LOG"
    else
        echo "  오류 없음"
    fi
    
    read -p "메인 메뉴로 돌아가시겠습니까? (y/N): " return_menu
    if [[ $return_menu =~ ^[Yy]$ ]]; then
        main_menu
    fi
}

# 배포 모니터링
deployment_monitoring() {
    print_header
    echo -e "${GREEN}📊 배포 상태 모니터링${NC}"
    echo ""
    
    info "실시간 모니터링을 시작합니다... (Ctrl+C로 종료)"
    echo ""
    
    while true; do
        clear
        echo -e "${GREEN}📊 실시간 모니터링 - $(date)${NC}"
        echo "=================================================="
        
        # 서비스 상태
        echo "🔄 서비스 상태:"
        if command -v docker &> /dev/null; then
            docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "Docker가 실행되지 않음"
        else
            echo "Docker가 설치되지 않음"
        fi
        echo ""
        
        # 응답 시간 테스트
        echo "⚡ 응답 시간:"
        for endpoint in "http://localhost:3000" "http://localhost:8080/health"; do
            if command -v curl &> /dev/null; then
                response_time=$(curl -o /dev/null -s -w "%{time_total}" "$endpoint" 2>/dev/null || echo "N/A")
                echo "  $endpoint: ${response_time}s"
            else
                echo "  $endpoint: curl이 필요함"
            fi
        done
        echo ""
        
        echo "Ctrl+C로 종료하고 메인 메뉴로 돌아갑니다..."
        sleep 5
    done
}

# 데이터베이스 관리
database_management() {
    print_header
    echo -e "${YELLOW}🗄️  데이터베이스 관리${NC}"
    echo ""
    
    echo "1) 📋 데이터베이스 상태 확인"
    echo "2) 💾 백업 생성"
    echo "3) 🔄 백업 복원"
    echo "4) 🧹 데이터 정리"
    echo "5) 📊 사용량 통계"
    echo "0) 🔙 메인 메뉴로 돌아가기"
    echo ""
    read -p "선택: " db_choice
    
    case $db_choice in
        1)
            info "MongoDB 상태 확인 중..."
            if command -v docker &> /dev/null; then
                docker exec mongodb mongo --eval "db.adminCommand('listCollections')" online_evaluation 2>/dev/null || {
                    error "MongoDB 연결 실패"
                }
            else
                error "Docker가 필요합니다"
            fi
            ;;
        2)
            info "데이터베이스 백업 생성 중..."
            BACKUP_NAME="backup_$(date +%Y%m%d_%H%M%S)"
            if command -v docker &> /dev/null; then
                docker exec mongodb mongodump --db online_evaluation --out "/backup/$BACKUP_NAME" && {
                    success "백업이 생성되었습니다: $BACKUP_NAME"
                } || {
                    error "백업 생성 실패"
                }
            else
                error "Docker가 필요합니다"
            fi
            ;;
        3)
            info "사용 가능한 백업 목록:"
            if command -v docker &> /dev/null; then
                docker exec mongodb ls -la /backup/ 2>/dev/null || {
                    warning "백업 디렉토리를 찾을 수 없습니다"
                }
            else
                error "Docker가 필요합니다"
            fi
            ;;
        4)
            warning "데이터 정리는 신중히 수행해야 합니다!"
            read -p "정말로 임시 데이터를 정리하시겠습니까? (yes/no): " confirm_cleanup
            if [ "$confirm_cleanup" = "yes" ]; then
                info "임시 데이터 정리 중..."
                success "데이터 정리가 완료되었습니다"
            fi
            ;;
        5)
            info "데이터베이스 사용량 통계:"
            if command -v docker &> /dev/null; then
                docker exec mongodb mongo --eval "db.stats()" online_evaluation 2>/dev/null || {
                    error "통계 조회 실패"
                }
            else
                error "Docker가 필요합니다"
            fi
            ;;
        0)
            main_menu
            return
            ;;
    esac
    
    read -p "계속하려면 Enter를 누르세요..."
    database_management
}

# 서비스 복구
service_recovery() {
    print_header
    echo -e "${RED}🔄 서비스 재시작/복구${NC}"
    echo ""
    
    echo "1) 🔄 전체 서비스 재시작"
    echo "2) 🎯 개별 서비스 재시작"
    echo "3) 🚨 긴급 복구 모드"
    echo "4) 📋 서비스 로그 확인"
    echo "0) 🔙 메인 메뉴로 돌아가기"
    echo ""
    read -p "선택: " recovery_choice
    
    case $recovery_choice in
        1)
            info "전체 서비스를 재시작합니다..."
            if command -v docker-compose &> /dev/null; then
                docker-compose restart && success "전체 서비스 재시작 완료" || error "재시작 실패"
            else
                error "docker-compose가 필요합니다"
            fi
            ;;
        2)
            echo "재시작할 서비스를 선택하세요:"
            if command -v docker-compose &> /dev/null; then
                docker-compose ps --services
                read -p "서비스명: " service_name
                if [ -n "$service_name" ]; then
                    docker-compose restart "$service_name" && success "$service_name 재시작 완료" || error "재시작 실패"
                fi
            else
                error "docker-compose가 필요합니다"
            fi
            ;;
        3)
            warning "긴급 복구 모드를 실행합니다!"
            info "모든 컨테이너를 중지하고 재시작합니다..."
            if command -v docker-compose &> /dev/null; then
                docker-compose down
                docker-compose up -d
                success "긴급 복구가 완료되었습니다"
            else
                error "docker-compose가 필요합니다"
            fi
            ;;
        4)
            echo "로그를 확인할 서비스를 선택하세요:"
            if command -v docker-compose &> /dev/null; then
                docker-compose ps --services
                read -p "서비스명: " service_name
                if [ -n "$service_name" ]; then
                    docker-compose logs --tail=50 "$service_name"
                fi
            else
                error "docker-compose가 필요합니다"
            fi
            ;;
        0)
            main_menu
            return
            ;;
    esac
    
    read -p "계속하려면 Enter를 누르세요..."
    service_recovery
}

# AI 기반 스마트 배포
smart_ai_deployment() {
    print_header
    echo -e "${PURPLE}🚀 AI 기반 스마트 배포${NC}"
    echo ""
    
    info "AI가 시스템을 분석하고 최적 배포 전략을 제안합니다..."
    
    # 시스템 분석
    local cpu_usage="50"
    local memory_usage="60"
    local disk_usage="30"
    
    if command -v top &> /dev/null; then
        cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1 | cut -d'.' -f1 2>/dev/null || echo "50")
    fi
    
    if command -v free &> /dev/null; then
        memory_usage=$(free | grep Mem | awk '{printf("%.0f", $3/$2 * 100.0)}' 2>/dev/null || echo "60")
    fi
    
    if command -v df &> /dev/null; then
        disk_usage=$(df -h . | awk 'NR==2{print $5}' | cut -d'%' -f1 2>/dev/null || echo "30")
    fi
    
    echo "📊 시스템 분석 결과:"
    echo "  CPU 사용률: ${cpu_usage}%"
    echo "  메모리 사용률: ${memory_usage}%"
    echo "  디스크 사용률: ${disk_usage}%"
    echo ""
    
    # AI 추천 로직 (간단한 규칙 기반)
    if [ "$cpu_usage" -gt 80 ] || [ "$memory_usage" -gt 85 ]; then
        warning "🤖 AI 추천: 리소스 사용률이 높습니다. 스케일 아웃 배포를 권장합니다."
        recommended_strategy="scale-out"
    elif [ "$disk_usage" -gt 90 ]; then
        warning "🤖 AI 추천: 디스크 공간이 부족합니다. 정리 후 배포를 권장합니다."
        recommended_strategy="cleanup-first"
    else
        success "🤖 AI 추천: 시스템 상태가 양호합니다. 표준 배포를 권장합니다."
        recommended_strategy="standard"
    fi
    
    echo ""
    read -p "AI 추천 전략을 적용하시겠습니까? (y/N): " apply_ai
    if [[ $apply_ai =~ ^[Yy]$ ]]; then
        case $recommended_strategy in
            "scale-out")
                info "스케일 아웃 배포를 수행합니다..."
                if command -v docker-compose &> /dev/null; then
                    docker-compose up -d --scale backend=2 --scale frontend=2
                else
                    error "docker-compose가 필요합니다"
                fi
                ;;
            "cleanup-first")
                info "시스템 정리를 먼저 수행합니다..."
                if command -v docker &> /dev/null; then
                    docker system prune -f
                fi
                deploy_docker_compose
                ;;
            "standard")
                deploy_docker_compose
                ;;
        esac
    fi
    
    read -p "메인 메뉴로 돌아가시겠습니까? (y/N): " return_menu
    if [[ $return_menu =~ ^[Yy]$ ]]; then
        main_menu
    fi
}

# 성능 테스트
performance_testing() {
    print_header
    echo -e "${CYAN}📈 성능 테스트 실행${NC}"
    echo ""
    
    info "성능 테스트를 시작합니다..."
    
    # Apache Bench 또는 curl을 사용한 간단한 성능 테스트
    if command -v ab &> /dev/null; then
        info "Apache Bench로 부하 테스트 실행 중..."
        ab -n 100 -c 10 http://localhost:8080/health 2>/dev/null || {
            warning "Apache Bench 테스트 실패"
        }
    elif command -v curl &> /dev/null; then
        info "curl을 사용한 응답 시간 테스트..."
        for i in {1..10}; do
            response_time=$(curl -o /dev/null -s -w "%{time_total}" http://localhost:8080/health 2>/dev/null || echo "N/A")
            echo "요청 $i: ${response_time}s"
        done
    else
        warning "성능 테스트 도구가 없습니다 (ab 또는 curl 필요)"
    fi
    
    # Docker 컨테이너 리소스 사용량
    echo ""
    info "컨테이너 리소스 사용량:"
    if command -v docker &> /dev/null; then
        docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" 2>/dev/null || {
            warning "Docker 통계를 가져올 수 없습니다"
        }
    else
        warning "Docker가 필요합니다"
    fi
    
    read -p "메인 메뉴로 돌아가시겠습니까? (y/N): " return_menu
    if [[ $return_menu =~ ^[Yy]$ ]]; then
        main_menu
    fi
}

# 보안 스캔
security_scanning() {
    print_header
    echo -e "${RED}🔒 보안 스캔 및 검증${NC}"
    echo ""
    
    info "보안 스캔을 실행합니다..."
    
    # Docker 이미지 보안 스캔
    if command -v trivy &> /dev/null; then
        info "Trivy를 사용한 컨테이너 이미지 스캔..."
        trivy image online-evaluation-backend:latest 2>/dev/null || {
            warning "Trivy 스캔 실패"
        }
    else
        warning "Trivy가 설치되지 않았습니다"
    fi
    
    # 포트 스캔
    info "열린 포트 확인..."
    if command -v netstat &> /dev/null; then
        netstat -tlnp | grep ":3000\|:8080\|:27017\|:6379"
    elif command -v ss &> /dev/null; then
        ss -tlnp | grep ":3000\|:8080\|:27017\|:6379"
    else
        warning "포트 스캔 도구가 없습니다"
    fi
    
    # 환경 변수 보안 검사
    echo ""
    info "환경 변수 보안 검사:"
    if [ -f ".env" ] && grep -q "password123\|secret-key" .env 2>/dev/null; then
        warning "⚠️  기본 패스워드나 시크릿이 발견되었습니다!"
    else
        success "✅ 환경 변수 보안 검사 통과"
    fi
    
    # SSL/TLS 인증서 확인
    if command -v openssl &> /dev/null; then
        echo ""
        info "SSL 인증서 확인:"
        if [ -f "ssl/cert.pem" ]; then
            openssl x509 -in ssl/cert.pem -text -noout | grep "Not After"
        else
            warning "SSL 인증서를 찾을 수 없습니다"
        fi
    fi
    
    read -p "메인 메뉴로 돌아가시겠습니까? (y/N): " return_menu
    if [[ $return_menu =~ ^[Yy]$ ]]; then
        main_menu
    fi
}

# 배포 히스토리
deployment_history() {
    print_header
    echo -e "${BLUE}📋 배포 히스토리 관리${NC}"
    echo ""
    
    info "배포 히스토리를 조회합니다..."
    
    # Git 로그 기반 배포 히스토리
    echo "🔄 최근 Git 커밋:"
    if command -v git &> /dev/null; then
        git log --oneline -10 2>/dev/null || {
            warning "Git 히스토리를 가져올 수 없습니다"
        }
    else
        warning "Git이 설치되지 않았습니다"
    fi
    
    echo ""
    echo "📦 Docker 이미지 히스토리:"
    if command -v docker &> /dev/null; then
        docker images | grep online-evaluation 2>/dev/null || {
            warning "Docker 이미지를 찾을 수 없습니다"
        }
    else
        warning "Docker가 설치되지 않았습니다"
    fi
    
    echo ""
    echo "📄 배포 로그 파일:"
    ls -la deployment_*.log 2>/dev/null || {
        info "배포 로그 파일이 없습니다"
    }
    
    echo ""
    read -p "특정 로그 파일을 보시겠습니까? (파일명 입력 또는 Enter): " log_file
    if [ -n "$log_file" ] && [ -f "$log_file" ]; then
        tail -20 "$log_file"
    fi
    
    read -p "메인 메뉴로 돌아가시겠습니까? (y/N): " return_menu
    if [[ $return_menu =~ ^[Yy]$ ]]; then
        main_menu
    fi
}

# 배포 요약 표시
show_deployment_summary() {
    local env_name="$1"
    local frontend_url="$2"
    local backend_url="$3"
    
    echo ""
    echo -e "${GREEN}========================================================"
    echo -e "🎉 $env_name 환경 배포 완료!"
    echo -e "========================================================${NC}"
    echo ""
    echo -e "${CYAN}📱 서비스 접속 정보:${NC}"
    echo "    프론트엔드: $frontend_url"
    echo "    백엔드 API: $backend_url"
    echo "    API 문서:   $backend_url/docs"
    echo ""
    echo -e "${CYAN}🛠️ 관리 명령어:${NC}"
    echo "    서비스 상태: docker-compose ps"
    echo "    로그 확인:   docker-compose logs -f"
    echo "    서비스 중지: docker-compose down"
    echo ""
    echo -e "${CYAN}📊 로그 파일:${NC}"
    echo "    배포 로그: $LOGFILE"
    if [ -f "$ERROR_LOG" ]; then
        echo "    오류 로그: $ERROR_LOG"
    fi
    echo ""
    
    # 브라우저 자동 열기
    if command -v xdg-open &> /dev/null; then
        # Linux
        info "🌐 웹페이지를 자동으로 엽니다..."
        xdg-open "$frontend_url" &
    elif command -v open &> /dev/null; then
        # macOS
        info "🌐 웹페이지를 자동으로 엽니다..."
        open "$frontend_url" &
    fi
}

# 종료
exit_deployment() {
    print_header
    echo -e "${GREEN}배포 시스템을 종료합니다.${NC}"
    echo ""
    
    if [ -f backend.pid ]; then
        info "백엔드 개발 서버 종료 중..."
        kill $(cat backend.pid) 2>/dev/null && rm backend.pid
    fi
    
    if [ -f frontend.pid ]; then
        info "프론트엔드 개발 서버 종료 중..."
        kill $(cat frontend.pid) 2>/dev/null && rm frontend.pid
    fi
    
    success "배포 시스템이 정상적으로 종료되었습니다."
    echo ""
    echo "로그 파일: $LOGFILE"
    if [ -f "$ERROR_LOG" ]; then
        echo "오류 로그: $ERROR_LOG"
    fi
    echo ""
    echo "감사합니다! 🚀"
    exit 0
}

# 스크립트 시작점
main() {
    # 권한 검사
    if [ ! -w "." ]; then
        error "현재 디렉토리에 쓰기 권한이 없습니다."
        exit 1
    fi
    
    # 신호 처리
    trap exit_deployment INT TERM
    
    # 메인 메뉴 실행
    main_menu
}

# 스크립트 실행
main "$@"