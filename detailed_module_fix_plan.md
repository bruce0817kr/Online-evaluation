# 🔧 온라인 평가 시스템 - 모듈별 세분화 수정 계획

## 📋 전체 개요

### 🚨 긴급 수정 사항 (Critical)
- 로그인 시스템의 MongoDB 필드 불일치 문제
- bcrypt 버전 호환성 경고

### 🟡 중요 개선 사항 (High Priority)
- 보안 시스템 강화
- 성능 최적화 
- 코드 품질 개선

### 🟢 기능 완성 사항 (Medium Priority)
- 평가 시스템 완성
- 내보내기 기능 구현
- UI/UX 개선

---

## 🎯 1. 인증 및 사용자 관리 모듈

### 📁 영향받는 파일
- `backend/server.py` (line 520: 로그인 버그)
- `backend/server_fixed.py` (동일 이슈)
- `backend/models.py` (User 모델)
- `backend/security.py` (인증 로직)

### 🐛 식별된 문제

#### A. 로그인 버그 (CRITICAL) 🔴
**위치**: `backend/server.py` line 520
```python
# 현재 (문제)
await db.users.update_one(
    {"id": user_data["id"]},  # ❌ KeyError 발생
    {"$set": {"last_login": datetime.utcnow()}}
)
```

**원인 분석**:
- MongoDB는 `_id` 필드를 기본키로 사용
- Pydantic User 모델은 `id` 필드를 `_id`로 alias 설정
- 하지만 실제 DB 쿼리에서는 일관성 없이 사용됨

**해결 방법**:
```python
# 수정 후
await db.users.update_one(
    {"_id": user_data["_id"]},  # ✅ MongoDB 표준 사용
    {"$set": {"last_login": datetime.utcnow()}}
)
```

#### B. User 모델 일관성 문제 🟡
**문제**: `models.py`에서 필드 alias 설정이 코드 전반에 일관되게 적용되지 않음

**수정 계획**:
```python
# models.py 개선
class User(UserBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    
    class Config:
        allow_population_by_field_name = True
        json_encoders = {datetime: lambda dt: dt.isoformat()}
```

### 🔧 세부 수정 작업

#### 1단계: 로그인 함수 수정 (30분)
```python
# server.py의 login_for_access_token 함수 수정
@api_router.post("/auth/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user_data = await db.users.find_one({"login_id": form_data.username})
    if not user_data or not verify_password(form_data.password, user_data["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="아이디 또는 비밀번호가 잘못되었습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # ✅ 수정: _id 필드 사용
    await db.users.update_one(
        {"_id": user_data["_id"]},
        {"$set": {"last_login": datetime.utcnow()}}
    )
    
    user = User(**user_data)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user_data["_id"])}, expires_delta=access_token_expires
    )
    user_response = UserResponse(**user.dict())
    return {"access_token": access_token, "token_type": "bearer", "user": user_response}
```

#### 2단계: 모든 사용자 CRUD 연산 검토 (1시간)
**점검 대상**:
- 사용자 생성 함수들
- 사용자 수정/삭제 함수들
- 인증 관련 함수들

**파일별 수정**:
```python
# server.py 내 모든 사용자 관련 쿼리
- create_user: ✅ 이미 올바름
- update_user: 🔍 검토 필요
- delete_user: 🔍 검토 필요
- get_current_user: 🔍 검토 필요
```

#### 3단계: bcrypt 호환성 수정 (30분)
```python
# 기존 사용자 비밀번호 재해시 스크립트
async def fix_password_hashes():
    """기존 사용자들의 비밀번호 해시 재생성"""
    users = await db.users.find({}).to_list(None)
    for user in users:
        if user.get("password_hash"):
            # 기본 비밀번호로 재설정 (또는 기존 평문 비밀번호가 있다면)
            new_hash = get_password_hash("기본비밀번호123")
            await db.users.update_one(
                {"_id": user["_id"]},
                {"$set": {"password_hash": new_hash}}
            )
```

---

## 🛡️ 2. 보안 시스템 모듈

### 📁 영향받는 파일
- `backend/security.py`
- `backend/api_security.py` 
- `backend/security_monitoring.py`
- `backend/middleware.py`

### 🔒 보안 강화 계획

#### A. JWT 토큰 보안 개선 (2시간)

**현재 설정**:
```python
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
JWT_ALGORITHM = "HS256"
```

**개선 설정**:
```python
# security.py 수정
class SecurityConfig:
    def __init__(self):
        self.JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 15  # 단축
        self.JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7     # 추가
        self.JWT_ALGORITHM = "HS256"  # 현재 유지, 향후 RS256 고려
        
        # 새로운 설정
        self.JWT_REFRESH_TOKEN_ENABLED = True
        self.JWT_BLACKLIST_ENABLED = True
```

**Refresh Token 구현**:
```python
# 새로운 엔드포인트 추가
@api_router.post("/auth/refresh")
async def refresh_access_token(refresh_token: str):
    """액세스 토큰 갱신"""
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        
        # 블랙리스트 확인
        if await is_token_blacklisted(refresh_token):
            raise HTTPException(status_code=401, detail="Token revoked")
            
        # 새로운 액세스 토큰 생성
        access_token = create_access_token(data={"sub": user_id})
        return {"access_token": access_token, "token_type": "bearer"}
        
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
```

**토큰 블랙리스트 구현**:
```python
# Redis 기반 블랙리스트
async def blacklist_token(token: str, expires_in: int):
    """토큰을 블랙리스트에 추가"""
    await cache_service.set(f"blacklist:{token}", "1", expire=expires_in)

async def is_token_blacklisted(token: str) -> bool:
    """토큰이 블랙리스트에 있는지 확인"""
    result = await cache_service.get(f"blacklist:{token}")
    return result is not None
```

#### B. CSRF 방어 구현 (3시간)

**미들웨어 추가**:
```python
# middleware.py에 추가
class CSRFMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app
    
    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
            
        request = Request(scope, receive)
        
        # POST, PUT, DELETE 요청에 CSRF 토큰 검증
        if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
            csrf_token = request.headers.get("X-CSRF-Token")
            session_token = request.cookies.get("csrf_token")
            
            if not csrf_token or csrf_token != session_token:
                response = JSONResponse(
                    status_code=403,
                    content={"detail": "CSRF token missing or invalid"}
                )
                await response(scope, receive, send)
                return
        
        await self.app(scope, receive, send)
```

**CSRF 토큰 생성 엔드포인트**:
```python
@api_router.get("/auth/csrf-token")
async def get_csrf_token():
    """CSRF 토큰 생성"""
    token = secrets.token_urlsafe(32)
    response = JSONResponse({"csrf_token": token})
    response.set_cookie(
        "csrf_token", 
        token, 
        max_age=3600, 
        httponly=True, 
        samesite="strict"
    )
    return response
```

#### C. XSS 방어 강화 (2시간)

**Content Security Policy 강화**:
```python
# security.py에 추가
class SecurityConfig:
    def __init__(self):
        self.CONTENT_SECURITY_POLICY = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
```

**입력 검증 강화**:
```python
# api_security.py 개선
import bleach

class InputSanitizer:
    @staticmethod
    def sanitize_html(content: str) -> str:
        """HTML 태그 제거 및 안전한 문자만 허용"""
        allowed_tags = []  # HTML 태그 완전 제거
        return bleach.clean(content, tags=allowed_tags, strip=True)
    
    @staticmethod
    def validate_input(data: dict) -> dict:
        """모든 문자열 입력 검증 및 정화"""
        for key, value in data.items():
            if isinstance(value, str):
                # XSS 방지를 위한 정화
                data[key] = InputSanitizer.sanitize_html(value)
        return data
```

---

## 💾 3. 데이터베이스 모듈

### 📁 영향받는 파일
- `backend/server.py` (DB 연결 및 쿼리)
- MongoDB 인덱스 설정
- 데이터베이스 보안 설정

### 🗄️ 데이터베이스 최적화 계획

#### A. 인덱스 최적화 (1시간)

**필수 인덱스 생성 스크립트**:
```javascript
// MongoDB에서 실행할 인덱스 생성 스크립트
// users 컬렉션
db.users.createIndex({ "login_id": 1 }, { unique: true, name: "idx_login_id" });
db.users.createIndex({ "email": 1 }, { unique: true, name: "idx_email" });
db.users.createIndex({ "role": 1, "is_active": 1 }, { name: "idx_role_active" });
db.users.createIndex({ "created_at": -1 }, { name: "idx_created_desc" });

// projects 컬렉션
db.projects.createIndex({ "created_by": 1 }, { name: "idx_created_by" });
db.projects.createIndex({ "is_active": 1, "created_at": -1 }, { name: "idx_active_date" });
db.projects.createIndex({ "deadline": 1 }, { name: "idx_deadline" });

// companies 컬렉션
db.companies.createIndex({ "project_id": 1 }, { name: "idx_project_id" });
db.companies.createIndex({ "name": 1 }, { name: "idx_company_name" });

// evaluations 컬렉션
db.evaluation_sheets.createIndex({ "project_id": 1, "evaluator_id": 1 }, { name: "idx_eval_project_user" });
db.evaluation_sheets.createIndex({ "status": 1, "created_at": -1 }, { name: "idx_status_date" });
db.evaluation_sheets.createIndex({ "company_id": 1 }, { name: "idx_company_eval" });
```

**Python에서 인덱스 생성**:
```python
# 서버 시작 시 인덱스 자동 생성
async def ensure_indexes():
    """필요한 인덱스가 없으면 생성"""
    try:
        # Users collection indexes
        await db.users.create_index([("login_id", 1)], unique=True, background=True)
        await db.users.create_index([("email", 1)], unique=True, background=True)
        await db.users.create_index([("role", 1), ("is_active", 1)], background=True)
        
        # Projects collection indexes
        await db.projects.create_index([("created_by", 1)], background=True)
        await db.projects.create_index([("is_active", 1), ("created_at", -1)], background=True)
        
        # Companies collection indexes
        await db.companies.create_index([("project_id", 1)], background=True)
        
        # Evaluation sheets indexes
        await db.evaluation_sheets.create_index([("project_id", 1), ("evaluator_id", 1)], background=True)
        await db.evaluation_sheets.create_index([("status", 1), ("created_at", -1)], background=True)
        
        logger.info("Database indexes ensured successfully")
    except Exception as e:
        logger.error(f"Failed to create indexes: {e}")

# startup 이벤트에 추가
@app.on_event("startup")
async def startup_event():
    await ensure_indexes()
```

#### B. 쿼리 최적화 (2시간)

**현재 비효율적인 쿼리 개선**:
```python
# AS-IS (비효율적)
async def get_admin_dashboard(current_user: User = Depends(get_current_user)):
    projects_count = await db.projects.count_documents({"is_active": True})
    companies_count = await db.companies.count_documents({})
    evaluators_count = await db.users.count_documents({"role": "evaluator", "is_active": True})
    # ... 여러 개별 쿼리

# TO-BE (최적화됨)
async def get_admin_dashboard(current_user: User = Depends(get_current_user)):
    # Aggregation pipeline으로 한번에 처리
    pipeline = [
        {
            "$facet": {
                "project_stats": [
                    {"$match": {"is_active": True}},
                    {"$count": "active_projects"}
                ],
                "user_stats": [
                    {"$group": {
                        "_id": "$role",
                        "count": {"$sum": 1},
                        "active_count": {
                            "$sum": {"$cond": [{"$eq": ["$is_active", True]}, 1, 0]}
                        }
                    }}
                ],
                "recent_projects": [
                    {"$match": {"is_active": True}},
                    {"$sort": {"created_at": -1}},
                    {"$limit": 5}
                ]
            }
        }
    ]
    
    result = await db.projects.aggregate(pipeline).to_list(1)
    # 결과 처리...
```

#### C. MongoDB 보안 설정 (1시간)

**Docker Compose 보안 강화**:
```yaml
# docker-compose.yml 수정
mongodb:
  image: mongo:7.0
  environment:
    MONGO_INITDB_ROOT_USERNAME: ${MONGO_ROOT_USER}
    MONGO_INITDB_ROOT_PASSWORD: ${MONGO_ROOT_PASSWORD}
    MONGO_INITDB_DATABASE: ${MONGO_DB_NAME}
  command: 
    - mongod
    - --auth
    - --bind_ip_all
    - --auditDestination=file
    - --auditPath=/var/log/mongodb/audit.log
    - --auditFormat=JSON
    - --setParameter
    - auditAuthorizationSuccess=false
  volumes:
    - mongodb_data:/data/db
    - ./logs/mongodb:/var/log/mongodb
  networks:
    - backend_network
  # 외부 노출 포트 제거 (내부 네트워크만 사용)
```

**사용자 권한 분리**:
```javascript
// MongoDB에서 실행할 사용자 생성 스크립트
use admin;

// 애플리케이션 전용 사용자 생성
db.createUser({
  user: "app_user",
  pwd: "secure_password_here",
  roles: [
    {
      role: "readWrite",
      db: "online_evaluation_db"
    }
  ]
});

// 읽기 전용 사용자 생성 (분석용)
db.createUser({
  user: "readonly_user", 
  pwd: "readonly_password_here",
  roles: [
    {
      role: "read",
      db: "online_evaluation_db"
    }
  ]
});
```

---

## 📊 4. 평가 시스템 모듈

### 📁 영향받는 파일
- `backend/server.py` (평가 관련 API)
- `frontend/src/App.js` (평가 UI)
- `backend/models.py` (평가 모델)

### 🎯 평가 시스템 완성 계획

#### A. 평가표 동적 생성 완성 (4시간)

**현재 상태**: 70% 완료, 동적 생성 로직 부분 구현됨

**완성 작업**:
```python
# 평가표 동적 생성 API 완성
@api_router.post("/evaluation-sheets/generate")
async def generate_evaluation_sheet(
    template_id: str,
    company_id: str,
    evaluator_id: str,
    current_user: User = Depends(get_current_user)
):
    """평가표 동적 생성"""
    
    # 템플릿 조회
    template = await db.evaluation_templates.find_one({"_id": template_id})
    if not template:
        raise HTTPException(status_code=404, detail="템플릿을 찾을 수 없습니다")
    
    # 회사 정보 조회
    company = await db.companies.find_one({"_id": company_id})
    if not company:
        raise HTTPException(status_code=404, detail="회사를 찾을 수 없습니다")
    
    # 평가표 생성
    evaluation_sheet = {
        "_id": str(uuid.uuid4()),
        "template_id": template_id,
        "company_id": company_id,
        "evaluator_id": evaluator_id,
        "project_id": company["project_id"],
        "status": "assigned",
        "questions": template["questions"],
        "scores": {},  # 평가 점수 저장용
        "comments": {},  # 질문별 코멘트
        "total_score": None,
        "weighted_score": None,
        "created_at": datetime.utcnow(),
        "assigned_at": datetime.utcnow(),
        "submitted_at": None
    }
    
    await db.evaluation_sheets.insert_one(evaluation_sheet)
    
    return {
        "evaluation_sheet_id": evaluation_sheet["_id"],
        "message": "평가표가 성공적으로 생성되었습니다"
    }
```

#### B. 실시간 진행률 추적 (3시간)

**WebSocket 기반 실시간 업데이트**:
```python
# WebSocket 연결 관리
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.user_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.user_connections[user_id] = websocket
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        self.active_connections.remove(websocket)
        if user_id in self.user_connections:
            del self.user_connections[user_id]
    
    async def send_personal_message(self, message: str, user_id: str):
        if user_id in self.user_connections:
            await self.user_connections[user_id].send_text(message)
    
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@api_router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            # 메시지 처리 로직
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)

# 평가 진행률 업데이트 함수
async def update_evaluation_progress(project_id: str):
    """평가 진행률 계산 및 실시간 업데이트"""
    
    # 전체 평가표 수 조회
    total_sheets = await db.evaluation_sheets.count_documents({"project_id": project_id})
    
    # 완료된 평가표 수 조회  
    completed_sheets = await db.evaluation_sheets.count_documents({
        "project_id": project_id,
        "status": "submitted"
    })
    
    # 진행률 계산
    progress = (completed_sheets / total_sheets * 100) if total_sheets > 0 else 0
    
    # 프로젝트 정보 업데이트
    await db.projects.update_one(
        {"_id": project_id},
        {"$set": {
            "total_evaluations": total_sheets,
            "completed_evaluations": completed_sheets,
            "completion_rate": round(progress, 1),
            "updated_at": datetime.utcnow()
        }}
    )
    
    # 실시간 업데이트 전송
    progress_data = {
        "type": "progress_update",
        "project_id": project_id,
        "total": total_sheets,
        "completed": completed_sheets,
        "percentage": round(progress, 1)
    }
    
    # 관련 사용자들에게 브로드캐스트
    await manager.broadcast(json.dumps(progress_data))
```

#### C. 평가 결과 집계 알고리즘 (3시간)

**점수 계산 및 집계**:
```python
@api_router.post("/evaluation-sheets/{sheet_id}/submit")
async def submit_evaluation(
    sheet_id: str,
    scores: Dict[str, float],
    comments: Dict[str, str],
    current_user: User = Depends(get_current_user)
):
    """평가 제출 및 점수 계산"""
    
    # 평가표 조회
    sheet = await db.evaluation_sheets.find_one({"_id": sheet_id})
    if not sheet:
        raise HTTPException(status_code=404, detail="평가표를 찾을 수 없습니다")
    
    # 권한 확인
    if sheet["evaluator_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다")
    
    # 템플릿 조회 (가중치 정보)
    template = await db.evaluation_templates.find_one({"_id": sheet["template_id"]})
    
    # 점수 계산
    total_score = 0
    weighted_score = 0
    total_weight = 0
    
    for question_id, score in scores.items():
        # 질문 정보 조회
        question = next((q for q in template["questions"] if q["id"] == question_id), None)
        if question:
            weight = question.get("weight", 1)
            max_score = question.get("max_score", 100)
            
            # 정규화된 점수 계산
            normalized_score = (score / max_score) * 100
            total_score += normalized_score
            weighted_score += normalized_score * weight
            total_weight += weight
    
    # 최종 점수 계산
    final_total_score = total_score / len(scores) if scores else 0
    final_weighted_score = weighted_score / total_weight if total_weight > 0 else 0
    
    # 평가표 업데이트
    await db.evaluation_sheets.update_one(
        {"_id": sheet_id},
        {"$set": {
            "scores": scores,
            "comments": comments,
            "total_score": round(final_total_score, 2),
            "weighted_score": round(final_weighted_score, 2),
            "status": "submitted",
            "submitted_at": datetime.utcnow()
        }}
    )
    
    # 진행률 업데이트
    await update_evaluation_progress(sheet["project_id"])
    
    # 회사별 종합 점수 계산
    await calculate_company_final_score(sheet["company_id"])
    
    return {
        "message": "평가가 성공적으로 제출되었습니다",
        "total_score": final_total_score,
        "weighted_score": final_weighted_score
    }

async def calculate_company_final_score(company_id: str):
    """회사별 최종 점수 계산"""
    
    # 해당 회사의 모든 제출된 평가 조회
    evaluations = await db.evaluation_sheets.find({
        "company_id": company_id,
        "status": "submitted"
    }).to_list(None)
    
    if not evaluations:
        return
    
    # 평균 점수 계산
    total_scores = [eval["total_score"] for eval in evaluations]
    weighted_scores = [eval["weighted_score"] for eval in evaluations]
    
    avg_total_score = sum(total_scores) / len(total_scores)
    avg_weighted_score = sum(weighted_scores) / len(weighted_scores)
    
    # 회사 정보 업데이트
    await db.companies.update_one(
        {"_id": company_id},
        {"$set": {
            "evaluation_count": len(evaluations),
            "average_total_score": round(avg_total_score, 2),
            "average_weighted_score": round(avg_weighted_score, 2),
            "updated_at": datetime.utcnow()
        }}
    )
```

---

## 📁 5. 내보내기 기능 모듈

### 📁 영향받는 파일
- `backend/export_utils.py`
- 새로운 파일: `backend/report_generator.py`
- 새로운 파일: `backend/excel_generator.py`

### 📄 내보내기 기능 구현 (6시간)

#### A. 엑셀 내보내기 구현 (3시간)

**Excel 생성 라이브러리 설치**:
```bash
pip install openpyxl pandas
```

**엑셀 생성 모듈**:
```python
# backend/excel_generator.py
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils.dataframe import dataframe_to_rows
from io import BytesIO

class ExcelGenerator:
    def __init__(self):
        self.wb = Workbook()
        self.ws = self.wb.active
    
    async def generate_evaluation_report(self, project_id: str) -> BytesIO:
        """프로젝트별 평가 결과 엑셀 생성"""
        
        # 프로젝트 정보 조회
        project = await db.projects.find_one({"_id": project_id})
        
        # 회사별 평가 결과 조회
        companies = await db.companies.find({"project_id": project_id}).to_list(None)
        
        # 평가 결과 데이터 수집
        evaluation_data = []
        for company in companies:
            evaluations = await db.evaluation_sheets.find({
                "company_id": company["_id"],
                "status": "submitted"
            }).to_list(None)
            
            for evaluation in evaluations:
                # 평가자 정보 조회
                evaluator = await db.users.find_one({"_id": evaluation["evaluator_id"]})
                
                evaluation_data.append({
                    "회사명": company["name"],
                    "평가자": evaluator["user_name"],
                    "총점": evaluation["total_score"],
                    "가중점수": evaluation["weighted_score"],
                    "제출일": evaluation["submitted_at"].strftime("%Y-%m-%d %H:%M"),
                    "상태": "완료"
                })
        
        # DataFrame 생성
        df = pd.DataFrame(evaluation_data)
        
        # 엑셀 파일 생성
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # 평가 결과 시트
            df.to_excel(writer, sheet_name='평가결과', index=False)
            
            # 통계 시트
            stats_data = {
                "항목": ["총 회사 수", "총 평가 수", "평균 점수", "최고 점수", "최저 점수"],
                "값": [
                    len(companies),
                    len(evaluation_data),
                    df["총점"].mean() if not df.empty else 0,
                    df["총점"].max() if not df.empty else 0,
                    df["총점"].min() if not df.empty else 0
                ]
            }
            
            stats_df = pd.DataFrame(stats_data)
            stats_df.to_excel(writer, sheet_name='통계', index=False)
        
        output.seek(0)
        return output

# API 엔드포인트
@api_router.get("/projects/{project_id}/export/excel")
async def export_project_excel(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """프로젝트 평가 결과 엑셀 내보내기"""
    
    check_admin_or_secretary(current_user)
    
    generator = ExcelGenerator()
    excel_data = await generator.generate_evaluation_report(project_id)
    
    # 프로젝트 이름으로 파일명 생성
    project = await db.projects.find_one({"_id": project_id})
    filename = f"{project['name']}_평가결과_{datetime.now().strftime('%Y%m%d')}.xlsx"
    
    return StreamingResponse(
        BytesIO(excel_data.getvalue()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
```

#### B. PDF 종합평가서 생성 (3시간)

**PDF 생성 라이브러리 설치**:
```bash
pip install reportlab weasyprint
```

**PDF 생성 모듈**:
```python
# backend/pdf_generator.py
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO

class PDFGenerator:
    def __init__(self):
        # 한글 폰트 등록 (필요시)
        try:
            pdfmetrics.registerFont(TTFont('NanumGothic', '/app/fonts/NanumGothic.ttf'))
        except:
            pass  # 폰트 파일이 없으면 기본 폰트 사용
    
    async def generate_comprehensive_report(self, project_id: str) -> BytesIO:
        """종합평가서 PDF 생성"""
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # 프로젝트 정보 조회
        project = await db.projects.find_one({"_id": project_id})
        
        # 제목
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1  # 중앙 정렬
        )
        
        story.append(Paragraph(f"{project['name']} 종합평가서", title_style))
        story.append(Spacer(1, 20))
        
        # 프로젝트 개요
        story.append(Paragraph("1. 프로젝트 개요", styles['Heading2']))
        
        project_info = [
            ["프로젝트명", project['name']],
            ["설명", project.get('description', '')],
            ["생성일", project['created_at'].strftime("%Y-%m-%d")],
            ["마감일", project.get('deadline', '').strftime("%Y-%m-%d") if project.get('deadline') else ''],
            ["상태", "진행중" if project.get('is_active') else "완료"]
        ]
        
        project_table = Table(project_info, colWidths=[2*inch, 4*inch])
        project_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.grey),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(project_table)
        story.append(Spacer(1, 20))
        
        # 평가 결과 요약
        story.append(Paragraph("2. 평가 결과 요약", styles['Heading2']))
        
        # 회사별 결과 조회
        companies = await db.companies.find({"project_id": project_id}).to_list(None)
        
        result_data = [["순위", "회사명", "평균점수", "가중평균", "평가완료"]]
        
        for i, company in enumerate(companies, 1):
            evaluations = await db.evaluation_sheets.find({
                "company_id": company["_id"],
                "status": "submitted"
            }).to_list(None)
            
            avg_score = sum(e["total_score"] for e in evaluations) / len(evaluations) if evaluations else 0
            avg_weighted = sum(e["weighted_score"] for e in evaluations) / len(evaluations) if evaluations else 0
            
            result_data.append([
                str(i),
                company["name"],
                f"{avg_score:.1f}",
                f"{avg_weighted:.1f}",
                f"{len(evaluations)}건"
            ])
        
        result_table = Table(result_data, colWidths=[0.8*inch, 2*inch, 1*inch, 1*inch, 1*inch])
        result_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(result_table)
        story.append(Spacer(1, 20))
        
        # 평가 분석
        story.append(Paragraph("3. 평가 분석", styles['Heading2']))
        
        analysis_text = f"""
        본 프로젝트에는 총 {len(companies)}개 회사가 참여하였으며, 
        전체 평가 완료율은 {project.get('completion_rate', 0)}%입니다.
        
        평균 점수는 {sum(float(row[2]) for row in result_data[1:]) / len(result_data[1:]):.1f}점이며,
        가중 평균 점수는 {sum(float(row[3]) for row in result_data[1:]) / len(result_data[1:]):.1f}점입니다.
        """
        
        story.append(Paragraph(analysis_text, styles['Normal']))
        
        # PDF 생성
        doc.build(story)
        buffer.seek(0)
        return buffer

# API 엔드포인트
@api_router.get("/projects/{project_id}/export/pdf")
async def export_project_pdf(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """프로젝트 종합평가서 PDF 내보내기"""
    
    check_admin_or_secretary(current_user)
    
    generator = PDFGenerator()
    pdf_data = await generator.generate_comprehensive_report(project_id)
    
    # 프로젝트 이름으로 파일명 생성
    project = await db.projects.find_one({"_id": project_id})
    filename = f"{project['name']}_종합평가서_{datetime.now().strftime('%Y%m%d')}.pdf"
    
    return StreamingResponse(
        BytesIO(pdf_data.getvalue()),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
```

---

## 🎨 6. 프론트엔드 모듈

### 📁 영향받는 파일
- `frontend/src/App.js`
- 새로운 파일들: 컴포넌트 분리

### 🖥️ 프론트엔드 개선 계획

#### A. 컴포넌트 분리 및 모듈화 (4시간)

**현재 문제**: 모든 기능이 `App.js`에 집중되어 있음 (2400+ 라인)

**개선 계획**:
```javascript
// src/components/Auth/LoginForm.js
import React, { useState } from 'react';
import axios from 'axios';

const LoginForm = ({ onLogin, onError }) => {
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const response = await axios.post('/api/auth/login', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 10000
      });
      
      const { access_token, user } = response.data;
      localStorage.setItem('token', access_token);
      localStorage.setItem('user', JSON.stringify(user));
      
      onLogin(user);
    } catch (error) {
      onError(error.response?.data?.detail || '로그인에 실패했습니다');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700">
          아이디
        </label>
        <input
          type="text"
          value={formData.username}
          onChange={(e) => setFormData({...formData, username: e.target.value})}
          className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
          required
        />
      </div>
      
      <div>
        <label className="block text-sm font-medium text-gray-700">
          비밀번호
        </label>
        <input
          type="password"
          value={formData.password}
          onChange={(e) => setFormData({...formData, password: e.target.value})}
          className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
          required
        />
      </div>
      
      <button
        type="submit"
        disabled={loading}
        className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50"
      >
        {loading ? '로그인 중...' : '로그인'}
      </button>
    </form>
  );
};

export default LoginForm;
```

**API 클라이언트 개선**:
```javascript
// src/services/apiClient.js
import axios from 'axios';

const BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8080';

class ApiClient {
  constructor() {
    this.client = axios.create({
      baseURL: `${BASE_URL}/api`,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json'
      }
    });

    // 요청 인터셉터 - 토큰 추가
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        
        // CSRF 토큰 추가
        const csrfToken = this.getCsrfToken();
        if (csrfToken) {
          config.headers['X-CSRF-Token'] = csrfToken;
        }
        
        return config;
      },
      (error) => Promise.reject(error)
    );

    // 응답 인터셉터 - 토큰 갱신
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;
        
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;
          
          try {
            // 토큰 갱신 로직 (Refresh Token 구현 후)
            const refreshToken = localStorage.getItem('refreshToken');
            if (refreshToken) {
              const response = await this.client.post('/auth/refresh', {
                refresh_token: refreshToken
              });
              
              const { access_token } = response.data;
              localStorage.setItem('token', access_token);
              
              originalRequest.headers.Authorization = `Bearer ${access_token}`;
              return this.client(originalRequest);
            }
          } catch (refreshError) {
            // 갱신 실패 시 로그아웃
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            window.location.href = '/login';
          }
        }
        
        return Promise.reject(error);
      }
    );
  }

  getCsrfToken() {
    return document.cookie
      .split('; ')
      .find(row => row.startsWith('csrf_token='))
      ?.split('=')[1];
  }

  // API 메서드들
  async get(url, config = {}) {
    return this.client.get(url, config);
  }

  async post(url, data = {}, config = {}) {
    return this.client.post(url, data, config);
  }

  async put(url, data = {}, config = {}) {
    return this.client.put(url, data, config);
  }

  async delete(url, config = {}) {
    return this.client.delete(url, config);
  }
}

export default new ApiClient();
```

#### B. 실시간 알림 시스템 (3시간)

**WebSocket 연결 관리**:
```javascript
// src/services/websocketService.js
class WebSocketService {
  constructor() {
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectInterval = 5000;
    this.listeners = new Map();
  }

  connect(userId) {
    const wsUrl = `ws://localhost:8080/api/ws/${userId}`;
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log('WebSocket 연결됨');
      this.reconnectAttempts = 0;
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.handleMessage(data);
      } catch (error) {
        console.error('WebSocket 메시지 파싱 오류:', error);
      }
    };

    this.ws.onclose = () => {
      console.log('WebSocket 연결 종료');
      this.attemptReconnect(userId);
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket 오류:', error);
    };
  }

  attemptReconnect(userId) {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      setTimeout(() => {
        console.log(`WebSocket 재연결 시도 ${this.reconnectAttempts}`);
        this.connect(userId);
      }, this.reconnectInterval);
    }
  }

  handleMessage(data) {
    const { type } = data;
    const listeners = this.listeners.get(type) || [];
    listeners.forEach(callback => callback(data));
  }

  on(eventType, callback) {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, []);
    }
    this.listeners.get(eventType).push(callback);
  }

  off(eventType, callback) {
    const listeners = this.listeners.get(eventType) || [];
    const index = listeners.indexOf(callback);
    if (index !== -1) {
      listeners.splice(index, 1);
    }
  }

  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

export default new WebSocketService();
```

**알림 컴포넌트**:
```javascript
// src/components/Notification/NotificationProvider.js
import React, { createContext, useContext, useReducer, useEffect } from 'react';
import websocketService from '../../services/websocketService';

const NotificationContext = createContext();

const notificationReducer = (state, action) => {
  switch (action.type) {
    case 'ADD_NOTIFICATION':
      return {
        ...state,
        notifications: [...state.notifications, {
          id: Date.now(),
          ...action.payload,
          timestamp: new Date()
        }]
      };
    
    case 'REMOVE_NOTIFICATION':
      return {
        ...state,
        notifications: state.notifications.filter(n => n.id !== action.payload)
      };
    
    case 'UPDATE_PROGRESS':
      return {
        ...state,
        progress: action.payload
      };
    
    default:
      return state;
  }
};

export const NotificationProvider = ({ children, user }) => {
  const [state, dispatch] = useReducer(notificationReducer, {
    notifications: [],
    progress: {}
  });

  useEffect(() => {
    if (user) {
      // WebSocket 연결
      websocketService.connect(user.id);

      // 진행률 업데이트 리스너
      websocketService.on('progress_update', (data) => {
        dispatch({ type: 'UPDATE_PROGRESS', payload: data });
        
        // 진행률 알림 표시
        dispatch({
          type: 'ADD_NOTIFICATION',
          payload: {
            type: 'info',
            title: '진행률 업데이트',
            message: `${data.project_name}: ${data.percentage}% 완료`
          }
        });
      });

      // 일반 알림 리스너
      websocketService.on('notification', (data) => {
        dispatch({ type: 'ADD_NOTIFICATION', payload: data });
      });

      return () => {
        websocketService.disconnect();
      };
    }
  }, [user]);

  const addNotification = (notification) => {
    dispatch({ type: 'ADD_NOTIFICATION', payload: notification });
    
    // 자동 제거 (5초 후)
    setTimeout(() => {
      removeNotification(notification.id || Date.now());
    }, 5000);
  };

  const removeNotification = (id) => {
    dispatch({ type: 'REMOVE_NOTIFICATION', payload: id });
  };

  return (
    <NotificationContext.Provider value={{
      ...state,
      addNotification,
      removeNotification
    }}>
      {children}
    </NotificationContext.Provider>
  );
};

export const useNotification = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotification must be used within NotificationProvider');
  }
  return context;
};
```

---

## 📝 7. 작업 우선순위 및 일정

### 🚨 1단계: 긴급 수정 (오늘 완료)

#### 우선순위 1: 로그인 버그 수정 (1시간)
- [ ] `server.py` line 520 수정
- [ ] `server_fixed.py` 동일 수정
- [ ] 테스트 실행 및 확인

#### 우선순위 2: 사용자 CRUD 일관성 (1시간)
- [ ] 모든 사용자 관련 쿼리 검토
- [ ] MongoDB `_id` 필드 사용 통일
- [ ] 기본 테스트 수행

### 🔒 2단계: 보안 강화 (1-2일)

#### JWT 개선 (4시간)
- [ ] Refresh Token 구현
- [ ] 토큰 블랙리스트 구현
- [ ] 만료 시간 단축

#### CSRF 방어 (3시간)
- [ ] CSRF 미들웨어 구현
- [ ] 토큰 생성 API 구현
- [ ] 프론트엔드 연동

#### XSS 방어 (2시간)
- [ ] CSP 헤더 강화
- [ ] 입력 검증 개선
- [ ] HTML 정화 구현

### 📊 3단계: 기능 완성 (2-3일)

#### 평가 시스템 (8시간)
- [ ] 동적 생성 완성
- [ ] 실시간 진행률
- [ ] 점수 계산 알고리즘

#### 내보내기 기능 (6시간)
- [ ] 엑셀 내보내기
- [ ] PDF 종합평가서
- [ ] 템플릿 시스템

#### 프론트엔드 개선 (6시간)
- [ ] 컴포넌트 분리
- [ ] 실시간 알림
- [ ] 성능 최적화

### 🚀 4단계: 최종 정리 (1일)

#### 테스트 및 문서화 (4시간)
- [ ] 통합 테스트
- [ ] API 문서 완성
- [ ] 사용자 매뉴얼

#### 배포 준비 (4시간)
- [ ] 환경 변수 설정
- [ ] Docker 최적화
- [ ] 모니터링 설정

---

## 📋 체크리스트 및 검증

### ✅ 로그인 버그 수정 검증
```bash
# 테스트 스크립트
curl -X POST "http://localhost:8080/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

### ✅ 보안 검증
```bash
# CSRF 테스트
curl -X POST "http://localhost:8080/api/projects" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"테스트"}'
```

### ✅ 성능 검증
```bash
# 응답 시간 측정
curl -w "@curl-format.txt" -o /dev/null -s "http://localhost:8080/api/projects"
```

---

**작성일**: 2025-06-13  
**예상 완료**: 2025-06-18 (5일)  
**우선순위**: Critical → High → Medium  
**담당자**: AI 개발 어시스턴트
