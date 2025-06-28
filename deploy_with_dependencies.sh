#!/bin/bash
# 온라인 평가 시스템 배포 스크립트 (의존성 포함)
# MongoDB와 Redis가 Docker 컨테이너에 포함되어 있음

set -e

echo "🚀 온라인 평가 시스템 배포를 시작합니다..."
echo "📅 배포 시작 시간: $(date)"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 환경 변수 설정
ENVIRONMENT=${1:-development}
FORCE_DEPLOY=${2:-false}

echo -e "${BLUE}🔧 배포 환경: $ENVIRONMENT${NC}"

# 함수 정의
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}❌ $1이 설치되지 않았습니다${NC}"
        echo "설치 방법:"
        case $1 in
            docker)
                echo "  Ubuntu/Debian: sudo apt-get install docker.io"
                echo "  CentOS/RHEL: sudo yum install docker"
                echo "  macOS: brew install docker"
                ;;
            docker-compose)
                echo "  pip install docker-compose"
                echo "  또는 Docker Desktop 설치"
                ;;
            node)
                echo "  Ubuntu/Debian: sudo apt-get install nodejs npm"
                echo "  CentOS/RHEL: sudo yum install nodejs npm"
                echo "  macOS: brew install node"
                ;;
            npm)
                echo "  Node.js와 함께 설치됩니다"
                ;;
        esac
        exit 1
    fi
}

check_port() {
    local port=$1
    if command -v lsof &> /dev/null && lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  포트 $port가 이미 사용 중입니다${NC}"
        if [ "$FORCE_DEPLOY" != "true" ]; then
            echo "강제 배포하려면 두 번째 인자로 'true'를 전달하세요"
            echo "예: ./deploy_with_dependencies.sh $ENVIRONMENT true"
            exit 1
        fi
    fi
}

# 1. 전제 조건 확인
echo -e "\n${BLUE}📋 전제 조건 확인 중...${NC}"
check_command docker
check_command docker-compose

# Docker 서비스 시작 확인
if ! docker info &> /dev/null; then
    echo -e "${YELLOW}⚠️ Docker 서비스가 실행되지 않고 있습니다${NC}"
    echo "Docker 서비스를 시작해주세요:"
    echo "  sudo systemctl start docker  # Linux"
    echo "  또는 Docker Desktop을 실행하세요  # Windows/macOS"
    exit 1
fi

echo -e "${GREEN}✅ Docker가 정상적으로 실행 중입니다${NC}"

# 2. 포트 확인
echo -e "\n${BLUE}🔍 포트 사용 상태 확인 중...${NC}"
check_port 8080  # 백엔드
check_port 3001  # 프론트엔드
check_port 27017 # MongoDB
check_port 6379  # Redis

echo -e "${GREEN}✅ 모든 포트가 사용 가능합니다${NC}"

# 3. 환경 설정 파일 확인
echo -e "\n${BLUE}⚙️ 환경 설정 파일 확인 중...${NC}"

if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️ .env 파일이 없습니다. .env.example에서 복사합니다...${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}✅ .env 파일이 생성되었습니다${NC}"
    else
        echo -e "${YELLOW}⚠️ .env.example 파일도 없습니다. 기본 환경 변수를 생성합니다...${NC}"
        cat > .env << EOF
# 데이터베이스 설정
MONGO_URL=mongodb://admin:password123@mongodb:27017/online_evaluation?authSource=admin
DB_NAME=online_evaluation

# Redis 설정
REDIS_URL=redis://redis:6379
REDIS_HOST=redis
REDIS_PORT=6379

# JWT 설정
JWT_SECRET=your-super-secret-jwt-key-change-in-production-$(date +%s)
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=24

# 서버 설정
HOST=0.0.0.0
PORT=8080
CORS_ORIGINS=http://localhost:3001,http://frontend:3000

# 로그 설정
LOG_LEVEL=INFO

# 업로드 설정
UPLOAD_DIR=/app/uploads
MAX_FILE_SIZE=50MB

# 환경 설정
ENVIRONMENT=$ENVIRONMENT
EOF
        echo -e "${GREEN}✅ 기본 .env 파일이 생성되었습니다${NC}"
    fi
fi

# 4. Docker Compose 파일 확인
echo -e "\n${BLUE}📄 Docker Compose 설정 확인 중...${NC}"

if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}❌ docker-compose.yml 파일이 없습니다${NC}"
    exit 1
fi

# MongoDB와 Redis 서비스가 포함되어 있는지 확인
if ! grep -q "mongodb:" docker-compose.yml; then
    echo -e "${RED}❌ docker-compose.yml에 MongoDB 서비스가 정의되지 않았습니다${NC}"
    exit 1
fi

if ! grep -q "redis:" docker-compose.yml; then
    echo -e "${RED}❌ docker-compose.yml에 Redis 서비스가 정의되지 않았습니다${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker Compose 설정이 올바릅니다 (MongoDB, Redis 포함)${NC}"

# 5. 필요한 디렉토리 생성
echo -e "\n${BLUE}📁 필요한 디렉토리 생성 중...${NC}"
mkdir -p uploads logs data/mongodb data/redis

echo -e "${GREEN}✅ 디렉토리가 생성되었습니다${NC}"

# 6. 기존 컨테이너 정리 (강제 배포인 경우)
if [ "$FORCE_DEPLOY" = "true" ]; then
    echo -e "\n${YELLOW}🧹 기존 컨테이너 정리 중...${NC}"
    docker-compose down -v 2>/dev/null || true
    echo -e "${GREEN}✅ 기존 컨테이너가 정리되었습니다${NC}"
fi

# 7. Docker 이미지 빌드 및 컨테이너 시작
echo -e "\n${BLUE}🏗️ Docker 이미지 빌드 및 컨테이너 시작 중...${NC}"
echo "이 과정은 몇 분이 소요될 수 있습니다..."

if [ "$ENVIRONMENT" = "production" ]; then
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
else
    docker-compose up --build -d
fi

# 8. 서비스 상태 확인
echo -e "\n${BLUE}🏥 서비스 상태 확인 중...${NC}"

# 서비스가 시작될 때까지 대기
echo "서비스 시작 대기 중..."
sleep 30

# 헬스체크
services=("mongodb:27017" "redis:6379" "backend:8080" "frontend:3000")
all_healthy=true

for service in "${services[@]}"; do
    IFS=':' read -r name port <<< "$service"
    
    if [ "$name" = "backend" ]; then
        if curl -f -s http://localhost:$port/health > /dev/null 2>&1; then
            echo -e "  ✅ $name ($port): 정상"
        else
            echo -e "  ❌ $name ($port): 비정상"
            all_healthy=false
        fi
    elif [ "$name" = "frontend" ]; then
        if curl -f -s http://localhost:3001 > /dev/null 2>&1; then
            echo -e "  ✅ $name (3001): 정상"
        else
            echo -e "  ❌ $name (3001): 비정상"
            all_healthy=false
        fi
    else
        # MongoDB와 Redis는 docker 컨테이너 상태로 확인
        if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "online-evaluation-$name.*Up"; then
            echo -e "  ✅ $name ($port): 정상"
        else
            echo -e "  ❌ $name ($port): 비정상"
            all_healthy=false
        fi
    fi
done

# 9. 컨테이너 상태 확인
echo -e "\n${BLUE}📊 컨테이너 상태:${NC}"
docker-compose ps

# 10. 로그 확인 (오류가 있는 경우)
if [ "$all_healthy" = false ]; then
    echo -e "\n${RED}❌ 일부 서비스에 문제가 있습니다. 로그를 확인하세요:${NC}"
    echo "  docker-compose logs backend"
    echo "  docker-compose logs frontend"
    echo "  docker-compose logs mongodb"
    echo "  docker-compose logs redis"
fi

# 11. 배포 완료 알림
echo -e "\n" + "="*70
if [ "$all_healthy" = true ]; then
    echo -e "${GREEN}🎉 배포가 성공적으로 완료되었습니다!${NC}"
    echo -e "${GREEN}="*70"
    echo -e "🌐 서비스 접속 정보:"
    echo -e "  📱 프론트엔드: ${BLUE}http://localhost:3001${NC}"
    echo -e "  🔧 백엔드 API: ${BLUE}http://localhost:8080${NC}"
    echo -e "  📚 API 문서: ${BLUE}http://localhost:8080/docs${NC}"
    echo -e "  🏥 헬스체크: ${BLUE}http://localhost:8080/health${NC}"
    echo ""
    echo -e "🗄️ 데이터베이스 접속 정보:"
    echo -e "  📊 MongoDB: ${BLUE}localhost:27017${NC}"
    echo -e "  ⚡ Redis: ${BLUE}localhost:6379${NC}"
    echo ""
    echo -e "👤 기본 관리자 계정:"
    echo -e "  📧 사용자명: ${BLUE}admin${NC}"
    echo -e "  🔑 비밀번호: ${BLUE}admin123${NC}"
    echo ""
    echo -e "📋 유용한 명령어:"
    echo -e "  서비스 중지: ${BLUE}docker-compose down${NC}"
    echo -e "  로그 확인: ${BLUE}docker-compose logs -f${NC}"
    echo -e "  서비스 재시작: ${BLUE}docker-compose restart${NC}"
else
    echo -e "${RED}❌ 배포 중 일부 서비스에 문제가 발생했습니다.${NC}"
    echo -e "${YELLOW}로그를 확인하고 문제를 해결한 후 다시 시도하세요.${NC}"
    exit 1
fi

echo -e "${GREEN}="*70"
echo -e "📅 배포 완료 시간: $(date)${NC}"
echo -e "🚀 온라인 평가 시스템이 성공적으로 실행되었습니다!"