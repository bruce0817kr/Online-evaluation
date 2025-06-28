#!/bin/bash

# 🚀 AI 모델 관리 시스템 - 인프라 프로비저닝 실행 스크립트
# 백엔드 페르소나 중심의 안전하고 체계적인 인프라 구축

set -euo pipefail

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
CHECK="✅"
CROSS="❌"
WARNING="⚠️"
INFO="ℹ️"
GEAR="⚙️"
SHIELD="🛡️"
CHART="📊"
CLOUD="☁️"

# 환경 변수 설정
ENVIRONMENT="${ENVIRONMENT:-staging}"
PROJECT_NAME="${PROJECT_NAME:-ai-model-mgmt}"
AWS_REGION="${AWS_REGION:-ap-northeast-2}"
TERRAFORM_STATE_BUCKET="ai-model-mgmt-terraform-state"
LOG_FILE="/tmp/infrastructure_provisioning_$(date +%Y%m%d_%H%M%S).log"

# 로깅 함수
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case $level in
        "INFO")
            echo -e "${BLUE}${INFO} ${WHITE}[${timestamp}] $message${NC}" | tee -a "$LOG_FILE"
            ;;
        "SUCCESS")
            echo -e "${GREEN}${CHECK} ${WHITE}[${timestamp}] $message${NC}" | tee -a "$LOG_FILE"
            ;;
        "ERROR")
            echo -e "${RED}${CROSS} ${WHITE}[${timestamp}] $message${NC}" | tee -a "$LOG_FILE"
            ;;
        "WARNING")
            echo -e "${YELLOW}${WARNING} ${WHITE}[${timestamp}] $message${NC}" | tee -a "$LOG_FILE"
            ;;
        "HEADER")
            echo -e "\n${CYAN}$message${NC}" | tee -a "$LOG_FILE"
            echo -e "${CYAN}$(printf '%.0s=' {1..60})${NC}" | tee -a "$LOG_FILE"
            ;;
    esac
}

# 시작 메시지
log "HEADER" "${ROCKET} AI 모델 관리 시스템 인프라 프로비저닝"
log "INFO" "환경: $ENVIRONMENT"
log "INFO" "프로젝트: $PROJECT_NAME"
log "INFO" "AWS 리전: $AWS_REGION"

# 사전 요구사항 검사
check_prerequisites() {
    log "HEADER" "${GEAR} 사전 요구사항 검사"
    
    # 필수 도구 확인
    local required_tools=("terraform" "aws" "jq")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log "ERROR" "$tool이 설치되지 않았습니다"
            exit 1
        fi
        log "SUCCESS" "$tool 확인됨"
    done
    
    # AWS 인증 확인
    if ! aws sts get-caller-identity &> /dev/null; then
        log "ERROR" "AWS 인증이 필요합니다"
        exit 1
    fi
    log "SUCCESS" "AWS 인증 확인됨"
    
    # Terraform 버전 확인
    terraform_version=$(terraform version -json | jq -r .terraform_version)
    log "INFO" "Terraform 버전: $terraform_version"
    
    # AWS 계정 정보 확인
    aws_account=$(aws sts get-caller-identity --query Account --output text)
    aws_user=$(aws sts get-caller-identity --query Arn --output text)
    log "INFO" "AWS 계정: $aws_account"
    log "INFO" "AWS 사용자: $aws_user"
}

# Terraform 백엔드 초기화
initialize_terraform_backend() {
    log "HEADER" "${CLOUD} Terraform 백엔드 초기화"
    
    # S3 버킷 존재 확인 및 생성
    if ! aws s3api head-bucket --bucket "$TERRAFORM_STATE_BUCKET" 2>/dev/null; then
        log "INFO" "Terraform 상태 버킷 생성 중: $TERRAFORM_STATE_BUCKET"
        aws s3api create-bucket \
            --bucket "$TERRAFORM_STATE_BUCKET" \
            --region "$AWS_REGION" \
            --create-bucket-configuration LocationConstraint="$AWS_REGION"
        
        # 버킷 버전 관리 활성화
        aws s3api put-bucket-versioning \
            --bucket "$TERRAFORM_STATE_BUCKET" \
            --versioning-configuration Status=Enabled
        
        # 버킷 암호화 설정
        aws s3api put-bucket-encryption \
            --bucket "$TERRAFORM_STATE_BUCKET" \
            --server-side-encryption-configuration '{
                "Rules": [{
                    "ApplyServerSideEncryptionByDefault": {
                        "SSEAlgorithm": "AES256"
                    }
                }]
            }'
        
        log "SUCCESS" "Terraform 상태 버킷 생성 완료"
    else
        log "SUCCESS" "Terraform 상태 버킷 확인됨"
    fi
    
    # DynamoDB 테이블 생성 (상태 잠금)
    local dynamodb_table="${PROJECT_NAME}-terraform-locks"
    if ! aws dynamodb describe-table --table-name "$dynamodb_table" &>/dev/null; then
        log "INFO" "DynamoDB 상태 잠금 테이블 생성 중: $dynamodb_table"
        aws dynamodb create-table \
            --table-name "$dynamodb_table" \
            --attribute-definitions AttributeName=LockID,AttributeType=S \
            --key-schema AttributeName=LockID,KeyType=HASH \
            --provisioned-throughput ReadCapacityUnits=1,WriteCapacityUnits=1
        
        # 테이블 생성 완료 대기
        aws dynamodb wait table-exists --table-name "$dynamodb_table"
        log "SUCCESS" "DynamoDB 상태 잠금 테이블 생성 완료"
    else
        log "SUCCESS" "DynamoDB 상태 잠금 테이블 확인됨"
    fi
}

# Terraform 초기화
terraform_init() {
    log "HEADER" "${GEAR} Terraform 초기화"
    
    cd "$(dirname "$0")"
    
    # Terraform 초기화 실행
    log "INFO" "Terraform 초기화 실행 중..."
    terraform init \
        -backend-config="bucket=$TERRAFORM_STATE_BUCKET" \
        -backend-config="key=$ENVIRONMENT/terraform.tfstate" \
        -backend-config="region=$AWS_REGION" \
        -backend-config="dynamodb_table=${PROJECT_NAME}-terraform-locks"
    
    log "SUCCESS" "Terraform 초기화 완료"
}

# Terraform 계획 검토
terraform_plan() {
    log "HEADER" "${CHART} Terraform 실행 계획 검토"
    
    # 계획 파일 생성
    local plan_file="terraform-plan-$ENVIRONMENT-$(date +%Y%m%d_%H%M%S).tfplan"
    
    log "INFO" "Terraform 계획 생성 중..."
    terraform plan \
        -var-file="staging.tfvars" \
        -out="$plan_file" \
        -detailed-exitcode
    
    local plan_exit_code=$?
    
    case $plan_exit_code in
        0)
            log "WARNING" "변경사항이 없습니다"
            return 0
            ;;
        1)
            log "ERROR" "Terraform 계획 실행 실패"
            return 1
            ;;
        2)
            log "SUCCESS" "변경사항이 감지되었습니다"
            ;;
    esac
    
    # 계획 요약 출력
    log "INFO" "계획 요약 생성 중..."
    terraform show -json "$plan_file" | jq '.planned_values.root_module.resources[].type' | sort | uniq -c > plan_summary.txt
    
    log "INFO" "생성될 리소스 요약:"
    cat plan_summary.txt | while read line; do
        log "INFO" "  $line"
    done
    
    # 사용자 확인
    echo
    log "WARNING" "위 계획을 검토하고 계속 진행하시겠습니까? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        log "INFO" "사용자에 의해 취소되었습니다"
        exit 0
    fi
    
    echo "$plan_file" > .last_plan_file
    log "SUCCESS" "Terraform 계획 승인됨"
}

# Terraform 적용
terraform_apply() {
    log "HEADER" "${ROCKET} Terraform 인프라 생성"
    
    local plan_file
    if [ -f .last_plan_file ]; then
        plan_file=$(cat .last_plan_file)
    else
        log "ERROR" "계획 파일을 찾을 수 없습니다"
        return 1
    fi
    
    log "INFO" "인프라 생성 시작..."
    local start_time=$(date +%s)
    
    terraform apply "$plan_file"
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    log "SUCCESS" "인프라 생성 완료 (소요시간: ${duration}초)"
    
    # 출력 값 저장
    terraform output -json > terraform_outputs.json
    log "SUCCESS" "Terraform 출력 값 저장됨"
}

# 인프라 검증
verify_infrastructure() {
    log "HEADER" "${SHIELD} 인프라 검증"
    
    # 출력 값 읽기
    if [ ! -f terraform_outputs.json ]; then
        log "ERROR" "Terraform 출력 파일을 찾을 수 없습니다"
        return 1
    fi
    
    local vpc_id=$(jq -r '.vpc_id.value' terraform_outputs.json)
    local alb_dns=$(jq -r '.alb_dns_name.value' terraform_outputs.json)
    local docdb_endpoint=$(jq -r '.docdb_endpoint.value' terraform_outputs.json)
    local redis_endpoint=$(jq -r '.redis_endpoint.value' terraform_outputs.json)
    local ecr_url=$(jq -r '.ecr_repository_url.value' terraform_outputs.json)
    
    log "INFO" "생성된 리소스 검증 중..."
    
    # VPC 검증
    if aws ec2 describe-vpcs --vpc-ids "$vpc_id" &>/dev/null; then
        log "SUCCESS" "VPC 검증 완료: $vpc_id"
    else
        log "ERROR" "VPC 검증 실패: $vpc_id"
        return 1
    fi
    
    # ALB 검증
    if nslookup "$alb_dns" &>/dev/null; then
        log "SUCCESS" "ALB DNS 검증 완료: $alb_dns"
    else
        log "WARNING" "ALB DNS 전파 대기 중: $alb_dns"
    fi
    
    # DocumentDB 검증
    if [[ "$docdb_endpoint" != "null" ]]; then
        log "SUCCESS" "DocumentDB 엔드포인트 확인: $docdb_endpoint"
    else
        log "ERROR" "DocumentDB 엔드포인트 검증 실패"
        return 1
    fi
    
    # Redis 검증
    if [[ "$redis_endpoint" != "null" ]]; then
        log "SUCCESS" "Redis 엔드포인트 확인: $redis_endpoint"
    else
        log "ERROR" "Redis 엔드포인트 검증 실패"
        return 1
    fi
    
    # ECR 검증
    if aws ecr describe-repositories --repository-names "ai-model-mgmt/backend" &>/dev/null; then
        log "SUCCESS" "ECR 리포지토리 확인: $ecr_url"
    else
        log "ERROR" "ECR 리포지토리 검증 실패"
        return 1
    fi
    
    log "SUCCESS" "모든 인프라 검증 완료"
}

# 환경 설정 파일 업데이트
update_environment_config() {
    log "HEADER" "${GEAR} 환경 설정 파일 업데이트"
    
    # Terraform 출력을 환경 변수 파일에 반영
    local docdb_endpoint=$(jq -r '.docdb_endpoint.value' terraform_outputs.json)
    local redis_endpoint=$(jq -r '.redis_endpoint.value' terraform_outputs.json)
    local ecr_url=$(jq -r '.ecr_repository_url.value' terraform_outputs.json)
    
    # .env.staging 파일 업데이트
    log "INFO" "환경 설정 파일 업데이트 중..."
    
    # MongoDB URL 업데이트
    sed -i "s|MONGO_URL=.*|MONGO_URL=mongodb://admin:StrongPassword123!@#@${docdb_endpoint}:27017/online_evaluation_staging?ssl=true\&replicaSet=rs0|" .env.staging
    
    # Redis URL 업데이트
    sed -i "s|REDIS_URL=.*|REDIS_URL=rediss://${redis_endpoint}:6379|" .env.staging
    
    # ECR Registry 업데이트
    local ecr_registry=$(echo "$ecr_url" | cut -d'/' -f1)
    sed -i "s|ECR_REGISTRY=.*|ECR_REGISTRY=${ecr_registry}|" .env.staging
    
    log "SUCCESS" "환경 설정 파일 업데이트 완료"
    
    # 설정 확인
    log "INFO" "최종 환경 설정:"
    log "INFO" "  MongoDB: $docdb_endpoint"
    log "INFO" "  Redis: $redis_endpoint"
    log "INFO" "  ECR: $ecr_registry"
}

# 인프라 상태 리포트 생성
generate_infrastructure_report() {
    log "HEADER" "${CHART} 인프라 상태 리포트 생성"
    
    local report_file="infrastructure_report_$(date +%Y%m%d_%H%M%S).json"
    
    cat <<EOF > "$report_file"
{
    "infrastructure_deployment": {
        "timestamp": "$(date -u +'%Y-%m-%dT%H:%M:%SZ')",
        "environment": "$ENVIRONMENT",
        "project_name": "$PROJECT_NAME",
        "aws_region": "$AWS_REGION",
        "deployed_by": "$(whoami)",
        "terraform_version": "$(terraform version -json | jq -r .terraform_version)"
    },
    "resources_created": $(terraform show -json | jq '.values.root_module.resources | length'),
    "infrastructure_endpoints": $(cat terraform_outputs.json),
    "deployment_status": "completed",
    "next_steps": [
        "백엔드 서비스 배포",
        "데이터베이스 마이그레이션",
        "모니터링 설정",
        "보안 강화",
        "성능 테스트"
    ]
}
EOF
    
    log "SUCCESS" "인프라 리포트 생성됨: $report_file"
    
    # 요약 출력
    echo
    log "HEADER" "${ROCKET} 인프라 프로비저닝 완료"
    echo -e "${GREEN}✅ 스테이징 인프라 구축 성공!${NC}"
    echo
    echo -e "${WHITE}🏗️ 생성된 인프라:${NC}"
    echo -e "  VPC: ${CYAN}$(jq -r '.vpc_id.value' terraform_outputs.json)${NC}"
    echo -e "  ALB: ${CYAN}$(jq -r '.alb_dns_name.value' terraform_outputs.json)${NC}"
    echo -e "  DocumentDB: ${CYAN}$(jq -r '.docdb_endpoint.value' terraform_outputs.json)${NC}"
    echo -e "  Redis: ${CYAN}$(jq -r '.redis_endpoint.value' terraform_outputs.json)${NC}"
    echo -e "  ECR: ${CYAN}$(jq -r '.ecr_repository_url.value' terraform_outputs.json)${NC}"
    echo
    echo -e "${WHITE}🔗 접속 정보:${NC}"
    echo -e "  도메인: ${BLUE}$(jq -r '.domain_name.value' terraform_outputs.json)${NC}"
    echo -e "  API: ${BLUE}$(jq -r '.api_domain_name.value' terraform_outputs.json)${NC}"
    echo
    echo -e "${WHITE}📋 다음 단계:${NC}"
    echo -e "  1. ${YELLOW}백엔드 서비스 배포${NC}"
    echo -e "  2. ${YELLOW}데이터베이스 초기화${NC}"
    echo -e "  3. ${YELLOW}모니터링 시스템 구축${NC}"
    echo -e "  4. ${YELLOW}보안 설정 강화${NC}"
    echo
}

# 메인 실행 함수
main() {
    local start_time=$(date +%s)
    
    check_prerequisites
    initialize_terraform_backend
    terraform_init
    terraform_plan
    terraform_apply
    verify_infrastructure
    update_environment_config
    generate_infrastructure_report
    
    local end_time=$(date +%s)
    local total_duration=$((end_time - start_time))
    
    log "SUCCESS" "🎉 인프라 프로비저닝이 성공적으로 완료되었습니다! (총 소요시간: ${total_duration}초)"
}

# 스크립트 실행
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi