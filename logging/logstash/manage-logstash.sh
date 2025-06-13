#!/bin/bash

# Logstash Pipeline Management Script
# This script helps manage Logstash pipelines, monitor performance, and troubleshoot issues

set -e

# Configuration
LOGSTASH_URL="${LOGSTASH_URL:-http://localhost:9600}"
LOGSTASH_CONFIG_DIR="${LOGSTASH_CONFIG_DIR:-/usr/share/logstash/config}"
LOGSTASH_LOGS_DIR="${LOGSTASH_LOGS_DIR:-/usr/share/logstash/logs}"

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

# Check if Logstash is responsive
check_logstash_health() {
    log_info "Checking Logstash health..."
    
    if curl -s -f "$LOGSTASH_URL" >/dev/null; then
        log_info "✓ Logstash is responsive"
        return 0
    else
        log_error "✗ Logstash is not responsive"
        return 1
    fi
}

# Get Logstash node info
get_node_info() {
    log_info "Getting Logstash node information..."
    
    local node_info=$(curl -s "$LOGSTASH_URL")
    if [ $? -eq 0 ]; then
        echo "$node_info" | jq '.' 2>/dev/null || echo "$node_info"
        return 0
    else
        log_error "Failed to retrieve node information"
        return 1
    fi
}

# Get pipeline stats
get_pipeline_stats() {
    log_info "Getting pipeline statistics..."
    
    local stats_response=$(curl -s "$LOGSTASH_URL/_node/stats/pipelines")
    if [ $? -eq 0 ]; then
        echo "$stats_response" | jq '.' 2>/dev/null || echo "$stats_response"
        return 0
    else
        log_error "Failed to retrieve pipeline statistics"
        return 1
    fi
}

# Get hot threads (for performance debugging)
get_hot_threads() {
    log_info "Getting hot threads information..."
    
    local hot_threads=$(curl -s "$LOGSTASH_URL/_node/hot_threads")
    if [ $? -eq 0 ]; then
        echo "$hot_threads"
        return 0
    else
        log_error "Failed to retrieve hot threads information"
        return 1
    fi
}

# Monitor pipeline performance
monitor_performance() {
    log_info "Monitoring pipeline performance..."
    
    local duration=${1:-60}  # Default 60 seconds
    local interval=5
    local count=$((duration / interval))
    
    log_info "Monitoring for $duration seconds (sampling every $interval seconds)..."
    
    for i in $(seq 1 $count); do
        local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
        echo "=== $timestamp (Sample $i/$count) ==="
        
        # Get pipeline stats
        local stats=$(curl -s "$LOGSTASH_URL/_node/stats/pipelines")
        if [ $? -eq 0 ]; then
            # Extract key metrics
            local events_in=$(echo "$stats" | jq -r '.pipelines.main.events.in // 0')
            local events_out=$(echo "$stats" | jq -r '.pipelines.main.events.out // 0')
            local events_filtered=$(echo "$stats" | jq -r '.pipelines.main.events.filtered // 0')
            local queue_events=$(echo "$stats" | jq -r '.pipelines.main.queue.events // 0')
            
            echo "Events In: $events_in"
            echo "Events Out: $events_out"
            echo "Events Filtered: $events_filtered"
            echo "Queue Events: $queue_events"
            echo "---"
        else
            log_warn "Failed to get stats for sample $i"
        fi
        
        sleep $interval
    done
    
    log_info "Performance monitoring completed"
}

# Reload pipeline configuration
reload_pipeline() {
    log_info "Reloading pipeline configuration..."
    
    local reload_response=$(curl -s -X PUT "$LOGSTASH_URL/_reload")
    if [ $? -eq 0 ]; then
        echo "$reload_response" | jq '.' 2>/dev/null || echo "$reload_response"
        log_info "Pipeline reload request sent"
        return 0
    else
        log_error "Failed to reload pipeline"
        return 1
    fi
}

# Test pipeline configuration
test_configuration() {
    log_info "Testing pipeline configuration..."
    
    if [ ! -f "$LOGSTASH_CONFIG_DIR/logstash.yml" ]; then
        log_error "Logstash configuration file not found: $LOGSTASH_CONFIG_DIR/logstash.yml"
        return 1
    fi
    
    # Test configuration syntax
    if logstash --config.test_and_exit --path.config="$LOGSTASH_CONFIG_DIR/pipeline"; then
        log_info "✓ Pipeline configuration is valid"
        return 0
    else
        log_error "✗ Pipeline configuration has errors"
        return 1
    fi
}

# Show pipeline configuration
show_configuration() {
    log_info "Current pipeline configuration:"
    
    echo "=== Main Pipeline ==="
    if [ -f "$LOGSTASH_CONFIG_DIR/pipeline/logstash.conf" ]; then
        head -20 "$LOGSTASH_CONFIG_DIR/pipeline/logstash.conf"
        echo "... (truncated)"
    else
        log_warn "Main pipeline configuration not found"
    fi
    
    echo ""
    echo "=== Logstash Settings ==="
    if [ -f "$LOGSTASH_CONFIG_DIR/logstash.yml" ]; then
        grep -v '^#' "$LOGSTASH_CONFIG_DIR/logstash.yml" | grep -v '^$' | head -15
        echo "... (truncated)"
    else
        log_warn "Logstash settings file not found"
    fi
}

# Check log files for errors
check_logs() {
    log_info "Checking Logstash logs for errors..."
    
    local log_file="$LOGSTASH_LOGS_DIR/logstash-plain.log"
    if [ -f "$log_file" ]; then
        log_info "Recent errors from $log_file:"
        tail -100 "$log_file" | grep -i "error\|exception\|failed" | tail -10
    else
        log_warn "Log file not found: $log_file"
    fi
    
    # Check for slow logs
    local slow_log="$LOGSTASH_LOGS_DIR/logstash-slowlog-plain.log"
    if [ -f "$slow_log" ]; then
        log_info "Recent slow operations from $slow_log:"
        tail -20 "$slow_log"
    else
        log_debug "Slow log file not found: $slow_log"
    fi
}

# Generate health report
generate_health_report() {
    log_info "Generating comprehensive health report..."
    
    local report_file="${1:-/tmp/logstash-health-$(date +%Y%m%d_%H%M%S).json}"
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    
    # Collect all health data
    local node_info=$(curl -s "$LOGSTASH_URL" 2>/dev/null || echo "{}")
    local pipeline_stats=$(curl -s "$LOGSTASH_URL/_node/stats/pipelines" 2>/dev/null || echo "{}")
    local jvm_stats=$(curl -s "$LOGSTASH_URL/_node/stats/jvm" 2>/dev/null || echo "{}")
    local process_stats=$(curl -s "$LOGSTASH_URL/_node/stats/process" 2>/dev/null || echo "{}")
    
    # Create comprehensive report
    cat > "$report_file" << EOF
{
    "timestamp": "$timestamp",
    "logstash_url": "$LOGSTASH_URL",
    "health_check": {
        "responsive": $(check_logstash_health >/dev/null 2>&1 && echo "true" || echo "false"),
        "timestamp": "$timestamp"
    },
    "node_info": $node_info,
    "pipeline_stats": $pipeline_stats,
    "jvm_stats": $jvm_stats,
    "process_stats": $process_stats
}
EOF
    
    log_info "Health report saved to: $report_file"
    
    # Display summary
    log_info "Health Summary:"
    if echo "$pipeline_stats" | jq -e '.pipelines.main' >/dev/null 2>&1; then
        local events_in=$(echo "$pipeline_stats" | jq -r '.pipelines.main.events.in // 0')
        local events_out=$(echo "$pipeline_stats" | jq -r '.pipelines.main.events.out // 0')
        local queue_events=$(echo "$pipeline_stats" | jq -r '.pipelines.main.queue.events // 0')
        
        echo "  Events processed: $events_in"
        echo "  Events output: $events_out"
        echo "  Queue depth: $queue_events"
    fi
}

# Main help function
show_help() {
    echo "Logstash Pipeline Management Script"
    echo ""
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  health                 - Check Logstash health status"
    echo "  info                   - Get node information"
    echo "  stats                  - Get pipeline statistics"
    echo "  hot-threads           - Get hot threads for debugging"
    echo "  monitor [duration]    - Monitor performance for specified seconds (default: 60)"
    echo "  reload                - Reload pipeline configuration"
    echo "  test                  - Test configuration syntax"
    echo "  config                - Show current configuration"
    echo "  logs                  - Check logs for errors"
    echo "  report [file]         - Generate comprehensive health report"
    echo "  help                  - Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  LOGSTASH_URL          - Logstash API URL (default: http://localhost:9600)"
    echo "  LOGSTASH_CONFIG_DIR   - Configuration directory (default: /usr/share/logstash/config)"
    echo "  LOGSTASH_LOGS_DIR     - Logs directory (default: /usr/share/logstash/logs)"
}

# Main function
main() {
    case "${1:-help}" in
        "health")
            check_logstash_health
            ;;
        "info")
            get_node_info
            ;;
        "stats")
            get_pipeline_stats
            ;;
        "hot-threads")
            get_hot_threads
            ;;
        "monitor")
            monitor_performance "${2:-60}"
            ;;
        "reload")
            reload_pipeline
            ;;
        "test")
            test_configuration
            ;;
        "config")
            show_configuration
            ;;
        "logs")
            check_logs
            ;;
        "report")
            generate_health_report "$2"
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# Run main function
main "$@"
