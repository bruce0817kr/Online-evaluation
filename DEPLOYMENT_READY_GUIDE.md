# 회사 배포용 파일 준비 가이드

## 📁 현재 폴더를 그대로 복사해도 되는가?

**답: 네, 현재 `C:\project\Online-evaluation` 폴더를 통째로 복사하시면 됩니다!**

## ✅ 배포 준비 완료 상태

### 1. 완전한 Docker 환경
현재 폴더에는 다음이 모두 준비되어 있습니다:
- `docker-compose.yml` - 원클릭 배포 설정
- `Dockerfile.backend` - 백엔드 컨테이너 설정  
- `Dockerfile.frontend` - 프론트엔드 컨테이너 설정
- 모든 소스코드 및 설정 파일

### 2. 즉시 실행 가능
새로운 서버에서 다음 명령어만 실행하면 됩니다:
```bash
# 1. 폴더 복사 후 이동
cd Online-evaluation

# 2. Docker 설치 확인 (필요시)
docker --version
docker-compose --version

# 3. 시스템 시작 (원클릭 배포)
docker-compose up -d

# 4. 배포 검증
python docker_deployment_checker.py
```

### 3. 자동 설정되는 것들
- **MongoDB**: 자동 설치 및 설정
- **Redis**: 자동 설치 및 설정  
- **Backend API**: 자동 빌드 및 실행
- **Frontend**: 자동 빌드 및 실행
- **네트워크**: 자동 연결 설정

## 📋 새 서버 배포 체크리스트

### 사전 요구사항 (새 서버에 필요한 것)
- [ ] **Docker** 설치 (최신 버전)
- [ ] **Docker Compose** 설치
- [ ] **Python 3.8+** 설치 (검증 스크립트용)
- [ ] 포트 개방: 3000(Frontend), 8080(Backend), 27017(MongoDB), 6379(Redis)

### 배포 단계
1. [ ] 현재 폴더 전체 복사
2. [ ] `cd Online-evaluation` 이동
3. [ ] `docker-compose up -d` 실행
4. [ ] `python docker_deployment_checker.py` 검증
5. [ ] 브라우저에서 `http://서버IP:3000` 접속 확인

## 🚀 배포 후 접속 URL
- **프론트엔드**: `http://서버IP:3000`
- **백엔드 API**: `http://서버IP:8080`
- **API 문서**: `http://서버IP:8080/docs`
- **헬스체크**: `http://서버IP:8080/health`

## 📁 복사할 폴더 구조
```
Online-evaluation/           ← 이 폴더 전체 복사
├── docker-compose.yml      ← 핵심 배포 설정
├── Dockerfile.backend      ← 백엔드 도커 설정
├── Dockerfile.frontend     ← 프론트엔드 도커 설정
├── backend/                ← 백엔드 소스코드
├── frontend/               ← 프론트엔드 소스코드
├── config/                 ← 데이터베이스 설정
├── data/                   ← 데이터베이스 데이터 (선택적)
├── docker_deployment_checker.py  ← 배포 검증 스크립트
├── build-and-deploy.bat    ← Windows 배포 스크립트
└── README.md               ← 사용 설명서
```

## ⚠️ 주의사항

### 1. 데이터 폴더 처리
- `data/` 폴더는 선택적으로 복사 (개발 데이터 포함)
- 운영 환경에서는 빈 데이터베이스로 시작하려면 `data/` 폴더 제외

### 2. 환경 설정
- `.env` 파일이 있다면 운영 환경에 맞게 수정
- 보안을 위해 SECRET_KEY, 비밀번호 등 변경 권장

### 3. 방화벽 설정
새 서버에서 다음 포트 개방 필요:
- 3000 (Frontend)
- 8080 (Backend API)  
- 27017 (MongoDB - 선택적)
- 6379 (Redis - 선택적)

## 🔧 트러블슈팅

### 문제 1: Docker 명령어 실행 안됨
```bash
# 해결: Docker 데몬 시작
sudo systemctl start docker    # Linux
# 또는 Docker Desktop 실행     # Windows/Mac
```

### 문제 2: 포트 충돌
```bash
# 해결: 사용 중인 포트 확인 및 종료
netstat -tulpn | grep :3000
sudo kill -9 [PID]
```

### 문제 3: 권한 문제
```bash
# 해결: Docker 권한 설정
sudo usermod -aG docker $USER
# 또는 sudo로 실행
sudo docker-compose up -d
```

## 📞 지원 정보
- **배포 검증**: `python docker_deployment_checker.py` 실행
- **로그 확인**: `docker-compose logs -f`
- **개별 서비스 로그**: `docker logs online-evaluation-backend`
- **시스템 종료**: `docker-compose down`

---
**결론**: 현재 폴더를 그대로 복사해서 새 서버에 배포하면 바로 동작합니다! 🚀
