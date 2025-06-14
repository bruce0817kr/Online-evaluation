from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks, Query, WebSocket, WebSocketDisconnect
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import FileResponse, StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request # 추가
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging  # Keep for compatibility with existing modules
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
import time  # Added for enhanced logging middleware

from cache_service import cache_service  # Import the instance directly

# Placeholder imports for missing models and functions
# These should be adjusted based on actual project structure
import models
from models import (  # Assuming a models.py or schemas.py
    Token, User, UserResponse, UserCreate, 
    SecretarySignupRequest, SecretaryApproval,
    UserInDB, # Assuming UserInDB might be used internally or by CRUD
    EvaluatorCreate, Project, ProjectCreate, Company, CompanyCreate,
    FileMetadata, EvaluationTemplateCreate, EvaluationTemplate,  # Added missing models
    AssignmentCreate, BatchAssignmentCreate, EvaluationScore, EvaluationSubmission,
    EvaluationSheet  # Added additional models
)
import security
from security import (
    create_access_token, 
    get_current_user, 
    get_password_hash, 
    verify_password, 
    check_admin_or_secretary, 
    get_current_user_optional,
    oauth2_scheme as security_oauth2_scheme, # Import with an alias if server.py defines its own
    imported_pwd_context, # Use the correctly named imported context
    security_config, # If server.py still needs direct access to config values
    generate_evaluator_credentials  # Added the new function
)
try:
    import middleware
    from middleware import (
        SecurityMiddleware, RequestValidationMiddleware, CORSSecurityMiddleware,
        IPWhitelistMiddleware, FileUploadSecurityMiddleware
    )
except ImportError:
    middleware = None
    print("Warning: Middleware module not found. Creating placeholder classes.")
# Import new comprehensive security systems
try:
    import security_monitoring
    from security_monitoring import (
        security_monitor, SecurityMiddleware as EnhancedSecurityMiddleware,
        SecurityEvent, SecurityEventType, SecuritySeverity
    )
except ImportError:
    security_monitoring = None
    print("Warning: Security monitoring module not found.")

try:
    import api_security
    from api_security import security_validator, ValidationConfig, SecurityLevel
except ImportError:
    api_security = None
    print("Warning: API security module not found.")

# Import Prometheus metrics and enhanced health monitoring
try:
    import prometheus_metrics
    from prometheus_metrics import setup_prometheus_metrics, get_prometheus_metrics
except ImportError:
    prometheus_metrics = None
    print("Warning: Prometheus metrics module not found.")

try:
    import enhanced_health_monitoring
    from enhanced_health_monitoring import setup_health_monitor, health_router
except ImportError:
    enhanced_health_monitoring = None
    print("Warning: Enhanced health monitoring module not found.")

# Import enhanced logging system
try:
    import enhanced_logging
    from enhanced_logging import (
        setup_logging, get_logger, RequestContext, log_async_performance,
        log_database_operation, log_security_event, log_startup_info, log_shutdown_info,
        request_id_context, user_id_context, session_id_context
    )
except ImportError:
    enhanced_logging = None
    import logging
    def get_logger(name):
        return logging.getLogger(name)
    print("Warning: Enhanced logging module not found. Using standard logging.")

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Initialize enhanced logging system
setup_logging(
    service_name="online-evaluation-backend",
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    log_file="/app/logs/app.log"
)

# Get enhanced logger instance
logger = get_logger(__name__)

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
# health_monitor = HealthMonitor(client) # This line is causing the NameError
# The HealthMonitor class definition or import is missing.
# For now, we will comment this out to allow the server to start.
# It should be properly defined or imported from enhanced_health_monitoring.py later.

# JWT settings - Now using security config
SECRET_KEY = security_config.JWT_SECRET_KEY
ALGORITHM = security_config.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = security_config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES

# Password context - Now using enhanced security
pwd_context = imported_pwd_context # Correctly assign the imported instance
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login") # This can be removed if security_oauth2_scheme from security.py is used

# Create the main app with enhanced security configuration
# Always enable /docs and /redoc for easier debugging
app = FastAPI(
    title=security_config.API_TITLE if hasattr(security_config, 'API_TITLE') else "온라인 평가 시스템",
    version="2.0.0", # Or "1.0.0" if that was the intended version from the previous edit
    description="Secure Online Evaluation System with comprehensive authentication and authorization",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Request logging middleware for context tracking
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Middleware to track request context and log HTTP requests"""
    import uuid
    from urllib.parse import urlparse
    
    # Generate request ID
    request_id = str(uuid.uuid4())
    
    # Extract user information from request if available
    user_id = None
    session_id = None
    
    # Try to extract user info from Authorization header
    authorization = request.headers.get("authorization")
    if authorization and authorization.startswith("Bearer "):
        try:
            # Decode JWT to get user info (simplified)
            token = authorization.split(" ")[1]
            # Note: In a real scenario, you'd decode the JWT here
            # For now, we'll set it when we have user context
            pass
        except Exception:
            pass
    
    # Extract session info from cookies if available
    session_id = request.cookies.get("session_id")
    
    # Set up request context
    with RequestContext(request_id=request_id, user_id=user_id, session_id=session_id):
        start_time = time.time()
        
        # Log incoming request
        logger.info(f"Incoming request: {request.method} {request.url.path}", extra={
            'custom_http_method': request.method,
            'custom_http_uri': str(request.url.path),
            'custom_http_user_agent': request.headers.get('user-agent', ''),
            'custom_http_remote_ip': request.client.host if request.client else 'unknown'
        })
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = (time.time() - start_time) * 1000
            
            # Log response
            logger.info(f"Request completed: {request.method} {request.url.path}", extra={
                'custom_http_method': request.method,
                'custom_http_uri': str(request.url.path),
                'custom_http_status_code': response.status_code,
                'custom_http_duration': duration
            })
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Calculate duration for error case
            duration = (time.time() - start_time) * 1000
            
            # Log error
            logger.error(f"Request failed: {request.method} {request.url.path}: {str(e)}", extra={
                'custom_http_method': request.method,
                'custom_http_uri': str(request.url.path),
                'custom_http_duration': duration,
                'custom_error_type': type(e).__name__
            })
            
            raise

# Enhanced logging configuration - replaced with enhanced logging system
# The enhanced logging system is now initialized above with structured logging
# log_level = os.getenv("LOG_LEVEL", "INFO")
# logging.basicConfig(
#     level=getattr(logging, log_level),
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# )
# logger = logging.getLogger(__name__)

# Add security middleware stack - Enhanced with comprehensive monitoring
app.add_middleware(EnhancedSecurityMiddleware, security_monitor)
app.add_middleware(SecurityMiddleware, enable_rate_limiting=True, enable_security_headers=True)
app.add_middleware(RequestValidationMiddleware)
app.add_middleware(FileUploadSecurityMiddleware)
app.add_middleware(IPWhitelistMiddleware, admin_paths=["/api/admin", "/api/init"])

# Enhanced CORS configuration using security config
app.add_middleware(
    CORSMiddleware,
    allow_origins=security_config.CORS_ORIGINS,
    allow_credentials=security_config.CORS_ALLOW_CREDENTIALS,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
    expose_headers=["X-Total-Count"],
    max_age=3600,
)

# Initialize Prometheus metrics and enhanced health monitoring
prometheus_metrics = setup_prometheus_metrics(app, cache_service.redis_client, client)
health_monitor_instance = setup_health_monitor(client, cache_service.redis_client)

# Application startup and shutdown events for enhanced logging
@app.on_event("startup")
async def startup_event():
    """Application startup event with enhanced logging"""
    # Set startup context
    with RequestContext(request_id="startup", user_id="system"):
        log_startup_info()
        logger.info("FastAPI application startup initiated", extra={
            'custom_event': 'application_startup',
            'custom_environment': os.getenv("ENVIRONMENT", "development"),
            'custom_mongodb_url': mongo_url.split('@')[-1] if '@' in mongo_url else 'localhost',  # Hide credentials
            'custom_services': ['mongodb', 'redis', 'prometheus']
        })
        
        # Initialize the database connection in security module
        from security import set_database
        set_database(db)
        logger.info("Database connection initialized in security module", extra={
            'custom_service': 'security_db_init',
            'custom_status': 'completed'
        })
        
        # Log MongoDB connection details
        try:
            await client.admin.command('ping')
            logger.info("MongoDB connection established", extra={
                'custom_service': 'mongodb',
                'custom_status': 'connected'
            })
        except Exception as e:
            logger.error("MongoDB connection failed", extra={
                'custom_service': 'mongodb',
                'custom_status': 'failed',
                'custom_error_type': type(e).__name__
            })
        
        # Initialize cache service
        try:
            await cache_service.connect()
            logger.info("Cache service initialized", extra={
                'custom_service': 'redis',
                'custom_status': 'connected'
            })
        except Exception as e:
            logger.error("Cache service initialization failed", extra={
                'custom_service': 'redis',
                'custom_status': 'failed',
                'custom_error_type': type(e).__name__
            })
        
        # Start Prometheus metrics background collection
        if prometheus_metrics:
            try:
                await prometheus_metrics.start_background_collection()
                logger.info("Prometheus metrics collection started", extra={
                    'custom_service': 'prometheus',
                    'custom_status': 'active'
                })
            except Exception as e:
                logger.error("Prometheus metrics initialization failed", extra={
                    'custom_service': 'prometheus',
                    'custom_status': 'failed',
                    'custom_error_type': type(e).__name__
                })
        
        # Log enhanced security systems status
        logger.info("Security systems initialized", extra={
            'custom_security_systems': ['rate_limiting', 'input_validation', 'threat_detection'],
            'custom_security_status': 'active'
        })
        
        log_startup_info()
    logger.info("FastAPI application startup completed", extra={
        'custom_event': 'application_startup',
        'custom_environment': os.getenv("ENVIRONMENT", "development"),
        'custom_mongodb_url': mongo_url.split('@')[-1] if '@' in mongo_url else 'localhost'  # Hide credentials
    })

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("FastAPI application shutdown initiated", extra={
        'custom_event': 'application_shutdown'
    })
    log_shutdown_info()

# Include health router
app.include_router(health_router)

# Health check endpoint (no prefix)
@app.get("/health", summary="Health Check", tags=["Health"])
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

# Initialize FastAPI app
# TODO: Consider making title and version configurable
# if os.getenv("ENVIRONMENT") == "development":
#     logger.info("Running in development mode, enabling docs and redoc.")
#     app = FastAPI(
#         title="Online Evaluation System API",
#         version="1.0.0",
#         description="API for managing online evaluations, users, and submissions.",
#         docs_url="/docs",
#         redoc_url="/redoc"
#     )
# else:
#     logger.info("Running in non-development mode, disabling docs and redoc.")
#     app = FastAPI(
#         title="Online Evaluation System API",
#         version="1.0.0",
#         description="API for managing online evaluations, users, and submissions.",
#         docs_url=None, # Disable docs
#         redoc_url=None # Disable redoc
#     )

# Enable /docs and /redoc for easier debugging, regardless of ENVIRONMENT
# We can make this conditional again later.
# app = FastAPI(
#     title="Online Evaluation System API",
#     version="1.0.0",
#     description="API for managing online evaluations, users, and submissions.",
#     docs_url="/docs",
#     redoc_url="/redoc"
# )


# Database connection
# client = None # This is initialized globally earlier with AsyncIOMotorClient
# db = None # This is initialized globally earlier

# Connect to MongoDB
async def connect_to_mongo():
    global client, db # client and db are already global and initialized
    # The logic here re-initializes client and db, which might be redundant
    # or could conflict if not handled carefully with the initial global setup.
    # For now, assuming the initial global setup is sufficient.
    # If this function is critical for re-connection or specific setup, it needs review.
    # try:
    #     # Create MongoDB client
    #     client = AsyncIOMotorClient(
    #         mongo_url,
    #         maxPoolSize=100,
    #         minPoolSize=10,
    #         maxIdleTimeMS=30000,
    #         connectTimeoutMS=20000,
    #         serverSelectionTimeoutMS=20000
    #     )
    #     db = client[os.environ['DB_NAME']]
    #     await client.admin.command('ping')
    #     logger.info("Successfully connected to MongoDB (via connect_to_mongo).")
    # except Exception as e:
    #     logger.error(f"Error connecting to MongoDB (via connect_to_mongo): {e}")
    #     raise
    pass # Assuming global client/db are sufficient

# API Router setup
api_router = APIRouter(prefix="/api")

# Include security and user routes
# Assuming user_routes and other specific route modules are defined elsewhere
# and imported if necessary. For now, focusing on the auth route.

# Authentication routes
@api_router.post("/auth/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # Set user context for failed login tracking
    try:
        user_id_context.set(form_data.username)
    except:
        pass
        
    user_data = await db.users.find_one({"login_id": form_data.username})
    if not user_data or not verify_password(form_data.password, user_data["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="아이디 또는 비밀번호가 잘못되었습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Convert MongoDB document to User object
    user = User.from_mongo(user_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 데이터 처리 오류"
        )
    
    # Update last login time using _id
    await db.users.update_one(
        {"_id": user_data["_id"]},
        {"$set": {"last_login": datetime.utcnow()}}
    )
    
    # Set user context for successful login
    user_id_context.set(user.id)
    
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
@log_async_performance("create_project")
@log_database_operation("projects")
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
@log_async_performance("create_company")
@log_database_operation("companies")
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
@log_async_performance("file_upload")
@log_database_operation("file_metadata")
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
            logger.error(f"Assignment creation failed: {result}", extra={
                'custom_operation': 'assignment_creation',
                'custom_error_type': type(result).__name__
            })
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
                deadline=deadline            )
            
            await db.evaluation_sheets.insert_one(sheet.dict())
            return sheet
    except Exception as e:
        logger.error(f"Failed to create assignment: {e}", extra={
            'custom_operation': 'create_single_assignment',
            'custom_evaluator_id': evaluator_id,
            'custom_company_id': company_id,
            'custom_template_id': template_id,
            'custom_error_type': type(e).__name__
        })
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
            logger.error(f"Batch assignment failed: {result}", extra={
                'custom_operation': 'batch_assignment',
                'custom_error_type': type(result).__name__
            })
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
@log_async_performance("submit_evaluation")
@log_database_operation("evaluation_sheets")
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
        await db.evaluation_scores.insert_many(new_scores)    # Update sheet status
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
        logger.error(f"Export error: {str(e)}", extra={
                'custom_operation': 'export_evaluation',
                'custom_error_type': type(e).__name__
            })
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
        logger.error(f"Bulk export error: {str(e)}", extra={
                'custom_operation': 'bulk_export',
                'custom_error_type': type(e).__name__
            })
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
        logger.error(f"Get exportable evaluations error: {str(e)}", extra={
                'custom_operation': 'get_exportable_evaluations',
                'custom_error_type': type(e).__name__
            })
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

# Background task functions
async def update_project_statistics(project_id: str):
    """
    Update project statistics in the background.
    
    Args:
        project_id: The ID of the project to update statistics for
    """
    try:
        # Count total assigned evaluations for this project
        total_assigned = await db.evaluation_sheets.count_documents({
            "project_id": project_id
        })
        
        # Count completed evaluations (submitted or completed status)
        completed = await db.evaluation_sheets.count_documents({
            "project_id": project_id, 
            "status": {"$in": ["submitted", "completed"]}
        })
        
        # Calculate average score for completed evaluations
        average_score = None
        if completed > 0:
            try:
                # Aggregate to calculate average score
                pipeline = [
                    {
                        "$match": {
                            "project_id": project_id, 
                            "status": {"$in": ["submitted", "completed"]},
                            "total_score": {"$exists": True, "$ne": None}
                        }
                    },
                    {
                        "$group": {
                            "_id": None, 
                            "avg_score": {"$avg": "$total_score"}
                        }
                    }
                ]
                
                result = await db.evaluation_sheets.aggregate(pipeline).to_list(1)
                if result and len(result) > 0:
                    average_score = result[0].get("avg_score")
            except Exception as e:
                logger.warning(f"Error calculating average score for project {project_id}: {e}")
        
        # Prepare statistics document
        stats = {
            "project_id": project_id,
            "total_assigned_evaluations": total_assigned,
            "completed_evaluations": completed,
            "average_score": average_score,
            "completion_rate": (completed / total_assigned * 100) if total_assigned > 0 else 0,
            "updated_at": datetime.utcnow()
        }
        
        # Upsert statistics in project_statistics collection
        await db.project_statistics.update_one(
            {"project_id": project_id},
            {"$set": stats},
            upsert=True
        )
        
        logger.info(f"Updated statistics for project {project_id}: {stats}")
        
    except Exception as e:
        logger.error(f"Error updating project statistics for {project_id}: {e}")

# Template Management API endpoints
@api_router.get("/templates")
async def get_templates(
    project_id: Optional[str] = Query(None, description="Filter templates by project ID"),
    current_user: User = Depends(get_current_user)
):
    """Get all evaluation templates, optionally filtered by project"""
    try:
        # Build query filter
        query_filter = {}
        if project_id:
            query_filter["project_id"] = project_id
        
        # Get templates from database
        templates_cursor = db.evaluation_templates.find(query_filter)
        templates_data = await templates_cursor.to_list(length=None)
        
        templates = [EvaluationTemplate(**template) for template in templates_data]
        
        return {
            "templates": templates,
            "total": len(templates),
            "project_id": project_id
        }
    except Exception as e:
        logger.error(f"Error fetching templates: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching templates: {str(e)}")

@api_router.post("/templates", response_model=EvaluationTemplate)
async def create_template(
    template_data: EvaluationTemplateCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(check_admin_or_secretary)
):
    """Create a new evaluation template"""
    try:
        # Create new template
        template = EvaluationTemplate(
            name=template_data.name,
            description=template_data.description,
            project_id=template_data.project_id,
            items=template_data.items,
            created_by=current_user.id,
            status="draft"
        )
        
        # Insert into database
        await db.evaluation_templates.insert_one(template.dict())
        
        # Update project statistics in background
        background_tasks.add_task(update_project_statistics, template_data.project_id)
        
        logger.info(f"Template created: {template.id} by user {current_user.id}")
        return template
        
    except Exception as e:
        logger.error(f"Error creating template: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating template: {str(e)}")

@api_router.get("/templates/{template_id}", response_model=EvaluationTemplate)
async def get_template(
    template_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific evaluation template by ID"""
    try:
        template_data = await db.evaluation_templates.find_one({"id": template_id})
        
        if not template_data:
            raise HTTPException(status_code=404, detail="Template not found")
        
        template = EvaluationTemplate(**template_data)
        return template
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching template {template_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching template: {str(e)}")

@api_router.put("/templates/{template_id}", response_model=EvaluationTemplate)
async def update_template(
    template_id: str,
    template_data: EvaluationTemplateCreate,
    current_user: User = Depends(check_admin_or_secretary)
):
    """Update an existing evaluation template"""
    try:
        # Check if template exists
        existing_template = await db.evaluation_templates.find_one({"id": template_id})
        if not existing_template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Update template data
        update_data = {
            "name": template_data.name,
            "description": template_data.description,
            "project_id": template_data.project_id,
            "items": template_data.items,
            "updated_at": datetime.utcnow()
        }
        
        # Update in database
        await db.evaluation_templates.update_one(
            {"id": template_id},
            {"$set": update_data}
        )
        
        # Get updated template
        updated_template_data = await db.evaluation_templates.find_one({"id": template_id})
        updated_template = EvaluationTemplate(**updated_template_data)
        
        logger.info(f"Template updated: {template_id} by user {current_user.id}")
        return updated_template
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating template {template_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating template: {str(e)}")

@api_router.delete("/templates/{template_id}")
async def delete_template(
    template_id: str,
    current_user: User = Depends(check_admin_or_secretary)
):
    """Delete an evaluation template (soft delete by setting status to archived)"""
    try:
        # Check if template exists
        existing_template = await db.evaluation_templates.find_one({"id": template_id})
        if not existing_template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Soft delete by updating status
        await db.evaluation_templates.update_one(
            {"id": template_id},
            {"$set": {
                "status": "archived",
                "updated_at": datetime.utcnow()
            }}
        )
        
        logger.info(f"Template archived: {template_id} by user {current_user.id}")
        return {"message": "Template successfully archived", "template_id": template_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting template {template_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting template: {str(e)}")

@api_router.post("/templates/{template_id}/clone", response_model=EvaluationTemplate)
async def clone_template(
    template_id: str,
    current_user: User = Depends(check_admin_or_secretary)
):
    """Clone an existing evaluation template"""
    try:
        # Get source template
        source_template_data = await db.evaluation_templates.find_one({"id": template_id})
        if not source_template_data:
            raise HTTPException(status_code=404, detail="Source template not found")
        
        source_template = EvaluationTemplate(**source_template_data)
        
        # Create cloned template
        cloned_template = EvaluationTemplate(
            name=f"{source_template.name} (복사본)",
            description=f"복사됨: {source_template.description or ''}",
            project_id=source_template.project_id,
            items=source_template.items.copy(),
            created_by=current_user.id,
            status="draft"
        )
        
        # Insert cloned template
        await db.evaluation_templates.insert_one(cloned_template.dict())
        
        logger.info(f"Template cloned: {template_id} -> {cloned_template.id} by user {current_user.id}")
        return cloned_template
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cloning template {template_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error cloning template: {str(e)}")

@api_router.patch("/templates/{template_id}/status")
async def update_template_status(
    template_id: str,
    status: str = Query(..., description="New status: draft, active, archived"),
    current_user: User = Depends(check_admin_or_secretary)
):
    """Update template status"""
    try:
        valid_statuses = ["draft", "active", "archived"]
        if status not in valid_statuses:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        
        # Check if template exists
        existing_template = await db.evaluation_templates.find_one({"id": template_id})
        if not existing_template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Update status
        await db.evaluation_templates.update_one(
            {"id": template_id},
            {"$set": {
                "status": status,
                "updated_at": datetime.utcnow()
            }}
        )
        
        logger.info(f"Template status updated: {template_id} -> {status} by user {current_user.id}")
        return {"message": f"Template status updated to {status}", "template_id": template_id, "status": status}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating template status {template_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating template status: {str(e)}")

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

# Security monitoring and management endpoints
@app.get("/api/security/health")
async def security_health_check():
    """Public endpoint to check security system health"""
    try:
        # Check Redis connection
        redis_status = "healthy"
        try:
            if security_monitor.redis_client:
                security_monitor.redis_client.ping()
        except:
            redis_status = "unavailable"
        
        # Check MongoDB connection
        mongo_status = "healthy"
        try:
            if security_monitor.mongo_client:
                security_monitor.mongo_client.admin.command('ping')
        except:
            mongo_status = "unavailable"
        
        return {
            "status": "healthy",
            "components": {
                "security_monitor": "active",
                "redis": redis_status,
                "mongodb": mongo_status,
                "rate_limiting": "active",
                "threat_detection": "active"
            },
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        return {
            "status": "degraded",
            "error": str(e),
            "timestamp": datetime.utcnow()
        }

@app.get("/api/security/metrics")
async def get_security_metrics(
    hours: int = Query(24, ge=1, le=168),  # 1 hour to 1 week
    current_user: User = Depends(get_current_user)
):
    """Get security metrics for the specified time period (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    metrics = await security_monitor.get_security_metrics(hours)
    return {"metrics": metrics, "generated_at": datetime.utcnow()}

@app.get("/api/security/threat-intelligence")
async def get_threat_intelligence_report(current_user: User = Depends(get_current_user)):
    """Get comprehensive threat intelligence report (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    report = await security_monitor.get_threat_intelligence_report()
    return {"report": report}

# Additional security endpoints for comprehensive monitoring
@app.get("/api/security/events")
async def get_security_events(
    limit: int = Query(100, ge=1, le=1000),
    event_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """Get recent security events (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        events = await security_monitor.get_security_events(
            limit=limit,
            event_type=event_type,
            severity=severity
        )
        return {
            "events": events,
            "total": len(events),
            "filters": {
                "event_type": event_type,
                "severity": severity,
                "limit": limit
            },
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve security events: {str(e)}"
        )

@app.post("/api/security/validate")
async def validate_input_security(
    request: Request,
    data: dict,
    current_user: User = Depends(get_current_user)
):
    """Validate input data against security policies"""
    try:
        # Use the security validator to check the request
        validation_results = security_validator.validate_api_request(request)
        
        # Validate JSON data if provided
        if data:
            validated_data = security_validator.validate_json_input(data)
            validation_results["data_validation"] = "passed"
        
        return {
            "validation_results": validation_results,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        return {
            "validation_results": {"valid": False, "error": str(e)},
            "timestamp": datetime.utcnow()
        }

# Include the API router in the main application
app.include_router(api_router)

# Main entry point for Uvicorn (if running directly)
if __name__ == "__main__":
    import uvicorn
    
    # Production-ready server configuration
    config = {
        "host": "0.0.0.0",
        "port": int(os.getenv("PORT", 8080)),
        "log_level": os.getenv("LOG_LEVEL", "info").lower(),
        "access_log": True,
        "use_colors": False,
        "server_header": False,  # Hide server information
        "date_header": False,    # Don't include date header
    }
    
    # Add SSL configuration for production
    if os.getenv("ENVIRONMENT") == "production":
        config.update({
            "ssl_keyfile": os.getenv("SSL_KEY_FILE"),
            "ssl_certfile": os.getenv("SSL_CERT_FILE"),
            "ssl_ca_certs": os.getenv("SSL_CA_CERTS"),
        })
    
    logger.info(f"🚀 Starting Online Evaluation System on {config['host']}:{config['port']}")
    uvicorn.run(app, **config)
