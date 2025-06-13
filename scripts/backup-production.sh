#!/bin/bash

# Production Backup Script for Online Evaluation System
# 프로덕션 환경용 자동 백업 스크립트

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="/backup"
LOG_FILE="/var/log/backup.log"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}
S3_BUCKET=${BACKUP_S3_BUCKET:-""}

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Error handling
error_exit() {
    log "ERROR: $1"
    exit 1
}

# Check dependencies
check_dependencies() {
    local deps=("mongodump" "aws" "gzip" "tar")
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            error_exit "$dep is not installed"
        fi
    done
}

# Create backup directory
create_backup_dir() {
    local backup_path="$BACKUP_DIR/$DATE"
    mkdir -p "$backup_path"
    echo "$backup_path"
}

# MongoDB backup
backup_mongodb() {
    local backup_path="$1"
    log "Starting MongoDB backup..."
    
    mongodump \
        --uri="$MONGO_URL" \
        --out="$backup_path/mongodb" \
        --gzip \
        --quiet
    
    if [ $? -eq 0 ]; then
        log "MongoDB backup completed successfully"
    else
        error_exit "MongoDB backup failed"
    fi
}

# Redis backup
backup_redis() {
    local backup_path="$1"
    log "Starting Redis backup..."
    
    # Copy Redis RDB file
    docker exec online-evaluation-redis-prod redis-cli --rdb "$backup_path/redis_dump.rdb" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        log "Redis backup completed successfully"
    else
        error_exit "Redis backup failed"
    fi
}

# Application data backup
backup_app_data() {
    local backup_path="$1"
    log "Starting application data backup..."
    
    # Backup uploads directory
    if [ -d "/var/lib/online-evaluation/uploads" ]; then
        tar -czf "$backup_path/uploads.tar.gz" -C "/var/lib/online-evaluation" uploads
        log "Uploads backup completed"
    fi
    
    # Backup logs (last 7 days)
    if [ -d "/var/log/online-evaluation" ]; then
        find /var/log/online-evaluation -name "*.log" -mtime -7 -exec tar -czf "$backup_path/logs.tar.gz" {} +
        log "Logs backup completed"
    fi
}

# Configuration backup
backup_config() {
    local backup_path="$1"
    log "Starting configuration backup..."
    
    # Backup Docker configurations
    mkdir -p "$backup_path/config"
    cp -r "$SCRIPT_DIR/../docker-compose.prod.yml" "$backup_path/config/"
    cp -r "$SCRIPT_DIR/../nginx" "$backup_path/config/" 2>/dev/null || true
    cp -r "$SCRIPT_DIR/../ssl" "$backup_path/config/" 2>/dev/null || true
    
    log "Configuration backup completed"
}

# Create backup metadata
create_metadata() {
    local backup_path="$1"
    local metadata_file="$backup_path/backup_metadata.json"
    
    cat > "$metadata_file" << EOF
{
    "backup_date": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "backup_type": "full",
    "environment": "production",
    "version": "2.0.0",
    "components": {
        "mongodb": true,
        "redis": true,
        "uploads": true,
        "logs": true,
        "config": true
    },
    "retention_days": $RETENTION_DAYS,
    "s3_upload": $([ -n "$S3_BUCKET" ] && echo "true" || echo "false")
}
EOF
    
    log "Backup metadata created"
}

# Upload to S3 (optional)
upload_to_s3() {
    local backup_path="$1"
    
    if [ -z "$S3_BUCKET" ]; then
        log "S3 bucket not configured, skipping upload"
        return 0
    fi
    
    log "Starting S3 upload..."
    
    # Create compressed archive
    local archive_name="backup_$DATE.tar.gz"
    tar -czf "/tmp/$archive_name" -C "$BACKUP_DIR" "$DATE"
    
    # Upload to S3
    aws s3 cp "/tmp/$archive_name" "s3://$S3_BUCKET/backups/$archive_name" \
        --storage-class STANDARD_IA
    
    if [ $? -eq 0 ]; then
        log "S3 upload completed successfully"
        rm -f "/tmp/$archive_name"
    else
        error_exit "S3 upload failed"
    fi
}

# Clean old backups
cleanup_old_backups() {
    log "Cleaning up old backups..."
    
    # Local cleanup
    find "$BACKUP_DIR" -maxdepth 1 -type d -name "20*" -mtime +$RETENTION_DAYS -exec rm -rf {} \;
    
    # S3 cleanup (if configured)
    if [ -n "$S3_BUCKET" ]; then
        aws s3 ls "s3://$S3_BUCKET/backups/" --recursive | \
        awk -v retention="$RETENTION_DAYS" '
        BEGIN { 
            now = systime(); 
            cutoff = now - (retention * 24 * 60 * 60); 
        }
        {
            date_str = $1 " " $2;
            if (mktime(gensub(/[-:]/, " ", "g", date_str)) < cutoff) {
                print $4;
            }
        }' | \
        while read -r file; do
            aws s3 rm "s3://$S3_BUCKET/$file"
            log "Deleted old S3 backup: $file"
        done
    fi
    
    log "Cleanup completed"
}

# Health check before backup
health_check() {
    log "Performing health check..."
    
    # Check MongoDB
    if ! docker exec online-evaluation-mongodb-prod mongosh --eval "db.adminCommand('ping')" &>/dev/null; then
        error_exit "MongoDB health check failed"
    fi
    
    # Check Redis
    if ! docker exec online-evaluation-redis-prod redis-cli --pass "$REDIS_PASSWORD" ping &>/dev/null; then
        error_exit "Redis health check failed"
    fi
    
    log "Health check passed"
}

# Send notification (optional)
send_notification() {
    local status="$1"
    local message="$2"
    
    # Webhook notification (예: Slack, Discord, Teams)
    if [ -n "${WEBHOOK_URL:-}" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"Backup $status: $message\"}" \
            "$WEBHOOK_URL" &>/dev/null || true
    fi
    
    # Email notification (예: AWS SES)
    if [ -n "${NOTIFICATION_EMAIL:-}" ]; then
        aws ses send-email \
            --from "backup@your-domain.com" \
            --to "$NOTIFICATION_EMAIL" \
            --message "Subject={Data=\"Backup $status\"},Body={Text={Data=\"$message\"}}" &>/dev/null || true
    fi
}

# Main backup function
main() {
    log "Starting backup process..."
    
    # Pre-backup checks
    check_dependencies
    health_check
    
    # Create backup
    local backup_path
    backup_path=$(create_backup_dir)
    
    # Perform backups
    backup_mongodb "$backup_path"
    backup_redis "$backup_path"
    backup_app_data "$backup_path"
    backup_config "$backup_path"
    create_metadata "$backup_path"
    
    # Upload and cleanup
    upload_to_s3 "$backup_path"
    cleanup_old_backups
    
    # Calculate backup size
    local backup_size
    backup_size=$(du -sh "$backup_path" | cut -f1)
    
    log "Backup completed successfully. Size: $backup_size"
    send_notification "SUCCESS" "Backup completed successfully. Size: $backup_size"
}

# Error handling
trap 'send_notification "FAILED" "Backup failed at line $LINENO"' ERR

# Run main function
main "$@"
