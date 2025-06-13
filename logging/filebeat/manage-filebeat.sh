#!/bin/bash

# Filebeat 관리 스크립트
# 용도: Filebeat 상태 모니터링, 설정 검증, 레지스트리 관리

set -e

FILEBEAT_HOME="${FILEBEAT_HOME:-/usr/share/filebeat}"
FILEBEAT_CONFIG="${FILEBEAT_CONFIG:-/usr/share/filebeat/filebeat.yml}"
FILEBEAT_DATA="${FILEBEAT_DATA:-/usr/share/filebeat/data}"
FILEBEAT_LOGS="${FILEBEAT_LOGS:-/var/log/filebeat}"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로깅 함수
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

# Filebeat 상태 확인
check_filebeat_status() {
    log_info "Filebeat 상태 확인 중..."
    
    if pgrep -f filebeat > /dev/null; then
        local pid=$(pgrep -f filebeat)
        log_success "Filebeat 실행 중 (PID: $pid)"
        
        # 메모리 사용량 확인
        local memory=$(ps -p $pid -o rss= | awk '{print $1/1024 "MB"}')
        log_info "메모리 사용량: $memory"
        
        # CPU 사용량 확인  
        local cpu=$(ps -p $pid -o %cpu= | awk '{print $1"%"}')
        log_info "CPU 사용량: $cpu"
        
        return 0
    else
        log_error "Filebeat 프로세스가 실행되지 않음"
        return 1
    fi
}

# 설정 파일 검증
validate_config() {
    log_info "Filebeat 설정 검증 중..."
    
    if [[ ! -f "$FILEBEAT_CONFIG" ]]; then
        log_error "설정 파일이 존재하지 않음: $FILEBEAT_CONFIG"
        return 1
    fi
    
    # 설정 문법 검증
    if filebeat test config -c "$FILEBEAT_CONFIG" >/dev/null 2>&1; then
        log_success "설정 파일 문법 검증 완료"
    else
        log_error "설정 파일 문법 오류 발견"
        filebeat test config -c "$FILEBEAT_CONFIG"
        return 1
    fi
    
    # 출력 연결 테스트
    log_info "Logstash 연결 테스트 중..."
    if filebeat test output -c "$FILEBEAT_CONFIG" >/dev/null 2>&1; then
        log_success "Logstash 연결 테스트 성공"
    else
        log_warning "Logstash 연결 테스트 실패 - 네트워크 또는 Logstash 상태 확인 필요"
    fi
}

# 입력 소스 상태 확인
check_input_sources() {
    log_info "입력 소스 상태 확인 중..."
    
    # 애플리케이션 로그 디렉토리
    local app_log_dirs=("/var/log/app" "/app/logs" "/var/log/online-evaluation")
    for dir in "${app_log_dirs[@]}"; do
        if [[ -d "$dir" ]]; then
            local count=$(find "$dir" -name "*.log" -type f 2>/dev/null | wc -l)
            log_info "애플리케이션 로그 디렉토리 $dir: $count 개 파일"
        else
            log_warning "애플리케이션 로그 디렉토리 없음: $dir"
        fi
    done
    
    # Nginx 로그 파일
    local nginx_logs=("/var/log/nginx/access.log" "/var/log/nginx/error.log")
    for log_file in "${nginx_logs[@]}"; do
        if [[ -f "$log_file" ]]; then
            local size=$(du -h "$log_file" | cut -f1)
            log_info "Nginx 로그 파일 $log_file: $size"
        else
            log_warning "Nginx 로그 파일 없음: $log_file"
        fi
    done
    
    # Docker 로그 디렉토리
    if [[ -d "/var/lib/docker/containers" ]]; then
        local container_count=$(find /var/lib/docker/containers -name "*.log" -type f 2>/dev/null | wc -l)
        log_info "Docker 컨테이너 로그: $container_count 개 파일"
    else
        log_warning "Docker 로그 디렉토리 없음: /var/lib/docker/containers"
    fi
}

# 레지스트리 정보 확인
check_registry() {
    log_info "Filebeat 레지스트리 확인 중..."
    
    local registry_file="$FILEBEAT_DATA/registry/filebeat/data.json"
    
    if [[ -f "$registry_file" ]]; then
        local tracked_files=$(jq -r '.[]' "$registry_file" 2>/dev/null | wc -l)
        log_info "추적 중인 파일 수: $tracked_files"
        
        # 레지스트리 파일 크기
        local registry_size=$(du -h "$registry_file" | cut -f1)
        log_info "레지스트리 파일 크기: $registry_size"
        
        # 최근 업데이트 시간
        local last_modified=$(stat -c %y "$registry_file" 2>/dev/null | cut -d' ' -f1-2)
        log_info "최근 업데이트: $last_modified"
    else
        log_warning "레지스트리 파일 없음: $registry_file"
    fi
}

# 로그 처리량 통계
show_throughput_stats() {
    log_info "로그 처리량 통계 조회 중..."
    
    local log_file="$FILEBEAT_LOGS/filebeat.log"
    
    if [[ -f "$log_file" ]]; then
        # 최근 1시간 내 이벤트 처리량
        local events_last_hour=$(grep "$(date --date='1 hour ago' '+%Y-%m-%dT%H')" "$log_file" 2>/dev/null | grep "events flushed" | wc -l)
        log_info "최근 1시간 처리된 이벤트 배치: $events_last_hour"
        
        # 최근 에러 확인
        local recent_errors=$(tail -100 "$log_file" | grep -i "error\|failed\|exception" | wc -l)
        if [[ $recent_errors -gt 0 ]]; then
            log_warning "최근 에러 발생: $recent_errors 건"
            tail -20 "$log_file" | grep -i "error\|failed\|exception"
        else
            log_success "최근 에러 없음"
        fi
    else
        log_warning "로그 파일 없음: $log_file"
    fi
}

# 레지스트리 정리
clean_registry() {
    log_info "Filebeat 레지스트리 정리 중..."
    
    # Filebeat 중지 확인
    if pgrep -f filebeat > /dev/null; then
        log_error "Filebeat가 실행 중입니다. 먼저 중지해주세요."
        return 1
    fi
    
    local registry_dir="$FILEBEAT_DATA/registry"
    
    if [[ -d "$registry_dir" ]]; then
        # 백업 생성
        local backup_file="$FILEBEAT_DATA/registry_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
        tar -czf "$backup_file" -C "$FILEBEAT_DATA" registry
        log_info "레지스트리 백업 생성: $backup_file"
        
        # 레지스트리 삭제
        rm -rf "$registry_dir"
        log_success "레지스트리 정리 완료"
        log_warning "Filebeat를 재시작하면 모든 파일을 처음부터 다시 읽습니다."
    else
        log_info "정리할 레지스트리 없음"
    fi
}

# 성능 모니터링
monitor_performance() {
    log_info "Filebeat 성능 모니터링 시작 (Ctrl+C로 중지)..."
    
    while true; do
        clear
        echo "=== Filebeat 성능 모니터링 ==="
        echo "시간: $(date)"
        echo
        
        # 프로세스 상태
        if pgrep -f filebeat > /dev/null; then
            local pid=$(pgrep -f filebeat)
            local cpu=$(ps -p $pid -o %cpu= | awk '{print $1}')
            local memory=$(ps -p $pid -o rss= | awk '{print $1/1024}')
            local memory_percent=$(ps -p $pid -o %mem= | awk '{print $1}')
            
            echo "프로세스 ID: $pid"
            echo "CPU 사용률: ${cpu}%"
            echo "메모리 사용량: ${memory}MB (${memory_percent}%)"
        else
            echo "❌ Filebeat 프로세스 없음"
        fi
        
        echo
        echo "=== 파일 상태 ==="
        
        # 로그 파일 처리 상태
        local log_file="$FILEBEAT_LOGS/filebeat.log"
        if [[ -f "$log_file" ]]; then
            local last_entry=$(tail -1 "$log_file" | cut -d' ' -f1-2)
            echo "마지막 로그: $last_entry"
            
            # 최근 1분간 처리량
            local recent_events=$(tail -50 "$log_file" | grep "$(date --date='1 minute ago' '+%Y-%m-%dT%H:%M')" | grep "events flushed" | wc -l)
            echo "최근 1분간 처리된 배치: $recent_events"
        fi
        
        # 레지스트리 정보
        local registry_file="$FILEBEAT_DATA/registry/filebeat/data.json"
        if [[ -f "$registry_file" ]]; then
            local tracked_files=$(jq -r '.[]' "$registry_file" 2>/dev/null | wc -l)
            echo "추적 중인 파일: $tracked_files"
        fi
        
        sleep 5
    done
}

# 도움말 출력
show_help() {
    cat << EOF
Filebeat 관리 스크립트

사용법: $0 [옵션]

옵션:
    status      - Filebeat 프로세스 상태 확인
    validate    - 설정 파일 검증 및 연결 테스트
    inputs      - 입력 소스 상태 확인
    registry    - 레지스트리 정보 확인
    stats       - 로그 처리량 통계
    clean       - 레지스트리 정리 (Filebeat 중지 후 실행)
    monitor     - 실시간 성능 모니터링
    help        - 이 도움말 출력

예제:
    $0 status           # 상태 확인
    $0 validate         # 설정 검증
    $0 clean           # 레지스트리 정리
    $0 monitor         # 성능 모니터링

EOF
}

# 메인 함수
main() {
    case "${1:-help}" in
        status)
            check_filebeat_status
            ;;
        validate)
            validate_config
            ;;
        inputs)
            check_input_sources
            ;;
        registry)
            check_registry
            ;;
        stats)
            show_throughput_stats
            ;;
        clean)
            read -p "레지스트리를 정리하시겠습니까? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                clean_registry
            fi
            ;;
        monitor)
            monitor_performance
            ;;
        help|*)
            show_help
            ;;
    esac
}

# 스크립트 실행
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
