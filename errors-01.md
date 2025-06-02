# 온라인 평가 시스템 Docker 환경 구축 - 오류 해결 기록

## 개요
본 문서는 온라인 평가 시스템을 Docker 환경에서 구축하는 과정에서 발생한 주요 오류들과 해결방법을 기록합니다.

**프로젝트**: 온라인 평가 시스템 (중소기업 지원사업 평가 플랫폼)  
**날짜**: 2025년 5월 31일  
**환경**: Windows, Docker Desktop, PowerShell  

---

## 1. Dockerfile 빌드 오류

### 오류 내용
```
invalid reference format: repository name (FROM python:3.11-slim as backend) must be lowercase
```

### 원인
- Dockerfile의 14번 라인에서 `FROM python:3.11-slim as backend`에서 `as`가 소문자로 되어 있음
- Docker에서는 alias 키워드가 대문자여야 함

### 해결방법
```dockerfile
# 수정 전
FROM python:3.11-slim as backend

# 수정 후  
FROM python:3.11-slim AS backend
```

**파일**: `c:\project\Online-evaluation\Dockerfile` 14번 라인

---

## 2. 엔트리포인트 스크립트 실행 오류

### 오류 내용
```
/bin/sh: 1: /entrypoint.sh: not found
```

### 원인
- `entrypoint.sh` 파일이 Windows에서 작성되어 CRLF(`\r\n`) 줄바꿈 문자가 포함됨
- Linux 컨테이너에서는 LF(`\n`)만 인식하므로 스크립트 실행 실패

### 해결방법
Dockerfile에 줄바꿈 문자 변환 명령 추가:
```dockerfile
# entrypoint.sh의 줄바꿈 문자를 Unix 형식으로 변환
RUN sed -i 's/\r$//' /entrypoint.sh
RUN chmod +x /entrypoint.sh
```

**파일**: `c:\project\Online-evaluation\Dockerfile`

---

## 3. 프론트엔드 백엔드 API 연결 오류

### 오류 내용
```
ERR_CONNECTION_REFUSED
net::ERR_CONNECTION_REFUSED at http://localhost:8001/api/auth/login
```

### 시도한 해결방법들

#### 3-1. 첫 번째 시도
- `REACT_APP_BACKEND_URL=http://localhost:8001` 설정
- **결과**: 컨테이너 내부에서 호스트의 localhost에 접근할 수 없어 실패

#### 3-2. 두 번째 시도  
- `REACT_APP_BACKEND_URL=/api` 설정
- **결과**: API 경로가 `/api/api/auth/login`으로 중복되어 404 오류 발생

#### 3-3. 최종 해결방법
- `REACT_APP_BACKEND_URL=""` (빈 문자열) 설정
- **결과**: 같은 도메인의 `/api` 경로로 올바르게 요청됨

**수정된 Docker 빌드 명령**:
```bash
docker build --build-arg FRONTEND_ENV='REACT_APP_BACKEND_URL=""' -t online-evaluation .
```

---

## 4. Nginx 프록시 연결 오류

### 오류 내용
```
connect() failed (111: Connection refused) while connecting to upstream
```

### 원인
- `nginx.conf`에서 `proxy_pass http://localhost:8001`이 IPv6 주소로 해석됨
- Docker 컨테이너 내부에서 IPv6 연결 실패

### 해결방법
```nginx
# 수정 전
proxy_pass http://localhost:8001;

# 수정 후
proxy_pass http://127.0.0.1:8001;
```

**파일**: `c:\project\Online-evaluation\nginx.conf`

---

## 5. MongoDB 연결 오류

### 오류 내용
```
[Errno -3] Temporary failure in name resolution: 'host.docker.internal'
```

### 원인
- Windows Docker Desktop에서 `host.docker.internal`이 제대로 작동하지 않음
- 컨테이너에서 호스트의 MongoDB에 접근할 수 없음

### 해결방법
MongoDB도 컨테이너로 실행하여 Docker 네트워크 내에서 통신하도록 변경

#### docker-compose.yml 생성
```yaml
version: '3.8'

services:
  mongodb:
    image: mongo:latest
    container_name: online-evaluation-mongodb
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: password123
      MONGO_INITDB_DATABASE: online_evaluation
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
    networks:
      - online-evaluation-network

  app:
    build:
      context: .
      args:
        FRONTEND_ENV: 'REACT_APP_BACKEND_URL=""'
    container_name: online-evaluation-app
    environment:
      - MONGO_URL=mongodb://admin:password123@mongodb:27017/online_evaluation?authSource=admin
      - DB_NAME=online_evaluation
    ports:
      - "8080:80"
    depends_on:
      - mongodb
    networks:
      - online-evaluation-network

volumes:
  mongodb_data:

networks:
  online-evaluation-network:
    driver: bridge
```

---

## 6. 시스템 초기화 및 로그인 테스트

### 최종 검증
1. **헬스체크**: `http://localhost:8080/api/health` ✅
2. **시스템 초기화**: `http://localhost:8080/api/init` ✅  
3. **로그인 테스트**: API 및 웹 인터페이스 모두 정상 작동 ✅

### 테스트 계정
- **관리자**: `admin` / `admin123`
- **간사**: `secretary01` / `secretary123`
- **평가위원**: `evaluator01` / `evaluator123`

---

## 실행 명령어 요약

### 1. 프로젝트 백업
```powershell
xcopy c:\project\Online-evaluation c:\project\Online-evaluation_1 /E /H /C /I /Y
```

### 2. Docker Compose로 전체 시스템 실행
```powershell
cd c:\project\Online-evaluation
docker-compose up -d
```

### 3. 상태 확인
```powershell
# 컨테이너 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs app
docker-compose logs mongodb

# 헬스체크
Invoke-WebRequest -Uri http://localhost:8080/api/health
```

### 4. 시스템 중지
```powershell
docker-compose down
```

---

## 주요 학습 사항

1. **Docker 컨테이너 간 통신**: 호스트의 localhost 대신 서비스명 사용
2. **Windows 호환성**: 줄바꿈 문자(CRLF vs LF) 주의
3. **Nginx 프록시**: IPv4 주소 명시로 연결 안정성 확보
4. **React 환경변수**: API URL을 빈 문자열로 설정하여 상대 경로 사용
5. **Docker Compose**: 복잡한 멀티 컨테이너 애플리케이션의 효과적인 관리

---

## 최종 상태
- ✅ Docker 환경에서 완전 동작
- ✅ MongoDB 컨테이너화 완료
- ✅ 프론트엔드-백엔드 통신 정상
- ✅ 사용자 로그인 기능 정상 작동
- ✅ 관리자 대시보드 접근 가능

**접속 URL**: http://localhost:8080
