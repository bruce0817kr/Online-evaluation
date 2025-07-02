# 🎯 사용자별 시나리오 테스트 가이드

MCP 기반 사용자별 시나리오 테스트 시스템 완전 가이드

## 📋 목차

1. [시스템 개요](#시스템-개요)
2. [설치 및 설정](#설치-및-설정)
3. [사용자 시나리오 구조](#사용자-시나리오-구조)
4. [테스트 실행 방법](#테스트-실행-방법)
5. [실시간 대시보드 사용법](#실시간-대시보드-사용법)
6. [고급 기능](#고급-기능)
7. [문제 해결](#문제-해결)

## 🚀 시스템 개요

### 주요 특징

- **사용자 역할별 시나리오**: 관리자, 간사, 평가위원별 맞춤 테스트
- **MCP 활용**: Model Context Protocol을 통한 지능형 테스트 실행
- **실시간 모니터링**: 웹 기반 대시보드로 실시간 테스트 현황 확인
- **교차 역할 통합**: 다중 사용자 환경에서의 협업 시나리오 테스트
- **자동화된 보고서**: 종합적인 테스트 결과 및 개선 권고사항 제공

### 시스템 구성

```
tests/
├── scenarios/                    # 시나리오 정의 파일들
│   ├── admin-scenarios.yml      # 관리자 시나리오
│   ├── secretary-scenarios.yml  # 간사 시나리오
│   ├── evaluator-scenarios.yml  # 평가위원 시나리오
│   └── cross-role-scenarios.yml # 교차 역할 시나리오
├── scenario-data/               # 테스트 데이터
│   ├── test-accounts.json       # 테스트 계정 정보
│   ├── sample-companies.json    # 샘플 회사 데이터
│   └── evaluation-templates.json # 평가 템플릿
├── mcp_scenario_runner.py       # 메인 시나리오 실행기
├── cross_role_integration_tester.py # 교차 역할 테스트
├── scenario_test_executor.py    # 테스트 실행 조정기
├── scenario_dashboard.html      # 실시간 대시보드
└── results/                     # 테스트 결과
    ├── screenshots/             # 스크린샷
    ├── videos/                  # 실행 비디오
    └── reports/                 # 보고서
```

## ⚙️ 설치 및 설정

### 필수 요구사항

```bash
# Python 3.8 이상
# Node.js 14 이상 (프론트엔드 실행용)

# Python 패키지 설치
pip install playwright pyyaml aiofiles websockets psutil

# Playwright 브라우저 설치
playwright install
```

### 환경 설정

1. **프로젝트 루트에서 실행**:
```bash
cd /mnt/c/Project/Online-evaluation
```

2. **테스트 계정 생성**:
```bash
# 백엔드 서버 시작
cd backend
python -m uvicorn server:app --reload --port 8002

# 프론트엔드 서버 시작 (별도 터미널)
cd frontend
npm start
```

3. **테스트 데이터 확인**:
```bash
# 테스트 계정이 데이터베이스에 있는지 확인
python scripts/create_test_accounts.py
```

## 🎭 사용자 시나리오 구조

### 관리자 (Admin) 시나리오

```yaml
# admin-scenarios.yml 예시
- id: "admin_initial_setup"
  name: "시스템 초기 설정"
  steps:
    - action: "login"
      data: {"email": "admin@company.com"}
    - action: "configure_ai_providers"
      data: {"provider": "OpenAI", "model": "gpt-4"}
    - action: "create_company"
      data: {"name": "테스트회사A"}
```

### 간사 (Secretary) 시나리오

```yaml
# secretary-scenarios.yml 예시
- id: "secretary_project_creation"
  name: "프로젝트 생성 및 관리"
  steps:
    - action: "create_project"
      data: {"name": "2024 평가 프로젝트"}
    - action: "assign_evaluators"
      data: {"evaluators": ["eval1", "eval2"]}
```

### 평가위원 (Evaluator) 시나리오

```yaml
# evaluator-scenarios.yml 예시
- id: "evaluator_ai_evaluation"
  name: "AI 도움 평가 수행"
  steps:
    - action: "ai_assistant_interaction"
      data: {"prompt": "이 회사를 평가해주세요"}
    - action: "conduct_evaluation"
      data: {"scores": {"기술혁신성": 8}}
```

## 🎮 테스트 실행 방법

### 1. 단일 시나리오 실행

```bash
# 특정 시나리오 실행
python tests/mcp_scenario_runner.py --scenario admin_initial_setup --role admin

# 평가위원 AI 평가 시나리오
python tests/mcp_scenario_runner.py --scenario evaluator_ai_evaluation --role evaluator
```

### 2. 모든 시나리오 실행

```bash
# 모든 주요 시나리오 자동 실행
python tests/mcp_scenario_runner.py --all
```

### 3. 교차 역할 통합 테스트

```bash
# 다중 사용자 통합 테스트
python tests/cross_role_integration_tester.py
```

### 4. 실시간 대시보드와 함께 실행

```bash
# 대시보드 서버 시작
python tests/scenario_test_executor.py --port 8765

# 브라우저에서 접속
open http://localhost:8765
```

## 📊 실시간 대시보드 사용법

### 대시보드 접속

```bash
# 대시보드 서버 시작
python tests/scenario_test_executor.py

# 브라우저에서 http://localhost:8765 접속
```

### 주요 기능

#### 1. 테스트 제어
- **전체 시나리오 실행**: 모든 시나리오 일괄 실행
- **선택 시나리오 실행**: 드롭다운에서 특정 시나리오 선택 실행
- **테스트 일시정지/중지**: 실행 중인 테스트 제어

#### 2. 실시간 모니터링
- **시나리오 진행 상황**: 각 시나리오별 실시간 진행률
- **사용자 세션**: 활성 사용자 및 현재 활동 모니터링
- **성능 메트릭**: 응답 시간, 오류율, 처리량 실시간 추적

#### 3. 키보드 단축키
- `Ctrl + R`: 모든 시나리오 실행
- `Ctrl + P`: 테스트 일시정지
- `Ctrl + S`: 모든 테스트 중지

### 대시보드 화면 구성

```
┌─────────────────────────────────────────────┐
│  🚀 실시간 시나리오 테스트 대시보드           │
├─────────────────────────────────────────────┤
│  [12] 총 시나리오  [3] 실행중  [87%] 성공률  │
├─────────────────────────────────────────────┤
│  📊 테스트 제어                              │
│  [전체실행] [선택실행] [일시정지] [중지]      │
├──────────────────┬──────────────────────────┤
│  📋 시나리오 상태  │  👥 사용자 세션          │
│  ✅ 관리자 설정    │  🟢 김관리 (Admin)      │
│  🔄 간사 프로젝트  │  🟢 박간사 (Secretary)  │
│  🔄 평가위원 평가  │  🟡 이평가 (Evaluator)  │
├──────────────────┴──────────────────────────┤
│  📊 실시간 로그 및 성능 메트릭                │
│  [14:23:45] Admin 로그인 성공                │
│  [14:24:02] Secretary 프로젝트 생성 시작      │
└─────────────────────────────────────────────┘
```

## 🔧 고급 기능

### 1. 커스텀 시나리오 작성

새로운 시나리오를 추가하려면:

```yaml
# tests/scenarios/custom-scenarios.yml
scenarios:
  - id: "custom_workflow"
    name: "커스텀 워크플로우"
    priority: "high"
    steps:
      - action: "custom_action"
        description: "커스텀 액션 설명"
        data:
          param1: "value1"
          param2: "value2"
        expected: "예상 결과"
```

### 2. 테스트 데이터 확장

```json
// tests/scenario-data/custom-data.json
{
  "custom_companies": [
    {
      "id": "custom_company_001",
      "name": "커스텀 회사",
      "industry": "맞춤 업종"
    }
  ]
}
```

### 3. 성능 최적화 설정

```python
# tests/performance_config.py
PERFORMANCE_SETTINGS = {
    "parallel_users": 10,
    "timeout_seconds": 60,
    "retry_count": 3,
    "screenshot_quality": "high",
    "video_recording": True
}
```

### 4. 알림 설정

```python
# tests/notification_config.py
NOTIFICATION_SETTINGS = {
    "email_alerts": True,
    "slack_webhook": "https://hooks.slack.com/...",
    "teams_webhook": "https://outlook.office.com/...",
    "alert_on_failure": True,
    "alert_on_completion": True
}
```

## 📈 보고서 분석

### 자동 생성 보고서

실행 완료 후 다음 보고서들이 자동 생성됩니다:

1. **JSON 보고서**: `tests/results/comprehensive_scenario_report_YYYYMMDD_HHMMSS.json`
2. **HTML 보고서**: `tests/results/comprehensive_scenario_report_YYYYMMDD_HHMMSS.html`
3. **스크린샷**: `tests/results/screenshots/`
4. **실행 비디오**: `tests/results/videos/`

### 보고서 내용

```json
{
  "test_summary": {
    "total_scenarios": 12,
    "success_rate": 87.5,
    "execution_duration": 245.6,
    "timestamp": "2024-06-28T14:30:00"
  },
  "scenario_results": [...],
  "performance_metrics": {
    "avg_response_time": 234.5,
    "error_rate": 2.1,
    "throughput": 89.3
  },
  "recommendations": [
    "시나리오 성공률 개선 필요",
    "응답 시간 최적화 권장"
  ]
}
```

## 🔍 문제 해결

### 일반적인 문제

#### 1. 브라우저 실행 오류
```bash
# 해결방법: Playwright 브라우저 재설치
playwright install --force
```

#### 2. 포트 충돌
```bash
# 해결방법: 포트 변경
python tests/scenario_test_executor.py --port 8766
```

#### 3. 로그인 실패
```bash
# 해결방법: 테스트 계정 확인 및 재생성
python scripts/create_test_accounts.py --reset
```

#### 4. 메모리 부족
```bash
# 해결방법: 병렬 실행 수 줄이기
# mcp_scenario_runner.py에서 workers 수 조정
```

### 디버그 모드

```bash
# 상세 로그와 함께 실행
python tests/mcp_scenario_runner.py --scenario admin_setup --role admin --debug

# 브라우저 헤드리스 모드 비활성화 (화면 보기)
python tests/mcp_scenario_runner.py --headed --slow-mo 1000
```

### 로그 분석

```bash
# 실시간 로그 확인
tail -f tests/results/scenario_test_runner.log

# 오류 로그만 필터링
grep ERROR tests/results/scenario_test_runner.log
```

## 🚀 베스트 프랙티스

### 1. 시나리오 설계 원칙

- **단일 책임**: 각 시나리오는 하나의 주요 기능만 테스트
- **독립성**: 시나리오 간 의존성 최소화
- **재사용성**: 공통 액션은 재사용 가능하게 설계
- **명확성**: 시나리오 이름과 설명을 명확하게 작성

### 2. 테스트 데이터 관리

- **현실적 데이터**: 실제 사용 환경과 유사한 테스트 데이터 사용
- **다양성**: 다양한 시나리오를 커버할 수 있는 데이터셋 구성
- **보안**: 실제 사용자 데이터 사용 금지, 테스트 전용 데이터만 사용

### 3. 성능 최적화

- **병렬 실행**: 독립적인 시나리오는 병렬로 실행
- **리소스 모니터링**: CPU, 메모리 사용량 지속적 모니터링
- **점진적 부하 증가**: 동시 사용자 수를 점진적으로 증가

### 4. 유지보수

- **정기적 업데이트**: 애플리케이션 변경사항에 맞춰 시나리오 업데이트
- **결과 분석**: 테스트 결과를 정기적으로 분석하여 개선점 도출
- **문서화**: 새로운 시나리오나 변경사항은 즉시 문서화

## 📞 지원 및 문의

### 기술 지원

- **이슈 리포팅**: GitHub Issues를 통한 버그 신고
- **기능 요청**: Feature Request 템플릿 사용
- **문서 개선**: Documentation Pull Request 환영

### 커뮤니티

- **토론**: GitHub Discussions에서 질문 및 토론
- **업데이트**: Release Notes를 통한 최신 변경사항 확인

---

## 📝 변경 이력

### v1.0.0 (2024-06-28)
- 초기 버전 릴리스
- 기본 시나리오 테스트 시스템 구현
- 실시간 대시보드 추가
- 교차 역할 통합 테스트 지원

---

*이 가이드는 지속적으로 업데이트됩니다. 최신 버전은 프로젝트 저장소에서 확인하세요.*