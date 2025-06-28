# Universal Port Manager (UPM) 🚀

여러 프로젝트 간 포트 충돌을 방지하고 자동으로 포트를 할당하는 범용 포트 관리 시스템

## 🎯 주요 특징

### 핵심 기능
- **🔍 지능형 포트 스캔**: 시스템, Docker 컨테이너, 프로세스 포트 분석
- **🎲 자동 포트 할당**: 서비스 타입별 포트 범위에서 충돌 방지 할당
- **📦 프로젝트 그룹 관리**: 프로젝트별 포트 그룹화 및 영속화
- **🐳 Docker 통합**: Docker Compose 파일 자동 생성
- **⚙️ 설정 파일 생성**: .env, bash, python, json 형식 지원
- **🌐 전역/로컬 모드**: 시스템 전역 또는 프로젝트 로컬 관리

### 해결하는 문제
- **newsscout**와 **online-evaluation** 같은 여러 프로젝트 동시 실행 시 포트 충돌
- 개발자가 수동으로 포트를 관리하는 번거로움
- Docker Compose 포트 설정의 복잡성
- 프로젝트 간 포트 정보 공유 부족

## 🚀 빠른 시작

### 1. 기본 사용법

```python
from universal_port_manager import PortManager

# 프로젝트별 포트 매니저 생성
pm = PortManager(project_name="my-awesome-project")

# 서비스에 포트 할당
ports = pm.allocate_services(['frontend', 'backend', 'mongodb', 'redis'])
print(ports)
# {
#   'frontend': AllocatedPort(port=3000, service_type='frontend', ...),
#   'backend': AllocatedPort(port=8080, service_type='backend', ...),
#   'mongodb': AllocatedPort(port=27017, service_type='mongodb', ...),
#   'redis': AllocatedPort(port=6379, service_type='redis', ...)
# }

# Docker Compose 및 환경 파일 생성
pm.generate_all_configs()

# 서비스 시작
pm.start_services()
```

### 2. CLI 사용법

```bash
# 포트 스캔
python -m universal_port_manager.cli scan --range 3000-9999

# 서비스 포트 할당
python -m universal_port_manager.cli allocate frontend backend mongodb --project my-project

# Docker Compose 생성
python -m universal_port_manager.cli generate --project my-project

# 서비스 시작
python -m universal_port_manager.cli start --project my-project

# 상태 확인
python -m universal_port_manager.cli status --project my-project
```

### 3. 템플릿 사용

```python
# 미리 정의된 템플릿 사용
pm = PortManager(project_name="fullstack-app")
ports = pm.allocate_from_template('fullstack-react-fastapi')
pm.generate_all_configs()
```

## 📋 지원하는 서비스 타입

### Frontend Services
- **react**: React 개발 서버 (기본 포트: 3000)
- **vue**: Vue.js 개발 서버 (기본 포트: 8080)
- **angular**: Angular 개발 서버 (기본 포트: 4200)
- **nextjs**: Next.js 애플리케이션 (기본 포트: 3000)

### Backend Services
- **fastapi**: FastAPI 서버 (기본 포트: 8000)
- **express**: Express.js 서버 (기본 포트: 3000)
- **django**: Django 서버 (기본 포트: 8000)
- **flask**: Flask 서버 (기본 포트: 5000)

### Database Services
- **mongodb**: MongoDB (기본 포트: 27017)
- **postgresql**: PostgreSQL (기본 포트: 5432)
- **mysql**: MySQL (기본 포트: 3306)
- **redis**: Redis (기본 포트: 6379)

### 기타 Services
- **elasticsearch**: Elasticsearch (기본 포트: 9200)
- **nginx**: Nginx (기본 포트: 80)
- **prometheus**: Prometheus (기본 포트: 9090)
- **grafana**: Grafana (기본 포트: 3000)

## 🔧 고급 사용법

### 1. 프로젝트 자동 감지

```python
pm = PortManager(project_name="detected-project")

# 프로젝트 디렉토리에서 자동으로 서비스 감지
# package.json, requirements.txt, docker-compose.yml 등 분석
ports = pm.allocate_services([], auto_detect=True)
```

### 2. 선호 포트 지정

```python
pm = PortManager(project_name="custom-ports")

preferred_ports = {
    'frontend': 3001,
    'backend': 8081,
    'mongodb': 27018
}

ports = pm.allocate_services(
    ['frontend', 'backend', 'mongodb'],
    preferred_ports=preferred_ports
)
```

### 3. 충돌 검사 및 해결

```python
pm = PortManager(project_name="conflict-check")

# 현재 할당된 포트의 충돌 검사
conflicts = pm.check_conflicts()

if conflicts:
    print("포트 충돌 감지:")
    for port, info in conflicts.items():
        print(f"  포트 {port}: {info.description}")
    
    # 자동으로 다른 포트 재할당
    pm.release_services()
    new_ports = pm.allocate_services(['frontend', 'backend'])
```

### 4. 전역 vs 로컬 모드

```python
# 전역 모드: 시스템 전역에서 포트 관리 (~/.port-manager/)
pm_global = PortManager(
    project_name="global-project", 
    global_mode=True
)

# 로컬 모드: 프로젝트 디렉토리에서만 관리 (./.port-manager/)
pm_local = PortManager(
    project_name="local-project", 
    global_mode=False
)
```

## 📁 생성되는 파일들

포트 매니저가 자동으로 생성하는 파일들:

```
project-directory/
├── docker-compose.yml          # 메인 Docker Compose 파일
├── docker-compose.override.yml # 개발환경용 오버라이드
├── .env                        # Docker 환경변수
├── set_ports.sh               # Bash 환경변수 스크립트
├── port_config.py             # Python 포트 설정
├── ports.json                 # JSON 포트 설정
├── start.sh                   # 시작 스크립트
└── .port-manager/             # 포트 매니저 설정 디렉토리
    ├── port_allocations.json  # 포트 할당 기록
    └── service_types.json     # 서비스 타입 정의
```

## 🌟 실제 사용 예시

### 시나리오: newsscout와 online-evaluation 동시 실행

```python
# newsscout 프로젝트
newsscout_pm = PortManager(project_name="newsscout")
newsscout_ports = newsscout_pm.allocate_services([
    'frontend', 'backend', 'postgresql', 'redis'
])
# 결과: frontend=3000, backend=8000, postgresql=5432, redis=6379

# online-evaluation 프로젝트  
evaluation_pm = PortManager(project_name="online-evaluation")
evaluation_ports = evaluation_pm.allocate_services([
    'frontend', 'backend', 'mongodb', 'redis'
])
# 결과: frontend=3001, backend=8001, mongodb=27017, redis=6380 (자동 충돌 회피)

# 두 프로젝트 모두 동시 실행 가능!
newsscout_pm.generate_all_configs()
evaluation_pm.generate_all_configs()

newsscout_pm.start_services()
evaluation_pm.start_services()
```

### 시나리오: CI/CD 파이프라인 통합

```yaml
# .github/workflows/deploy.yml
- name: 포트 할당 및 배포
  run: |
    python -c "
    from universal_port_manager import PortManager
    pm = PortManager(project_name='${{ github.repository }}')
    pm.allocate_services(['frontend', 'backend', 'database'])
    pm.generate_all_configs()
    "
    docker-compose up -d
```

## 🎯 AI 코더를 위한 통합 가이드

### 1. 새 프로젝트 시작 시

```python
# 1단계: 포트 매니저 초기화
from universal_port_manager import PortManager

pm = PortManager(project_name="new-project")

# 2단계: 프로젝트 구조 자동 감지 또는 수동 정의
services = ['frontend', 'backend', 'mongodb']  # 또는 auto_detect=True

# 3단계: 포트 할당
ports = pm.allocate_services(services)

# 4단계: 모든 설정 파일 생성
pm.generate_all_configs()

# 5단계: 개발 시작!
pm.start_services()
```

### 2. 기존 프로젝트에 통합

```python
# 기존 docker-compose.yml 백업
import shutil
shutil.copy('docker-compose.yml', 'docker-compose.yml.backup')

# 포트 매니저로 마이그레이션
pm = PortManager(project_name="existing-project")
pm.allocate_services([], auto_detect=True)  # 기존 설정 자동 감지
pm.generate_all_configs()
```

### 3. 다른 개발자와 협업

```python
# 개발자 A
pm_a = PortManager(project_name="shared-project", global_mode=True)
ports_a = pm_a.allocate_services(['frontend', 'backend'])

# 개발자 B (같은 시스템)
pm_b = PortManager(project_name="shared-project", global_mode=True) 
ports_b = pm_b.get_allocated_ports()  # A가 할당한 포트 정보 공유

# 또는 프로젝트별 독립 실행
pm_b = PortManager(project_name="shared-project-dev-b")
ports_b = pm_b.allocate_services(['frontend', 'backend'])  # 자동으로 다른 포트 할당
```

## 🛠️ 설치 및 설정

### 의존성 설치

```bash
pip install click psutil pyyaml
```

### 환경 설정

```python
# 전역 설정 디렉토리: ~/.port-manager/
# 로컬 설정 디렉토리: {project}/.port-manager/

# 커스텀 설정 디렉토리 사용
pm = PortManager(
    project_name="custom-config",
    config_dir="/custom/path/.port-manager"
)
```

## 🔍 트러블슈팅

### 일반적인 문제들

#### 1. 포트가 이미 사용 중일 때
```python
# 충돌 확인
conflicts = pm.check_conflicts()
if conflicts:
    # 자동 해결: 다른 포트로 재할당
    pm.release_services()
    new_ports = pm.allocate_services(['frontend', 'backend'])
```

#### 2. Docker 컨테이너 포트 충돌
```bash
# 실행 중인 컨테이너 확인
docker ps

# 불필요한 컨테이너 중지
docker-compose down

# 포트 매니저로 재시작
python -m universal_port_manager.cli start --project my-project
```

#### 3. 권한 오류 (포트 80, 443 등)
```python
# 높은 번호 포트 사용
pm = PortManager(
    project_name="safe-ports",
    scan_range=(3000, 9999)  # 안전한 포트 범위
)
```

### 디버깅 모드

```python
import logging
logging.basicConfig(level=logging.INFO)

pm = PortManager(project_name="debug-project")
# 상세한 로그 출력으로 문제 파악
```

## 🤝 다른 프로젝트에 통합하기

### 1. 라이브러리로 사용

```python
# requirements.txt에 추가
# git+https://github.com/your-repo/universal-port-manager.git

from universal_port_manager import PortManager

def setup_development_environment():
    pm = PortManager(project_name="my-framework")
    ports = pm.allocate_services(['frontend', 'backend', 'database'])
    pm.generate_all_configs()
    return ports
```

### 2. 서브모듈로 사용

```bash
# Git 서브모듈 추가
git submodule add https://github.com/your-repo/universal-port-manager.git tools/port-manager

# 사용
cd tools/port-manager
python cli.py allocate frontend backend --project parent-project
```

### 3. Docker 컨테이너로 사용

```dockerfile
FROM python:3.11-slim

COPY universal_port_manager /app/port_manager
WORKDIR /app

RUN pip install click psutil pyyaml

ENTRYPOINT ["python", "-m", "port_manager.cli"]
```

```bash
# 컨테이너로 실행
docker run --rm -v $(pwd):/workspace port-manager allocate frontend backend
```

## 📊 성능 및 확장성

### 포트 스캔 성능
- **범위**: 1000-65535 포트 스캔 시 약 2-3초
- **캐싱**: 스캔 결과 메모리 캐싱으로 반복 호출 시 즉시 응답
- **Docker 통합**: Docker API 직접 연동으로 빠른 컨테이너 포트 분석

### 메모리 사용량
- **기본**: 10-20MB (포트 스캔 정보 포함)
- **대규모**: 1000개 프로젝트 관리 시 50MB 이하

### 동시성
- **멀티 프로젝트**: 동시에 여러 프로젝트 포트 관리 지원
- **파일 락**: 설정 파일 동시 접근 시 안전성 보장

## 🔮 로드맵

### v1.1 (진행 중)
- [ ] GUI 인터페이스 (웹 기반)
- [ ] Kubernetes 포트 관리 지원
- [ ] 포트 사용량 통계 및 모니터링

### v1.2 (계획)
- [ ] 클라우드 환경 지원 (AWS, GCP, Azure)
- [ ] 팀 협업 기능 (포트 예약, 공유)
- [ ] API 서버 모드

### v2.0 (장기)
- [ ] 네트워크 토폴로지 자동 관리
- [ ] 로드 밸런싱 포트 관리
- [ ] 마이크로서비스 포트 오케스트레이션

## 📄 라이선스

MIT License - 자유롭게 사용, 수정, 배포 가능

## 🤝 기여하기

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)  
5. Open a Pull Request

## 💬 지원 및 문의

- **Issues**: GitHub Issues를 통한 버그 리포트 및 기능 요청
- **Wiki**: 상세한 사용법 및 예제
- **Discussions**: 커뮤니티 질문 및 아이디어 공유

---

**Universal Port Manager**로 포트 충돌 걱정 없는 개발 환경을 만들어보세요! 🚀