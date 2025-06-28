#!/usr/bin/env python3
"""
프로덕션 환경용 보안 키 생성 스크립트
안전한 랜덤 키들을 생성하여 프로덕션 배포에 사용합니다.
"""

import secrets
import string
import base64
import os
from datetime import datetime

def generate_jwt_secret(length=64):
    """JWT용 강력한 비밀키 생성 (256비트 이상)"""
    return base64.urlsafe_b64encode(secrets.token_bytes(length)).decode('utf-8')

def generate_password(length=32):
    """강력한 비밀번호 생성"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_hex_key(length=32):
    """16진수 키 생성 (암호화용)"""
    return secrets.token_hex(length)

def generate_session_secret(length=64):
    """세션 비밀키 생성"""
    return secrets.token_urlsafe(length)

def generate_production_env():
    """프로덕션 환경 설정 파일 생성"""
    
    # 강력한 키들 생성
    jwt_secret = generate_jwt_secret(64)
    session_secret = generate_session_secret(64)
    mongodb_password = generate_password(24)
    redis_password = generate_password(24)
    db_encryption_key = generate_hex_key(32)
    
    # 현재 시간
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    env_content = f"""# 프로덕션 환경 설정 파일
# 생성일시: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
# 주의: 이 파일은 보안이 중요합니다. 절대 공개하지 마세요.

# ===========================================
# 데이터베이스 설정
# ===========================================
MONGO_URL=mongodb://admin:{mongodb_password}@mongodb:27017/online_evaluation?authSource=admin
DB_NAME=online_evaluation

# MongoDB 관리자 계정
MONGO_INITDB_ROOT_USERNAME=admin
MONGO_INITDB_ROOT_PASSWORD={mongodb_password}

# ===========================================
# 보안 설정
# ===========================================
# JWT 비밀키 (안전하게 생성됨)
JWT_SECRET={jwt_secret}
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=8

# 세션 보안
SESSION_SECRET={session_secret}

# ===========================================
# 서버 설정
# ===========================================
HOST=0.0.0.0
PORT=8080

# CORS 설정 (실제 도메인으로 변경 필요)
CORS_ORIGINS=https://evaluation.your-domain.com

# ===========================================
# Redis 설정
# ===========================================
REDIS_URL=redis://:{redis_password}@redis:6379
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD={redis_password}

# ===========================================
# 파일 업로드 설정
# ===========================================
UPLOAD_DIR=/app/uploads
MAX_FILE_SIZE=100MB
ALLOWED_FILE_TYPES=application/pdf,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document

# ===========================================
# 로깅 설정
# ===========================================
LOG_LEVEL=INFO
LOG_FORMAT=json

# ===========================================
# 데이터베이스 보안
# ===========================================
# 데이터베이스 암호화 키 (AES-256)
DB_ENCRYPTION_KEY={db_encryption_key}

# 개인정보 마스킹 설정
ENABLE_DATA_MASKING=true
MASK_PHONE_NUMBERS=true
MASK_EMAIL_ADDRESSES=true

# ===========================================
# 감사 로그 설정
# ===========================================
AUDIT_LOG_ENABLED=true
AUDIT_LOG_LEVEL=INFO
AUDIT_LOG_RETENTION_DAYS=365

# ===========================================
# 보안 헤더 설정
# ===========================================
SECURITY_HEADERS_ENABLED=true
CONTENT_SECURITY_POLICY=default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:
X_FRAME_OPTIONS=DENY
X_CONTENT_TYPE_OPTIONS=nosniff
STRICT_TRANSPORT_SECURITY=max-age=31536000; includeSubDomains

# ===========================================
# 환경 식별
# ===========================================
ENVIRONMENT=production
DEBUG=false

# ===========================================
# 프로덕션 보안 설정
# ===========================================
SECURE_COOKIES=true
RATE_LIMIT_ENABLED=true
RATE_LIMIT_MAX=100
RATE_LIMIT_WINDOW=3600

# HTTPS 강제 설정
FORCE_HTTPS=true
HSTS_ENABLED=true

# ===========================================
# 백업 및 모니터링 (설정 후 활성화)
# ===========================================
# BACKUP_SCHEDULE=0 2 * * *
# BACKUP_RETENTION_DAYS=30
# PROMETHEUS_ENABLED=true
# METRICS_PORT=9090

# ===========================================
# 외부 서비스 API 키 (필요시 설정)
# ===========================================
# OPENAI_API_KEY=sk-...
# OPENAI_MODEL=gpt-4o-mini
# CLAUDE_API_KEY=...

# ===========================================
# 이메일 설정 (필요시 설정)
# ===========================================
# SMTP_HOST=smtp.gmail.com
# SMTP_PORT=587
# SMTP_USERNAME=your-email@gmail.com
# SMTP_PASSWORD=app-specific-password
# SMTP_TLS=true
"""

    # 파일 저장
    filename = f".env.production.{timestamp}"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    # 권한 설정 (읽기 전용)
    os.chmod(filename, 0o600)
    
    return filename, {
        'jwt_secret': jwt_secret,
        'mongodb_password': mongodb_password,
        'redis_password': redis_password,
        'session_secret': session_secret,
        'db_encryption_key': db_encryption_key
    }

def generate_docker_compose_production():
    """프로덕션용 docker-compose 파일 생성"""
    
    docker_compose_content = """version: '3.8'

services:
  # Redis 캐시 서버 (보안 강화)
  redis:
    image: redis:7-alpine
    container_name: online-evaluation-redis-prod
    restart: unless-stopped
    ports:
      - "127.0.0.1:6379:6379"  # 로컬호스트에서만 접근
    command: redis-server --requirepass ${REDIS_PASSWORD} --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    networks:
      - online-evaluation-network
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
    security_opt:
      - no-new-privileges:true

  # MongoDB 데이터베이스 (보안 강화)
  mongodb:
    image: mongo:7
    container_name: online-evaluation-mongodb-prod
    restart: unless-stopped
    ports:
      - "127.0.0.1:27017:27017"  # 로컬호스트에서만 접근
    environment:
      MONGO_INITDB_ROOT_USERNAME: ${MONGO_INITDB_ROOT_USERNAME}
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_INITDB_ROOT_PASSWORD}
      MONGO_INITDB_DATABASE: online_evaluation
    volumes:
      - mongodb_data:/data/db
      - ./scripts/init-sample-data.js:/docker-entrypoint-initdb.d/init-sample-data.js:ro
      - ./config/mongod-prod.conf:/etc/mongod.conf:ro
    command: mongod --config /etc/mongod.conf
    networks:
      - online-evaluation-network
    healthcheck:
      test: ["CMD", "mongosh", "--eval", "db.adminCommand('ping')"]
      interval: 30s
      timeout: 10s
      retries: 3
    security_opt:
      - no-new-privileges:true

  # 백엔드 API 서버 (프로덕션 설정)
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
      target: production
    container_name: online-evaluation-backend-prod
    restart: unless-stopped
    ports:
      - "127.0.0.1:8080:8080"  # 내부 네트워크에서만 접근
    env_file:
      - .env.production
    volumes:
      - ./uploads:/app/uploads:rw
      - ./logs:/app/logs:rw
      - ./ssl:/app/ssl:ro  # SSL 인증서 마운트
    depends_on:
      mongodb:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - online-evaluation-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
      - /var/cache
    ulimits:
      nofile:
        soft: 65536
        hard: 65536

  # 프론트엔드 웹 서버 (프로덕션 빌드)
  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
      target: production
    container_name: online-evaluation-frontend-prod
    restart: unless-stopped
    environment:
      REACT_APP_BACKEND_URL: "https://api.your-domain.com"
      REACT_APP_WS_URL: "wss://api.your-domain.com"
    depends_on:
      backend:
        condition: service_healthy
    networks:
      - online-evaluation-network
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
      - /var/cache

  # Nginx 리버스 프록시 (SSL 종료 및 보안 헤더)
  nginx:
    image: nginx:alpine
    container_name: online-evaluation-nginx-prod
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx-prod.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
      - ./logs/nginx:/var/log/nginx:rw
    depends_on:
      - frontend
      - backend
    networks:
      - online-evaluation-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    security_opt:
      - no-new-privileges:true

  # 모니터링 (Prometheus)
  prometheus:
    image: prom/prometheus:latest
    container_name: online-evaluation-prometheus
    restart: unless-stopped
    ports:
      - "127.0.0.1:9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
    networks:
      - online-evaluation-network
    security_opt:
      - no-new-privileges:true

volumes:
  mongodb_data:
    driver: local
  redis_data:
    driver: local
  prometheus_data:
    driver: local

networks:
  online-evaluation-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
"""

    with open("docker-compose.production.yml", 'w', encoding='utf-8') as f:
        f.write(docker_compose_content)
    
    return "docker-compose.production.yml"

def main():
    print("🔐 프로덕션 환경 보안 설정 생성 중...")
    print("="*50)
    
    # 환경 설정 파일 생성
    env_filename, secrets = generate_production_env()
    print(f"✅ 환경 설정 파일 생성: {env_filename}")
    
    # Docker Compose 파일 생성
    docker_filename = generate_docker_compose_production()
    print(f"✅ Docker Compose 파일 생성: {docker_filename}")
    
    print("\n🔑 생성된 보안 키들:")
    print(f"   JWT Secret: {secrets['jwt_secret'][:20]}...")
    print(f"   MongoDB Password: {secrets['mongodb_password'][:10]}...")
    print(f"   Redis Password: {secrets['redis_password'][:10]}...")
    print(f"   Session Secret: {secrets['session_secret'][:20]}...")
    print(f"   DB Encryption Key: {secrets['db_encryption_key'][:16]}...")
    
    print("\n📋 다음 단계:")
    print("1. 생성된 .env.production 파일을 안전한 곳에 백업하세요")
    print("2. 실제 도메인으로 CORS_ORIGINS를 수정하세요")
    print("3. SSL 인증서를 ./ssl/ 디렉토리에 배치하세요")
    print("4. 이메일 및 외부 API 설정을 완성하세요")
    print("5. docker-compose -f docker-compose.production.yml up -d 로 배포하세요")
    
    print("\n⚠️  보안 주의사항:")
    print("- 생성된 .env.production 파일은 절대 공개하지 마세요")
    print("- 정기적으로 비밀번호를 변경하세요")
    print("- 방화벽 설정을 확인하세요")
    print("- 정기적인 보안 업데이트를 수행하세요")

if __name__ == "__main__":
    main()