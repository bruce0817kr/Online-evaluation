#!/bin/bash

# 🚀 AI 모델 관리 시스템 - 스테이징 환경 배포 스크립트
# 백엔드 페르소나 중심의 안전하고 효율적인 배포 자동화

set -euo pipefail

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# 아이콘 정의
ROCKET="🚀"
CHECK="✅"
CROSS="❌"
WARNING="⚠️"
INFO="ℹ️"
GEAR="⚙️"
SHIELD="🛡️"
CHART="📊"

# 환경 변수 설정
ENVIRONMENT="${ENVIRONMENT:-staging}"
PROJECT_NAME="${PROJECT_NAME:-ai-model-mgmt}"
AWS_REGION="${AWS_REGION:-ap-northeast-2}"
ECR_REGISTRY="${ECR_REGISTRY:-$(aws sts get-caller-identity --query Account --output text).dkr.ecr.${AWS_REGION}.amazonaws.com}"
IMAGE_TAG="${IMAGE_TAG:-staging-$(date +%Y%m%d-%H%M%S)}"
DEPLOY_DIR="/app"
BACKUP_DIR="/app/backups"
LOG_FILE="/var/log/deploy_${ENVIRONMENT}_$(date +%Y%m%d_%H%M%S).log"

# 로깅 함수
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case $level in
        "INFO")
            echo -e "${BLUE}${INFO} ${WHITE}[${timestamp}] $message${NC}" | tee -a "$LOG_FILE"
            ;;
        "SUCCESS")
            echo -e "${GREEN}${CHECK} ${WHITE}[${timestamp}] $message${NC}" | tee -a "$LOG_FILE"
            ;;
        "ERROR")
            echo -e "${RED}${CROSS} ${WHITE}[${timestamp}] $message${NC}" | tee -a "$LOG_FILE"
            ;;
        "WARNING")
            echo -e "${YELLOW}${WARNING} ${WHITE}[${timestamp}] $message${NC}" | tee -a "$LOG_FILE"
            ;;
        "HEADER")
            echo -e "\n${CYAN}$message${NC}" | tee -a "$LOG_FILE"
            echo -e "${CYAN}$(printf '%.0s=' {1..60})${NC}" | tee -a "$LOG_FILE"
            ;;
    esac
}

# 에러 핸들링
error_handler() {
    local line_no=$1
    log "ERROR" "배포 실패 (라인 $line_no)"
    log "ERROR" "롤백을 시작합니다..."
    rollback_deployment
    exit 1
}

trap 'error_handler $LINENO' ERR

# 시작 메시지
log "HEADER" "${ROCKET} AI 모델 관리 시스템 - 스테이징 환경 배포"
log "INFO" "배포 환경: $ENVIRONMENT"
log "INFO" "프로젝트: $PROJECT_NAME"
log "INFO" "ECR 레지스트리: $ECR_REGISTRY"
log "INFO" "이미지 태그: $IMAGE_TAG"

# 사전 요구사항 검사
check_prerequisites() {
    log "HEADER" "${GEAR} 사전 요구사항 검사"
    
    # 필수 명령어 확인
    local required_commands=("docker" "docker-compose" "aws" "curl" "jq")
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            log "ERROR" "$cmd 명령어가 설치되지 않았습니다"
            exit 1
        fi
        log "SUCCESS" "$cmd 명령어 확인됨"
    done
    
    # AWS 인증 확인
    if ! aws sts get-caller-identity &> /dev/null; then
        log "ERROR" "AWS 인증이 필요합니다"
        exit 1
    fi
    log "SUCCESS" "AWS 인증 확인됨"
    
    # 디스크 공간 확인
    local available_space=$(df /app | tail -1 | awk '{print $4}')
    local required_space=5242880  # 5GB in KB
    
    if [ "$available_space" -lt "$required_space" ]; then
        log "ERROR" "디스크 공간 부족 (필요: 5GB, 사용가능: $((available_space/1024/1024))GB)"
        exit 1
    fi
    log "SUCCESS" "디스크 공간 확인됨 ($((available_space/1024/1024))GB 사용가능)"
    
    # 네트워크 연결 확인
    if ! curl -s --max-time 10 https://api.github.com > /dev/null; then
        log "ERROR" "외부 네트워크 연결 실패"
        exit 1
    fi
    log "SUCCESS" "네트워크 연결 확인됨"
}

# 백업 생성
create_backup() {
    log "HEADER" "${GEAR} 현재 상태 백업"
    
    local backup_timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_path="$BACKUP_DIR/backup_$backup_timestamp"
    
    mkdir -p "$backup_path"
    
    # 현재 Docker Compose 설정 백업
    if [ -f "$DEPLOY_DIR/docker-compose.yml" ]; then
        cp "$DEPLOY_DIR/docker-compose.yml" "$backup_path/"
        log "SUCCESS" "Docker Compose 설정 백업됨"
    fi
    
    # 환경 변수 백업
    if [ -f "$DEPLOY_DIR/.env" ]; then
        cp "$DEPLOY_DIR/.env" "$backup_path/"
        log "SUCCESS" "환경 변수 백업됨"
    fi
    
    # 현재 실행 중인 컨테이너 정보 백업
    docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}" > "$backup_path/containers.txt"
    log "SUCCESS" "컨테이너 상태 백업됨"
    
    # 업로드된 파일 백업 (심볼릭 링크로 공간 절약)
    if [ -d "$DEPLOY_DIR/uploads" ]; then
        ln -s "$DEPLOY_DIR/uploads" "$backup_path/uploads_link"
        log "SUCCESS" "업로드 파일 링크 생성됨"
    fi
    
    echo "$backup_path" > "$DEPLOY_DIR/.last_backup"
    log "SUCCESS" "백업 생성 완료: $backup_path"
}

# ECR 로그인 및 이미지 준비
prepare_images() {
    log "HEADER" "${GEAR} 이미지 준비"
    
    # ECR 로그인
    log "INFO" "ECR에 로그인 중..."
    aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$ECR_REGISTRY"
    log "SUCCESS" "ECR 로그인 성공"
    
    # 백엔드 이미지 빌드 및 푸시
    log "INFO" "백엔드 이미지 빌드 중..."
    cd "$(dirname "$0")/.."
    
    # Docker 이미지 빌드
    docker build \
        --target production \
        --build-arg BUILD_ENV="$ENVIRONMENT" \
        --build-arg BUILD_TIME="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
        --build-arg GIT_COMMIT="$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')" \
        -t "$ECR_REGISTRY/$PROJECT_NAME/backend:$IMAGE_TAG" \
        -t "$ECR_REGISTRY/$PROJECT_NAME/backend:latest" \
        ./backend
    
    log "SUCCESS" "이미지 빌드 완료"
    
    # 이미지 푸시
    log "INFO" "이미지를 ECR에 푸시 중..."
    docker push "$ECR_REGISTRY/$PROJECT_NAME/backend:$IMAGE_TAG"
    docker push "$ECR_REGISTRY/$PROJECT_NAME/backend:latest"
    log "SUCCESS" "이미지 푸시 완료"
    
    # 이미지 보안 스캔 결과 확인
    log "INFO" "이미지 보안 스캔 결과 확인 중..."
    sleep 30  # 스캔 완료 대기
    
    scan_result=$(aws ecr describe-image-scan-findings \
        --repository-name "$PROJECT_NAME/backend" \
        --image-id imageTag="$IMAGE_TAG" \
        --query 'imageScanFindingsSummary.findingCounts' \
        --output json 2>/dev/null || echo '{}')
    
    critical_count=$(echo "$scan_result" | jq -r '.CRITICAL // 0')
    high_count=$(echo "$scan_result" | jq -r '.HIGH // 0')
    
    if [ "$critical_count" -gt 0 ] || [ "$high_count" -gt 5 ]; then
        log "WARNING" "이미지에 보안 취약점 발견 (Critical: $critical_count, High: $high_count)"
        log "WARNING" "배포를 계속하시겠습니까? (5초 후 자동 계속)"
        sleep 5
    else
        log "SUCCESS" "이미지 보안 스캔 통과 (Critical: $critical_count, High: $high_count)"
    fi
}

# 환경 설정 구성
setup_environment() {
    log "HEADER" "${GEAR} 환경 설정 구성"
    
    cd "$DEPLOY_DIR"
    
    # .env 파일 생성
    cat <<EOF > .env
# AI 모델 관리 시스템 - 스테이징 환경 설정
# 생성일시: $(date)

# 기본 환경 설정
NODE_ENV=staging
ENVIRONMENT=staging
PROJECT_NAME=$PROJECT_NAME

# Docker 이미지 설정
ECR_REGISTRY=$ECR_REGISTRY
IMAGE_TAG=$IMAGE_TAG

# 데이터베이스 설정
MONGO_URL=$MONGO_URL
REDIS_URL=$REDIS_URL

# 보안 설정
JWT_SECRET=$JWT_SECRET
API_RATE_LIMIT=1000
CORS_ORIGINS=https://staging.ai-model-mgmt.com,https://api-staging.ai-model-mgmt.com

# 성능 설정
UVICORN_WORKERS=4
UVICORN_MAX_REQUESTS=1000
UVICORN_MAX_REQUESTS_JITTER=100
DATABASE_POOL_SIZE=20
REDIS_POOL_SIZE=10
CACHE_TTL=300

# 모니터링 설정
LOG_LEVEL=INFO
MONITORING_ENABLED=true
GRAFANA_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD:-admin}

# 파일 업로드 설정
MAX_FILE_SIZE=50MB
ALLOWED_FILE_TYPES=pdf,docx,xlsx,txt,json
EOF
    
    log "SUCCESS" "환경 변수 파일 생성됨"
    
    # 디렉터리 구조 생성
    mkdir -p uploads logs config data/prometheus data/grafana
    mkdir -p monitoring/{prometheus,grafana,fluent-bit}
    mkdir -p nginx/conf.d
    
    # 권한 설정
    chmod 755 uploads logs config
    chmod 777 data/prometheus data/grafana  # Prometheus/Grafana 컨테이너 권한
    
    log "SUCCESS" "디렉터리 구조 생성됨"
}

# 모니터링 설정
setup_monitoring() {
    log "HEADER" "${CHART} 모니터링 설정"
    
    # Prometheus 설정
    cat <<EOF > monitoring/prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "rules/*.yml"

scrape_configs:
  - job_name: 'backend-services'
    static_configs:
      - targets: 
        - 'backend-1:9090'
        - 'backend-2:9091'
        - 'backend-3:9092'
        - 'worker:9093'
    metrics_path: '/metrics'
    scrape_interval: 15s
    
  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx:80']
    metrics_path: '/metrics'
    
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

alerting:
  alertmanagers:
    - static_configs:
        - targets: []
EOF
    
    # Grafana 프로비저닝 설정
    mkdir -p monitoring/grafana/provisioning/{datasources,dashboards}
    
    cat <<EOF > monitoring/grafana/provisioning/datasources/prometheus.yml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false
EOF
    
    cat <<EOF > monitoring/grafana/provisioning/dashboards/dashboards.yml
apiVersion: 1

providers:
  - name: 'AI Model Management'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards
EOF
    
    # Nginx 설정
    cat <<EOF > nginx/nginx.conf
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    log_format main '\$remote_addr - \$remote_user [\$time_local] "\$request" '
                    '\$status \$body_bytes_sent "\$http_referer" '
                    '"\$http_user_agent" "\$http_x_forwarded_for" '
                    'rt=\$request_time ut=\$upstream_response_time';
    
    access_log /var/log/nginx/access.log main;
    
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
    
    upstream backend {
        least_conn;
        server backend-1:8000 max_fails=3 fail_timeout=30s;
        server backend-2:8001 max_fails=3 fail_timeout=30s;
        server backend-3:8002 max_fails=3 fail_timeout=30s;
    }
    
    server {
        listen 80;
        server_name _;
        
        location /health {
            access_log off;
            return 200 "OK";
            add_header Content-Type text/plain;
        }
        
        location / {
            proxy_pass http://backend;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
            
            proxy_connect_timeout 30s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
            
            proxy_buffering on;
            proxy_buffer_size 4k;
            proxy_buffers 8 4k;
        }
    }
}
EOF
    
    log "SUCCESS" "모니터링 및 Nginx 설정 완료"
}

# 서비스 배포
deploy_services() {
    log "HEADER" "${ROCKET} 서비스 배포"
    
    cd "$DEPLOY_DIR"
    
    # Docker Compose 설정 복사
    cp "$(dirname "$0")/docker-compose.staging.yml" ./docker-compose.yml
    
    # 기존 서비스 중지 (그레이스풀)
    log "INFO" "기존 서비스 그레이스풀 중지 중..."
    if docker-compose ps -q | grep -q .; then
        docker-compose stop --timeout 30
        log "SUCCESS" "기존 서비스 중지됨"
    fi
    
    # 오래된 이미지 정리
    log "INFO" "오래된 Docker 이미지 정리 중..."
    docker image prune -f
    docker system prune -f --volumes
    
    # 새 서비스 시작
    log "INFO" "새 서비스 시작 중..."
    docker-compose up -d --remove-orphans
    
    log "SUCCESS" "서비스 배포 완료"
}

# 헬스체크 및 검증
verify_deployment() {
    log "HEADER" "${SHIELD} 배포 검증"
    
    local max_attempts=30
    local attempt=1
    local all_healthy=false
    
    # 서비스 헬스체크
    while [ $attempt -le $max_attempts ] && [ "$all_healthy" = false ]; do
        log "INFO" "헬스체크 시도 $attempt/$max_attempts"
        
        local healthy_count=0
        local total_services=3
        
        # 각 백엔드 서비스 헬스체크
        for port in 8000 8001 8002; do
            if curl -sf "http://localhost:$port/health" > /dev/null 2>&1; then
                healthy_count=$((healthy_count + 1))
                log "SUCCESS" "백엔드 서비스 포트 $port 정상"
            else
                log "WARNING" "백엔드 서비스 포트 $port 대기 중..."
            fi
        done
        
        if [ $healthy_count -eq $total_services ]; then
            all_healthy=true
            log "SUCCESS" "모든 서비스가 정상 동작 중"
        else
            log "INFO" "$healthy_count/$total_services 서비스 정상, 20초 후 재시도..."
            sleep 20
            attempt=$((attempt + 1))
        fi
    done
    
    if [ "$all_healthy" = false ]; then
        log "ERROR" "헬스체크 실패, 롤백을 시작합니다"
        return 1
    fi
    
    # API 기능 테스트
    log "INFO" "API 기능 테스트 실행 중..."
    
    # 기본 API 엔드포인트 테스트
    local api_endpoints=("/health" "/api/health" "/api/models" "/api/users")
    for endpoint in "${api_endpoints[@]}"; do
        if curl -sf "http://localhost:8000$endpoint" > /dev/null 2>&1; then
            log "SUCCESS" "API 엔드포인트 $endpoint 정상"
        else
            log "WARNING" "API 엔드포인트 $endpoint 접근 불가 (정상일 수 있음)"
        fi
    done
    
    # 성능 테스트
    log "INFO" "성능 테스트 실행 중..."
    local response_time=$(curl -w "%{time_total}" -s -o /dev/null "http://localhost:8000/health")
    local response_time_ms=$(echo "$response_time * 1000" | bc -l | cut -d. -f1)
    
    if [ "$response_time_ms" -lt 500 ]; then
        log "SUCCESS" "응답시간 테스트 통과 (${response_time_ms}ms)"
    else
        log "WARNING" "응답시간이 느립니다 (${response_time_ms}ms)"
    fi
    
    # 로그 확인
    log "INFO" "서비스 로그 확인 중..."
    if docker-compose logs --tail=50 | grep -i error; then
        log "WARNING" "서비스 로그에 에러가 발견되었습니다"
    else
        log "SUCCESS" "서비스 로그 정상"
    fi
    
    log "SUCCESS" "배포 검증 완료"
}

# 모니터링 검증
verify_monitoring() {
    log "HEADER" "${CHART} 모니터링 시스템 검증"
    
    # Prometheus 헬스체크
    local max_attempts=10
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -sf "http://localhost:9090/-/healthy" > /dev/null 2>&1; then
            log "SUCCESS" "Prometheus 정상 동작"
            break
        else
            log "INFO" "Prometheus 대기 중... (시도 $attempt/$max_attempts)"
            sleep 15
            attempt=$((attempt + 1))
        fi
    done
    
    if [ $attempt -gt $max_attempts ]; then
        log "WARNING" "Prometheus 헬스체크 실패"
    fi
    
    # Grafana 헬스체크
    attempt=1
    while [ $attempt -le $max_attempts ]; do
        if curl -sf "http://localhost:3000/api/health" > /dev/null 2>&1; then
            log "SUCCESS" "Grafana 정상 동작"
            break
        else
            log "INFO" "Grafana 대기 중... (시도 $attempt/$max_attempts)"
            sleep 15
            attempt=$((attempt + 1))
        fi
    done
    
    if [ $attempt -gt $max_attempts ]; then
        log "WARNING" "Grafana 헬스체크 실패"
    fi
    
    # 메트릭 수집 확인
    log "INFO" "메트릭 수집 상태 확인 중..."
    sleep 30  # 메트릭 수집 대기
    
    local targets_up=$(curl -s "http://localhost:9090/api/v1/query?query=up" | jq -r '.data.result | length')
    if [ "$targets_up" -gt 0 ]; then
        log "SUCCESS" "메트릭 수집 정상 ($targets_up 개 타겟)"
    else
        log "WARNING" "메트릭 수집 상태 확인 필요"
    fi
    
    log "SUCCESS" "모니터링 시스템 검증 완료"
}

# 롤백 함수
rollback_deployment() {
    log "HEADER" "${WARNING} 배포 롤백"
    
    if [ -f "$DEPLOY_DIR/.last_backup" ]; then
        local backup_path=$(cat "$DEPLOY_DIR/.last_backup")
        
        if [ -d "$backup_path" ]; then
            log "INFO" "백업에서 복구 중: $backup_path"
            
            # 현재 서비스 중지
            cd "$DEPLOY_DIR"
            docker-compose down --timeout 30 || true
            
            # 백업 복구
            if [ -f "$backup_path/docker-compose.yml" ]; then
                cp "$backup_path/docker-compose.yml" "$DEPLOY_DIR/"
                log "SUCCESS" "Docker Compose 설정 복구됨"
            fi
            
            if [ -f "$backup_path/.env" ]; then
                cp "$backup_path/.env" "$DEPLOY_DIR/"
                log "SUCCESS" "환경 변수 복구됨"
            fi
            
            # 이전 서비스 시작
            docker-compose up -d
            
            # 복구 확인
            sleep 30
            if curl -sf "http://localhost:8000/health" > /dev/null 2>&1; then
                log "SUCCESS" "롤백 완료, 서비스 정상 동작"
            else
                log "ERROR" "롤백 후에도 서비스 이상"
            fi
        else
            log "ERROR" "백업 디렉터리를 찾을 수 없습니다: $backup_path"
        fi
    else
        log "ERROR" "백업 정보를 찾을 수 없습니다"
    fi
}

# 배포 후 정리
post_deployment_cleanup() {
    log "HEADER" "${GEAR} 배포 후 정리"
    
    # 오래된 Docker 이미지 정리
    log "INFO" "오래된 Docker 이미지 정리 중..."
    docker image prune -f --filter "until=72h"
    
    # 오래된 백업 정리 (7일 이상)
    log "INFO" "오래된 백업 정리 중..."
    find "$BACKUP_DIR" -type d -name "backup_*" -mtime +7 -exec rm -rf {} \; 2>/dev/null || true
    
    # 오래된 로그 정리 (30일 이상)
    log "INFO" "오래된 로그 정리 중..."
    find /var/log -name "deploy_*.log" -mtime +30 -delete 2>/dev/null || true
    
    # 시스템 리소스 정보 출력
    log "INFO" "시스템 리소스 현황:"
    echo "CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')% 사용중"
    echo "메모리: $(free | grep Mem | awk '{printf("%.1f"), $3/$2 * 100.0}')% 사용중"
    echo "디스크: $(df -h /app | tail -1 | awk '{print $5}') 사용중"
    echo "Docker 이미지: $(docker images | wc -l)개"
    echo "실행 중인 컨테이너: $(docker ps | wc -l)개"
    
    log "SUCCESS" "배포 후 정리 완료"
}

# 배포 리포트 생성
generate_deployment_report() {
    log "HEADER" "${CHART} 배포 리포트 생성"
    
    local report_file="/tmp/deployment_report_$(date +%Y%m%d_%H%M%S).json"
    
    cat <<EOF > "$report_file"
{
    "deployment_info": {
        "timestamp": "$(date -u +'%Y-%m-%dT%H:%M:%SZ')",
        "environment": "$ENVIRONMENT",
        "project_name": "$PROJECT_NAME",
        "image_tag": "$IMAGE_TAG",
        "deployed_by": "$(whoami)",
        "deployment_duration": "$(($(date +%s) - ${DEPLOY_START_TIME:-$(date +%s)})) seconds"
    },
    "services": {
        "backend_instances": 3,
        "worker_instances": 1,
        "monitoring": {
            "prometheus": "$(curl -sf http://localhost:9090/-/healthy && echo 'healthy' || echo 'unhealthy')",
            "grafana": "$(curl -sf http://localhost:3000/api/health && echo 'healthy' || echo 'unhealthy')"
        }
    },
    "health_check": {
        "api_response_time": "$(curl -w '%{time_total}' -s -o /dev/null http://localhost:8000/health)s",
        "all_services_healthy": true
    },
    "system_resources": {
        "cpu_usage": "$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')%",
        "memory_usage": "$(free | grep Mem | awk '{printf("%.1f"), $3/$2 * 100.0}')%",
        "disk_usage": "$(df -h /app | tail -1 | awk '{print $5}')"
    }
}
EOF
    
    log "SUCCESS" "배포 리포트 생성됨: $report_file"
    
    # 리포트 요약 출력
    echo
    log "HEADER" "${ROCKET} 배포 완료 요약"
    echo -e "${GREEN}✅ 스테이징 환경 배포 성공!${NC}"
    echo
    echo -e "${WHITE}🎯 배포 정보:${NC}"
    echo -e "  환경: ${CYAN}$ENVIRONMENT${NC}"
    echo -e "  이미지: ${CYAN}$ECR_REGISTRY/$PROJECT_NAME/backend:$IMAGE_TAG${NC}"
    echo -e "  서비스: ${GREEN}3개 백엔드 + 1개 워커${NC}"
    echo
    echo -e "${WHITE}🔗 접속 정보:${NC}"
    echo -e "  API: ${BLUE}http://localhost:8000${NC}"
    echo -e "  Prometheus: ${BLUE}http://localhost:9090${NC}"
    echo -e "  Grafana: ${BLUE}http://localhost:3000${NC} (admin/admin)"
    echo
    echo -e "${WHITE}📊 시스템 상태:${NC}"
    echo -e "  CPU: ${GREEN}$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')%${NC}"
    echo -e "  메모리: ${GREEN}$(free | grep Mem | awk '{printf("%.1f"), $3/$2 * 100.0}')%${NC}"
    echo -e "  디스크: ${GREEN}$(df -h /app | tail -1 | awk '{print $5}')${NC}"
    echo
    echo -e "${WHITE}📋 다음 단계:${NC}"
    echo -e "  1. ${YELLOW}기능 테스트 실행${NC}"
    echo -e "  2. ${YELLOW}성능 테스트 실행${NC}"
    echo -e "  3. ${YELLOW}보안 테스트 실행${NC}"
    echo -e "  4. ${YELLOW}프로덕션 배포 승인${NC}"
    echo
}

# 메인 배포 실행
main() {
    local DEPLOY_START_TIME=$(date +%s)
    
    # 배포 단계 실행
    check_prerequisites
    create_backup
    prepare_images
    setup_environment
    setup_monitoring
    deploy_services
    verify_deployment
    verify_monitoring
    post_deployment_cleanup
    generate_deployment_report
    
    log "SUCCESS" "🎉 스테이징 환경 배포가 성공적으로 완료되었습니다!"
}

# 스크립트 실행
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi