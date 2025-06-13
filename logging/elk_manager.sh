#!/bin/bash
# ELK Stack 배포 및 관리 스크립트
# Online Evaluation System - ELK Stack Management

set -e

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

# ELK 스택 상태 확인
check_elk_status() {
    log_info "ELK 스택 상태 확인 중..."
    
    # Elasticsearch 상태 확인
    if curl -f -s http://localhost:9200/_cluster/health > /dev/null 2>&1; then
        log_success "Elasticsearch: 정상 작동"
    else
        log_error "Elasticsearch: 연결 실패"
        return 1
    fi
    
    # Logstash 상태 확인
    if curl -f -s http://localhost:9600 > /dev/null 2>&1; then
        log_success "Logstash: 정상 작동"
    else
        log_error "Logstash: 연결 실패"
        return 1
    fi
    
    # Kibana 상태 확인
    if curl -f -s http://localhost:5601/api/status > /dev/null 2>&1; then
        log_success "Kibana: 정상 작동"
    else
        log_error "Kibana: 연결 실패"
        return 1
    fi
    
    log_success "모든 ELK 컴포넌트가 정상적으로 작동 중입니다!"
}

# ELK 스택 시작
start_elk() {
    log_info "ELK 스택 시작 중..."
    
    # logging 프로파일로 ELK 스택 시작
    docker-compose --profile logging up -d
    
    log_info "ELK 서비스 시작 대기 중..."
    sleep 30
    
    # 초기화 스크립트 실행
    log_info "Elasticsearch 초기화 실행 중..."
    docker-compose --profile logging-init up elasticsearch-setup-dev
    
    log_info "Kibana 대시보드 설정 중..."
    docker-compose --profile logging-init up kibana-setup-dev
    
    log_success "ELK 스택이 성공적으로 시작되었습니다!"
    
    # 상태 확인
    sleep 10
    check_elk_status
}

# ELK 스택 중지
stop_elk() {
    log_info "ELK 스택 중지 중..."
    
    docker-compose --profile logging --profile logging-init down
    
    log_success "ELK 스택이 중지되었습니다."
}

# ELK 스택 재시작
restart_elk() {
    log_info "ELK 스택 재시작 중..."
    
    stop_elk
    sleep 5
    start_elk
}

# 로그 확인
view_logs() {
    local service=${1:-""}
    
    if [ -z "$service" ]; then
        log_info "모든 ELK 서비스 로그 확인..."
        docker-compose logs -f elasticsearch-dev logstash-dev kibana-dev filebeat-dev
    else
        log_info "$service 로그 확인..."
        docker-compose logs -f "$service"
    fi
}

# 인덱스 정리
cleanup_indices() {
    local days=${1:-30}
    
    log_info "$days 일 이상 된 인덱스 정리 중..."
    
    # 30일 이상 된 인덱스 목록 조회
    old_indices=$(curl -s "http://localhost:9200/_cat/indices/app-logs-*?h=index,creation.date.string" | \
        awk -v cutoff_date="$(date -d "$days days ago" +%Y-%m-%d)" \
        '$2 < cutoff_date {print $1}')
    
    if [ -z "$old_indices" ]; then
        log_info "정리할 인덱스가 없습니다."
        return 0
    fi
    
    log_warning "다음 인덱스들이 삭제됩니다:"
    echo "$old_indices"
    
    read -p "계속하시겠습니까? (y/N): " confirm
    if [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]]; then
        for index in $old_indices; do
            log_info "인덱스 삭제 중: $index"
            curl -X DELETE "http://localhost:9200/$index"
        done
        log_success "인덱스 정리 완료!"
    else
        log_info "인덱스 정리가 취소되었습니다."
    fi
}

# 백업 생성
backup_elk() {
    local backup_dir="elk_backup_$(date +%Y%m%d_%H%M%S)"
    
    log_info "ELK 설정 백업 생성 중: $backup_dir"
    
    mkdir -p "$backup_dir"
    
    # 설정 파일 백업
    cp -r logging/ "$backup_dir/"
    
    # Elasticsearch 매핑 및 설정 백업
    curl -s "http://localhost:9200/_cluster/settings" > "$backup_dir/cluster_settings.json"
    curl -s "http://localhost:9200/_template" > "$backup_dir/index_templates.json"
    curl -s "http://localhost:9200/_ilm/policy" > "$backup_dir/ilm_policies.json"
    
    # 압축
    tar -czf "$backup_dir.tar.gz" "$backup_dir"
    rm -rf "$backup_dir"
    
    log_success "백업이 생성되었습니다: $backup_dir.tar.gz"
}

# 성능 모니터링
monitor_performance() {
    log_info "ELK 성능 모니터링 시작..."
    
    if [ -f "logging/elk_performance_monitor.py" ]; then
        python3 logging/elk_performance_monitor.py "$@"
    else
        log_error "성능 모니터링 스크립트를 찾을 수 없습니다."
        return 1
    fi
}

# 인덱스 상태 확인
check_indices() {
    log_info "인덱스 상태 확인 중..."
    
    echo -e "\n📊 인덱스 상태:"
    curl -s "http://localhost:9200/_cat/indices/app-logs-*?v&s=index"
    
    echo -e "\n💾 인덱스 크기:"
    curl -s "http://localhost:9200/_cat/indices/app-logs-*?v&h=index,store.size,docs.count&s=store.size:desc"
    
    echo -e "\n🏥 클러스터 상태:"
    curl -s "http://localhost:9200/_cluster/health?pretty"
}

# 도움말 출력
show_help() {
    echo "ELK Stack 관리 스크립트"
    echo ""
    echo "사용법: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  start                 ELK 스택 시작"
    echo "  stop                  ELK 스택 중지"
    echo "  restart               ELK 스택 재시작"
    echo "  status                ELK 스택 상태 확인"
    echo "  logs [service]        로그 확인 (서비스명 선택사항)"
    echo "  cleanup [days]        오래된 인덱스 정리 (기본: 30일)"
    echo "  backup                설정 백업 생성"
    echo "  monitor [--watch]     성능 모니터링"
    echo "  indices               인덱스 상태 확인"
    echo "  help                  이 도움말 출력"
    echo ""
    echo "Examples:"
    echo "  $0 start              # ELK 스택 시작"
    echo "  $0 logs elasticsearch-dev # Elasticsearch 로그 확인"
    echo "  $0 cleanup 7          # 7일 이상 된 인덱스 삭제"
    echo "  $0 monitor --watch    # 지속적인 성능 모니터링"
}

# 메인 실행 로직
main() {
    case "${1:-help}" in
        start)
            start_elk
            ;;
        stop)
            stop_elk
            ;;
        restart)
            restart_elk
            ;;
        status)
            check_elk_status
            ;;
        logs)
            view_logs "$2"
            ;;
        cleanup)
            cleanup_indices "$2"
            ;;
        backup)
            backup_elk
            ;;
        monitor)
            shift
            monitor_performance "$@"
            ;;
        indices)
            check_indices
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "알 수 없는 명령어: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# 스크립트 실행
main "$@"
