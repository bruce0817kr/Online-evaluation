# 🚀 AI 모델 관리 시스템 - 스테이징 환경 변수
# Terraform Variables for Staging Environment

# 기본 환경 설정
aws_region     = "ap-northeast-2"
environment    = "staging"
project_name   = "ai-model-mgmt"

# 도메인 설정
domain_name     = "staging.ai-model-mgmt.com"
api_domain_name = "api-staging.ai-model-mgmt.com"

# 데이터베이스 보안 설정
docdb_password = "StrongPassword123!@#"
redis_auth_token = "RedisAuthToken456$%^"

# 추가 환경별 설정
tags = {
  Environment = "staging"
  Project     = "ai-model-management"
  Team        = "backend"
  Owner       = "devops@company.com"
  CostCenter  = "engineering"
}