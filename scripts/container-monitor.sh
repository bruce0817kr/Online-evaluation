#!/bin/bash

# Container Health Monitoring Script
# 컨테이너 상태 모니터링 및 자동 복구 스크립트

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/var/log/container-monitor.log"
HEALTH_CHECK_INTERVAL=${HEALTH_CHECK_INTERVAL:-60}
MAX_RESTART_ATTEMPTS=${MAX_RESTART_ATTEMPTS:-3}
NOTIFICATION_WEBHOOK=${NOTIFICATION_WEBHOOK:-""}

# Container configurations
declare -A CONTAINERS=(
    ["online-evaluation-backend-prod"]="http://localhost:8080/health"
    ["online-evaluation-frontend-prod"]="http://localhost:80/health"
    ["online-evaluation-mongodb-prod"]="mongodb"
    ["online-evaluation-redis-prod"]="redis"
    ["online-evaluation-nginx-prod"]="http://localhost:80/health"
)

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Send notification
send_notification() {
    local message="$1"
    local severity="${2:-INFO}"
    
    log "$severity: $message"
    
    if [ -n "$NOTIFICATION_WEBHOOK" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"[$severity] Container Monitor: $message\"}" \
            "$NOTIFICATION_WEBHOOK" &>/dev/null || true
    fi
}

# Check container status
check_container_status() {
    local container="$1"
    
    # Check if container is running
    if ! docker ps --format "table {{.Names}}" | grep -q "^$container$"; then
        return 1
    fi
    
    # Check container health status
    local health_status
    health_status=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo "no-health-check")
    
    if [ "$health_status" = "healthy" ] || [ "$health_status" = "no-health-check" ]; then
        return 0
    else
        return 1
    fi
}

# Perform application-specific health check
app_health_check() {
    local container="$1"
    local endpoint="$2"
    
    case "$endpoint" in
        http*)
            # HTTP health check
            if curl -f -s --max-time 10 "$endpoint" > /dev/null 2>&1; then
                return 0
            else
                return 1
            fi
            ;;
        mongodb)
            # MongoDB health check
            if docker exec "$container" mongosh --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
                return 0
            else
                return 1
            fi
            ;;
        redis)
            # Redis health check
            if docker exec "$container" redis-cli --pass "$REDIS_PASSWORD" ping > /dev/null 2>&1; then
                return 0
            else
                return 1
            fi
            ;;
        *)
            # Generic container check
            return 0
            ;;
    esac
}

# Restart container
restart_container() {
    local container="$1"
    local attempt="$2"
    
    log "Attempting to restart $container (attempt $attempt)"
    
    # Graceful restart
    docker restart "$container"
    
    # Wait for container to be ready
    sleep 30
    
    # Verify restart success
    if check_container_status "$container"; then
        send_notification "Successfully restarted $container" "INFO"
        return 0
    else
        send_notification "Failed to restart $container (attempt $attempt)" "ERROR"
        return 1
    fi
}

# Get container metrics
get_container_metrics() {
    local container="$1"
    
    if ! docker ps --format "table {{.Names}}" | grep -q "^$container$"; then
        echo "Container not running"
        return 1
    fi
    
    # Get resource usage
    local stats
    stats=$(docker stats "$container" --no-stream --format "table {{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" | tail -n 1)
    
    echo "$stats"
}

# Check system resources
check_system_resources() {
    local cpu_usage
    local memory_usage
    local disk_usage
    
    # CPU usage
    cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')
    
    # Memory usage
    memory_usage=$(free | grep Mem | awk '{printf("%.1f"), ($3/$2) * 100.0}')
    
    # Disk usage
    disk_usage=$(df -h / | awk 'NR==2{printf("%s"), $5}' | sed 's/%//')
    
    # Check thresholds
    if (( $(echo "$cpu_usage > 90" | bc -l) )); then
        send_notification "High CPU usage: ${cpu_usage}%" "WARNING"
    fi
    
    if (( $(echo "$memory_usage > 90" | bc -l) )); then
        send_notification "High memory usage: ${memory_usage}%" "WARNING"
    fi
    
    if (( disk_usage > 90 )); then
        send_notification "High disk usage: ${disk_usage}%" "WARNING"
    fi
}

# Monitor single container
monitor_container() {
    local container="$1"
    local endpoint="$2"
    local restart_count=0
    
    while [ $restart_count -lt $MAX_RESTART_ATTEMPTS ]; do
        if check_container_status "$container" && app_health_check "$container" "$endpoint"; then
            # Container is healthy
            return 0
        else
            # Container is unhealthy
            send_notification "$container is unhealthy" "WARNING"
            
            # Get container logs for debugging
            docker logs --tail 50 "$container" >> "/var/log/${container}_error.log" 2>&1
            
            # Attempt restart
            if restart_container "$container" $((restart_count + 1)); then
                return 0
            else
                restart_count=$((restart_count + 1))
                sleep 60
            fi
        fi
    done
    
    # Max restart attempts reached
    send_notification "$container failed after $MAX_RESTART_ATTEMPTS restart attempts" "CRITICAL"
    return 1
}

# Generate health report
generate_health_report() {
    local report_file="/var/log/health_report_$(date +%Y%m%d_%H%M%S).json"
    
    cat > "$report_file" << EOF
{
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "environment": "production",
    "containers": {
EOF
    
    local first=true
    for container in "${!CONTAINERS[@]}"; do
        if [ "$first" = false ]; then
            echo "," >> "$report_file"
        fi
        first=false
        
        local status="unknown"
        local metrics="N/A"
        
        if check_container_status "$container"; then
            status="healthy"
            metrics=$(get_container_metrics "$container" || echo "N/A")
        else
            status="unhealthy"
        fi
        
        cat >> "$report_file" << EOF
        "$container": {
            "status": "$status",
            "metrics": "$metrics",
            "endpoint": "${CONTAINERS[$container]}"
        }
EOF
    done
    
    cat >> "$report_file" << EOF
    },
    "system": {
        "cpu_usage": "$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')%",
        "memory_usage": "$(free | grep Mem | awk '{printf("%.1f"), ($3/$2) * 100.0}')%",
        "disk_usage": "$(df -h / | awk 'NR==2{printf("%s"), $5}')"
    }
}
EOF
    
    log "Health report generated: $report_file"
}

# Main monitoring loop
main() {
    log "Starting container health monitoring..."
    
    while true; do
        local all_healthy=true
        
        # Check each container
        for container in "${!CONTAINERS[@]}"; do
            if ! monitor_container "$container" "${CONTAINERS[$container]}"; then
                all_healthy=false
            fi
        done
        
        # Check system resources
        check_system_resources
        
        # Generate periodic health reports
        local current_minute
        current_minute=$(date +%M)
        if [ "$current_minute" = "00" ]; then
            generate_health_report
        fi
        
        # Log overall status
        if [ "$all_healthy" = true ]; then
            log "All containers are healthy"
        else
            log "Some containers are unhealthy"
        fi
        
        # Wait before next check
        sleep "$HEALTH_CHECK_INTERVAL"
    done
}

# Signal handlers
cleanup() {
    log "Shutting down container monitor..."
    exit 0
}

trap cleanup SIGTERM SIGINT

# Run main function
main "$@"
