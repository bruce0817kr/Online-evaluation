#!/bin/bash

# Elasticsearch Initialization Script
# This script sets up index templates and ILM policies for the ELK stack

set -e

# Configuration
ELASTICSEARCH_URL="${ELASTICSEARCH_URL:-http://localhost:9200}"
ELASTICSEARCH_USER="${ELASTICSEARCH_USER:-}"
ELASTICSEARCH_PASSWORD="${ELASTICSEARCH_PASSWORD:-}"
CONFIG_DIR="/usr/share/elasticsearch/config"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Wait for Elasticsearch to be ready
wait_for_elasticsearch() {
    log_info "Waiting for Elasticsearch to be ready..."
    
    local max_attempts=60
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$ELASTICSEARCH_URL/_cluster/health" >/dev/null 2>&1; then
            log_info "Elasticsearch is ready!"
            return 0
        fi
        
        log_warn "Attempt $attempt/$max_attempts: Elasticsearch not ready yet, waiting..."
        sleep 5
        ((attempt++))
    done
    
    log_error "Elasticsearch did not become ready after $max_attempts attempts"
    return 1
}

# Apply ILM policies
apply_ilm_policies() {
    log_info "Applying ILM policies..."
    
    local policies_dir="$CONFIG_DIR/ilm-policies"
    
    for policy_file in "$policies_dir"/*.json; do
        if [ -f "$policy_file" ]; then
            local policy_name=$(basename "$policy_file" .json)
            log_info "Applying ILM policy: $policy_name"
            
            if curl -s -X PUT "$ELASTICSEARCH_URL/_ilm/policy/$policy_name" \
                -H "Content-Type: application/json" \
                -d @"$policy_file" >/dev/null; then
                log_info "Successfully applied ILM policy: $policy_name"
            else
                log_error "Failed to apply ILM policy: $policy_name"
                return 1
            fi
        fi
    done
}

# Apply index templates
apply_index_templates() {
    log_info "Applying index templates..."
    
    local templates_dir="$CONFIG_DIR/index-templates"
    
    for template_file in "$templates_dir"/*.json; do
        if [ -f "$template_file" ]; then
            local template_name=$(basename "$template_file" -template.json)
            log_info "Applying index template: $template_name"
            
            if curl -s -X PUT "$ELASTICSEARCH_URL/_index_template/$template_name" \
                -H "Content-Type: application/json" \
                -d @"$template_file" >/dev/null; then
                log_info "Successfully applied index template: $template_name"
            else
                log_error "Failed to apply index template: $template_name"
                return 1
            fi
        fi
    done
}

# Create initial indices with aliases
create_initial_indices() {
    log_info "Creating initial indices with aliases..."
    
    # Create app-logs initial index
    local app_logs_index="app-logs-$(date +%Y.%m.%d)-000001"
    if curl -s -X PUT "$ELASTICSEARCH_URL/$app_logs_index" \
        -H "Content-Type: application/json" \
        -d '{
            "aliases": {
                "app-logs": {
                    "is_write_index": true
                }
            }
        }' >/dev/null; then
        log_info "Created initial app-logs index: $app_logs_index"
    else
        log_warn "Failed to create initial app-logs index (may already exist)"
    fi
    
    # Create nginx-logs initial index
    local nginx_logs_index="nginx-logs-$(date +%Y.%m.%d)-000001"
    if curl -s -X PUT "$ELASTICSEARCH_URL/$nginx_logs_index" \
        -H "Content-Type: application/json" \
        -d '{
            "aliases": {
                "nginx-logs": {
                    "is_write_index": true
                }
            }
        }' >/dev/null; then
        log_info "Created initial nginx-logs index: $nginx_logs_index"
    else
        log_warn "Failed to create initial nginx-logs index (may already exist)"
    fi
}

# Verify setup
verify_setup() {
    log_info "Verifying Elasticsearch setup..."
    
    # Check cluster health
    local health=$(curl -s "$ELASTICSEARCH_URL/_cluster/health" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
    if [ "$health" = "green" ] || [ "$health" = "yellow" ]; then
        log_info "Cluster health: $health"
    else
        log_error "Cluster health is not good: $health"
        return 1
    fi
    
    # Check ILM policies
    log_info "Checking ILM policies..."
    curl -s "$ELASTICSEARCH_URL/_ilm/policy" | grep -q '"app-logs-policy"' && log_info "✓ app-logs-policy found"
    curl -s "$ELASTICSEARCH_URL/_ilm/policy" | grep -q '"nginx-logs-policy"' && log_info "✓ nginx-logs-policy found"
    curl -s "$ELASTICSEARCH_URL/_ilm/policy" | grep -q '"docker-logs-policy"' && log_info "✓ docker-logs-policy found"
    
    # Check index templates
    log_info "Checking index templates..."
    curl -s "$ELASTICSEARCH_URL/_index_template" | grep -q '"app-logs"' && log_info "✓ app-logs template found"
    curl -s "$ELASTICSEARCH_URL/_index_template" | grep -q '"nginx-logs"' && log_info "✓ nginx-logs template found"
    curl -s "$ELASTICSEARCH_URL/_index_template" | grep -q '"docker-logs"' && log_info "✓ docker-logs template found"
    
    log_info "Elasticsearch setup verification completed successfully!"
}

# Main execution
main() {
    log_info "Starting Elasticsearch initialization..."
    
    # Wait for Elasticsearch to be ready
    if ! wait_for_elasticsearch; then
        log_error "Elasticsearch initialization failed - service not ready"
        exit 1
    fi
    
    # Apply configurations
    if apply_ilm_policies && apply_index_templates && create_initial_indices; then
        log_info "Elasticsearch configuration applied successfully"
    else
        log_error "Failed to apply Elasticsearch configuration"
        exit 1
    fi
    
    # Verify setup
    if verify_setup; then
        log_info "Elasticsearch initialization completed successfully!"
    else
        log_error "Elasticsearch setup verification failed"
        exit 1
    fi
}

# Run main function
main "$@"