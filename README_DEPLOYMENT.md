# 🚀 온라인 평가 시스템 원클릭 배포 가이드

포트 스캔 → 할당 → 도커 실행 → 웹페이지 오픈까지 모든 과정을 자동화한 원클릭 배포 시스템입니다.

## 📋 사전 요구사항

### 필수 소프트웨어
- **Python 3.7+** (Universal Port Manager 실행용)
- **Docker** (컨테이너 실행용)
- **Docker Compose** (멀티 컨테이너 관리용)

### 의존성 설치
```bash
# Python 의존성 (선택사항 - 없어도 기본 기능 동작)
pip install psutil PyYAML requests

# 또는 자동 설치 (추천)
python -m universal_port_manager.dependency_manager install full
```

## 🎯 배포 방법

### 1️⃣ Windows 사용자
```cmd
# 관리자 권한으로 실행 (포트 스캔을 위해 필요)
one-click-deploy.bat
```

### 2️⃣ Linux/Mac 사용자
```bash
# 실행 권한 부여 (최초 1회)
chmod +x one-click-deploy.sh

# 배포 실행
./one-click-deploy.sh
```

### 3️⃣ 크로스 플랫폼 (Python)
```bash
# 모든 운영체제에서 동작
python quick-deploy.py
```

## 🔄 배포 프로세스

### 자동화된 7단계 프로세스

1. **시스템 진단** 🩺
   - Universal Port Manager 상태 확인
   - 필수 의존성 검증
   - 시스템 호환성 확인

2. **포트 스캔** 🔍
   - 현재 사용 중인 포트 전체 스캔
   - 시스템 포트, Docker 포트, 프로세스 포트 감지
   - 충돌 가능성 분석

3. **포트 할당** 🎯
   - 지능형 포트 할당 시스템
   - 충돌 회피 알고리즘 적용
   - 서비스별 최적 포트 배정

4. **설정 파일 생성** ⚙️
   - `.env` 파일 자동 생성
   - `docker-compose.yml` 업데이트
   - `ports.json` 설정 저장

5. **Docker 컨테이너 실행** 🐳
   - 기존 컨테이너 정리
   - 새로운 설정으로 빌드 및 실행
   - 서비스 간 네트워킹 설정

6. **서비스 대기** ⏳
   - 백엔드 헬스체크 (최대 120초)
   - 프론트엔드 응답 확인
   - 서비스 준비 상태 모니터링

7. **웹페이지 오픈** 🌐
   - 프론트엔드 자동 실행
   - API 문서 페이지 오픈
   - 접속 정보 안내

## 📊 할당되는 서비스

| 서비스 | 기본 포트 | 용도 |
|--------|----------|------|
| **Frontend** | 3001+ | React 웹 애플리케이션 |
| **Backend** | 8001+ | FastAPI 서버 |
| **MongoDB** | 27018+ | 데이터베이스 |
| **Redis** | 6381+ | 캐시 및 세션 |
| **Nginx** | 8081+ | 리버스 프록시 |

> **참고**: 실제 포트는 충돌 상황에 따라 자동으로 조정됩니다.

## 🎉 배포 완료 후 접속

배포가 완료되면 다음 서비스에 접속할 수 있습니다:

- **📱 웹 애플리케이션**: `http://localhost:[frontend_port]`
- **📚 API 문서**: `http://localhost:[backend_port]/docs`
- **🔧 API 엔드포인트**: `http://localhost:[backend_port]/api`

## 🛠️ 관리 명령어

### 서비스 상태 확인
```bash
docker-compose -p online-evaluation ps
```

### 실시간 로그 확인
```bash
docker-compose -p online-evaluation logs -f
```

### 특정 서비스 로그
```bash
# 백엔드 로그
docker-compose -p online-evaluation logs -f backend

# 프론트엔드 로그
docker-compose -p online-evaluation logs -f frontend
```

### 서비스 중지
```bash
docker-compose -p online-evaluation down
```

### 서비스 재시작
```bash
docker-compose -p online-evaluation restart
```

## 🔧 문제 해결

### 일반적인 문제들

#### 1. 포트 충돌 오류
```bash
# 포트 상태 확인
python -m universal_port_manager.cli --project online-evaluation status

# 포트 재할당
python -m universal_port_manager.cli --project online-evaluation allocate frontend backend mongodb redis nginx
```

#### 2. Docker 관련 오류
```bash
# Docker 상태 확인
docker info

# 컨테이너 강제 정리
docker-compose -p online-evaluation down --remove-orphans
docker system prune -f

# 재시작
docker-compose -p online-evaluation up --build -d
```

#### 3. 서비스 응답 없음
```bash
# 헬스체크
curl http://localhost:[backend_port]/health

# 상세 로그 확인
docker-compose -p online-evaluation logs --tail=50
```

### 고급 문제 해결

#### 수동 포트 지정
```bash
# 특정 포트로 강제 할당
python -m universal_port_manager.cli --project online-evaluation allocate frontend --preferred-ports '{"frontend": 3005}'
```

#### 백업에서 복원
```bash
# 설정 백업 목록
python -m universal_port_manager.cli --project online-evaluation list-backups

# 특정 백업 복원
python -m universal_port_manager.cli --project online-evaluation restore [backup_name]
```

## 📈 성능 최적화

### 개발 환경
- 컨테이너 리소스: 최소 2GB RAM
- 포트 범위: 3000-4000 (프론트엔드), 8000-9000 (백엔드)

### 프로덕션 환경
- 컨테이너 리소스: 4GB+ RAM 권장
- 모니터링: Prometheus + Grafana 스택 추가
- 로드밸런싱: Nginx 다중 인스턴스

## 🔐 보안 고려사항

### 포트 보안
- Privileged 포트 (1024 미만) 사용 금지
- 방화벽 설정으로 외부 접근 제한
- SSL/TLS 인증서 적용 (프로덕션)

### 컨테이너 보안
- 최소 권한 원칙 적용
- 정기적인 이미지 업데이트
- 보안 스캔 도구 사용

## 📞 지원 및 문의

### 로그 수집
문제 발생 시 다음 정보를 함께 제공해주세요:

1. **시스템 정보**
   ```bash
   python -m universal_port_manager.cli doctor --report
   ```

2. **포트 상태**
   ```bash
   python -m universal_port_manager.cli scan --format json
   ```

3. **Docker 로그**
   ```bash
   docker-compose -p online-evaluation logs --tail=100 > deployment_logs.txt
   ```

### 자동 진단 도구
```bash
# 종합 시스템 진단
python simple_system_validation.py
```

---

## 🎯 Quick Start

가장 빠른 시작 방법:

```bash
# 1. 저장소 클론
git clone [repository_url]
cd Online-evaluation

# 2. 원클릭 배포 실행
python quick-deploy.py

# 3. 웹 브라우저에서 확인
# http://localhost:[할당된_포트] 자동 오픈
```

**🎉 3단계만으로 완전한 온라인 평가 시스템이 실행됩니다!**