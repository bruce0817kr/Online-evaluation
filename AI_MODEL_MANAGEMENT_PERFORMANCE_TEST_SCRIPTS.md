# ⚡ AI 모델 관리 시스템 - 성능 및 부하 테스트 스크립트

## 📋 목차

1. [성능 테스트 개요](#성능-테스트-개요)
2. [테스트 스크립트 구조](#테스트-스크립트-구조)
3. [환경 설정](#환경-설정)
4. [부하 테스트 스크립트](#부하-테스트-스크립트)
5. [API 성능 테스트](#api-성능-테스트)
6. [데이터베이스 성능 테스트](#데이터베이스-성능-테스트)
7. [프론트엔드 성능 테스트](#프론트엔드-성능-테스트)
8. [모니터링 및 분석](#모니터링-및-분석)
9. [실행 가이드](#실행-가이드)

---

## 🎯 성능 테스트 개요

### 테스트 목표
```
📊 성능 목표:
- 동시 사용자: 100명 지원
- 평균 응답시간: 2초 이하
- 95% 응답시간: 5초 이하
- 에러율: 1% 이하
- 시스템 가용성: 99.9% 이상

🔍 측정 지표:
- API 응답시간 (Response Time)
- 처리량 (Throughput - RPS)
- 동시 연결수 (Concurrent Users)
- 에러율 (Error Rate)
- 리소스 사용률 (CPU, Memory, Network)
```

### 테스트 도구
```
🛠️ 사용 도구:
- Artillery.js: 부하 테스트 및 API 성능 테스트
- Lighthouse: 프론트엔드 성능 측정
- MongoDB Profiler: 데이터베이스 성능 분석
- Prometheus + Grafana: 실시간 모니터링
- Custom Python Scripts: 커스텀 성능 측정
```

---

## 🏗️ 테스트 스크립트 구조

### 파일 구조
```
performance_tests/
├── artillery/
│   ├── load_test_config.yml          # 부하 테스트 설정
│   ├── api_performance_test.yml      # API 성능 테스트
│   └── stress_test_config.yml        # 스트레스 테스트
├── python/
│   ├── performance_test_runner.py    # 테스트 실행기
│   ├── database_performance.py       # DB 성능 테스트
│   ├── ai_api_performance.py         # AI API 성능 테스트
│   └── resource_monitor.py           # 리소스 모니터링
├── lighthouse/
│   ├── frontend_performance.js       # 프론트엔드 성능 테스트
│   └── lighthouse_config.js          # Lighthouse 설정
├── monitoring/
│   ├── grafana_dashboard.json        # Grafana 대시보드
│   └── prometheus_config.yml         # Prometheus 설정
└── reports/
    ├── generate_report.py             # 리포트 생성기
    └── template.html                  # 리포트 템플릿
```

---

## ⚙️ 환경 설정

### 필수 패키지 설치
```bash
# Node.js 패키지
npm install -g artillery lighthouse

# Python 패키지  
pip install requests asyncio aiohttp psutil matplotlib pandas

# 시스템 모니터링 도구
# Ubuntu/Debian
sudo apt-get install htop iotop nethogs

# macOS
brew install htop
```

### 환경 변수 설정
```bash
# .env.performance 파일 생성
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000
MONGODB_URL=mongodb://localhost:27017/online_evaluation_test
REDIS_URL=redis://localhost:6379

# 테스트 사용자 정보
TEST_ADMIN_EMAIL=admin@test.com
TEST_ADMIN_PASSWORD=testpass123
TEST_SECRETARY_EMAIL=secretary@test.com
TEST_SECRETARY_PASSWORD=testpass123

# AI API 테스트 키 (제한된 토큰)
OPENAI_TEST_API_KEY=sk-test-xxx
ANTHROPIC_TEST_API_KEY=sk-ant-test-xxx
```

---

## 🚀 부하 테스트 스크립트

### Artillery 부하 테스트 설정

#### 기본 부하 테스트 (load_test_config.yml)
```yaml
config:
  target: "{{ $processEnvironment.BACKEND_URL }}"
  phases:
    # 워밍업 단계
    - duration: 300  # 5분
      arrivalRate: 5
      name: "Warm up"
    
    # 점진적 증가
    - duration: 600  # 10분  
      arrivalRate: 10
      rampTo: 50
      name: "Gradual increase"
    
    # 정상 부하
    - duration: 1800 # 30분
      arrivalRate: 50
      name: "Normal load"
    
    # 피크 부하
    - duration: 900  # 15분
      arrivalRate: 100
      name: "Peak load"
    
    # 스트레스 테스트
    - duration: 300  # 5분
      arrivalRate: 150
      name: "Stress test"

  payload:
    path: "./test_data.csv"
    fields:
      - "email"
      - "password"

  defaults:
    headers:
      Content-Type: "application/json"

scenarios:
  # 로그인 시나리오
  - name: "User Login"
    weight: 20
    flow:
      - post:
          url: "/api/auth/login"
          json:
            email: "{{ email }}"
            password: "{{ password }}"
          capture:
            - json: "$.access_token"
              as: "authToken"
      - think: 2

  # 모델 목록 조회
  - name: "Get Models"
    weight: 40
    flow:
      - post:
          url: "/api/auth/login"
          json:
            email: "{{ email }}"
            password: "{{ password }}"
          capture:
            - json: "$.access_token"
              as: "authToken"
      - get:
          url: "/api/ai-models/available"
          headers:
            Authorization: "Bearer {{ authToken }}"
      - think: 1

  # 연결 테스트 실행
  - name: "Connection Test"
    weight: 30
    flow:
      - post:
          url: "/api/auth/login" 
          json:
            email: "{{ email }}"
            password: "{{ password }}"
          capture:
            - json: "$.access_token"
              as: "authToken"
      - post:
          url: "/api/ai-models/test-connection"
          headers:
            Authorization: "Bearer {{ authToken }}"
          json:
            model_id: "openai-gpt35-turbo"
      - think: 5

  # 성능 메트릭 조회
  - name: "Performance Metrics"
    weight: 10
    flow:
      - post:
          url: "/api/auth/login"
          json:
            email: "{{ email }}"
            password: "{{ password }}"
          capture:
            - json: "$.access_token"
              as: "authToken"
      - get:
          url: "/api/ai-models/performance-metrics"
          headers:
            Authorization: "Bearer {{ authToken }}"
      - think: 3
```

### 테스트 데이터 파일 (test_data.csv)
```csv
email,password
admin@test.com,testpass123
secretary@test.com,testpass123
admin2@test.com,testpass123
secretary2@test.com,testpass123
admin3@test.com,testpass123
secretary3@test.com,testpass123
```

---

## 📊 API 성능 테스트

### 상세 API 테스트 설정 (api_performance_test.yml)
```yaml
config:
  target: "{{ $processEnvironment.BACKEND_URL }}"
  phases:
    - duration: 60
      arrivalRate: 20
      name: "API Performance Test"
  
  defaults:
    headers:
      Content-Type: "application/json"

before:
  flow:
    - log: "API Performance Test Starting..."

after:
  flow:
    - log: "API Performance Test Completed"

scenarios:
  # 인증 API 성능
  - name: "Auth API Performance"
    weight: 100
    flow:
      # 로그인 성능 측정
      - post:
          url: "/api/auth/login"
          json:
            email: "admin@test.com"
            password: "testpass123"
          capture:
            - json: "$.access_token"
              as: "authToken"
          afterResponse: "captureMetrics"
      
      # 사용자 정보 조회 성능
      - get:
          url: "/api/auth/me"
          headers:
            Authorization: "Bearer {{ authToken }}"
          afterResponse: "captureMetrics"
      
      # 모델 목록 조회 성능 (인증 필요)
      - get:
          url: "/api/ai-models/available"
          headers:
            Authorization: "Bearer {{ authToken }}"
          afterResponse: "captureMetrics"
      
      # 모델 생성 성능 (관리자만)
      - post:
          url: "/api/ai-models/create"
          headers:
            Authorization: "Bearer {{ authToken }}"
          json:
            model_id: "test-model-{{ $randomString() }}"
            provider: "openai"
            model_name: "gpt-3.5-turbo"
            display_name: "Performance Test Model"
            quality_score: 0.8
            speed_score: 0.9
            cost_efficiency: 0.85
            reliability_score: 0.9
          afterResponse: "captureMetrics"
      
      # 생성된 모델 삭제 (정리)
      - delete:
          url: "/api/ai-models/test-model-{{ $randomString() }}"
          headers:
            Authorization: "Bearer {{ authToken }}"
          ifTrue: "{{ $statusCode == 201 }}" # 생성 성공 시만 삭제
      
      - think: 1

functions:
  captureMetrics: |
    function(requestParams, response, context, ee, next) {
      // 응답시간 기록
      const responseTime = response.timings.response;
      console.log(`API: ${requestParams.url}, Response Time: ${responseTime}ms, Status: ${response.statusCode}`);
      
      // 커스텀 메트릭 기록
      ee.emit('customStat', 'api_response_time', responseTime);
      ee.emit('customStat', 'api_status_code', response.statusCode);
      
      return next();
    }
```

---

## 🐍 Python 성능 테스트 러너

다음으로 Python 기반의 성능 테스트 스크립트들을 작성하겠습니다. 파일이 길어지므로 개별 파일로 나누어 생성하겠습니다.

먼저 메인 성능 테스트 러너를 생성하겠습니다:
