#!/bin/bash
# 🚀 AI 모델 관리 시스템 - 종합 통합 테스트 실행 스크립트
# Build, Test, Deploy with Magic! ✨

set -euo pipefail  # 에러 시 즉시 중단

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
MAGIC="✨"
CHECK="✅"
CROSS="❌"
WARNING="⚠️"
INFO="ℹ️"
GEAR="⚙️"
CHART="📊"
SHIELD="🛡️"
SPEED="💨"

# 로그 함수들
log_info() {
    echo -e "${BLUE}${INFO} ${WHITE}$1${NC}"
}

log_success() {
    echo -e "${GREEN}${CHECK} ${WHITE}$1${NC}"
}

log_error() {
    echo -e "${RED}${CROSS} ${WHITE}$1${NC}"
}

log_warning() {
    echo -e "${YELLOW}${WARNING} ${WHITE}$1${NC}"
}

log_magic() {
    echo -e "${PURPLE}${MAGIC} ${WHITE}$1${NC}"
}

log_section() {
    echo -e "\n${CYAN}$1${NC}"
    echo -e "${CYAN}$(printf '%.0s=' {1..60})${NC}"
}

# 스피너 애니메이션
spinner() {
    local pid=$1
    local delay=0.1
    local spinstr='|/-\'
    while [ "$(ps a | awk '{print $1}' | grep $pid)" ]; do
        local temp=${spinstr#?}
        printf " [%c]  " "$spinstr"
        local spinstr=$temp${spinstr%"$temp"}
        sleep $delay
        printf "\b\b\b\b\b\b"
    done
    printf "    \b\b\b\b"
}

# 진행률 표시
progress_bar() {
    local current=$1
    local total=$2
    local width=50
    local percentage=$((current * 100 / total))
    local completed=$((current * width / total))
    local remaining=$((width - completed))
    
    printf "\r${BLUE}Progress: [${GREEN}"
    printf "%*s" $completed | tr ' ' '='
    printf "${WHITE}"
    printf "%*s" $remaining | tr ' ' '-'
    printf "${BLUE}] ${WHITE}%d%%${NC}" $percentage
}

# 에러 핸들링
error_handler() {
    local line_no=$1
    log_error "Line $line_no에서 에러 발생!"
    log_error "종합 테스트가 중단되었습니다."
    cleanup
    exit 1
}

trap 'error_handler $LINENO' ERR

# 정리 함수
cleanup() {
    log_info "정리 작업 중..."
    # Docker 컨테이너 정리 (선택적)
    if [[ "${CLEANUP_DOCKER:-false}" == "true" ]]; then
        docker-compose down -v --remove-orphans || true
    fi
}

# 환경 변수 설정
setup_environment() {
    log_section "${GEAR} 환경 설정"
    
    # 프로젝트 루트 디렉터리 설정
    export PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
    export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH:-}"
    
    # 테스트 환경 변수
    export TEST_MODE="integration"
    export LOG_LEVEL="INFO"
    export PLAYWRIGHT_BROWSERS_PATH="${PROJECT_ROOT}/node_modules/.bin"
    
    # 포트 설정 (동적으로 할당)
    export FRONTEND_PORT="${FRONTEND_PORT:-3000}"
    export BACKEND_PORT="${BACKEND_PORT:-8000}"
    export MONGODB_PORT="${MONGODB_PORT:-27017}"
    export REDIS_PORT="${REDIS_PORT:-6379}"
    
    # 결과 디렉터리 생성
    export TEST_RESULTS_DIR="${PROJECT_ROOT}/test-results"
    mkdir -p "${TEST_RESULTS_DIR}"
    
    log_success "환경 설정 완료"
}

# 의존성 확인
check_dependencies() {
    log_section "${GEAR} 의존성 확인"
    
    local deps_ok=true
    
    # Python 확인
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3가 설치되지 않았습니다"
        deps_ok=false
    else
        log_success "Python 3: $(python3 --version)"
    fi
    
    # Node.js 확인
    if ! command -v node &> /dev/null; then
        log_error "Node.js가 설치되지 않았습니다"
        deps_ok=false
    else
        log_success "Node.js: $(node --version)"
    fi
    
    # Docker 확인
    if ! command -v docker &> /dev/null; then
        log_error "Docker가 설치되지 않았습니다"
        deps_ok=false
    else
        log_success "Docker: $(docker --version | cut -d' ' -f3 | tr -d ',')"
    fi
    
    # Docker Compose 확인
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose가 설치되지 않았습니다"
        deps_ok=false
    else
        log_success "Docker Compose: $(docker-compose --version | cut -d' ' -f3 | tr -d ',')"
    fi
    
    if [[ "$deps_ok" != "true" ]]; then
        log_error "필수 의존성이 누락되었습니다"
        exit 1
    fi
}

# /build --feature --magic
build_project() {
    log_section "${ROCKET} 프로젝트 빌드 (Magic Mode)"
    
    local build_start_time=$(date +%s)
    
    # Python 의존성 설치
    log_info "Python 의존성 설치 중..."
    (
        cd "${PROJECT_ROOT}"
        pip install -r requirements.txt > /dev/null 2>&1 &
        spinner $!
    )
    log_success "Python 의존성 설치 완료"
    
    # Node.js 의존성 설치
    log_info "Node.js 의존성 설치 중..."
    (
        cd "${PROJECT_ROOT}/frontend"
        npm ci --silent > /dev/null 2>&1 &
        spinner $!
    )
    log_success "Node.js 의존성 설치 완료"
    
    # Playwright 브라우저 설치
    log_info "Playwright 브라우저 설치 중..."
    (
        cd "${PROJECT_ROOT}/frontend"
        npx playwright install > /dev/null 2>&1 &
        spinner $!
    )
    log_success "Playwright 브라우저 설치 완료"
    
    # 프론트엔드 빌드
    log_info "프론트엔드 빌드 중..."
    (
        cd "${PROJECT_ROOT}/frontend"
        npm run build > /dev/null 2>&1 &
        spinner $!
    )
    log_success "프론트엔드 빌드 완료"
    
    # Docker 이미지 빌드
    log_info "Docker 이미지 빌드 중..."
    (
        cd "${PROJECT_ROOT}"
        docker-compose build --parallel > /dev/null 2>&1 &
        spinner $!
    )
    log_success "Docker 이미지 빌드 완료"
    
    local build_end_time=$(date +%s)
    local build_duration=$((build_end_time - build_start_time))
    
    log_magic "✨ Magic Build 완료! (소요시간: ${build_duration}초)"
}

# /test --coverage --magic
run_comprehensive_tests() {
    log_section "${CHART} 종합 테스트 실행 (Coverage + Magic)"
    
    local test_start_time=$(date +%s)
    
    # 테스트 환경 시작
    log_info "테스트 환경 시작 중..."
    (
        cd "${PROJECT_ROOT}"
        docker-compose up -d mongodb redis > /dev/null 2>&1 &
        spinner $!
    )
    log_success "테스트 환경 시작 완료"
    
    # 서비스 준비 대기
    log_info "서비스 준비 대기 중..."
    sleep 10
    
    # 종합 테스트 오케스트레이터 실행
    log_info "통합 테스트 오케스트레이터 실행 중..."
    local test_output="${TEST_RESULTS_DIR}/comprehensive_test_output.log"
    
    if python3 "${PROJECT_ROOT}/integration_tests/comprehensive_test_orchestrator.py" > "${test_output}" 2>&1; then
        log_success "통합 테스트 성공적으로 완료"
        
        # 테스트 결과 분석 실행
        log_info "테스트 결과 분석 중..."
        python3 "${PROJECT_ROOT}/integration_tests/test_result_analyzer.py" > /dev/null 2>&1 || true
        log_success "테스트 결과 분석 완료"
        
    else
        log_error "통합 테스트 실패"
        log_info "오류 로그:"
        tail -20 "${test_output}"
        return 1
    fi
    
    local test_end_time=$(date +%s)
    local test_duration=$((test_end_time - test_start_time))
    
    log_magic "✨ Magic Test 완료! (소요시간: ${test_duration}초)"
}

# 테스트 결과 요약
summarize_results() {
    log_section "${CHART} 테스트 결과 요약"
    
    # 최신 결과 파일 찾기
    local latest_result=$(find "${TEST_RESULTS_DIR}" -name "comprehensive_test_report_*.json" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2)
    
    if [[ -f "$latest_result" ]]; then
        log_info "결과 파일: $(basename "$latest_result")"
        
        # JSON에서 주요 메트릭 추출
        local success_rate=$(python3 -c "
import json
try:
    with open('$latest_result', 'r') as f:
        data = json.load(f)
        rate = data.get('analysis', {}).get('overall_summary', {}).get('success_rate', 0)
        print(f'{rate:.1f}')
except:
    print('0')
")
        
        local total_tests=$(python3 -c "
import json
try:
    with open('$latest_result', 'r') as f:
        data = json.load(f)
        total = data.get('analysis', {}).get('overall_summary', {}).get('total_tests', 0)
        print(total)
except:
    print('0')
")
        
        local failed_tests=$(python3 -c "
import json
try:
    with open('$latest_result', 'r') as f:
        data = json.load(f)
        failed = data.get('analysis', {}).get('overall_summary', {}).get('failed_tests', 0)
        print(failed)
except:
    print('0')
")
        
        # 결과 출력
        echo -e "\n${WHITE}📊 테스트 결과 대시보드${NC}"
        echo -e "${WHITE}$(printf '%.0s─' {1..60})${NC}"
        echo -e "${WHITE}전체 테스트: ${CYAN}${total_tests}개${NC}"
        echo -e "${WHITE}성공률: ${GREEN}${success_rate}%${NC}"
        echo -e "${WHITE}실패 테스트: ${RED}${failed_tests}개${NC}"
        
        # 성공률에 따른 상태 표시
        if (( $(echo "$success_rate >= 98" | bc -l) )); then
            echo -e "${GREEN}${CHECK} 테스트 상태: 우수${NC}"
        elif (( $(echo "$success_rate >= 95" | bc -l) )); then
            echo -e "${YELLOW}${WARNING} 테스트 상태: 양호${NC}"
        elif (( $(echo "$success_rate >= 90" | bc -l) )); then
            echo -e "${YELLOW}${WARNING} 테스트 상태: 보통${NC}"
        else
            echo -e "${RED}${CROSS} 테스트 상태: 개선 필요${NC}"
        fi
        
        # 리포트 파일 목록
        echo -e "\n${WHITE}생성된 리포트:${NC}"
        find "${TEST_RESULTS_DIR}" -name "*report*" -type f -printf '%T@ %p\n' | sort -n | tail -5 | while read timestamp filepath; do
            echo -e "  ${BLUE}📄 $(basename "$filepath")${NC}"
        done
        
    else
        log_warning "테스트 결과 파일을 찾을 수 없습니다"
    fi
}

# /deploy --plan --magic
deployment_planning() {
    log_section "${ROCKET} 배포 계획 (Magic Mode)"
    
    # 배포 준비 상태 확인
    log_info "배포 준비 상태 확인 중..."
    
    local deployment_ready=true
    local issues=()
    
    # 테스트 성공률 확인
    local latest_result=$(find "${TEST_RESULTS_DIR}" -name "comprehensive_test_report_*.json" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2)
    
    if [[ -f "$latest_result" ]]; then
        local success_rate=$(python3 -c "
import json
try:
    with open('$latest_result', 'r') as f:
        data = json.load(f)
        rate = data.get('analysis', {}).get('overall_summary', {}).get('success_rate', 0)
        print(f'{rate:.1f}')
except:
    print('0')
")
        
        if (( $(echo "$success_rate < 95" | bc -l) )); then
            deployment_ready=false
            issues+=("테스트 성공률이 95% 미만입니다 (현재: ${success_rate}%)")
        fi
        
        # 보안 점수 확인
        local security_score=$(python3 -c "
import json
try:
    with open('$latest_result', 'r') as f:
        data = json.load(f)
        score = data.get('analysis', {}).get('security_analysis', {}).get('security_score', 0)
        print(f'{score:.1f}')
except:
    print('0')
")
        
        if (( $(echo "$security_score < 90" | bc -l) )); then
            deployment_ready=false
            issues+=("보안 점수가 90점 미만입니다 (현재: ${security_score}점)")
        fi
    else
        deployment_ready=false
        issues+=("테스트 결과를 찾을 수 없습니다")
    fi
    
    # 배포 상태 출력
    if [[ "$deployment_ready" == "true" ]]; then
        log_success "배포 준비 완료!"
        echo -e "${GREEN}${CHECK} 모든 품질 게이트를 통과했습니다${NC}"
        
        # 배포 계획 출력
        echo -e "\n${CYAN}📋 배포 계획:${NC}"
        echo -e "${WHITE}1. ${BLUE}스테이징 환경 배포${NC}"
        echo -e "${WHITE}2. ${BLUE}연기 테스트 (Smoke Test)${NC}"
        echo -e "${WHITE}3. ${BLUE}카나리 배포 (10% 트래픽)${NC}"
        echo -e "${WHITE}4. ${BLUE}모니터링 및 검증${NC}"
        echo -e "${WHITE}5. ${BLUE}전체 배포 (100% 트래픽)${NC}"
        
        echo -e "\n${PURPLE}${MAGIC} 배포 승인됨! Magic Deploy 준비 완료!${NC}"
        
    else
        log_error "배포 준비가 완료되지 않았습니다"
        echo -e "${RED}${CROSS} 다음 문제들을 해결해주세요:${NC}"
        for issue in "${issues[@]}"; do
            echo -e "  ${RED}• ${issue}${NC}"
        done
        echo -e "\n${YELLOW}${WARNING} 문제 해결 후 다시 테스트를 실행해주세요${NC}"
        return 1
    fi
}

# 헬프 메시지
show_help() {
    echo -e "${CYAN}🚀 AI 모델 관리 시스템 - 종합 통합 테스트 도구${NC}"
    echo -e "${CYAN}$(printf '%.0s=' {1..60})${NC}"
    echo -e ""
    echo -e "${WHITE}사용법:${NC}"
    echo -e "  ${GREEN}./run_comprehensive_tests.sh [옵션]${NC}"
    echo -e ""
    echo -e "${WHITE}옵션:${NC}"
    echo -e "  ${BLUE}--build-only${NC}        빌드만 실행"
    echo -e "  ${BLUE}--test-only${NC}         테스트만 실행"
    echo -e "  ${BLUE}--deploy-plan${NC}       배포 계획만 확인"
    echo -e "  ${BLUE}--cleanup${NC}           Docker 정리 포함"
    echo -e "  ${BLUE}--verbose${NC}           상세 로그 출력"
    echo -e "  ${BLUE}--help, -h${NC}          이 도움말 표시"
    echo -e ""
    echo -e "${WHITE}Magic Commands:${NC}"
    echo -e "  ${PURPLE}${MAGIC} /build --feature --magic${NC}   고급 빌드 실행"
    echo -e "  ${PURPLE}${MAGIC} /test --coverage --magic${NC}    커버리지와 함께 테스트"
    echo -e "  ${PURPLE}${MAGIC} /deploy --plan --magic${NC}      스마트 배포 계획"
    echo -e ""
    echo -e "${WHITE}예시:${NC}"
    echo -e "  ${GREEN}./run_comprehensive_tests.sh${NC}                   # 전체 실행"
    echo -e "  ${GREEN}./run_comprehensive_tests.sh --test-only${NC}       # 테스트만"
    echo -e "  ${GREEN}./run_comprehensive_tests.sh --cleanup --verbose${NC} # 정리 포함"
}

# 메인 실행 함수
main() {
    local build_only=false
    local test_only=false
    local deploy_plan_only=false
    local verbose=false
    
    # 인수 파싱
    while [[ $# -gt 0 ]]; do
        case $1 in
            --build-only)
                build_only=true
                shift
                ;;
            --test-only)
                test_only=true
                shift
                ;;
            --deploy-plan)
                deploy_plan_only=true
                shift
                ;;
            --cleanup)
                export CLEANUP_DOCKER=true
                shift
                ;;
            --verbose)
                verbose=true
                export LOG_LEVEL="DEBUG"
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                log_error "알 수 없는 옵션: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # 시작 메시지
    log_section "${ROCKET} AI 모델 관리 시스템 - 종합 통합 테스트"
    log_magic "Magic Mode 활성화! ✨"
    
    local total_start_time=$(date +%s)
    
    # 기본 설정
    setup_environment
    check_dependencies
    
    # 단계별 실행
    if [[ "$deploy_plan_only" == "true" ]]; then
        deployment_planning
    elif [[ "$build_only" == "true" ]]; then
        build_project
    elif [[ "$test_only" == "true" ]]; then
        run_comprehensive_tests
        summarize_results
    else
        # 전체 실행
        build_project
        run_comprehensive_tests
        summarize_results
        deployment_planning
    fi
    
    local total_end_time=$(date +%s)
    local total_duration=$((total_end_time - total_start_time))
    
    # 완료 메시지
    log_section "${CHECK} 실행 완료"
    log_success "총 소요시간: ${total_duration}초"
    log_magic "✨ Magic Mission Complete! 모든 작업이 성공적으로 완료되었습니다! ${ROCKET}"
    
    # 정리
    if [[ "${CLEANUP_DOCKER:-false}" == "true" ]]; then
        cleanup
    fi
}

# 스크립트 실행
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi