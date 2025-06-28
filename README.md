# 🏢 중소기업 지원사업 온라인 평가 시스템

**SME Support Program Online Evaluation System**

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/your-repo/online-evaluation)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://python.org)
[![React](https://img.shields.io/badge/react-18+-blue.svg)](https://reactjs.org)
[![Docker](https://img.shields.io/badge/docker-ready-green.svg)](https://docker.com)

---

## 📋 목차

- [🎯 프로젝트 개요](#-프로젝트-개요)
- [✨ 주요 기능](#-주요-기능)
- [🏗️ 시스템 아키텍처](#️-시스템-아키텍처)
- [🚀 빠른 시작](#-빠른-시작)
- [🔧 설치 및 설정](#-설치-및-설정)
- [🤖 AI 공급자 관리](#-ai-공급자-관리)
- [📊 Excel 대량 업로드](#-excel-대량-업로드)
- [📁 프로젝트 구조](#-프로젝트-구조)
- [🔒 보안 기능](#-보안-기능)
- [📈 모니터링](#-모니터링)
- [🛠️ 개발 가이드](#️-개발-가이드)
- [🐛 문제 해결](#-문제-해결)
- [📚 API 문서](#-api-문서)

---

## 🎯 프로젝트 개요

중소기업 지원사업을 담당하는 **공공기관**을 위한 **온라인 평가 시스템**입니다. 체계적이고 투명한 평가 프로세스를 통해 중소기업의 성장을 지원합니다.

### 🎪 핵심 특징

- **🏛️ 공공기관 특화**: 중소기업 지원사업 평가 전문
- **👥 역할 기반 권한**: 관리자, 서기, 평가위원 3단계 권한
- **🤖 AI 분석 지원**: 다중 AI 공급자 통합 (OpenAI, Claude, Gemini, Groq)
- **📊 Excel 대량 처리**: 기업 정보 일괄 업로드 및 평가서 추출
- **🔒 보안 강화**: 파일 암호화, 워터마크, 접근 제어
- **📱 반응형 UI**: 모바일부터 데스크톱까지 완벽 지원

---

## ✨ 주요 기능

### 👥 사용자 관리
- **관리자 (Admin)**: 시스템 전체 관리, 사용자 승인, AI 설정
- **서기 (Secretary)**: 프로젝트 생성, 기업 등록, 평가 배정
- **평가위원 (Evaluator)**: 평가 수행, 의견 작성

### 📝 평가 관리
- **템플릿 관리**: 다양한 평가 기준 설정 (디지털전환, 스마트팩토리, R&D 등)
- **평가 배정**: 자동/수동 평가위원 배정
- **진행 추적**: 실시간 평가 진행상황 모니터링
- **결과 출력**: PDF/Excel 형태 평가서 생성

### 🤖 AI 분석 기능
- **문서 분석**: 사업계획서 자동 분석 및 평가
- **점수 제안**: AI 기반 평가 점수 추천
- **표절 검사**: 기존 문서와의 유사도 분석
- **정보 추출**: 핵심 정보 자동 추출

### 📊 데이터 관리
- **Excel 일괄 업로드**: 기업 정보 대량 등록
- **데이터 내보내기**: 평가 결과 Excel/PDF 추출
- **통계 분석**: 평가 결과 통계 및 시각화

---

## 🏗️ 시스템 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React.js      │    │   FastAPI       │    │   MongoDB       │
│   Frontend      │◄──►│   Backend       │◄──►│   Database      │
│   (Port 3001)   │    │   (Port 8080)   │    │   (Port 27017)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │              ┌─────────────────┐
         │                       │              │   Redis Cache   │
         │                       └─────────────►│   (Port 6379)   │
         │                                      └─────────────────┘
         │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx Proxy   │    │   AI Services   │    │   File Storage  │
│   (Port 80/443) │    │   Multi-Provider│    │   /uploads      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 기술 스택

**Frontend**
- React.js 18+ with Hooks
- Material-UI / TailwindCSS
- Axios for API communication

**Backend**
- FastAPI (Python 3.9+)
- Motor (Async MongoDB driver)
- JWT Authentication
- OpenAPI 3.0 (Swagger)

**Database**
- MongoDB 7.x (Primary database)
- Redis 7.x (Caching & Sessions)

**Infrastructure**
- Docker & Docker Compose
- Nginx (Reverse proxy)
- Ubuntu/CentOS compatible

---

## 🚀 빠른 시작

### 전제 조건
- Docker 20.10+
- Docker Compose 2.0+
- 16GB RAM 권장
- 20GB 이상 디스크 공간

### 1분 설치

```bash
# 1. 저장소 클론
git clone https://github.com/your-repo/online-evaluation.git
cd online-evaluation

# 2. 환경 설정
cp .env.example .env

# 3. 배포 스크립트 실행 (권장)
chmod +x deploy_with_dependencies.sh
./deploy_with_dependencies.sh development

# 또는 기존 방식
docker-compose up --build -d
```

### 접속 정보
- **🌐 프론트엔드**: http://localhost:3001
- **🔧 백엔드 API**: http://localhost:8080
- **📚 API 문서**: http://localhost:8080/docs
- **🏥 헬스체크**: http://localhost:8080/health

### 기본 관리자 계정
- **사용자명**: `admin`
- **비밀번호**: `admin123`

---

## 🔧 설치 및 설정

### 개발 환경 설정

```bash
# 백엔드 설정
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 프론트엔드 설정
cd frontend
npm install
npm start
```

### 환경 변수 설정

```bash
# .env 파일 주요 설정
MONGO_URL=mongodb://admin:password123@mongodb:27017/online_evaluation?authSource=admin
REDIS_URL=redis://redis:6379
JWT_SECRET=your-super-secret-key-change-in-production
CORS_ORIGINS=http://localhost:3001,http://frontend:3000

# AI 공급자 설정 (선택사항 - 필요한 것만 설정)
OPENAI_API_KEY=your_openai_key          # ChatGPT 모델용
ANTHROPIC_API_KEY=your_claude_key       # Claude 모델용
GOOGLE_API_KEY=your_gemini_key          # Gemini 모델용
GROQ_API_KEY=your_groq_key              # Groq (Llama3 등) 모델용
DEEPSEEK_API_KEY=your_deepseek_key      # DeepSeek 모델용
MINIMAX_API_KEY=your_minimax_key        # MiniMax 모델용

# 추가 AI 공급자들 (선택사항)
TOGETHER_API_KEY=your_together_key      # Together AI
PERPLEXITY_API_KEY=your_perplexity_key  # Perplexity AI
MISTRAL_API_KEY=your_mistral_key        # Mistral AI
COHERE_API_KEY=your_cohere_key          # Cohere
```

---

## 🤖 AI 공급자 관리

### Groq 다중 모델 지원

**질문**: *"AI 공급자인 Groq의 경우 하나의 API로 다양한 LLM 모델을 사용할 수 있는데, 우리 프로젝트에서는 어떻게 적용되고 있지?"*

우리 시스템은 **Groq의 다중 모델 API**를 완벽하게 지원합니다:

#### 🔧 구현 방식

**1. Groq 클라이언트 생성 (`ai_service_enhanced.py:176-180`)**
```python
elif provider_name == "groq" and HAS_OPENAI:
    return openai.AsyncOpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1"  # Groq API 엔드포인트
    )
```

**2. 다양한 모델 지원 (`ai_service_enhanced.py:322-332`)**
```python
async def _analyze_with_groq(self, client, document_text: str, document_type: str, config: Dict):
    response = await client.chat.completions.create(
        model="llama3-70b-8192",  # 기본 모델
        # 다른 지원 모델들:
        # "llama3-8b-8192"
        # "mixtral-8x7b-32768"
        # "gemma-7b-it"
        messages=[...],
        temperature=config["temperature"],
        max_tokens=min(config["max_tokens"], 1500)
    )
```

#### 🎯 관리자 설정 방법

1. **관리자 로그인** → **AI 관리** 메뉴
2. **AI 공급자 추가** 버튼 클릭
3. Groq 설정:
   ```
   공급자명: groq
   표시명: Groq (Llama3-70B)
   API 키: your_groq_api_key
   기본 모델: llama3-70b-8192
   최대 토큰: 8192
   온도: 0.3
   우선순위: 1-10
   ```

#### 📈 지원 모델 목록 및 비용 분석

| 모델명 | 속도(토큰/초) | Blended 비용 | 컨텍스트 | 특징/용도 |
|-------|-------------|-------------|----------|-----------|
| **⚡ 초고속 저비용 (Groq)** ||||
| `llama3.1-8b-instant` | 750-1,250 | $0.13/1M | 8K-128K | ⚡ 초고속, 최저비용, 실시간 처리 |
| `qwq-32b-preview` | 400 | $0.68/1M | 128K | 🔧 툴 사용, step-by-step 최적화 |
| `gemma2-9b-it` | 500 | $0.40/1M | 8K | ⚖️ 균형잡힌 성능, 실용적 |
| **🎯 고성능 분석 (OpenAI)** ||||
| `gpt-4o-mini` | ~100 | $0.60/1M | 128K | 💰 비용효율적, 고품질 |
| `gpt-4o` | ~80 | $5.00/1M | 128K | 🏆 최신 성능, 멀티모달 |
| `gpt-3.5-turbo` | ~150 | $1.00/1M | 16K | 🚀 빠른 처리, 범용적 |
| **🧠 논리적 분석 (DeepSeek)** ||||
| `deepseek-chat` | ~50 | $0.27/1M | 32K | 🧠 논리적 사고, 저비용 |
| `deepseek-coder` | ~50 | $0.27/1M | 32K | 💻 코드/구조 분석 특화 |
| **📚 장문 특화 (MiniMax)** ||||
| `minimax-text-01` | 34 | $0.42/1M | 1M | 📚 초대용량 컨텍스트 |
| `minimax-m1-40k` | 28 | $0.82/1M | 1M | 🎓 고지능, 복잡한 reasoning |
| **🎨 전문 분야** ||||
| `claude-3-5-haiku` | ~60 | $1.00/1M | 200K | ⚡ 빠른 Claude, 효율적 |
| `claude-3-5-sonnet` | ~50 | $3.00/1M | 200K | 🎯 균형잡힌 Claude |
| `gemini-1.5-flash` | ~100 | $0.35/1M | 1M | ⚡ 구글 고속 모델 |
| `mistral-small` | ~80 | $1.00/1M | 32K | 🇫🇷 유럽산, 효율적 |

#### 💡 비용효율 분석 및 추천

**🏆 최고 비용효율**: `llama3.1-8b-instant`
- 최저 비용($0.13/1M) + 최고 속도(1,250 tps)
- **용도**: 실시간 문서 분석, 대량 처리, 빠른 응답 필요한 작업

**🎯 균형잡힌 선택**: `qwq-32b-preview`
- 중간 비용($0.68/1M) + 우수한 속도(400 tps)
- **용도**: 평가 점수 제안, 복잡한 분석, 툴 사용 작업

**📚 장문 특화**: `minimax-text-01`
- 저렴한 비용($0.42/1M) + 1M 토큰 컨텍스트
- **용도**: 대용량 사업계획서 분석, 종합 보고서 생성

**🚀 최고 성능**: `llama3.3-70b-versatile`
- 고성능 + 안정성, 비용은 높음($1.38/1M)
- **용도**: 정확도가 중요한 최종 평가, 심층 분석

#### 🔄 스마트 모델 선택 로직

```python
def select_optimal_model(document_length: int, analysis_type: str, budget_priority: str) -> str:
    """문서 길이, 분석 유형, 예산 우선순위에 따른 최적 모델 선택"""
    
    # 초장문 문서 (50K+ 토큰)
    if document_length > 50000:
        return "minimax-text-01"  # 1M 컨텍스트로 처리
    
    # 예산 우선 (빠른 응답, 저비용)
    if budget_priority == "cost_first":
        if document_length < 4000:
            return "llama3.1-8b-instant"  # $0.13/1M, 1250 tps
        else:
            return "gemma2-9b-it"  # $0.40/1M, 500 tps
    
    # 성능 우선 (정확도 중시)
    elif budget_priority == "performance_first":
        if analysis_type in ["scoring", "complex_analysis"]:
            return "llama3.3-70b-versatile"  # $1.38/1M, 고성능
        else:
            return "qwen-32b-preview"  # $0.88/1M, reasoning 강점
    
    # 균형 (기본 선택)
    else:
        if analysis_type == "tool_usage":
            return "qwq-32b-preview"  # $0.68/1M, 툴 최적화
        elif document_length < 8000:
            return "llama3.1-8b-instant"  # 빠른 처리
        else:
            return "qwen-32b-preview"  # 중간 성능+비용
```

#### 📊 실제 비용 예시 (월 1,000건 평가 기준)

| 시나리오 | 평균 토큰 | 선택 모델 | 월 비용 | 특징 |
|---------|----------|----------|---------|------|
| 빠른 검토 | 2K | llama3.1-8b | $0.26 | ⚡ 초고속 처리 |
| 표준 평가 | 5K | qwq-32b | $3.40 | ⚖️ 균형잡힌 성능 |
| 정밀 분석 | 8K | llama3.3-70b | $11.04 | 🎯 최고 정확도 |
| 장문 처리 | 20K | minimax-text-01 | $8.40 | 📚 대용량 컨텍스트 |

---

## 📊 Excel 대량 업로드

### 기업 정보 일괄 업로드

**질문**: *"기업 정보를 한번에 여러 기업을 엑셀을 통해서도 업로드 할 수 있냐?"*

**✅ 네, 완벽하게 지원됩니다!** 

#### 🎯 지원 기능

**1. 기업 정보 대량 업로드**
- Excel 파일로 여러 기업 정보 일괄 등록
- 템플릿 다운로드 제공
- 데이터 검증 및 오류 보고

**2. 평가 결과 일괄 추출**
- 여러 평가서를 하나의 Excel로 통합
- 요약 시트 + 개별 상세 시트
- 통계 분석 포함

#### 📥 업로드 방법

**1. 관리자/서기 권한으로 로그인**

**2. 기업 관리 → 일괄 업로드 메뉴**

**3. Excel 템플릿 다운로드**
```
기업명 | 사업자번호 | 담당자 | 전화번호 | 이메일 | 주소 | 업종 | 설립년도
──────┼──────────┼────────┼─────────┼───────┼──────┼──────┼────────
샘플㈜ | 123-45-67890 | 홍길동 | 02-1234-5678 | test@test.com | 서울시... | 제조업 | 2020
```

**4. Excel 파일 업로드**
- 지원 형식: `.xlsx`, `.xls`
- 최대 1,000개 기업 동시 등록
- 실시간 검증 및 진행상황 표시

#### 🔧 구현 코드

**업로드 엔드포인트 (`backend/server.py`)**
```python
@app.post("/api/companies/bulk-upload")
async def bulk_upload_companies(
    file: UploadFile = File(...),
    current_user: User = Depends(check_admin_or_secretary)
):
    """Excel 파일로 기업 정보 일괄 등록"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(400, "Excel 파일만 업로드 가능합니다")
    
    # Excel 파일 읽기 및 처리
    companies_data = await process_excel_upload(file)
    
    # 데이터 검증
    validation_results = await validate_companies_data(companies_data)
    
    # 데이터베이스 저장
    if validation_results["is_valid"]:
        result = await bulk_insert_companies(companies_data)
        return {
            "success": True,
            "inserted_count": result["inserted_count"],
            "validation_results": validation_results
        }
    else:
        return {
            "success": False,
            "errors": validation_results["errors"]
        }
```

**Excel 처리 함수**
```python
async def process_excel_upload(file: UploadFile) -> List[Dict]:
    """Excel 파일 처리"""
    contents = await file.read()
    df = pd.read_excel(io.BytesIO(contents))
    
    companies = []
    for _, row in df.iterrows():
        company = {
            "name": row["기업명"],
            "business_number": row["사업자번호"],
            "contact_person": row["담당자"],
            "phone": row["전화번호"],
            "email": row["이메일"],
            "address": row["주소"],
            "industry": row["업종"],
            "established_year": int(row["설립년도"]),
            "created_at": datetime.utcnow(),
            "status": "active"
        }
        companies.append(company)
    
    return companies
```

#### 📤 추출 방법

**1. 평가 관리 → 결과 추출 메뉴**

**2. 추출 옵션 선택**
- 전체 평가 또는 선택된 평가
- PDF 개별 추출 또는 Excel 통합 추출
- 요약 정보 포함 여부

**3. 추출된 Excel 구조**
```
시트1: 전체요약
┌─────────┬──────────┬────────┬─────────┬──────┐
│ 프로젝트명 │ 평가대상기업 │ 평가위원 │ 제출일시 │ 총점 │
├─────────┼──────────┼────────┼─────────┼──────┤
│ 디지털전환 │ 샘플㈜     │ 김위원   │ 2024-01-15 │ 85.5 │
└─────────┴──────────┴────────┴─────────┴──────┘

시트2: 평가_1_샘플㈜
- 기본 정보 섹션
- 평가 항목별 상세 점수
- 평가 의견
```

#### ⚡ 성능 최적화

- **청크 처리**: 대용량 파일을 1,000개씩 분할 처리
- **비동기 처리**: 백그라운드에서 업로드 진행
- **진행상황 표시**: WebSocket으로 실시간 업데이트
- **오류 복구**: 실패한 항목만 재시도

---

## 📁 프로젝트 구조

```
online-evaluation/
├── 📂 backend/                 # FastAPI 백엔드
│   ├── 🚀 server.py           # 메인 서버
│   ├── 🔒 security.py         # 인증/보안
│   ├── 📋 models.py           # 데이터 모델
│   ├── 🤖 ai_service_enhanced.py  # AI 서비스
│   ├── 📊 export_utils.py     # Excel/PDF 추출
│   └── 📁 endpoints/          # API 엔드포인트들
├── 📂 frontend/               # React 프론트엔드
│   ├── 📁 src/
│   │   ├── 🎨 components/     # React 컴포넌트
│   │   ├── 🔧 services/       # API 클라이언트
│   │   └── 📱 App.js          # 메인 앱
│   └── 📦 package.json
├── 📂 uploads/                # 업로드 파일 저장소
├── 📂 logs/                   # 로그 파일
├── 📂 monitoring/             # 모니터링 설정
├── 📂 logging/                # ELK 스택 설정
├── 🐳 docker-compose.yml      # Docker 설정
├── 🚀 deploy_with_dependencies.sh  # 배포 스크립트
└── 📚 README.md              # 이 문서
```

---

## 🔒 보안 기능

### 인증 및 권한
- **JWT 토큰**: 안전한 세션 관리
- **역할 기반 접근**: Admin/Secretary/Evaluator 권한
- **API 키 암호화**: AI 설정 정보 보안

### 파일 보안
- **보안 토큰**: 파일 접근 시 토큰 검증
- **워터마크**: PDF 뷰어에 사용자 정보 표시
- **접근 로그**: 모든 파일 접근 기록

### 데이터 보호
- **입력 검증**: SQL Injection, XSS 방지
- **CORS 설정**: 허용된 도메인만 접근
- **암호화**: 민감 정보 데이터베이스 암호화

---

## 📈 모니터링

### ELK 스택 통합
- **Elasticsearch**: 로그 저장 및 검색
- **Logstash**: 로그 수집 및 처리
- **Kibana**: 로그 시각화 및 대시보드

### Prometheus 메트릭
- **시스템 메트릭**: CPU, 메모리, 디스크 사용량
- **애플리케이션 메트릭**: API 응답시간, 오류율
- **비즈니스 메트릭**: 평가 완료율, 사용자 활동

### 헬스체크
```bash
# 전체 시스템 상태 확인
curl http://localhost:8080/health

# 개별 서비스 상태
curl http://localhost:8080/health/database
curl http://localhost:8080/health/redis
curl http://localhost:8080/health/ai-services
```

---

## 🛠️ 개발 가이드

### 코드 스타일
- **Python**: Black 포매터 + flake8 린터
- **JavaScript**: Prettier + ESLint
- **커밋**: Conventional Commits 스타일

### 테스트
```bash
# 백엔드 테스트
cd backend
pytest tests/ -v

# 프론트엔드 테스트
cd frontend
npm test

# E2E 테스트
npm run test:e2e
```

### API 개발
```bash
# 새 엔드포인트 추가 후
cd backend
python -m uvicorn server:app --reload --host 0.0.0.0 --port 8080

# API 문서 확인
open http://localhost:8080/docs
```

---

## 🐛 문제 해결

### 자주 발생하는 문제

**1. Docker 컨테이너 시작 실패**
```bash
# 로그 확인
docker-compose logs backend
docker-compose logs frontend

# 포트 충돌 확인
sudo lsof -i :8080
sudo lsof -i :3001

# 컨테이너 재시작
docker-compose restart
```

**2. AI 서비스 오류**
```bash
# AI 공급자 설정 확인
curl http://localhost:8080/ai-admin/status

# 로그 확인
docker-compose logs backend | grep -i "ai"
```

**3. 데이터베이스 연결 오류**
```bash
# MongoDB 상태 확인
docker-compose exec mongodb mongosh --eval "db.adminCommand('ping')"

# Redis 상태 확인
docker-compose exec redis redis-cli ping
```

### 성능 최적화

**데이터베이스 최적화**
```javascript
// MongoDB 인덱스 생성
db.evaluations.createIndex({"project_id": 1, "status": 1})
db.companies.createIndex({"business_number": 1}, {"unique": true})
db.users.createIndex({"email": 1}, {"unique": true})
```

**Redis 캐시 활용**
```python
# 자주 조회되는 데이터 캐싱
@cache_service.cached(expire=3600)
async def get_evaluation_templates():
    return await db.templates.find().to_list(length=None)
```

---

## 📚 API 문서

### 주요 엔드포인트

**인증 관련**
```
POST /auth/login          # 로그인
POST /auth/register       # 회원가입 (서기)
GET  /auth/me            # 현재 사용자 정보
POST /auth/logout        # 로그아웃
```

**사용자 관리**
```
GET    /api/users              # 사용자 목록
POST   /api/users              # 사용자 생성
GET    /api/users/{id}         # 사용자 상세
PUT    /api/users/{id}         # 사용자 수정
DELETE /api/users/{id}         # 사용자 삭제
```

**프로젝트 관리**
```
GET    /api/projects           # 프로젝트 목록
POST   /api/projects           # 프로젝트 생성
GET    /api/projects/{id}      # 프로젝트 상세
PUT    /api/projects/{id}      # 프로젝트 수정
```

**기업 관리**
```
GET    /api/companies          # 기업 목록
POST   /api/companies          # 기업 등록
POST   /api/companies/bulk-upload  # Excel 일괄 업로드
GET    /api/companies/{id}     # 기업 상세
```

**평가 관리**
```
GET    /evaluations            # 평가 목록
POST   /evaluations            # 평가 생성
GET    /evaluations/{id}       # 평가 상세
POST   /evaluations/{id}/assign   # 평가 배정
POST   /evaluations/{id}/submit   # 평가 제출
```

**AI 분석**
```
POST   /ai/analyze-document    # 문서 AI 분석
POST   /ai/suggest-scores      # AI 점수 제안
POST   /ai/check-plagiarism    # 표절 검사
GET    /ai/status             # AI 서비스 상태
```

**AI 비용 최적화**
```
GET    /api/ai/cost-optimization   # 비용 최적화 통계
POST   /api/ai/cost-estimate       # 분석 비용 예상
GET    /api/ai/usage-analytics     # 사용량 및 비용 분석
```

**파일 관리**
```
POST   /api/files/upload       # 파일 업로드
GET    /api/files/{id}         # 파일 다운로드
GET    /secure-files/{token}   # 보안 파일 접근
```

**내보내기**
```
POST   /export/evaluation-pdf     # 평가서 PDF 생성
POST   /export/evaluation-excel   # 평가서 Excel 생성
POST   /export/bulk-excel         # 대량 Excel 추출
```

### 상세 API 문서
- **개발환경**: http://localhost:8080/docs
- **프로덕션**: https://your-domain.com/docs

---

## 🤝 기여하기

### 개발 참여 방법

1. **Fork** 이 저장소
2. **Feature 브랜치** 생성 (`git checkout -b feature/amazing-feature`)
3. **커밋** (`git commit -m 'Add some amazing feature'`)
4. **Push** (`git push origin feature/amazing-feature`)
5. **Pull Request** 생성

### 코드 리뷰 기준
- 테스트 코드 포함
- 문서화 업데이트
- 보안 가이드라인 준수
- 성능 영향 검토

---

## 📄 라이선스

이 프로젝트는 **MIT 라이선스** 하에 있습니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

---

## 📞 지원 및 문의

### 기술 지원
- **GitHub Issues**: [Issues 페이지](https://github.com/your-repo/online-evaluation/issues)
- **이메일**: support@your-domain.com
- **문서**: [Wiki 페이지](https://github.com/your-repo/online-evaluation/wiki)

### 커뮤니티
- **Slack**: [개발자 채널](https://your-slack.slack.com)
- **Discord**: [커뮤니티 서버](https://discord.gg/your-invite)

---

## 🎉 감사의 말

이 프로젝트는 **중소기업의 성장과 혁신**을 지원하는 공공기관의 미션에 기여하고자 개발되었습니다. 

모든 **기여자들**과 **피드백을 주신 분들**께 깊은 감사를 드립니다.

---

<div align="center">

**🚀 중소기업의 성장을 함께 만들어갑니다 🚀**

Made with ❤️ for SME Support Programs

[⬆ 맨 위로 돌아가기](#-중소기업-지원사업-온라인-평가-시스템)

</div>