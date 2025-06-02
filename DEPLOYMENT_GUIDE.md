# 🚀 온라인 평가 시스템 배포 가이드

이 문서는 온라인 평가 시스템을 다른 서버에서 바로 실행할 수 있도록 하는 완전한 배포 가이드입니다.

## 📋 목차

1. [시스템 요구사항](#시스템-요구사항)
2. [빠른 시작](#빠른-시작)
3. [상세 설치 방법](#상세-설치-방법)
4. [환경 설정](#환경-설정)
5. [배포 스크립트 사용법](#배포-스크립트-사용법)
6. [서비스 확인](#서비스-확인)
7. [문제 해결](#문제-해결)
8. [모니터링 및 관리](#모니터링-및-관리)

## 🔧 시스템 요구사항

### 필수 소프트웨어

- **Docker**: 20.10.0 이상
- **Docker Compose**: 2.0.0 이상
- **Git**: 2.30.0 이상 (소스 코드 다운로드용)

### 권장 하드웨어

- **CPU**: 2코어 이상
- **RAM**: 4GB 이상
- **디스크**: 10GB 이상 여유 공간
- **네트워크**: 인터넷 연결 (초기 이미지 다운로드용)

### 지원 운영체제

- **Linux**: Ubuntu 18.04+, CentOS 7+, Debian 10+
- **Windows**: Windows 10/11 (Docker Desktop 설치)
- **macOS**: macOS 10.15+ (Docker Desktop 설치)

## ⚡ 빠른 시작

### 1. 프로젝트 다운로드

```bash
# Git 클론 (추천)
git clone <repository-url> online-evaluation
cd online-evaluation

# 또는 ZIP 파일 다운로드 후 압축 해제
```

### 2. 즉시 실행 (자동 스크립트)

#### Linux/macOS 사용자

```bash
# 실행 권한 부여
chmod +x build-and-deploy.sh

# 개발 환경으로 전체 배포
./build-and-deploy.sh development full

# 프로덕션 환경으로 전체 배포
./build-and-deploy.sh production full
```

#### Windows 사용자

```cmd
# 개발 환경으로 전체 배포
build-and-deploy.bat development full

# 프로덕션 환경으로 전체 배포
build-and-deploy.bat production full
```

### 3. 서비스 접속

배포 완료 후 다음 URL로 접속:

- **웹 애플리케이션**: http://localhost:3000
- **API 서버**: http://localhost:8080
- **API 문서**: http://localhost:8080/docs

## 📖 상세 설치 방법

### 1. Docker 설치

#### Ubuntu/Debian

```bash
# Docker 설치
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Docker Compose 설치
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 사용자 권한 추가
sudo usermod -aG docker $USER
newgrp docker
```

#### CentOS/RHEL

```bash
# Docker 설치
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install -y docker-ce docker-ce-cli containerd.io

# Docker 시작
sudo systemctl start docker
sudo systemctl enable docker

# Docker Compose 설치
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### Windows

1. [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/) 다운로드
2. 설치 프로그램 실행
3. 재부팅 후 Docker Desktop 시작

#### macOS

1. [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/) 다운로드
2. DMG 파일 실행하여 설치
3. Applications 폴더에서 Docker 실행

### 2. 프로젝트 설정

```bash
# 프로젝트 디렉토리로 이동
cd online-evaluation

# 필요한 디렉토리 생성
mkdir -p logs uploads backups

# 실행 권한 부여 (Linux/macOS)
chmod +x build-and-deploy.sh
chmod +x scripts/*.sh
```

## ⚙️ 환경 설정

### 환경변수 파일

프로젝트에는 두 가지 환경 설정 파일이 포함되어 있습니다:

- `.env.development`: 개발 환경용
- `.env.production`: 프로덕션 환경용

### 프로덕션 환경 커스터마이징

`.env.production` 파일을 편집하여 프로덕션 환경에 맞게 설정을 변경할 수 있습니다:

```bash
# 보안 설정 변경 (필수)
JWT_SECRET=your-production-jwt-secret-key-here
MONGODB_PASSWORD=your-secure-mongodb-password

# 도메인 설정 (선택)
REACT_APP_API_URL=https://your-domain.com/api
REACT_APP_WS_URL=wss://your-domain.com/ws
CORS_ORIGIN=https://your-domain.com

# 성능 설정 (선택)
MAX_CONCURRENT_CONNECTIONS=2000
CACHE_TTL=7200
```

### 포트 변경

기본 포트가 이미 사용 중인 경우 `docker-compose.yml` 파일에서 포트를 변경할 수 있습니다:

```yaml
services:
  nginx:
    ports:
      - "8080:80"  # 3000 대신 8080 포트 사용
  
  backend:
    ports:
      - "8081:8080"  # 8080 대신 8081 포트 사용
```

## 🚀 배포 스크립트 사용법

### 자동 스크립트 명령어

#### Linux/macOS

```bash
# 전체 배포 (빌드 + 실행)
./build-and-deploy.sh [environment] full

# 이미지만 빌드
./build-and-deploy.sh [environment] build

# 컨테이너만 실행
./build-and-deploy.sh [environment] deploy

# 서비스 재시작
./build-and-deploy.sh [environment] restart

# 서비스 중지
./build-and-deploy.sh [environment] stop

# 데이터 백업
./build-and-deploy.sh [environment] backup

# 실시간 로그 확인
./build-and-deploy.sh [environment] logs
```

#### Windows

```cmd
# 전체 배포 (빌드 + 실행)
build-and-deploy.bat [environment] full

# 이미지만 빌드
build-and-deploy.bat [environment] build

# 컨테이너만 실행
build-and-deploy.bat [environment] deploy

# 기타 명령어들도 동일
```

### 수동 Docker Compose 명령어

```bash
# 환경변수 파일 복사
cp .env.production .env

# 이미지 빌드
docker-compose build

# 서비스 시작
docker-compose up -d

# 서비스 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs -f

# 서비스 중지
docker-compose down

# 완전 정리 (볼륨 포함)
docker-compose down -v --remove-orphans
```

## ✅ 서비스 확인

### 1. 컨테이너 상태 확인

```bash
docker-compose ps
```

모든 서비스가 `Up` 상태여야 합니다:

```
NAME                          IMAGE                     STATUS
online-evaluation-mongodb     mongo:7                   Up (healthy)
online-evaluation-redis       redis:7-alpine            Up (healthy)
online-evaluation-backend     online-evaluation_backend Up (healthy)
online-evaluation-frontend    online-evaluation_frontend Up
online-evaluation-nginx       nginx:alpine              Up
```

### 2. 헬스 체크

```bash
# 백엔드 API 헬스 체크
curl http://localhost:8080/health

# 프론트엔드 접근 확인
curl http://localhost:3000

# 데이터베이스 연결 확인
docker-compose exec mongodb mongosh --eval "db.adminCommand('ping')"

# Redis 연결 확인
docker-compose exec redis redis-cli ping
```

### 3. 자동 테스트 실행

```bash
# Python 테스트 스크립트 실행 (의존성 설치 필요)
pip install aiohttp websockets pymongo redis
python final_deployment_test.py

# 또는 통합 테스트 스크립트 실행
python final_integration_test.py
```

## 🔧 문제 해결

### 일반적인 문제

#### 1. 포트 이미 사용 중

**증상**: `Port already in use` 에러

**해결책**:
```bash
# 포트 사용 프로세스 확인
sudo netstat -tulpn | grep :3000
sudo netstat -tulpn | grep :8080

# 프로세스 종료
sudo kill -9 <PID>

# 또는 docker-compose.yml에서 다른 포트 사용
```

#### 2. Docker 권한 문제

**증상**: `Permission denied` 에러

**해결책**:
```bash
# Docker 그룹에 사용자 추가
sudo usermod -aG docker $USER
newgrp docker

# 재로그인 또는 재부팅
```

#### 3. 메모리 부족

**증상**: 컨테이너가 계속 재시작

**해결책**:
```bash
# 사용하지 않는 Docker 객체 정리
docker system prune -f

# Docker 메모리 제한 조정 (docker-compose.yml)
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 512M
```

#### 4. 데이터베이스 연결 실패

**증상**: MongoDB 또는 Redis 연결 에러

**해결책**:
```bash
# 컨테이너 로그 확인
docker-compose logs mongodb
docker-compose logs redis

# 컨테이너 재시작
docker-compose restart mongodb redis

# 네트워크 확인
docker network ls
docker network inspect online-evaluation_online-evaluation-network
```

### 로그 분석

```bash
# 모든 서비스 로그
docker-compose logs -f

# 특정 서비스 로그
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f mongodb

# 에러 로그만 필터링
docker-compose logs | grep -i error
```

## 📊 모니터링 및 관리

### 시스템 모니터링

#### 1. 리소스 사용량 확인

```bash
# Docker 컨테이너 리소스 사용량
docker stats

# 시스템 리소스 확인
htop
df -h
free -m
```

#### 2. 애플리케이션 메트릭

- **헬스 체크**: http://localhost:8080/health
- **시스템 메트릭**: http://localhost:8080/metrics
- **API 문서**: http://localhost:8080/docs

### 데이터 백업

#### 자동 백업

```bash
# 스크립트를 통한 백업
./build-and-deploy.sh production backup
```

#### 수동 백업

```bash
# MongoDB 백업
docker-compose exec mongodb mongodump --out /tmp/backup
docker cp $(docker-compose ps -q mongodb):/tmp/backup ./backup_$(date +%Y%m%d)

# Redis 백업
docker-compose exec redis redis-cli BGSAVE
docker cp $(docker-compose ps -q redis):/data/dump.rdb ./redis_backup_$(date +%Y%m%d).rdb
```

### 업데이트

```bash
# 코드 업데이트
git pull origin main

# 이미지 다시 빌드
docker-compose build --no-cache

# 무중단 업데이트
docker-compose up -d --force-recreate
```

### 로그 로테이션

```bash
# Docker 로그 크기 제한 (docker-compose.yml)
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## 🔒 보안 고려사항

### 프로덕션 환경 보안 체크리스트

- [ ] 기본 비밀번호 변경 (MongoDB, JWT Secret)
- [ ] HTTPS 설정 (리버스 프록시 사용)
- [ ] 방화벽 설정 (필요한 포트만 오픈)
- [ ] 정기적인 보안 업데이트
- [ ] 로그 모니터링 설정
- [ ] 백업 및 복구 계획 수립

### SSL/TLS 설정 (선택사항)

Let's Encrypt를 사용한 HTTPS 설정:

```bash
# Certbot 설치
sudo apt-get install certbot

# SSL 인증서 발급
sudo certbot certonly --standalone -d your-domain.com

# Nginx 설정에 SSL 추가
```

## 📞 지원 및 문의

### 기술 지원

- **시스템 로그**: `docker-compose logs`
- **테스트 스크립트**: `python final_deployment_test.py`
- **헬스 체크**: http://localhost:8080/health

### 추가 정보

- **API 문서**: http://localhost:8080/docs
- **프로젝트 문서**: `README.md`
- **완성도 보고서**: `100_PERCENT_COMPLETION_REPORT.md`

---

## 🎉 배포 완료!

이 가이드를 따라 성공적으로 배포했다면, 엔터프라이즈급 온라인 평가 시스템이 프로덕션 환경에서 실행되고 있습니다.

**주요 기능:**
- ✅ 실시간 WebSocket 알림
- ✅ Redis 캐싱 시스템
- ✅ 고급 헬스 모니터링
- ✅ 다크 모드 테마
- ✅ 완전한 Docker 컨테이너화
- ✅ 자동화된 배포 스크립트
- ✅ 통합 테스트 시스템

**다음 단계:**
1. 사용자 가이드 작성
2. 성능 최적화
3. 추가 기능 개발
4. 모니터링 대시보드 구축

**Happy Coding! 🚀**
