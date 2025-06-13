#!/bin/bash

# Kibana 대시보드 자동 프로비저닝 스크립트
# 용도: Kibana 시작 시 모든 대시보드와 인덱스 패턴을 자동으로 생성

set -e

KIBANA_URL="${KIBANA_URL:-http://localhost:5601}"
DASHBOARD_DIR="${DASHBOARD_DIR:-/usr/share/kibana/dashboards}"
INDEX_PATTERN_DIR="${INDEX_PATTERN_DIR:-/usr/share/kibana/provisioning/index-patterns}"

echo "🚀 Kibana 대시보드 프로비저닝 시작..."

# Kibana 서비스 준비 대기
wait_for_kibana() {
    echo "⏳ Kibana 서비스 준비 대기 중..."
    for i in {1..30}; do
        if curl -s "$KIBANA_URL/api/status" > /dev/null 2>&1; then
            echo "✅ Kibana 서비스 준비 완료"
            return 0
        fi
        echo "  재시도 $i/30 (5초 후 재시도)..."
        sleep 5
    done
    echo "❌ Kibana 서비스 연결 실패"
    exit 1
}

# 인덱스 패턴 생성
create_index_patterns() {
    echo "📋 인덱스 패턴 생성 중..."
    
    local patterns=(
        "app-logs-*:애플리케이션 로그"
        "nginx-logs-*:Nginx 액세스 로그"
        "docker-logs-*:Docker 컨테이너 로그"
    )
    
    for pattern_info in "${patterns[@]}"; do
        IFS=':' read -r pattern title <<< "$pattern_info"
        
        echo "  📝 인덱스 패턴 생성: $pattern"
        
        curl -X POST "$KIBANA_URL/api/saved_objects/index-pattern" \
            -H "Content-Type: application/json" \
            -H "kbn-xsrf: true" \
            -d "{
                \"attributes\": {
                    \"title\": \"$pattern\",
                    \"timeFieldName\": \"@timestamp\",
                    \"fields\": \"[]\",
                    \"notExpandable\": false
                }
            }" > /dev/null 2>&1 || echo "    ⚠️  인덱스 패턴이 이미 존재하거나 생성 실패: $pattern"
    done
}

# 대시보드 가져오기
import_dashboards() {
    echo "📊 대시보드 가져오기 중..."
    
    local dashboards=(
        "overview-dashboard.json:전체 로그 현황"
        "error-analysis-dashboard.json:에러 분석"
        "performance-monitoring-dashboard.json:성능 모니터링"
        "security-events-dashboard.json:보안 이벤트"
    )
    
    for dashboard_info in "${dashboards[@]}"; do
        IFS=':' read -r filename description <<< "$dashboard_info"
        local filepath="$DASHBOARD_DIR/$filename"
        
        if [[ -f "$filepath" ]]; then
            echo "  📈 대시보드 가져오기: $description"
            
            curl -X POST "$KIBANA_URL/api/saved_objects/_import" \
                -H "kbn-xsrf: true" \
                -F "file=@$filepath" > /dev/null 2>&1 || echo "    ⚠️  대시보드 가져오기 실패: $filename"
        else
            echo "    ❌ 대시보드 파일 없음: $filepath"
        fi
    done
}

# 기본 설정 구성
configure_kibana_settings() {
    echo "⚙️  Kibana 기본 설정 구성 중..."
    
    # 기본 인덱스 패턴 설정
    curl -X POST "$KIBANA_URL/api/kibana/settings" \
        -H "Content-Type: application/json" \
        -H "kbn-xsrf: true" \
        -d '{
            "changes": {
                "defaultIndex": "app-logs-*",
                "defaultColumns": ["@timestamp", "log.level", "service.name", "message"],
                "dateFormat": "YYYY-MM-DD HH:mm:ss.SSS",
                "dateFormat:tz": "Asia/Seoul"
            }
        }' > /dev/null 2>&1 || echo "    ⚠️  기본 설정 구성 실패"
}

# 프로비저닝 상태 확인
verify_provisioning() {
    echo "🔍 프로비저닝 결과 확인 중..."
    
    # 인덱스 패턴 확인
    local index_patterns=$(curl -s "$KIBANA_URL/api/saved_objects/_find?type=index-pattern" | jq -r '.saved_objects[].attributes.title' 2>/dev/null || echo "")
    
    if [[ -n "$index_patterns" ]]; then
        echo "✅ 생성된 인덱스 패턴:"
        echo "$index_patterns" | sed 's/^/  - /'
    else
        echo "❌ 인덱스 패턴 생성 실패"
    fi
    
    # 대시보드 확인
    local dashboards=$(curl -s "$KIBANA_URL/api/saved_objects/_find?type=dashboard" | jq -r '.saved_objects[].attributes.title' 2>/dev/null || echo "")
    
    if [[ -n "$dashboards" ]]; then
        echo "✅ 생성된 대시보드:"
        echo "$dashboards" | sed 's/^/  - /'
    else
        echo "❌ 대시보드 생성 실패"
    fi
}

# 메인 실행 함수
main() {
    echo "==============================================="
    echo "🎯 Kibana 대시보드 자동 프로비저닝"
    echo "==============================================="
    
    wait_for_kibana
    sleep 10  # Kibana 완전 초기화 대기
    
    create_index_patterns
    sleep 5
    
    import_dashboards
    sleep 5
    
    configure_kibana_settings
    sleep 5
    
    verify_provisioning
    
    echo "==============================================="
    echo "✅ Kibana 대시보드 프로비저닝 완료!"
    echo "🌐 Kibana 접속: $KIBANA_URL"
    echo "==============================================="
}

# 스크립트 실행
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
