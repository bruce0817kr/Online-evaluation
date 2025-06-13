#!/bin/bash

# Elasticsearch Health Check Script
# This script performs comprehensive health checks for Elasticsearch

set -e

# Configuration
ELASTICSEARCH_URL="${ELASTICSEARCH_URL:-http://localhost:9200}"
OUTPUT_FILE="${OUTPUT_FILE:-/tmp/elasticsearch-health.json}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

# Check if Elasticsearch is responsive
check_elasticsearch_responsive() {
    log_info "Checking if Elasticsearch is responsive..."
    
    if curl -s -f "$ELASTICSEARCH_URL" >/dev/null; then
        log_info "✓ Elasticsearch is responsive"
        return 0
    else
        log_error "✗ Elasticsearch is not responsive"
        return 1
    fi
}

# Check cluster health
check_cluster_health() {
    log_info "Checking cluster health..."
    
    local health_response=$(curl -s "$ELASTICSEARCH_URL/_cluster/health")
    local status=$(echo "$health_response" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
    local nodes=$(echo "$health_response" | grep -o '"number_of_nodes":[0-9]*' | cut -d':' -f2)
    local data_nodes=$(echo "$health_response" | grep -o '"number_of_data_nodes":[0-9]*' | cut -d':' -f2)
    
    log_info "Cluster status: $status"
    log_info "Number of nodes: $nodes"
    log_info "Number of data nodes: $data_nodes"
    
    case "$status" in
        "green")
            log_info "✓ Cluster health is GREEN - all is well"
            return 0
            ;;
        "yellow")
            log_warn "⚠ Cluster health is YELLOW - some replicas are missing"
            return 0
            ;;
        "red")
            log_error "✗ Cluster health is RED - some primary shards are missing"
            return 1
            ;;
        *)
            log_error "✗ Unknown cluster health status: $status"
            return 1
            ;;
    esac
}

# Check indices
check_indices() {
    log_info "Checking indices..."
    
    local indices_response=$(curl -s "$ELASTICSEARCH_URL/_cat/indices?v&h=index,health,status,docs.count,store.size")
    
    if [ -n "$indices_response" ]; then
        log_info "Indices status:"
        echo "$indices_response" | while IFS= read -r line; do
            log_debug "  $line"
        done
        log_info "✓ Indices information retrieved"
        return 0
    else
        log_error "✗ Failed to retrieve indices information"
        return 1
    fi
}

# Check ILM policies
check_ilm_policies() {
    log_info "Checking ILM policies..."
    
    local expected_policies=("app-logs-policy" "nginx-logs-policy" "docker-logs-policy")
    local policies_response=$(curl -s "$ELASTICSEARCH_URL/_ilm/policy")
    
    for policy in "${expected_policies[@]}"; do
        if echo "$policies_response" | grep -q "\"$policy\""; then
            log_info "✓ ILM policy found: $policy"
        else
            log_warn "⚠ ILM policy missing: $policy"
        fi
    done
}

# Check index templates
check_index_templates() {
    log_info "Checking index templates..."
    
    local expected_templates=("app-logs" "nginx-logs" "docker-logs")
    local templates_response=$(curl -s "$ELASTICSEARCH_URL/_index_template")
    
    for template in "${expected_templates[@]}"; do
        if echo "$templates_response" | grep -q "\"$template\""; then
            log_info "✓ Index template found: $template"
        else
            log_warn "⚠ Index template missing: $template"
        fi
    done
}

# Check node stats
check_node_stats() {
    log_info "Checking node statistics..."
    
    local stats_response=$(curl -s "$ELASTICSEARCH_URL/_nodes/stats")
    local heap_used=$(echo "$stats_response" | grep -o '"heap_used_in_bytes":[0-9]*' | head -1 | cut -d':' -f2)
    local heap_max=$(echo "$stats_response" | grep -o '"heap_max_in_bytes":[0-9]*' | head -1 | cut -d':' -f2)
    
    if [ -n "$heap_used" ] && [ -n "$heap_max" ]; then
        local heap_usage_percent=$((heap_used * 100 / heap_max))
        log_info "JVM heap usage: ${heap_usage_percent}%"
        
        if [ $heap_usage_percent -lt 80 ]; then
            log_info "✓ Heap usage is healthy"
        elif [ $heap_usage_percent -lt 90 ]; then
            log_warn "⚠ Heap usage is high (${heap_usage_percent}%)"
        else
            log_error "✗ Heap usage is critical (${heap_usage_percent}%)"
        fi
    else
        log_warn "⚠ Could not retrieve heap usage information"
    fi
}

# Generate comprehensive health report
generate_health_report() {
    log_info "Generating comprehensive health report..."
    
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local cluster_health=$(curl -s "$ELASTICSEARCH_URL/_cluster/health")
    local node_stats=$(curl -s "$ELASTICSEARCH_URL/_nodes/stats")
    local indices_stats=$(curl -s "$ELASTICSEARCH_URL/_stats")
    
    cat > "$OUTPUT_FILE" << EOF
{
    "timestamp": "$timestamp",
    "elasticsearch_url": "$ELASTICSEARCH_URL",
    "cluster_health": $cluster_health,
    "node_stats": $node_stats,
    "indices_stats": $indices_stats,
    "health_check": {
        "responsive": $(check_elasticsearch_responsive && echo "true" || echo "false"),
        "cluster_status": "$(echo "$cluster_health" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)",
        "timestamp": "$timestamp"
    }
}
EOF
    
    log_info "Health report saved to: $OUTPUT_FILE"
}

# Main health check function
main() {
    log_info "Starting comprehensive Elasticsearch health check..."
    
    local exit_code=0
    
    # Run all health checks
    check_elasticsearch_responsive || exit_code=1
    check_cluster_health || exit_code=1
    check_indices || exit_code=1
    check_ilm_policies
    check_index_templates
    check_node_stats
    
    # Generate report
    generate_health_report
    
    if [ $exit_code -eq 0 ]; then
        log_info "All health checks passed!"
    else
        log_error "Some health checks failed. Please review the output above."
    fi
    
    return $exit_code
}

# Run main function
main "$@"