from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks, Query, WebSocket, WebSocketDisconnect
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import FileResponse, StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request # 추가
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
import re
import asyncio
import aiofiles
import io
import base64
from concurrent.futures import ThreadPoolExecutor
import json
from export_utils import exporter
from cache_service import cache_service
from websocket_service import connection_manager, notification_service
from health_monitor import HealthMonitor

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection with connection pooling
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(
    mongo_url,
    maxPoolSize=100,  # Maximum connections in pool
    minPoolSize=10,   # Minimum connections in pool
    maxIdleTimeMS=30000,  # Close connections after 30 seconds of inactivity
    connectTimeoutMS=20000,  # 20 second connection timeout
    serverSelectionTimeoutMS=20000  # 20 second server selection timeout
)
db = client[os.environ['DB_NAME']]

# Thread pool for CPU-intensive tasks
executor = ThreadPoolExecutor(max_workers=4)

# Initialize health monitor
health_monitor = HealthMonitor(client)

# JWT settings
SECRET_KEY = "your-secret-key-here-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Create the main app without a prefix
app = FastAPI(title="온라인 평가 시스템", version="2.0.0")

# 로깅 설정
logging.basicConfig(level=logging.INFO) # 추가
logger = logging.getLogger(__name__) # 추가

# 요청 로깅 미들웨어 추가
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url}")
    logger.info(f"Request headers: {request.headers}")
    response = await call_next(request)
    logger.info(f"Outgoing response: {response.status_code}")
    return response

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://c9538c52-9ad8-41a7-9b0c-0f121f66378a.preview.emergentagent.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint (no prefix)
@app.get("/health")
async def health_check():
    """헬스체크 엔드포인트"""
    try:
        # MongoDB 연결 확인
        await client.admin.command('ping')
        
        # Redis 연결 확인 (cache_service를 통해)
        redis_status = "healthy"
        try:
            await cache_service.ping()
        except Exception:
            redis_status = "unhealthy"
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "mongodb": "healthy",
                "redis": redis_status,
                "api": "healthy"
            },
            "version": "2.0.0"
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

# Database status endpoint
@app.get("/db-status")
async def database_status():
    """데이터베이스 상태 확인 엔드포인트"""
    try:
        # MongoDB 상태 확인
        mongodb_status = await client.admin.command('ping')
        
        # Redis 상태 확인
        redis_status = "healthy"
        redis_info = {}
        try:
            await cache_service.ping()
            redis_info = {"status": "connected", "ping": "pong"}
        except Exception as e:
            redis_status = "unhealthy"
            redis_info = {"status": "disconnected", "error": str(e)}
        
        # 데이터베이스 통계
        db_stats = await db.command("dbStats")
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "databases": {
                "mongodb": {
                    "status": "healthy",
                    "ping": mongodb_status,
                    "stats": {
                        "collections": db_stats.get("collections", 0),
                        "dataSize": db_stats.get("dataSize", 0),
                        "storageSize": db_stats.get("storageSize", 0)
                    }
                },
                "redis": {
                    "status": redis_status,
                    "info": redis_info
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database unhealthy: {str(e)}")

# API Root endpoint
@app.get("/")
async def root():
    """API 루트 엔드포인트"""
    return {
        "message": "온라인 평가 시스템 API",
        "version": "2.0.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "docs": "/docs",
        "health": "/health",
        "db_status": "/db-status"
    }

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    login_id: str
    password_hash: str
    user_name: str
    email: str
    phone: Optional[str] = None
    role: str  # admin, secretary, evaluator
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    last_login: Optional[datetime] = None

class UserCreate(BaseModel):
    login_id: str
    password: str
    user_name: str
    email: str
    role: str
    phone: Optional[str] = None

class EvaluatorCreate(BaseModel):
    user_name: str
    phone: str
    email: str

class SecretarySignupRequest(BaseModel):
    name: str
    phone: str
    email: str
    reason: str

class SecretaryApproval(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    phone: str
    email: str
    reason: str
    status: str = "pending"  # pending, approved, rejected
    created_at: datetime = Field(default_factory=datetime.utcnow)
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    login_id: str
    user_name: str
    email: str
    phone: Optional[str] = None
    role: str
    created_at: datetime
    is_active: bool
    last_login: Optional[datetime] = None

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class Project(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    deadline: datetime
    created_by: str  # secretary user_id
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    total_companies: int = 0
    total_evaluations: int = 0
    completed_evaluations: int = 0

class ProjectCreate(BaseModel):
    name: str
    description: str
    deadline: str

class Company(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    business_number: str
    address: str
    project_id: str
    files: List[Dict[str, Any]] = []  # Enhanced file metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    evaluation_status: str = "pending"  # pending, in_progress, completed

class CompanyCreate(BaseModel):
    name: str
    business_number: str
    address: str
    project_id: str

class EvaluationItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    max_score: int
    weight: float = 1.0
    project_id: str

class EvaluationItemCreate(BaseModel):
    name: str
    description: str
    max_score: int
    weight: float = 1.0

class EvaluationTemplate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    project_id: str
    items: List[EvaluationItem]
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

class EvaluationTemplateCreate(BaseModel):
    name: str
    description: str
    items: List[EvaluationItemCreate]

class EvaluationSheet(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    evaluator_id: str
    company_id: str
    project_id: str
    template_id: str
    status: str  # draft, submitted, reviewed
    deadline: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    submitted_at: Optional[datetime] = None
    last_modified: datetime = Field(default_factory=datetime.utcnow)
    total_score: Optional[float] = None
    weighted_score: Optional[float] = None

class EvaluationScore(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sheet_id: str
    item_id: str
    score: int
    opinion: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class EvaluationSubmission(BaseModel):
    sheet_id: str
    scores: List[Dict[str, Any]]

class BulkExportRequest(BaseModel):
    project_id: str
    template_id: Optional[str] = None
    format: str = "excel"  # pdf, excel
    export_type: str = "separate"  # separate, combined

class ExportableEvaluation(BaseModel):
    evaluation_id: str
    project_name: str
    company_name: str
    template_name: str
    evaluator_name: str
    submitted_at: Optional[datetime]
    total_score: Optional[float]
    weighted_score: Optional[float]

class AssignmentCreate(BaseModel):
    evaluator_ids: List[str]
    company_ids: List[str]
    template_id: str
    deadline: Optional[str] = None

class BatchAssignmentCreate(BaseModel):
    assignments: List[AssignmentCreate]

class FileMetadata(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    file_type: str
    uploaded_by: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    company_id: str
    is_processed: bool = False

# Utility functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def generate_evaluator_credentials(name: str, phone: str):
    """Generate login credentials from name and phone"""
    # Remove spaces and special characters from name
    clean_name = re.sub(r'[^가-힣a-zA-Z]', '', name)
    # Remove hyphens and spaces from phone
    clean_phone = re.sub(r'[^0-9]', '', phone)
    
    login_id = f"{clean_name}{clean_phone[-4:]}"  # name + last 4 digits
    password = clean_phone[-8:] if len(clean_phone) >= 8 else clean_phone  # last 8 digits of phone
    
    # Debug logging
    logging.info(f"Generated credentials for {name}: login_id={login_id}, password={password}")
    
    return login_id, password

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="자격 증명을 확인할 수 없습니다",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user_data = await db.users.find_one({"id": user_id})
    if user_data is None:
        raise credentials_exception
    
    return User(**user_data)

async def get_current_user_optional(token: Optional[str] = None):
    """선택적 사용자 인증 (토큰이 있으면 검증, 없으면 None 반환)"""
    if not token:
        return None
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
            
        user_data = await db.users.find_one({"id": user_id})
        if user_data is None:
            return None
            
        return User(**user_data)
    except JWTError:
        return None
    return User(**user_data)

def check_admin_or_secretary(user: User):
    if user.role not in ["admin", "secretary"]:
        raise HTTPException(status_code=403, detail="관리자 또는 간사만 접근할 수 있습니다")

async def calculate_evaluation_scores(sheet_id: str, scores_data: List[Dict[str, Any]]):
    """Calculate total and weighted scores"""
    template_data = await db.evaluation_sheets.find_one({"id": sheet_id})
    if not template_data:
        return 0, 0
    
    template = await db.evaluation_templates.find_one({"id": template_data["template_id"]})
    if not template:
        return 0, 0
    
    total_score = 0
    weighted_total = 0
    total_weight = 0
    
    for score_data in scores_data:
        item = next((item for item in template["items"] if item["id"] == score_data["item_id"]), None)
        if item:
            score = score_data["score"]
            weight = item["weight"]
            total_score += score
            weighted_total += score * weight
            total_weight += weight
    
    avg_total_score = total_score / len(scores_data) if scores_data else 0
    avg_weighted_score = weighted_total / total_weight if total_weight > 0 else 0
    
    return avg_total_score, avg_weighted_score

async def update_project_statistics(project_id: str):
    """Update project statistics asynchronously"""
    companies_count = await db.companies.count_documents({"project_id": project_id})
    evaluations_count = await db.evaluation_sheets.count_documents({"project_id": project_id})
    completed_count = await db.evaluation_sheets.count_documents({
        "project_id": project_id, 
        "status": "submitted"
    })
    
    await db.projects.update_one(
        {"id": project_id},
        {"$set": {
            "total_companies": companies_count,
            "total_evaluations": evaluations_count,
            "completed_evaluations": completed_count
        }}
    )

async def background_file_processing(file_path: str, file_id: str):
    """Background task for file processing"""
    try:
        # Simulate file processing (virus scan, format validation, etc.)
        await asyncio.sleep(1)
        
        # Mark file as processed
        await db.file_metadata.update_one(
            {"id": file_id},
            {"$set": {"is_processed": True}}
        )
        
        logging.info(f"File {file_id} processed successfully")
    except Exception as e:
        logging.error(f"File processing failed for {file_id}: {e}")

# Authentication routes
@api_router.post("/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user_data = await db.users.find_one({"login_id": form_data.username})
    if not user_data or not verify_password(form_data.password, user_data["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="아이디 또는 비밀번호가 잘못되었습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login time
    await db.users.update_one(
        {"id": user_data["id"]},
        {"$set": {"last_login": datetime.utcnow()}}
    )
    
    user = User(**user_data)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )
    user_response = UserResponse(**user.dict())
    return {"access_token": access_token, "token_type": "bearer", "user": user_response}

@api_router.post("/auth/secretary-signup")
async def secretary_signup(request: SecretarySignupRequest):
    """간사 회원가입 신청"""
    # 중복 이메일 또는 전화번호 체크
    existing_user = await db.users.find_one({
        "$or": [
            {"email": request.email},
            {"phone": request.phone}
        ]
    })
    
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="이미 등록된 이메일 또는 전화번호입니다"
        )
    
    # 이미 신청한 내역이 있는지 체크
    existing_request = await db.secretary_requests.find_one({
        "$or": [
            {"email": request.email},
            {"phone": request.phone}
        ]
    })
    
    if existing_request:
        raise HTTPException(
            status_code=400,
            detail="이미 신청한 내역이 있습니다. 관리자 승인을 기다려주세요."
        )
    
    # 신청 내역 저장
    approval_request = SecretaryApproval(
        name=request.name,
        phone=request.phone,
        email=request.email,
        reason=request.reason
    )
    await db.secretary_requests.insert_one(approval_request.dict())
    return {
        "message": "간사 회원가입 신청이 완료되었습니다. 관리자 승인 후 로그인이 가능합니다.",
        "request_id": approval_request.id
    }

@api_router.get("/admin/secretary-requests")
async def get_secretary_requests(current_user: User = Depends(get_current_user)):
    """간사 신청 목록 조회 (관리자만)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="관리자만 접근 가능합니다")
    
    requests = await db.secretary_requests.find({"status": "pending"}).to_list(None)
    return requests

@api_router.post("/admin/secretary-requests/{request_id}/approve")
async def approve_secretary_request(
    request_id: str, 
    current_user: User = Depends(get_current_user)
):
    """간사 신청 승인 (관리자만)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="관리자만 접근 가능합니다")
    
    # 신청 내역 찾기
    request_data = await db.secretary_requests.find_one({"id": request_id})
    if not request_data:
        raise HTTPException(status_code=404, detail="신청 내역을 찾을 수 없습니다")
    
    if request_data["status"] != "pending":
        raise HTTPException(status_code=400, detail="이미 처리된 신청입니다")
    
    # 사용자 계정 생성
    user_id = str(uuid.uuid4())
    login_id = request_data["name"]  # 이름을 로그인 ID로 사용
    password_hash = get_password_hash(request_data["phone"].replace("-", ""))  # 전화번호를 비밀번호로 사용
    
    user_data = {
        "id": user_id,
        "login_id": login_id,
        "password_hash": password_hash,
        "user_name": request_data["name"],
        "email": request_data["email"],
        "phone": request_data["phone"],
        "role": "secretary",
        "created_at": datetime.utcnow(),
        "is_active": True
    }
    
    # 사용자 생성
    await db.users.insert_one(user_data)
    
    # 신청 상태 업데이트
    await db.secretary_requests.update_one(
        {"id": request_id},
        {
            "$set": {
                "status": "approved",
                "reviewed_at": datetime.utcnow(),
                "reviewed_by": current_user.id
            }
        }
    )
    
    return {
        "message": "간사 계정이 생성되었습니다",
        "login_id": login_id,
        "user_id": user_id
    }

@api_router.post("/admin/secretary-requests/{request_id}/reject")
async def reject_secretary_request(
    request_id: str,
    current_user: User = Depends(get_current_user)
):
    """간사 신청 거부 (관리자만)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="관리자만 접근 가능합니다")
    
    # 신청 내역 찾기
    request_data = await db.secretary_requests.find_one({"id": request_id})
    if not request_data:
        raise HTTPException(status_code=404, detail="신청 내역을 찾을 수 없습니다")
    
    if request_data["status"] != "pending":
        raise HTTPException(status_code=400, detail="이미 처리된 신청입니다")
    
    # 신청 상태 업데이트
    await db.secretary_requests.update_one(
        {"id": request_id},
        {
            "$set": {
                "status": "rejected",
                "reviewed_at": datetime.utcnow(),
                "reviewed_by": current_user.id
            }
        }
    )
    
    return {"message": "간사 신청이 거부되었습니다"}

@api_router.get("/auth/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return UserResponse(**current_user.dict())

# User management routes
@api_router.post("/users", response_model=UserResponse)
async def create_user(user_data: UserCreate, current_user: User = Depends(get_current_user)):
    check_admin_or_secretary(current_user)
    
    # Check if user already exists
    existing_user = await db.users.find_one({"login_id": user_data.login_id})
    if existing_user:
        raise HTTPException(status_code=400, detail="이미 존재하는 아이디입니다")
    
    hashed_password = get_password_hash(user_data.password)
    user = User(
        login_id=user_data.login_id,
        password_hash=hashed_password,
        user_name=user_data.user_name,
        email=user_data.email,
        phone=user_data.phone,
        role=user_data.role
    )
    
    await db.users.insert_one(user.dict())
    return UserResponse(**user.dict())

# Get all users (for admin and verification)
@api_router.get("/users")
async def get_users(current_user: Optional[User] = Depends(get_current_user_optional)):
    """모든 사용자 목록 조회 (관리자용 또는 검증용)"""
    # 검증용으로 호출된 경우 간단한 정보만 반환
    if not current_user:
        users_count = await db.users.count_documents({})
        sample_users = await db.users.find({}, {"login_id": 1, "user_name": 1, "role": 1}).limit(5).to_list(5)
        return {
            "status": "success",
            "total_users": users_count,
            "sample_users": sample_users,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    # 인증된 사용자인 경우 권한 확인
    check_admin_or_secretary(current_user)
    users = await db.users.find({"is_active": True}).to_list(1000)
    return [UserResponse(**user) for user in users]

# Get all tests/evaluations (basic list)
@api_router.get("/tests")
async def get_tests(current_user: Optional[User] = Depends(get_current_user_optional)):
    """평가/테스트 목록 조회 (인증된 사용자용 또는 검증용)"""
    # 검증용으로 호출된 경우 간단한 정보만 반환
    if not current_user:
        projects_count = await db.projects.count_documents({})
        sample_projects = await db.projects.find({}, {"name": 1, "description": 1, "created_at": 1}).limit(5).to_list(5)
        return {
            "status": "success",
            "total_projects": projects_count,
            "sample_projects": sample_projects,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    # Get evaluation sheets based on user role
    if current_user.role == "evaluator":
        # Evaluators can only see their assigned evaluations
        sheets = await db.evaluation_sheets.find({"evaluator_id": current_user.id}).to_list(1000)
    else:
        # Admin and secretary can see all evaluations
        sheets = await db.evaluation_sheets.find({}).to_list(1000)
    
    # Return simplified test/evaluation data
    tests = []
    for sheet in sheets:
        tests.append({
            "id": sheet.get("id"),
            "company_id": sheet.get("company_id"),
            "template_id": sheet.get("template_id"),
            "status": sheet.get("status", "assigned"),
            "created_at": sheet.get("created_at"),
            "submitted_at": sheet.get("submitted_at"),
            "total_score": sheet.get("total_score", 0)
        })
    
    return tests

@api_router.post("/evaluators")
async def create_evaluator(evaluator_data: EvaluatorCreate, current_user: User = Depends(get_current_user)):
    check_admin_or_secretary(current_user)
    
    # Generate credentials
    login_id, password = generate_evaluator_credentials(evaluator_data.user_name, evaluator_data.phone)
    
    # Check if user already exists
    existing_user = await db.users.find_one({"login_id": login_id})
    if existing_user:
        raise HTTPException(status_code=400, detail="이미 존재하는 평가위원입니다 (이름/전화번호 중복)")
    
    hashed_password = get_password_hash(password)
    user = User(
        login_id=login_id,
        password_hash=hashed_password,
        user_name=evaluator_data.user_name,
        email=evaluator_data.email,
        phone=evaluator_data.phone,
        role="evaluator"
    )
    
    await db.users.insert_one(user.dict())
    response = UserResponse(**user.dict())
    
    # Return with generated credentials for display
    return {
        **response.dict(), 
        "generated_login_id": login_id, 
        "generated_password": password,
        "message": f"평가위원이 성공적으로 생성되었습니다. 아이디: {login_id}, 비밀번호: {password}"
    }

@api_router.get("/evaluators", response_model=List[UserResponse])
async def get_evaluators(current_user: User = Depends(get_current_user)):
    check_admin_or_secretary(current_user)
    
    evaluators = await db.users.find({"role": "evaluator", "is_active": True}).to_list(1000)
    return [UserResponse(**evaluator) for evaluator in evaluators]

# Batch operations
@api_router.post("/evaluators/batch")
async def create_evaluators_batch(
    evaluators_data: List[EvaluatorCreate], 
    current_user: User = Depends(get_current_user)
):
    check_admin_or_secretary(current_user)
    
    created_evaluators = []
    errors = []
    
    # Process in parallel using asyncio.gather
    async def create_single_evaluator(evaluator_data):
        try:
            login_id, password = generate_evaluator_credentials(evaluator_data.user_name, evaluator_data.phone)
            
            existing_user = await db.users.find_one({"login_id": login_id})
            if existing_user:
                return {"error": f"이미 존재하는 평가위원: {evaluator_data.user_name}"}
            
            hashed_password = get_password_hash(password)
            user = User(
                login_id=login_id,
                password_hash=hashed_password,
                user_name=evaluator_data.user_name,
                email=evaluator_data.email,
                phone=evaluator_data.phone,
                role="evaluator"
            )
            
            await db.users.insert_one(user.dict())
            return {
                "user": UserResponse(**user.dict()).dict(),
                "credentials": {"login_id": login_id, "password": password}
            }
        except Exception as e:
            return {"error": f"평가위원 생성 실패 ({evaluator_data.user_name}): {str(e)}"}
    
    # Execute all operations concurrently
    results = await asyncio.gather(*[create_single_evaluator(evaluator) for evaluator in evaluators_data])
    
    for result in results:
        if "error" in result:
            errors.append(result["error"])
        else:
            created_evaluators.append(result)
    
    return {
        "created_count": len(created_evaluators),
        "error_count": len(errors),
        "created_evaluators": created_evaluators,
        "errors": errors
    }

# Project routes
@api_router.get("/projects", response_model=List[Project])
async def get_projects(current_user: User = Depends(get_current_user)):
    projects = await db.projects.find({"is_active": True}).to_list(1000)
    return [Project(**project) for project in projects]

@api_router.post("/projects", response_model=Project)
async def create_project(
    project_data: ProjectCreate, 
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    check_admin_or_secretary(current_user)
    
    deadline_dt = datetime.fromisoformat(project_data.deadline.replace('Z', '+00:00'))
    project = Project(
        name=project_data.name,
        description=project_data.description,
        deadline=deadline_dt,
        created_by=current_user.id
    )
    
    await db.projects.insert_one(project.dict())
    
    # Background task to initialize project statistics
    background_tasks.add_task(update_project_statistics, project.id)
    
    return project

# Company routes with enhanced file handling
@api_router.get("/companies", response_model=List[Company])
async def get_companies(project_id: Optional[str] = None, current_user: User = Depends(get_current_user)):
    query = {}
    if project_id:
        query["project_id"] = project_id
    
    companies = await db.companies.find(query).to_list(1000)
    return [Company(**company) for company in companies]

@api_router.post("/companies", response_model=Company)
async def create_company(
    company_data: CompanyCreate, 
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    check_admin_or_secretary(current_user)
    
    company = Company(**company_data.dict())
    await db.companies.insert_one(company.dict())
    
    # Update project statistics in background
    background_tasks.add_task(update_project_statistics, company.project_id)
    
    return company

# Enhanced file upload with async processing
@api_router.post("/upload")
async def upload_file(
    background_tasks: BackgroundTasks,
    company_id: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    check_admin_or_secretary(current_user)
    
    # Create uploads directory if it doesn't exist
    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)    # Generate unique filename with proper encoding
    file_id = str(uuid.uuid4())
    file_extension = Path(file.filename).suffix
    unique_filename = f"{company_id}_{file_id}{file_extension}"
    file_path = upload_dir / unique_filename
    
    # Save file asynchronously
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    # Create file metadata
    file_metadata = FileMetadata(
        id=file_id,
        filename=unique_filename,
        original_filename=file.filename,
        file_path=str(file_path),
        file_size=len(content),
        file_type=file.content_type,
        uploaded_by=current_user.id,
        company_id=company_id
    )
    
    # Save metadata to database
    await db.file_metadata.insert_one(file_metadata.dict())
    
    # Update company's files list
    await db.companies.update_one(
        {"id": company_id},
        {"$push": {"files": file_metadata.dict()}}
    )
    
    # Add background task for file processing
    background_tasks.add_task(background_file_processing, str(file_path), file_id)
    
    return {
        "message": "파일이 성공적으로 업로드되었습니다",
        "file_id": file_id,
        "filename": file.filename
    }

@api_router.get("/files/{file_id}")
async def get_file(file_id: str, current_user: User = Depends(get_current_user)):
    """Serve files for preview"""
    file_metadata = await db.file_metadata.find_one({"id": file_id})
    if not file_metadata:
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")
    
    file_path = Path(file_metadata["file_path"])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="파일이 존재하지 않습니다")
    
    return FileResponse(
        path=file_path,
        filename=file_metadata["original_filename"],
        media_type=file_metadata["file_type"]
    )

@api_router.get("/files/{file_id}/preview")
async def preview_file(file_id: str):
    """Get file content for inline preview - 권한 체크 없이 누구나 접근 가능"""
    file_metadata = await db.file_metadata.find_one({"id": file_id})
    if not file_metadata:
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")
    
    file_path = Path(file_metadata["file_path"])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="파일이 존재하지 않습니다")
    
    # For PDF files, return as base64 for PDF.js
    if file_metadata["file_type"] == "application/pdf":
        async with aiofiles.open(file_path, 'rb') as f:
            content = await f.read()
            base64_content = base64.b64encode(content).decode('utf-8')
            return {
                "content": base64_content,
                "type": "pdf",
                "filename": file_metadata["original_filename"]
            }
    
    # For other files, return metadata
    return {
        "type": "other",
        "filename": file_metadata["original_filename"],
        "size": file_metadata["file_size"],
        "download_url": f"/api/files/{file_id}"
    }

# Enhanced assignment system
@api_router.post("/assignments")
async def create_assignments(
    assignment_data: AssignmentCreate, 
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    check_admin_or_secretary(current_user)
    
    deadline = None
    if assignment_data.deadline:
        deadline = datetime.fromisoformat(assignment_data.deadline.replace('Z', '+00:00'))
    
    created_sheets = []
    
    # Create evaluation sheets for each evaluator-company combination
    tasks = []
    for evaluator_id in assignment_data.evaluator_ids:
        for company_id in assignment_data.company_ids:
            tasks.append(create_single_assignment(evaluator_id, company_id, assignment_data.template_id, deadline))
    
    # Execute assignments concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for result in results:
        if isinstance(result, Exception):
            logging.error(f"Assignment creation failed: {result}")
        elif result:
            created_sheets.append(result)
    
    # Update project statistics in background
    if created_sheets:
        company_data = await db.companies.find_one({"id": assignment_data.company_ids[0]})
        if company_data:
            background_tasks.add_task(update_project_statistics, company_data["project_id"])
    
    return {"message": f"{len(created_sheets)}개의 평가가 할당되었습니다", "count": len(created_sheets)}

async def create_single_assignment(evaluator_id: str, company_id: str, template_id: str, deadline: datetime):
    """Helper function to create a single assignment"""
    try:
        # Get company to find project_id
        company_data = await db.companies.find_one({"id": company_id})
        if not company_data:
            return None
            
        # Check if assignment already exists
        existing_sheet = await db.evaluation_sheets.find_one({
            "evaluator_id": evaluator_id,
            "company_id": company_id,
            "template_id": template_id
        })
        
        if not existing_sheet:
            sheet = EvaluationSheet(
                evaluator_id=evaluator_id,
                company_id=company_id,
                project_id=company_data["project_id"],
                template_id=template_id,
                status="draft",
                deadline=deadline
            )
            
            await db.evaluation_sheets.insert_one(sheet.dict())
            return sheet
    except Exception as e:
        logging.error(f"Failed to create assignment: {e}")
        return None

@api_router.post("/assignments/batch")
async def create_batch_assignments(
    batch_data: BatchAssignmentCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    check_admin_or_secretary(current_user)
    
    total_created = 0
    
    # Process all assignments concurrently
    tasks = []
    for assignment in batch_data.assignments:
        tasks.append(create_assignments(assignment, background_tasks, current_user))
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for result in results:
        if isinstance(result, Exception):
            logging.error(f"Batch assignment failed: {result}")
        else:
            total_created += result.get("count", 0)
    
    return {"message": f"총 {total_created}개의 평가가 일괄 할당되었습니다", "total_count": total_created}

# Enhanced evaluation system
@api_router.get("/evaluation/{sheet_id}")
async def get_evaluation_sheet(sheet_id: str, current_user: User = Depends(get_current_user)):
    sheet_data = await db.evaluation_sheets.find_one({"id": sheet_id})
    if not sheet_data:
        raise HTTPException(status_code=404, detail="평가지를 찾을 수 없습니다")
    
    sheet = EvaluationSheet(**sheet_data)
    
    # Check permissions
    if current_user.role == "evaluator" and sheet.evaluator_id != current_user.id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다")
    
    # Get related data concurrently
    company_task = db.companies.find_one({"id": sheet.company_id})
    project_task = db.projects.find_one({"id": sheet.project_id})
    template_task = db.evaluation_templates.find_one({"id": sheet.template_id})
    scores_task = db.evaluation_scores.find({"sheet_id": sheet_id}).to_list(1000)
    
    company_data, project_data, template_data, scores = await asyncio.gather(
        company_task, project_task, template_task, scores_task
    )
    
    return {
        "sheet": sheet,
        "company": Company(**company_data) if company_data else None,
        "project": Project(**project_data) if project_data else None,
        "template": EvaluationTemplate(**template_data) if template_data else None,
        "scores": [EvaluationScore(**score) for score in scores]
    }

@api_router.post("/evaluation/submit")
async def submit_evaluation(
    submission: EvaluationSubmission, 
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    sheet_data = await db.evaluation_sheets.find_one({"id": submission.sheet_id})
    if not sheet_data:
        raise HTTPException(status_code=404, detail="평가지를 찾을 수 없습니다")
    
    sheet = EvaluationSheet(**sheet_data)
    
    # Check permissions
    if current_user.role == "evaluator" and sheet.evaluator_id != current_user.id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다")
    
    # Calculate scores
    total_score, weighted_score = await calculate_evaluation_scores(submission.sheet_id, submission.scores)
    
    # Delete existing scores and save new ones concurrently
    delete_task = db.evaluation_scores.delete_many({"sheet_id": submission.sheet_id})
    
    # Prepare new scores
    new_scores = []
    for score_data in submission.scores:
        score = EvaluationScore(
            sheet_id=submission.sheet_id,
            item_id=score_data["item_id"],
            score=score_data["score"],
            opinion=score_data.get("opinion", "")
        )
        new_scores.append(score.dict())
    
    # Execute operations
    await delete_task
    if new_scores:
        await db.evaluation_scores.insert_many(new_scores)
      # Update sheet status
    await db.evaluation_sheets.update_one(
        {"id": submission.sheet_id},
        {"$set": {
            "status": "submitted", 
            "submitted_at": datetime.utcnow(),
            "last_modified": datetime.utcnow(),
            "total_score": total_score,
            "weighted_score": weighted_score
        }}
    )
    
    # Invalidate cache for the evaluator
    await cache_service.invalidate_user_cache(current_user.id)
    
    # Send real-time notification
    evaluation_data = {
        "sheet_id": submission.sheet_id,
        "project_id": sheet.project_id,
        "total_score": total_score,
        "weighted_score": weighted_score,
        "evaluator_name": current_user.user_name
    }
    
    # Notify the evaluator
    await notification_service.send_evaluation_complete_notification(
        current_user.id, 
        evaluation_data
    )
    
    # Notify project room members (admins, secretaries)
    await notification_service.send_project_update_notification(
        sheet.project_id,
        {
            "title": "평가 완료",
            "message": f"{current_user.user_name}님이 평가를 완료했습니다",
            "type": "evaluation_submitted",
            "data": evaluation_data
        }
    )
    
    # Update project statistics in background
    background_tasks.add_task(update_project_statistics, sheet.project_id)
    
    return {"message": "평가가 성공적으로 제출되었습니다", "total_score": total_score, "weighted_score": weighted_score}

@api_router.post("/evaluation/save")
async def save_evaluation(submission: EvaluationSubmission, current_user: User = Depends(get_current_user)):
    sheet_data = await db.evaluation_sheets.find_one({"id": submission.sheet_id})
    if not sheet_data:
        raise HTTPException(status_code=404, detail="평가지를 찾을 수 없습니다")
    
    sheet = EvaluationSheet(**sheet_data)
    
    # Check permissions
    if current_user.role == "evaluator" and sheet.evaluator_id != current_user.id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다")
    
    # Delete existing scores and save new ones
    await db.evaluation_scores.delete_many({"sheet_id": submission.sheet_id})
    
    # Save new scores
    new_scores = []
    for score_data in submission.scores:
        score = EvaluationScore(
            sheet_id=submission.sheet_id,
            item_id=score_data["item_id"],
            score=score_data["score"],
            opinion=score_data.get("opinion", "")
        )
        new_scores.append(score.dict())
    
    if new_scores:
        await db.evaluation_scores.insert_many(new_scores)
    
    # Update last modified time
    await db.evaluation_sheets.update_one(
        {"id": submission.sheet_id},
        {"$set": {"last_modified": datetime.utcnow()}}
    )
    
    return {"message": "평가가 임시저장되었습니다"}

# Enhanced dashboard routes
@api_router.get("/dashboard/evaluator")
async def get_evaluator_dashboard(current_user: User = Depends(get_current_user)):
    if current_user.role != "evaluator":
        raise HTTPException(status_code=403, detail="평가위원만 접근할 수 있습니다")
    
    # Try to get cached dashboard data
    cached_data = await cache_service.get_cached_dashboard_data(current_user.id)
    if cached_data:
        logger.info(f"🚀 Returning cached dashboard data for user {current_user.id}")
        return cached_data
    
    # Get assigned evaluation sheets
    sheets = await db.evaluation_sheets.find({"evaluator_id": current_user.id}).to_list(1000)
    
    # Get related data for all sheets concurrently
    tasks = []
    for sheet_data in sheets:
        sheet = EvaluationSheet(**sheet_data)
        company_task = db.companies.find_one({"id": sheet.company_id})
        project_task = db.projects.find_one({"id": sheet.project_id})
        template_task = db.evaluation_templates.find_one({"id": sheet.template_id})
        tasks.extend([company_task, project_task, template_task])
    
    if tasks:
        results = await asyncio.gather(*tasks)
        # Reorganize results into groups of 3 (company, project, template)
        result_groups = [results[i:i+3] for i in range(0, len(results), 3)]
    else:
        result_groups = []
    
    # Build response
    response = []
    for i, sheet_data in enumerate(sheets):
        sheet = EvaluationSheet(**sheet_data)
        if i < len(result_groups):
            company_data, project_data, template_data = result_groups[i]
            if company_data and project_data and template_data:
                response.append({
                    "sheet": sheet,
                    "company": Company(**company_data),
                    "project": Project(**project_data),
                    "template": EvaluationTemplate(**template_data)
                })
    
    # Cache the dashboard data for 5 minutes
    await cache_service.cache_dashboard_data(current_user.id, response, ttl=300)
    
    return response

@api_router.get("/dashboard/admin")
async def get_admin_dashboard(current_user: User = Depends(get_current_user)):
    if current_user.role not in ["admin", "secretary"]:
        raise HTTPException(status_code=403, detail="관리자 또는 간사만 접근할 수 있습니다")
    
    # Get all statistics concurrently
    stats_tasks = [
        db.projects.count_documents({"is_active": True}),
        db.companies.count_documents({}),
        db.users.count_documents({"role": "evaluator", "is_active": True}),
        db.evaluation_sheets.count_documents({}),
        db.evaluation_sheets.count_documents({"status": "submitted"}),
        db.projects.find({"is_active": True}).sort("created_at", -1).limit(5).to_list(5)
    ]
    
    projects_count, companies_count, evaluators_count, total_sheets, completed_sheets, recent_projects = await asyncio.gather(*stats_tasks)
    
    return {
        "stats": {
            "projects": projects_count,
            "companies": companies_count,
            "evaluators": evaluators_count,
            "total_evaluations": total_sheets,
            "completed_evaluations": completed_sheets,
            "completion_rate": round((completed_sheets / total_sheets * 100) if total_sheets > 0 else 0, 1)
        },
        "recent_projects": [Project(**project) for project in recent_projects]
    }

# Analytics and reporting
@api_router.get("/analytics/project/{project_id}")
async def get_project_analytics(project_id: str, current_user: User = Depends(get_current_user)):
    check_admin_or_secretary(current_user)
    
    # Get project analytics concurrently
    tasks = [
        db.evaluation_sheets.find({"project_id": project_id, "status": "submitted"}).to_list(1000),
        db.companies.find({"project_id": project_id}).to_list(1000),
        db.evaluation_templates.find({"project_id": project_id}).to_list(1000)
    ]
    
    sheets, companies, templates = await asyncio.gather(*tasks)
    
    # Calculate analytics
    total_evaluations = len(sheets)
    companies_evaluated = len(set(sheet["company_id"] for sheet in sheets))
    
    # Score analytics
    avg_scores = {}
    if sheets:
        for sheet in sheets:
            if sheet.get("total_score"):
                template_name = next((t["name"] for t in templates if t["id"] == sheet["template_id"]), "Unknown")
                if template_name not in avg_scores:
                    avg_scores[template_name] = []
                avg_scores[template_name].append(sheet["total_score"])
    
    for template_name in avg_scores:
        scores = avg_scores[template_name]
        avg_scores[template_name] = {
            "average": sum(scores) / len(scores),
            "min": min(scores),
            "max": max(scores),
            "count": len(scores)
        }
    
    return {
        "project_id": project_id,
        "total_companies": len(companies),
        "companies_evaluated": companies_evaluated,
        "total_evaluations": total_evaluations,
        "completion_rate": round((companies_evaluated / len(companies) * 100) if companies else 0, 1),        "score_analytics": avg_scores
    }

# Export routes for comprehensive evaluation reports
@api_router.get("/evaluations/{evaluation_id}/export")
async def export_single_evaluation(
    evaluation_id: str,
    format: str = Query(..., regex="^(pdf|excel)$", description="Export format: pdf or excel"),
    current_user: User = Depends(get_current_user)
):
    """단일 평가 데이터를 PDF 또는 Excel로 추출"""
    check_admin_or_secretary(current_user)
    
    try:
        # Get evaluation sheet data
        sheet_data = await db.evaluation_sheets.find_one({"id": evaluation_id})
        if not sheet_data:
            raise HTTPException(status_code=404, detail="평가지를 찾을 수 없습니다")
        
        sheet = EvaluationSheet(**sheet_data)
        
        # Only export submitted evaluations
        if sheet.status != "submitted":
            raise HTTPException(status_code=400, detail="제출된 평가만 추출할 수 있습니다")
        
        # Get related data concurrently
        company_task = db.companies.find_one({"id": sheet.company_id})
        project_task = db.projects.find_one({"id": sheet.project_id})
        template_task = db.evaluation_templates.find_one({"id": sheet.template_id})
        scores_task = db.evaluation_scores.find({"sheet_id": evaluation_id}).to_list(1000)
        evaluator_task = db.users.find_one({"id": sheet.evaluator_id})
        
        company_data, project_data, template_data, scores, evaluator_data = await asyncio.gather(
            company_task, project_task, template_task, scores_task, evaluator_task
        )
        
        if not all([company_data, project_data, template_data, evaluator_data]):
            raise HTTPException(status_code=404, detail="관련 데이터를 찾을 수 없습니다")
        
        # Prepare evaluation data
        evaluation_data = {
            "sheet": sheet.dict(),
            "company": company_data,
            "project": project_data,
            "template": template_data,
            "scores": [{"item_id": s["item_id"], "score": s["score"], "opinion": s["opinion"]} for s in scores],
            "evaluator": evaluator_data
        }
        
        # Generate filename
        submitted_date = sheet.submitted_at or datetime.utcnow()
        filename = exporter.generate_filename(
            project_data["name"],
            company_data["name"],
            submitted_date,
            format
        )
        
        # Export based on format
        if format == "pdf":
            buffer = await exporter.export_single_evaluation_pdf(evaluation_data)
            media_type = "application/pdf"
        else:  # excel
            buffer = await exporter.export_single_evaluation_excel(evaluation_data)
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        
        return StreamingResponse(
            io.BytesIO(buffer.read()),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Export error: {str(e)}")
        raise HTTPException(status_code=500, detail="파일 생성 중 오류가 발생했습니다")

@api_router.post("/evaluations/bulk-export")
async def export_bulk_evaluations(
    export_request: dict,
    current_user: User = Depends(get_current_user)
):
    """여러 평가 데이터를 일괄 추출"""
    check_admin_or_secretary(current_user)
    
    try:
        project_id = export_request.get("project_id")
        template_id = export_request.get("template_id")
        format_type = export_request.get("format", "excel")
        export_type = export_request.get("export_type", "separate")  # separate, combined
        
        if not project_id:
            raise HTTPException(status_code=400, detail="프로젝트 ID가 필요합니다")
        
        # Build query for submitted evaluations
        query = {
            "project_id": project_id,
            "status": "submitted"
        }
        
        if template_id:
            query["template_id"] = template_id
        
        # Get evaluation sheets
        sheets = await db.evaluation_sheets.find(query).to_list(1000)
        
        if not sheets:
            raise HTTPException(status_code=404, detail="추출할 평가 데이터가 없습니다")
        
        # Get all related data
        evaluation_data_list = []
        for sheet_data in sheets:
            sheet = EvaluationSheet(**sheet_data)
            
            # Get related data concurrently
            company_task = db.companies.find_one({"id": sheet.company_id})
            project_task = db.projects.find_one({"id": sheet.project_id})
            template_task = db.evaluation_templates.find_one({"id": sheet.template_id})
            scores_task = db.evaluation_scores.find({"sheet_id": sheet.id}).to_list(1000)
            evaluator_task = db.users.find_one({"id": sheet.evaluator_id})
            
            company_data, project_data, template_data, scores, evaluator_data = await asyncio.gather(
                company_task, project_task, template_task, scores_task, evaluator_task
            )
            
            if all([company_data, project_data, template_data, evaluator_data]):
                evaluation_data = {
                    "sheet": sheet.dict(),
                    "company": company_data,
                    "project": project_data,
                    "template": template_data,
                    "scores": [{"item_id": s["item_id"], "score": s["score"], "opinion": s["opinion"]} for s in scores],
                    "evaluator": evaluator_data
                }
                evaluation_data_list.append(evaluation_data)
        
        if not evaluation_data_list:
            raise HTTPException(status_code=404, detail="유효한 평가 데이터가 없습니다")
        
        if export_type == "combined":
            # 하나의 Excel 파일로 결합
            if format_type == "pdf":
                raise HTTPException(status_code=400, detail="PDF는 개별 파일로만 추출 가능합니다")
            
            buffer = await exporter.export_bulk_evaluations_excel(evaluation_data_list)
            project_name = evaluation_data_list[0]["project"]["name"]
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{project_name}_종합평가서_{timestamp}.xlsx"
            
            return StreamingResponse(
                io.BytesIO(buffer.read()),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"}
            )
        else:
            # 개별 파일들을 ZIP으로 압축
            import zipfile
            
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for eval_data in evaluation_data_list:
                    # Generate individual file
                    submitted_date = eval_data["sheet"]["submitted_at"] or datetime.utcnow()
                    filename = exporter.generate_filename(
                        eval_data["project"]["name"],
                        eval_data["company"]["name"],
                        submitted_date,
                        format_type
                    )
                    
                    if format_type == "pdf":
                        file_buffer = await exporter.export_single_evaluation_pdf(eval_data)
                    else:
                        file_buffer = await exporter.export_single_evaluation_excel(eval_data)
                    
                    zip_file.writestr(filename, file_buffer.read())
            
            zip_buffer.seek(0)
            project_name = evaluation_data_list[0]["project"]["name"]
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            zip_filename = f"{project_name}_종합평가서_일괄추출_{timestamp}.zip"
            
            return StreamingResponse(
                zip_buffer,
                media_type="application/zip",
                headers={"Content-Disposition": f"attachment; filename*=UTF-8''{zip_filename}"}
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Bulk export error: {str(e)}")
        raise HTTPException(status_code=500, detail="일괄 추출 중 오류가 발생했습니다")

@api_router.get("/evaluations/export-list")
async def get_exportable_evaluations(
    project_id: Optional[str] = None,
    template_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """추출 가능한 평가 목록 조회 (제출된 평가만)"""
    check_admin_or_secretary(current_user)
    
    try:
        # Build query for submitted evaluations
        query = {"status": "submitted"}
        
        if project_id:
            query["project_id"] = project_id
        if template_id:
            query["template_id"] = template_id
        
        # Get evaluation sheets
        sheets = await db.evaluation_sheets.find(query).to_list(1000)
        
        # Get related data for display
        result = []
        for sheet_data in sheets:
            sheet = EvaluationSheet(**sheet_data)
            
            # Get related data concurrently
            company_task = db.companies.find_one({"id": sheet.company_id})
            project_task = db.projects.find_one({"id": sheet.project_id})
            template_task = db.evaluation_templates.find_one({"id": sheet.template_id})
            evaluator_task = db.users.find_one({"id": sheet.evaluator_id})
            
            company_data, project_data, template_data, evaluator_data = await asyncio.gather(
                company_task, project_task, template_task, evaluator_task
            )
            
            if all([company_data, project_data, template_data, evaluator_data]):
                result.append({
                    "evaluation_id": sheet.id,
                    "project_name": project_data["name"],
                    "company_name": company_data["name"],
                    "template_name": template_data["name"],
                    "evaluator_name": evaluator_data["user_name"],
                    "submitted_at": sheet.submitted_at,
                    "total_score": sheet.total_score,
                    "weighted_score": sheet.weighted_score
                })
        
        return result
        
    except Exception as e:
        logging.error(f"Get exportable evaluations error: {str(e)}")
        raise HTTPException(status_code=500, detail="추출 가능한 평가 목록 조회 중 오류가 발생했습니다")

# Template routes
@api_router.get("/templates", response_model=List[EvaluationTemplate])
async def get_templates(project_id: Optional[str] = None, current_user: User = Depends(get_current_user)):
    query = {"is_active": True}
    if project_id:
        query["project_id"] = project_id
    
    templates = await db.evaluation_templates.find(query).to_list(1000)
    return [EvaluationTemplate(**template) for template in templates]

@api_router.post("/templates", response_model=EvaluationTemplate)
async def create_template(
    template_data: EvaluationTemplateCreate, 
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    check_admin_or_secretary(current_user)
    
    # Create evaluation items
    items = []
    for item_data in template_data.items:
        item = EvaluationItem(
            **item_data.dict(),
            project_id=project_id
        )
        items.append(item)
    
    template = EvaluationTemplate(
        name=template_data.name,
        description=template_data.description,
        project_id=project_id,
        items=items,
        created_by=current_user.id
    )
    
    await db.evaluation_templates.insert_one(template.dict())
    return template

# System health and monitoring
#@api_router.get("/health")
#async def health_check():
#    """헬스체크 엔드포인트"""
#    try:
#        # MongoDB 연결 확인
#        await client.admin.command('ping')
#        
#        # Redis 연결 확인 (cache_service를 통해)
#        redis_status = "healthy"
#        try:
#            await cache_service.ping()
#        except Exception:
#            redis_status = "unhealthy"
#        
#        return {
#            "status": "healthy",
#            "timestamp": datetime.utcnow().isoformat(),
#            "services": {
#                "mongodb": "healthy",
#                "redis": redis_status,
#                "api": "healthy"
#            },
#            "version": "2.0.0"
#        }
#    except Exception as e:
#        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

# Enhanced health monitoring endpoints
@api_router.get("/health/detailed")
async def detailed_health_check():
    """Comprehensive health check with system metrics"""
    return await health_monitor.get_comprehensive_health_report()

@api_router.get("/health/liveness")
async def liveness_probe():
    """Kubernetes-style liveness probe"""
    return await health_monitor.get_liveness_probe()

@api_router.get("/health/readiness")
async def readiness_probe():
    """Kubernetes-style readiness probe"""
    return await health_monitor.get_readiness_probe()

@api_router.get("/health/metrics")
async def system_metrics():
    """System performance metrics"""
    return await health_monitor.get_system_metrics()

# WebSocket endpoint for real-time notifications
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time notifications"""
    await connection_manager.connect(websocket, user_id)
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "join_room":
                room_id = message.get("room_id")
                if room_id:
                    await connection_manager.join_room(websocket, room_id)
            elif message.get("type") == "leave_room":
                room_id = message.get("room_id")
                if room_id:
                    await connection_manager.leave_room(websocket, room_id)
            elif message.get("type") == "ping":
                # Respond to ping with pong
                await connection_manager.send_personal_message({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                }, websocket)
                
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        connection_manager.disconnect(websocket)

# Initialize default users
@api_router.post("/init")
async def initialize_system():
    # Check if users already exist
    existing_users = await db.users.count_documents({})
    if existing_users > 0:
        return {"message": "시스템이 이미 초기화되었습니다"}
    
    # Create default users
    default_users = [
        {
            "login_id": "admin",
            "password": "admin123",
            "user_name": "시스템 관리자",
            "email": "admin@test.com",
            "role": "admin"
        },
        {
            "login_id": "secretary01",
            "password": "secretary123",
            "user_name": "간사 1",
            "email": "secretary01@test.com",
            "role": "secretary"
        },
        {
            "login_id": "evaluator01",
            "password": "evaluator123",
            "user_name": "평가위원 1",
            "email": "evaluator01@test.com",
            "role": "evaluator"
        }
    ]
    
    # Create users concurrently
    tasks = []
    for user_data in default_users:
        hashed_password = get_password_hash(user_data["password"])
        user = User(
            login_id=user_data["login_id"],
            password_hash=hashed_password,
            user_name=user_data["user_name"],
            email=user_data["email"],
            role=user_data["role"]
        )
        tasks.append(db.users.insert_one(user.dict()))
    
    await asyncio.gather(*tasks)
    
    return {"message": "시스템이 성공적으로 초기화되었습니다", "users": len(default_users)}

# Additional API endpoints for deployment verification
@api_router.get("/status")
async def api_status():
    """API 상태 확인 엔드포인트 (deployment checker용)"""
    try:
        # MongoDB 연결 확인
        await client.admin.command('ping')
        mongodb_status = "connected"
        
        # Redis 연결 확인
        redis_status = "connected"
        try:
            await cache_service.ping()
        except Exception:
            redis_status = "disconnected"        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": {
                "status": mongodb_status,
                "type": "mongodb"
            },
            "cache": {
                "status": redis_status,
                "type": "redis"
            },
            "api": {
                "status": "connected",
                "version": "2.0.0"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")

# Include the router in the main app
app.include_router(api_router)

# ...existing code...

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 온라인 평가 시스템 v2.0.0 시작됨")
    logger.info(f"🔗 MongoDB 연결: {mongo_url}")
    
    # Initialize cache service
    await cache_service.connect()
    
    # Log startup completion
    logger.info("✅ 모든 서비스가 성공적으로 시작되었습니다")

@app.on_event("shutdown")
async def shutdown_db_client():
    logger.info("🔄 시스템 종료 중...")
    
    # Disconnect cache service
    await cache_service.disconnect()
    
    # Close database connection
    client.close()
    
    # Shutdown thread pool
    executor.shutdown(wait=True)
    
    logger.info("✅ 시스템이 안전하게 종료되었습니다")
