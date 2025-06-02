#!/bin/bash

# 온라인 평가 시스템 빌드 및 배포 스크립트
# 사용법: ./build-and-deploy.sh [production|development]

set -e  # 에러 발생 시 스크립트 종료

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 환경 설정
ENVIRONMENT=${1:-development}
PROJECT_NAME="online-evaluation"
DOCKER_REGISTRY=${DOCKER_REGISTRY:-""}

echo -e "${BLUE}=== 온라인 평가 시스템 빌드 및 배포 스크립트 ===${NC}"
echo -e "${YELLOW}환경: $ENVIRONMENT${NC}"
echo -e "${YELLOW}프로젝트: $PROJECT_NAME${NC}"

# 함수 정의
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 사전 검사
check_requirements() {
    log_info "시스템 요구사항 확인 중..."
    
    # Docker 설치 확인
    if ! command -v docker &> /dev/null; then
        log_error "Docker가 설치되지 않았습니다."
        exit 1
    fi
    
    # Docker Compose 설치 확인
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose가 설치되지 않았습니다."
        exit 1
    fi
    
    # .env 파일 확인
    if [ ! -f ".env.$ENVIRONMENT" ]; then
        log_error ".env.$ENVIRONMENT 파일이 없습니다."
        exit 1
    fi
    
    log_info "시스템 요구사항 확인 완료"
}

# Docker 이미지 빌드
build_images() {
    log_info "Docker 이미지 빌드 중..."
    
    # 환경변수 파일 복사
    cp ".env.$ENVIRONMENT" .env
    
    # 기존 이미지 정리 (선택적)
    if [ "$2" == "--clean" ]; then
        log_warn "기존 이미지 정리 중..."
        docker-compose down -v --remove-orphans
        docker system prune -f
    fi
    
    # 이미지 빌드
    docker-compose build --no-cache
    
    log_info "Docker 이미지 빌드 완료"
}

# 컨테이너 배포
deploy_containers() {
    log_info "컨테이너 배포 중..."
    
    # 기존 컨테이너 중지
    docker-compose down
    
    # 새 컨테이너 시작
    docker-compose up -d
    
    # 헬스 체크
    log_info "서비스 헬스 체크 중..."
    sleep 10
    
    # MongoDB 연결 확인
    if docker-compose exec -T mongodb mongosh --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
        log_info "MongoDB 연결 확인됨"
    else
        log_error "MongoDB 연결 실패"
        exit 1
    fi
    
    # Redis 연결 확인
    if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
        log_info "Redis 연결 확인됨"
    else
        log_error "Redis 연결 실패"
        exit 1
    fi
    
    # 백엔드 헬스 체크
    sleep 15
    if curl -f http://localhost:8080/health > /dev/null 2>&1; then
        log_info "백엔드 서비스 정상"
    else
        log_error "백엔드 서비스 헬스 체크 실패"
        exit 1
    fi
    
    # 프론트엔드 헬스 체크
    if curl -f http://localhost:3000 > /dev/null 2>&1; then
        log_info "프론트엔드 서비스 정상"
    else
        log_error "프론트엔드 서비스 헬스 체크 실패"
        exit 1
    fi
    
    log_info "모든 서비스 배포 완료"
}

# 서비스 상태 확인
check_services() {
    log_info "서비스 상태 확인 중..."
    
    echo -e "\n${BLUE}=== 컨테이너 상태 ===${NC}"
    docker-compose ps
    
    echo -e "\n${BLUE}=== 서비스 접속 정보 ===${NC}"
    echo -e "프론트엔드: ${GREEN}http://localhost:3000${NC}"
    echo -e "백엔드 API: ${GREEN}http://localhost:8080${NC}"
    echo -e "MongoDB: ${GREEN}mongodb://localhost:27017${NC}"
    echo -e "Redis: ${GREEN}redis://localhost:6379${NC}"
    
    echo -e "\n${BLUE}=== 로그 확인 명령어 ===${NC}"
    echo -e "전체 로그: ${YELLOW}docker-compose logs -f${NC}"
    echo -e "백엔드 로그: ${YELLOW}docker-compose logs -f backend${NC}"
    echo -e "프론트엔드 로그: ${YELLOW}docker-compose logs -f frontend${NC}"
}

# 백업 생성
create_backup() {
    log_info "데이터 백업 생성 중..."
    
    BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # MongoDB 백업
    docker-compose exec -T mongodb mongodump --out /tmp/backup
    docker cp "$(docker-compose ps -q mongodb)":/tmp/backup "$BACKUP_DIR/mongodb"
    
    # 설정 파일 백업
    cp -r ./scripts "$BACKUP_DIR/"
    cp .env "$BACKUP_DIR/"
    cp docker-compose.yml "$BACKUP_DIR/"
    
    log_info "백업 생성 완료: $BACKUP_DIR"
}

# 메인 실행 로직
main() {
    case "$1" in
        "build")
            check_requirements
            build_images "$@"
            ;;
        "deploy")
            check_requirements
            deploy_containers
            check_services
            ;;
        "restart")
            log_info "서비스 재시작 중..."
            docker-compose restart
            check_services
            ;;
        "stop")
            log_info "서비스 중지 중..."
            docker-compose down
            ;;
        "backup")
            create_backup
            ;;
        "logs")
            docker-compose logs -f
            ;;
        "full")
            check_requirements
            build_images "$@"
            deploy_containers
            check_services
            ;;
        *)
            echo -e "${BLUE}온라인 평가 시스템 관리 스크립트${NC}"
            echo ""
            echo "사용법: $0 [명령어] [환경]"
            echo ""
            echo "명령어:"
            echo "  build     - Docker 이미지 빌드"
            echo "  deploy    - 컨테이너 배포 및 실행"
            echo "  restart   - 서비스 재시작"
            echo "  stop      - 서비스 중지"
            echo "  backup    - 데이터 백업"
            echo "  logs      - 실시간 로그 확인"
            echo "  full      - 빌드 + 배포 (전체 과정)"
            echo ""
            echo "환경: development (기본값) | production"
            echo ""
            echo "예시:"
            echo "  $0 full production     # 프로덕션 환경으로 전체 배포"
            echo "  $0 build development   # 개발 환경으로 이미지 빌드"
            echo "  $0 deploy             # 개발 환경으로 배포"
            exit 1
            ;;
    esac
}

# 스크립트 실행
main "$@"
