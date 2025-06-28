#!/bin/bash

# Online Evaluation System - Production Deployment Script
# 프로덕션 배포 자동화 스크립트 (포트: 기본포트 + 19)

set -e  # 에러 발생 시 스크립트 중단

echo "🚀 Online Evaluation System - 프로덕션 배포 시작"
echo "================================================"
echo "배포 시간: $(date)"
echo "프로덕션 포트: 3019(Frontend), 8019(Backend), 27036(MongoDB), 6398(Redis)"
echo ""

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로그 함수
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 프로덕션 포트 확인
check_ports() {
    log_info "프로덕션 포트 사용 가능 여부 확인..."
    
    PORTS=(3019 8019 27036 6398)
    for port in "${PORTS[@]}"; do
        if netstat -tuln 2>/dev/null | grep -q ":$port " || docker ps --format "{{.Ports}}" | grep -q ":$port->"; then
            log_error "포트 $port가 이미 사용 중입니다."
            echo "사용 중인 프로세스:"
            netstat -tuln | grep ":$port " || echo "Docker 컨테이너에서 사용 중"
            exit 1
        else
            log_success "포트 $port 사용 가능"
        fi
    done
}

# 기존 프로덕션 컨테이너 정리
cleanup_production() {
    log_info "기존 프로덕션 컨테이너 정리..."
    
    # 프로덕션 컨테이너 중지 및 제거
    docker-compose -f docker-compose.production.yml down -v 2>/dev/null || true
    
    # 프로덕션 이미지 정리 (선택적)
    if [ "$1" = "--clean-images" ]; then
        log_info "프로덕션 이미지 정리..."
        docker images | grep "online-evaluation.*prod" | awk '{print $3}' | xargs -r docker rmi -f
    fi
    
    log_success "정리 완료"
}

# 프로덕션 환경 빌드
build_production() {
    log_info "프로덕션 환경 빌드 시작..."
    
    # 환경 변수 설정
    export NODE_ENV=production
    
    # 프로덕션 Docker 이미지 빌드
    docker-compose -f docker-compose.production.yml build --no-cache
    
    log_success "프로덕션 빌드 완료"
}

# 프로덕션 배포 실행
deploy_production() {
    log_info "프로덕션 배포 실행..."
    
    # 프로덕션 환경 변수 로드
    if [ -f ".env.production" ]; then
        log_info "프로덕션 환경 변수 로드"
        set -a
        source .env.production
        set +a
    fi
    
    # 프로덕션 컨테이너 시작
    docker-compose -f docker-compose.production.yml up -d
    
    log_success "프로덕션 컨테이너 시작 완료"
}

# 배포 검증
verify_deployment() {
    log_info "배포 검증 시작..."
    
    # 컨테이너 상태 확인
    sleep 10
    
    CONTAINERS=("online-evaluation-frontend-prod" "online-evaluation-backend-prod" "online-evaluation-mongodb-prod" "online-evaluation-redis-prod")
    
    for container in "${CONTAINERS[@]}"; do
        if docker ps | grep -q "$container"; then
            log_success "$container: 정상 실행 중"
        else
            log_error "$container: 실행 실패"
            docker logs "$container" --tail 20
            exit 1
        fi
    done
    
    # 헬스체크
    log_info "헬스체크 수행..."
    
    # 백엔드 헬스체크
    for i in {1..30}; do
        if curl -s -f http://localhost:8019/health > /dev/null; then
            log_success "백엔드 헬스체크 성공"
            break
        else
            if [ $i -eq 30 ]; then
                log_error "백엔드 헬스체크 실패"
                exit 1
            fi
            log_info "백엔드 시작 대기... ($i/30)"
            sleep 2
        fi
    done
    
    # 프론트엔드 헬스체크
    for i in {1..30}; do
        if curl -s -f http://localhost:3019 > /dev/null; then
            log_success "프론트엔드 헬스체크 성공"
            break
        else
            if [ $i -eq 30 ]; then
                log_error "프론트엔드 헬스체크 실패"
                exit 1
            fi
            log_info "프론트엔드 시작 대기... ($i/30)"
            sleep 2
        fi
    done
}

# 배포 완료 정보 출력
show_deployment_info() {
    echo ""
    echo "🎉 프로덕션 배포 완료!"
    echo "=========================="
    echo "프론트엔드: http://localhost:3019"
    echo "백엔드 API: http://localhost:8019"
    echo "헬스체크: http://localhost:8019/health"
    echo ""
    echo "관리자 로그인:"
    echo "- 사용자명: admin"
    echo "- 비밀번호: admin123!"
    echo ""
    echo "컨테이너 상태 확인: docker-compose -f docker-compose.production.yml ps"
    echo "로그 확인: docker-compose -f docker-compose.production.yml logs -f"
    echo "중지: docker-compose -f docker-compose.production.yml down"
    echo ""
    echo "배포 시간: $(date)"
}

# 메인 실행 함수
main() {
    case "${1:-deploy}" in
        "check")
            check_ports
            ;;
        "cleanup")
            cleanup_production "${2:-}"
            ;;
        "build")
            build_production
            ;;
        "deploy")
            check_ports
            cleanup_production
            build_production
            deploy_production
            verify_deployment
            show_deployment_info
            ;;
        "verify")
            verify_deployment
            ;;
        "info")
            show_deployment_info
            ;;
        *)
            echo "사용법: $0 [check|cleanup|build|deploy|verify|info]"
            echo ""
            echo "명령어:"
            echo "  check   - 포트 사용 가능 여부 확인"
            echo "  cleanup - 기존 프로덕션 환경 정리"
            echo "  build   - 프로덕션 이미지 빌드"
            echo "  deploy  - 전체 배포 과정 실행 (기본값)"
            echo "  verify  - 배포 검증"
            echo "  info    - 배포 정보 출력"
            echo ""
            echo "예시:"
            echo "  $0 deploy              # 전체 배포"
            echo "  $0 cleanup --clean-images  # 이미지까지 정리"
            echo "  $0 check               # 포트 확인만"
            exit 1
            ;;
    esac
}

# 스크립트 실행
main "$@"