#!/bin/bash

# Enhanced Deployment Script for Online Evaluation System
# 환경별 배포 및 관리를 위한 향상된 스크립트

set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="/var/log/deployment.log"

# Default values
ENVIRONMENT=${1:-development}
COMMAND=${2:-deploy}
FORCE=${3:-false}

# Environment configurations
declare -A ENV_CONFIGS=(
    ["development"]="docker-compose.dev.yml:.env.dev"
    ["staging"]="docker-compose.staging.yml:.env.staging"
    ["production"]="docker-compose.prod.yml:.env.prod"
)

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    echo -e "${timestamp} [${level}] ${message}" | tee -a "$LOG_FILE"
}

# Colored output functions
info() { echo -e "${BLUE}[INFO]${NC} $1"; log "INFO" "$1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; log "SUCCESS" "$1"; }
warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; log "WARNING" "$1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; log "ERROR" "$1"; exit 1; }

# Show usage
show_usage() {
    cat << EOF
Enhanced Deployment Script for Online Evaluation System

Usage: $0 [ENVIRONMENT] [COMMAND] [OPTIONS]

Environments:
  development (default) - Development environment with hot reload
  staging              - Staging environment for testing
  production           - Production environment with security hardening

Commands:
  deploy     - Build and deploy all services (default)
  build      - Build Docker images only
  start      - Start existing containers
  stop       - Stop all containers
  restart    - Restart all containers
  logs       - Show container logs
  status     - Show deployment status
  backup     - Create backup (staging/production only)
  restore    - Restore from backup
  scale      - Scale services
  update     - Update to latest images
  rollback   - Rollback to previous version
  cleanup    - Clean up unused resources

Options:
  --force    - Force operation without confirmation
  --no-cache - Build without cache
  --verbose  - Enable verbose output

Examples:
  $0 development deploy
  $0 production deploy --force
  $0 staging logs --verbose
  $0 production backup
  $0 staging scale backend=3
EOF
}

# Validate environment
validate_environment() {
    local env="$1"
    
    if [[ ! "${ENV_CONFIGS[$env]:-}" ]]; then
        error "Invalid environment: $env. Valid options: ${!ENV_CONFIGS[*]}"
    fi
    
    # Parse environment configuration
    IFS=':' read -r COMPOSE_FILE ENV_FILE <<< "${ENV_CONFIGS[$env]}"
    
    # Check if files exist
    [[ -f "$PROJECT_ROOT/$COMPOSE_FILE" ]] || error "Compose file not found: $COMPOSE_FILE"
    [[ -f "$PROJECT_ROOT/$ENV_FILE" ]] || error "Environment file not found: $ENV_FILE"
    
    # Load environment variables
    set -a
    source "$PROJECT_ROOT/$ENV_FILE"
    set +a
    
    info "Environment: $env"
    info "Compose file: $COMPOSE_FILE"
    info "Environment file: $ENV_FILE"
}

# Check prerequisites
check_prerequisites() {
    local required_tools=("docker" "docker-compose" "curl" "jq")
    
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            error "$tool is not installed or not in PATH"
        fi
    done
    
    # Check Docker daemon
    if ! docker info &> /dev/null; then
        error "Docker daemon is not running"
    fi
    
    success "All prerequisites satisfied"
}

# Pre-deployment security checks
security_checks() {
    local env="$1"
    
    info "Performing security checks for $env environment..."
    
    if [[ "$env" == "production" ]]; then
        # Production-specific security checks
        if [[ "$JWT_SECRET_KEY" == *"CHANGE_THIS"* ]]; then
            error "JWT secret key must be changed for production"
        fi
        
        if [[ "$MONGO_ROOT_PASSWORD" == *"CHANGE_THIS"* ]]; then
            error "MongoDB password must be changed for production"
        fi
        
        if [[ "$REDIS_PASSWORD" == *"CHANGE_THIS"* ]]; then
            error "Redis password must be changed for production"
        fi
        
        # Check SSL certificates for production
        if [[ -n "${SSL_CERT_PATH:-}" ]] && [[ ! -f "$SSL_CERT_PATH" ]]; then
            warning "SSL certificate not found: $SSL_CERT_PATH"
        fi
    fi
    
    success "Security checks passed"
}

# Build Docker images
build_images() {
    local no_cache_flag=""
    
    if [[ "${NO_CACHE:-false}" == "true" ]]; then
        no_cache_flag="--no-cache"
    fi
    
    info "Building Docker images for $ENVIRONMENT environment..."
    
    docker-compose -f "$COMPOSE_FILE" build $no_cache_flag
    
    success "Docker images built successfully"
}

# Deploy services
deploy_services() {
    info "Deploying services for $ENVIRONMENT environment..."
    
    # Stop existing containers
    docker-compose -f "$COMPOSE_FILE" down --remove-orphans
    
    # Start services
    docker-compose -f "$COMPOSE_FILE" up -d
    
    # Wait for services to be ready
    wait_for_services
    
    success "Services deployed successfully"
}

# Wait for services to be ready
wait_for_services() {
    info "Waiting for services to be ready..."
    
    local max_attempts=30
    local attempt=0
    
    while [[ $attempt -lt $max_attempts ]]; do
        if check_services_health; then
            success "All services are ready"
            return 0
        fi
        
        attempt=$((attempt + 1))
        info "Waiting for services... (attempt $attempt/$max_attempts)"
        sleep 10
    done
    
    error "Services failed to become ready within timeout"
}

# Check services health
check_services_health() {
    local all_healthy=true
    
    # Check backend health
    if ! curl -f -s "http://localhost:8080/health" > /dev/null 2>&1; then
        all_healthy=false
    fi
    
    # Check frontend health
    if ! curl -f -s "http://localhost:3000" > /dev/null 2>&1; then
        all_healthy=false
    fi
    
    [[ "$all_healthy" == "true" ]]
}

# Show deployment status
show_status() {
    info "Deployment Status for $ENVIRONMENT environment:"
    
    echo "=== Container Status ==="
    docker-compose -f "$COMPOSE_FILE" ps
    
    echo -e "\n=== Service Health ==="
    local services=("backend:8080/health" "frontend:3000")
    
    for service in "${services[@]}"; do
        IFS=':' read -r name endpoint <<< "$service"
        if curl -f -s "http://localhost:$endpoint" > /dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} $name: Healthy"
        else
            echo -e "${RED}✗${NC} $name: Unhealthy"
        fi
    done
    
    echo -e "\n=== Resource Usage ==="
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"
}

# Show logs
show_logs() {
    local service="${1:-}"
    
    if [[ -n "$service" ]]; then
        docker-compose -f "$COMPOSE_FILE" logs -f "$service"
    else
        docker-compose -f "$COMPOSE_FILE" logs -f
    fi
}

# Scale services
scale_services() {
    local scale_args="$1"
    
    info "Scaling services: $scale_args"
    
    docker-compose -f "$COMPOSE_FILE" up -d --scale $scale_args
    
    success "Services scaled successfully"
}

# Backup data
backup_data() {
    if [[ "$ENVIRONMENT" == "development" ]]; then
        warning "Backup not recommended for development environment"
        return 0
    fi
    
    info "Creating backup for $ENVIRONMENT environment..."
    
    # Run backup script
    if [[ -f "$SCRIPT_DIR/backup-production.sh" ]]; then
        bash "$SCRIPT_DIR/backup-production.sh"
    else
        warning "Backup script not found"
    fi
}

# Update services
update_services() {
    info "Updating services to latest images..."
    
    # Pull latest images
    docker-compose -f "$COMPOSE_FILE" pull
    
    # Restart with new images
    docker-compose -f "$COMPOSE_FILE" up -d
    
    success "Services updated successfully"
}

# Cleanup resources
cleanup_resources() {
    info "Cleaning up unused Docker resources..."
    
    # Remove unused containers, networks, images
    docker system prune -f
    
    # Remove unused volumes (with confirmation)
    if [[ "$FORCE" == "true" ]]; then
        docker volume prune -f
    else
        docker volume prune
    fi
    
    success "Cleanup completed"
}

# Rollback deployment
rollback_deployment() {
    warning "Rollback functionality not yet implemented"
    warning "Please manually restore from backup if needed"
}

# Main function
main() {
    case "$COMMAND" in
        deploy)
            check_prerequisites
            validate_environment "$ENVIRONMENT"
            security_checks "$ENVIRONMENT"
            build_images
            deploy_services
            show_status
            ;;
        build)
            check_prerequisites
            validate_environment "$ENVIRONMENT"
            build_images
            ;;
        start)
            validate_environment "$ENVIRONMENT"
            docker-compose -f "$COMPOSE_FILE" up -d
            wait_for_services
            ;;
        stop)
            validate_environment "$ENVIRONMENT"
            docker-compose -f "$COMPOSE_FILE" down
            ;;
        restart)
            validate_environment "$ENVIRONMENT"
            docker-compose -f "$COMPOSE_FILE" restart
            wait_for_services
            ;;
        logs)
            validate_environment "$ENVIRONMENT"
            show_logs "${4:-}"
            ;;
        status)
            validate_environment "$ENVIRONMENT"
            show_status
            ;;
        backup)
            validate_environment "$ENVIRONMENT"
            backup_data
            ;;
        scale)
            validate_environment "$ENVIRONMENT"
            scale_services "${4:-backend=2}"
            ;;
        update)
            validate_environment "$ENVIRONMENT"
            update_services
            ;;
        cleanup)
            cleanup_resources
            ;;
        rollback)
            rollback_deployment
            ;;
        help|--help|-h)
            show_usage
            ;;
        *)
            error "Unknown command: $COMMAND. Use 'help' for usage information."
            ;;
    esac
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --force)
            FORCE=true
            shift
            ;;
        --no-cache)
            NO_CACHE=true
            shift
            ;;
        --verbose)
            set -x
            shift
            ;;
        *)
            break
            ;;
    esac
done

# Run main function
main "$@"
