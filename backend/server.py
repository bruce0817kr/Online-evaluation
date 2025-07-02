from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks, Query, WebSocket, WebSocketDisconnect
from contextlib import asynccontextmanager
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
    generate_evaluator_credentials, # Add missing function import
)
from secure_file_endpoints import check_file_access_permission, log_file_access

# AI 기능 임포트
try:
    from ai_endpoints import ai_router
    from ai_admin_endpoints import ai_admin_router
    from ai_service_enhanced import enhanced_ai_service
    AI_ENABLED = True
    AI_ADMIN_ENABLED = True
except ImportError as e:
    AI_ENABLED = False
    AI_ADMIN_ENABLED = False
    print(f"⚠️ AI 기능이 비활성화되었습니다: {e}")
    print("AI 라이브러리를 설치하려면 pip install openai anthropic google-generativeai cryptography 를 실행하세요.")

# 향상된 권한 시스템 임포트
try:
    from enhanced_permissions import permission_checker
    from permission_admin_endpoints import permission_admin_router
    ENHANCED_PERMISSIONS_ENABLED = True
except ImportError as e:
    ENHANCED_PERMISSIONS_ENABLED = False
    print(f"⚠️ 향상된 권한 시스템이 비활성화되었습니다: {e}")

# 향상된 템플릿 관리 시스템 임포트
try:
    from template_endpoints import template_router
    ENHANCED_TEMPLATES_ENABLED = True
except ImportError as e:
    ENHANCED_TEMPLATES_ENABLED = False
    print(f"⚠️ 향상된 템플릿 시스템이 비활성화되었습니다: {e}")

# 보안 파일 엔드포인트 임포트
from secure_file_endpoints import secure_file_router
SECURE_FILE_ENABLED = True

# 평가표 출력 엔드포인트 임포트
try:
    from evaluation_print_endpoints import evaluation_print_router
    EVALUATION_PRINT_ENABLED = True
except ImportError as e:
    EVALUATION_PRINT_ENABLED = False
    print(f"⚠️ 평가표 출력 시스템이 비활성화되었습니다: {e}")

# 향상된 평가표 출력 엔드포인트 임포트
try:
    from enhanced_export_endpoints import enhanced_export_router
    ENHANCED_EXPORT_ENABLED = True
    print("향상된 내보내기 시스템을 로드했습니다.")
except ImportError as e:
    ENHANCED_EXPORT_ENABLED = False
    print(f"⚠️ 향상된 내보내기 시스템이 비활성화되었습니다: {e}")

# AI 평가 제어 엔드포인트 임포트
try:
    from ai_evaluation_control_endpoints import ai_evaluation_control_router
    AI_EVALUATION_CONTROL_ENABLED = True
except ImportError as e:
    AI_EVALUATION_CONTROL_ENABLED = False
    print(f"⚠️ AI 평가 제어 시스템이 비활성화되었습니다: {e}")

# AI 모델 설정 엔드포인트 임포트
try:
    from ai_model_settings_endpoints import ai_model_settings_router
    AI_MODEL_SETTINGS_ENABLED = True
    print("AI 모델 설정 시스템을 로드했습니다.")
except ImportError as e:
    AI_MODEL_SETTINGS_ENABLED = False
    print(f"⚠️ AI 모델 설정 시스템이 비활성화되었습니다: {e}")

# 배포 관리 엔드포인트 임포트
try:
    from deployment_api_endpoints import deployment_router
    DEPLOYMENT_MANAGER_ENABLED = True
except ImportError as e:
    DEPLOYMENT_MANAGER_ENABLED = False
    print(f"⚠️ 배포 관리 시스템이 비활성화되었습니다: {e}")
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

# try:
#     import enhanced_health_monitoring
#     from enhanced_health_monitoring import setup_health_monitor, health_router
# except ImportError:
#     enhanced_health_monitoring = None
#     print("Warning: Enhanced health monitoring module not found.")

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

# Import stub services for undefined functions
# try:
#     from stub_services import (
#         calculate_evaluation_scores,
#         notification_service,
#         exporter,
#         EvaluationItem,
#         update_project_statistics,
#         background_file_processing
#     )
#     print("Successfully imported stub services for undefined functions.")
# except ImportError:
#     print("Warning: stub_services.py not found. Some functions may be undefined.")

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Initialize enhanced logging system
setup_logging(
    service_name="online-evaluation-backend",
    log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
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

# AI 관련 컬렉션 설정
ai_providers_collection = db.ai_providers
ai_models_collection = db.ai_models
ai_jobs_collection = db.ai_analysis_jobs

# 향상된 AI 서비스 초기화
if AI_ENABLED:
    try:
        enhanced_ai_service._setup_database(client)
        logger.info("향상된 AI 서비스가 초기화되었습니다.")
    except Exception as e:
        logger.error(f"AI 서비스 초기화 오류: {e}")

# 향상된 권한 시스템 초기화
if ENHANCED_PERMISSIONS_ENABLED:
    try:
        permission_checker.db = db
        permission_checker.user_permissions_collection = db.user_permissions
        permission_checker.project_members_collection = db.project_members
        logger.info("향상된 권한 시스템이 초기화되었습니다.")
    except Exception as e:
        logger.error(f"권한 시스템 초기화 오류: {e}")

# Thread pool for CPU-intensive tasks
executor = ThreadPoolExecutor(max_workers=4)

# Initialize health monitor
# health_monitor = HealthMonitor(client) # This line is causing the NameError
# The HealthMonitor class definition or import is missing.
# For now, we will comment this out to allow the server to start.
# It should be properly defined or imported from enhanced_health_monitoring.py later.

# JWT settings - Now using security config with lazy initialization
from security import get_security_config
config = get_security_config()
SECRET_KEY = config.JWT_SECRET_KEY
ALGORITHM = config.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES

# Password context - Now using enhanced security
pwd_context = imported_pwd_context # Correctly assign the imported instance
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login") # This can be removed if security_oauth2_scheme from security.py is used

# API Router 정의
api_router = APIRouter()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan event handler"""
    # Startup
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
        
        # Initialize Redis client for performance monitoring
        try:
            await cache_service.connect()
            if cache_service.redis_client:
                await cache_service.redis_client.ping()
                logger.info("Redis connection verified", extra={
                    'custom_service': 'redis_init',
                    'custom_status': 'connected'
                })
            else:
                logger.warning("Redis client not available", extra={
                    'custom_service': 'redis_init',
                    'custom_status': 'unavailable'
                })
        except Exception as e:
            logger.error("Redis connection failed", extra={
                'custom_service': 'redis_init',
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
    
    yield  # Application runs here
    
    # Shutdown
    logger.info("FastAPI application shutdown initiated", extra={
        'custom_event': 'application_shutdown'
    })
    log_shutdown_info()

# Create the main app with enhanced security configuration
# Always enable /docs and /redoc for easier debugging
app = FastAPI(
    title=config.API_TITLE if hasattr(config, 'API_TITLE') else "온라인 평가 시스템",
    version="2.0.0", # Or "1.0.0" if that was the intended version from the previous edit
    description="Secure Online Evaluation System with comprehensive authentication and authorization",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
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
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=config.CORS_ALLOW_CREDENTIALS,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
    expose_headers=["X-Total-Count"],
    max_age=3600,
)

# Initialize enhanced health monitoring
try:
    from enhanced_health_monitoring import setup_health_monitor
    health_monitor_instance = setup_health_monitor(client, cache_service.redis_client)
except ImportError:
    print("Warning: Enhanced health monitoring not available")
    health_monitor_instance = None

# Initialize Prometheus metrics (optional)
try:
    from prometheus_metrics import setup_prometheus_metrics
    prometheus_metrics = setup_prometheus_metrics(app, cache_service.redis_client, client)
except (ImportError, AttributeError):
    print("Warning: Prometheus metrics not available")
    prometheus_metrics = None


# api_router registration moved to centralized location to avoid duplicates

# Import and include core API routers
try:
    from evaluation_api import router as evaluation_router
    app.include_router(evaluation_router, prefix="/api", tags=["Evaluations"])
    print("평가 API 라우터가 등록되었습니다.")
except ImportError as e:
    print(f"⚠️ 평가 API 라우터 로드 실패: {e}")
    print("⚠️ evaluation_api.py 파일을 확인해주세요.")
print("모든 라우터가 활성화되었습니다.")

# Removed duplicate get_dashboard_statistics - better implementation exists at line 3019

# 파일 관리 엔드포인트 - REMOVED to avoid conflict with secure_file_router
# Files are now handled by secure_file_endpoints.py with prefix /api/files

# 사용자 관리 엔드포인트들
@api_router.get("/users")
async def get_users(current_user: User = Depends(get_current_user)):
    """사용자 목록 조회"""
    check_admin_or_secretary(current_user)
    try:
        users = await db.users.find({}).to_list(1000)
        user_responses = []
        for user in users:
            # Convert _id to id for UserResponse
            user_data = user.copy()
            user_data["id"] = str(user_data.pop("_id"))
            user_responses.append(UserResponse(**user_data))
        return user_responses
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"사용자 목록 조회 실패: {str(e)}")

# Removed duplicate get_projects - better implementation exists at line 1082

# Removed duplicate get_companies - better implementation exists at line 1113

# 템플릿 관리 엔드포인트들 - REMOVED to avoid conflict with template_router
# Templates are now handled by template_endpoints.py with prefix /api/templates

# 관리자 전용 엔드포인트들
@api_router.get("/admin/users")
async def get_admin_users(current_user: User = Depends(get_current_user)):
    """관리자용 사용자 목록 조회"""
    # 관리자 권한 체크
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    
    try:
        users = await db.users.find({}).to_list(1000)
        user_responses = []
        for user in users:
            # Convert _id to id for UserResponse
            user_data = user.copy()
            user_data["id"] = str(user_data.pop("_id"))
            user_responses.append(UserResponse(**user_data))
        return user_responses
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"관리자 사용자 목록 조회 실패: {str(e)}")

# 평가 관리 엔드포인트들은 evaluation_print_endpoints.py에서 처리

# 기본 API 라우터에 기존 엔드포인트들 추가
# 인증 엔드포인트들은 이미 server.py에 정의되어 있음

# Health check endpoint (no prefix)
@app.get("/health", operation_id="health_check", summary="Health Check", tags=["Health"])
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
@app.get("/db-status", operation_id="database_status")
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
@app.get("/", operation_id="root_endpoint")
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

# API Router setup (기존 api_router에 엔드포인트 추가)
# api_router는 이미 252번째 줄에서 정의됨 - 재정의하지 않음

# Include security and user routes
# Assuming user_routes and other specific route modules are defined elsewhere
# and imported if necessary. For now, focusing on the auth route.

# Authentication routes
@api_router.get("/auth/test")
async def test_auth_router():
    print("🔍 TEST: Auth router is working!")
    return {"status": "AUTH_ROUTER_WORKING", "timestamp": "2025-06-22"}

@api_router.post("/auth/login-test")
async def test_login(username: str, password: str):
    print(f"🔍 TEST LOGIN: {username} / {password}")
    
    # Direct database check
    user_data = await db.users.find_one({"login_id": username})
    print(f"🔍 TEST USER: found={user_data is not None}")
    
    if user_data and username == "admin" and password == "admin123":
        print("🔍 TEST: Hardcoded success!")
        return {"status": "SUCCESS", "user": "admin"}
    else:
        print("🔍 TEST: Failed!")
        return {"status": "FAILED", "reason": "Invalid credentials"}

# DISABLED: Conflicting login endpoint - using clean_login_endpoint instead
# @api_router.post("/auth/login", response_model=Token)
# async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
#     # Set user context for failed login tracking
#     try:
#         user_id_context.set(form_data.username)
#     except:
#         pass
#     
#     print(f"🔍 LOGIN: user={form_data.username}, pwd_len={len(form_data.password)}")
#     user_data = await db.users.find_one({"login_id": form_data.username})
#     print(f"🔍 USER: found={user_data is not None}")
#     if user_data:
#         pwd_valid = verify_password(form_data.password, user_data["password_hash"])
#         print(f"🔍 PWD: valid={pwd_valid}")
#     if not user_data or not verify_password(form_data.password, user_data["password_hash"]):
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="아이디 또는 비밀번호가 잘못되었습니다",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#     
#     # Convert MongoDB document to User object
#     user = User.from_mongo(user_data)
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="사용자 데이터 처리 오류"
#         )
#     
#     # Update last login time using _id
#     await db.users.update_one(
#         {"_id": user_data["_id"]},
#         {"$set": {"last_login": datetime.utcnow()}}
#     )
#     
#     # Set user context for successful login
#     user_id_context.set(user.id)
#     
#     access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     access_token = create_access_token(
#         data={"sub": user.id}, expires_delta=access_token_expires
#     )
#     user_response = UserResponse(**user.dict())
#     return {"access_token": access_token, "token_type": "bearer", "user": user_response}

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
# REMOVED: Duplicate /users endpoint that was causing authentication conflicts

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

# Enhanced file upload with async processing and comprehensive error handling
@api_router.post("/upload")
@log_async_performance("file_upload")
@log_database_operation("file_metadata")
async def upload_file(
    background_tasks: BackgroundTasks,
    company_id: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    try:
        check_admin_or_secretary(current_user)
        
        # Input validation
        if not file.filename:
            raise HTTPException(status_code=400, detail="파일명이 없습니다.")
        
        if not company_id or not company_id.strip():
            raise HTTPException(status_code=400, detail="회사 ID가 필요합니다.")
        
        # File size validation (50MB limit)
        MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="파일 크기가 50MB를 초과합니다.")
        
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="빈 파일은 업로드할 수 없습니다.")
        
        # File type validation
        ALLOWED_EXTENSIONS = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.txt', '.png', '.jpg', '.jpeg'}
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=415, 
                detail=f"지원하지 않는 파일 형식입니다. 허용된 형식: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # Check if company exists
        company = await db.companies.find_one({"id": company_id})
        if not company:
            raise HTTPException(status_code=404, detail="존재하지 않는 회사입니다.")
        
        # Create uploads directory if it doesn't exist
        upload_dir = Path("uploads")
        try:
            upload_dir.mkdir(exist_ok=True)
        except OSError as e:
            logging.error(f"Failed to create uploads directory: {e}")
            raise HTTPException(status_code=500, detail="파일 저장 공간을 준비할 수 없습니다.")
        
        # Generate unique filename with proper encoding
        file_id = str(uuid.uuid4())
        # Sanitize filename to prevent directory traversal
        safe_filename = re.sub(r'[^\w\s.-]', '', file.filename)
        unique_filename = f"{company_id}_{file_id}_{safe_filename}"
        file_path = upload_dir / unique_filename
        
        # Save file asynchronously with error handling
        try:
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)
        except OSError as e:
            logging.error(f"Failed to save file {file_path}: {e}")
            raise HTTPException(status_code=500, detail="파일 저장에 실패했습니다.")
        
        # Create file metadata
        try:
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
            
            # Save metadata to database with error handling
            await db.file_metadata.insert_one(file_metadata.dict())
            
            # Update company's files list
            await db.companies.update_one(
                {"id": company_id},
                {"$push": {"files": file_metadata.dict()}}
            )
            
        except Exception as e:
            # If database operation fails, clean up the uploaded file
            try:
                if file_path.exists():
                    file_path.unlink()
            except OSError:
                pass  # File cleanup failed, but don't raise another exception
            
            logging.error(f"Database operation failed for file upload: {e}")
            raise HTTPException(status_code=500, detail="파일 메타데이터 저장에 실패했습니다.")
        
        # Add background task for file processing
        try:
            # background_tasks.add_task(background_file_processing, str(file_path), file_id)
            pass
        except Exception as e:
            logging.warning(f"Failed to add background task for file processing: {e}")
            # Don't fail the upload just because background task failed
        
        return {
            "message": "파일이 성공적으로 업로드되었습니다",
            "file_id": file_id,
            "filename": file.filename,
            "file_size": len(content),
            "file_type": file.content_type
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logging.error(f"Unexpected error in file upload: {e}")
        raise HTTPException(status_code=500, detail="파일 업로드 중 예상치 못한 오류가 발생했습니다.")

# File management endpoints
@api_router.get("/files", response_model=List[Dict[str, Any]])
async def get_files(
    company_id: Optional[str] = Query(None, description="회사 ID로 필터링"),
    project_id: Optional[str] = Query(None, description="프로젝트 ID로 필터링"),
    current_user: User = Depends(get_current_user)
):
    """파일 목록 조회"""
    filter_criteria = {}
    
    if company_id:
        filter_criteria["company_id"] = company_id
    
    # 프로젝트별 필터링을 위해 회사를 통해 간접 조회
    if project_id:
        companies = await db.companies.find({"project_id": project_id}).to_list(1000)
        company_ids = [str(company["_id"]) for company in companies]
        if company_ids:
            filter_criteria["company_id"] = {"$in": company_ids}
        else:
            return []  # 프로젝트에 회사가 없으면 빈 결과 반환
    
    files = await db.file_metadata.find(filter_criteria).to_list(1000)
    
    # 파일 정보와 회사 정보를 조합하여 반환
    result = []
    for file_doc in files:
        company = await db.companies.find_one({"_id": file_doc["company_id"]})
        file_info = {
            "id": file_doc["id"],
            "filename": file_doc["original_filename"],
            "file_size": file_doc["file_size"],
            "file_type": file_doc["file_type"],
            "uploaded_at": file_doc["uploaded_at"],
            "uploaded_by": file_doc["uploaded_by"],
            "company_id": file_doc["company_id"],
            "company_name": company["name"] if company else "알 수 없음"
        }
        result.append(file_info)
    
    return result

@api_router.get("/files/{file_id}")
async def get_file(
    file_id: str, 
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """보안 강화된 파일 다운로드 - 권한 검사 및 접근 로그 포함"""
    try:
        # 입력 검증
        if not file_id or not file_id.strip():
            raise HTTPException(status_code=400, detail="파일 ID가 필요합니다.")
        
        # 권한 검사
        if not await check_file_access_permission(current_user, file_id):
            # 권한 없는 접근 시도 로그 기록
            await log_file_access(
                user_id=current_user.id,
                file_id=file_id,
                action="download_denied",
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent"),
                success=False,
                error_message="접근 권한 없음"
            )
            raise HTTPException(status_code=403, detail="이 파일을 다운로드할 권한이 없습니다.")
        
        # 파일 메타데이터 조회
        file_metadata = await db.file_metadata.find_one({"id": file_id})
        if not file_metadata:
            await log_file_access(
                user_id=current_user.id,
                file_id=file_id,
                action="download_failed",
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent"),
                success=False,
                error_message="파일을 찾을 수 없음"
            )
            raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
        
        # 파일 경로 보안 검증
        file_path_str = file_metadata["file_path"]
        if ".." in file_path_str or file_path_str.startswith("/"):
            await log_file_access(
                user_id=current_user.id,
                file_id=file_id,
                action="download_blocked",
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent"),
                success=False,
                error_message="잘못된 파일 경로"
            )
            raise HTTPException(status_code=400, detail="잘못된 파일 경로입니다.")
        
        file_path = Path(file_path_str)
        if not file_path.exists():
            await log_file_access(
                user_id=current_user.id,
                file_id=file_id,
                action="download_failed",
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent"),
                success=False,
                error_message="파일이 존재하지 않음"
            )
            raise HTTPException(status_code=404, detail="파일이 존재하지 않습니다.")
        
        # 성공적인 다운로드 로그 기록
        await log_file_access(
            user_id=current_user.id,
            file_id=file_id,
            action="download_success",
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            success=True
        )
        
        # 안전한 파일명 생성 (한글 파일명 처리)
        safe_filename = file_metadata["original_filename"]
        try:
            # UTF-8로 인코딩 가능한지 확인
            safe_filename.encode('utf-8')
        except UnicodeEncodeError:
            # 인코딩 실패 시 파일 ID로 대체
            extension = Path(safe_filename).suffix
            safe_filename = f"file_{file_id}{extension}"
        
        return FileResponse(
            path=file_path,
            filename=safe_filename,
            media_type=file_metadata.get("file_type", "application/octet-stream"),
            headers={
                "X-User": current_user.user_name,
                "X-Download-Time": datetime.utcnow().isoformat(),
                "X-File-ID": file_id
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # 예상치 못한 오류 로그 기록
        await log_file_access(
            user_id=current_user.id if 'current_user' in locals() else "unknown",
            file_id=file_id,
            action="download_error",
            ip_address=request.client.host if 'request' in locals() else "unknown",
            user_agent=request.headers.get("user-agent") if 'request' in locals() else "unknown",
            success=False,
            error_message=f"예상치 못한 오류: {str(e)}"
        )
        logging.error(f"파일 다운로드 예상치 못한 오류: {e}")
        raise HTTPException(status_code=500, detail="파일 다운로드 중 오류가 발생했습니다.")

# 파일 접근 로그 관리 엔드포인트
@api_router.get("/files/access-logs")
async def get_file_access_logs(
    file_id: Optional[str] = Query(None, description="특정 파일의 로그만 조회"),
    user_id: Optional[str] = Query(None, description="특정 사용자의 로그만 조회"),
    action: Optional[str] = Query(None, description="특정 액션의 로그만 조회"),
    start_date: Optional[str] = Query(None, description="시작 날짜 (ISO 형식)"),
    end_date: Optional[str] = Query(None, description="종료 날짜 (ISO 형식)"),
    limit: int = Query(100, description="조회할 로그 수 제한"),
    current_user: User = Depends(get_current_user)
):
    """파일 접근 로그 조회 (관리자 및 간사만 접근 가능)"""
    try:
        # 관리자 및 간사만 접근 가능
        if current_user.role not in ["admin", "secretary"]:
            raise HTTPException(status_code=403, detail="파일 접근 로그를 조회할 권한이 없습니다.")
        
        # 쿼리 조건 구성
        query = {}
        if file_id:
            query["file_id"] = file_id
        if user_id:
            query["user_id"] = user_id
        if action:
            query["action"] = action
        
        # 날짜 범위 필터
        if start_date or end_date:
            date_filter = {}
            if start_date:
                try:
                    date_filter["$gte"] = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                except ValueError:
                    raise HTTPException(status_code=400, detail="잘못된 시작 날짜 형식입니다.")
            if end_date:
                try:
                    date_filter["$lte"] = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                except ValueError:
                    raise HTTPException(status_code=400, detail="잘못된 종료 날짜 형식입니다.")
            query["access_time"] = date_filter
        
        # 로그 조회 (최신순 정렬)
        logs = await db.file_access_logs.find(query).sort("access_time", -1).limit(limit).to_list(limit)
        
        # 사용자 정보 및 파일 정보 보강
        enhanced_logs = []
        for log in logs:
            # 사용자 정보 조회
            user_info = await db.users.find_one({"id": log["user_id"]})
            user_name = user_info.get("user_name", "알 수 없음") if user_info else "알 수 없음"
            
            # 파일 정보 조회
            file_info = await db.file_metadata.find_one({"id": log["file_id"]})
            file_name = file_info.get("original_filename", "알 수 없음") if file_info else "알 수 없음"
            
            enhanced_log = {
                **log,
                "user_name": user_name,
                "file_name": file_name,
                "access_time_formatted": log["access_time"].strftime("%Y-%m-%d %H:%M:%S")
            }
            enhanced_logs.append(enhanced_log)
        
        return {
            "logs": enhanced_logs,
            "total_count": len(enhanced_logs),
            "query_params": {
                "file_id": file_id,
                "user_id": user_id,
                "action": action,
                "start_date": start_date,
                "end_date": end_date,
                "limit": limit
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"파일 접근 로그 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="파일 접근 로그 조회 중 오류가 발생했습니다.")

@api_router.get("/files/security-analytics")
async def get_file_security_analytics(
    current_user: User = Depends(get_current_user)
):
    """파일 보안 분석 정보 (관리자만 접근 가능)"""
    try:
        # 관리자만 접근 가능
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="보안 분석 정보를 조회할 권한이 없습니다.")
        
        # 최근 24시간 통계
        yesterday = datetime.utcnow() - timedelta(days=1)
        
        # 파이프라인으로 통계 집계
        pipeline = [
            {"$match": {"access_time": {"$gte": yesterday}}},
            {"$group": {
                "_id": "$action",
                "count": {"$sum": 1},
                "success_count": {"$sum": {"$cond": [{"$eq": ["$success", True]}, 1, 0]}},
                "failure_count": {"$sum": {"$cond": [{"$eq": ["$success", False]}, 1, 0]}}
            }}
        ]
        
        action_stats = await db.file_access_logs.aggregate(pipeline).to_list(None)
        
        # 의심스러운 활동 감지
        suspicious_pipeline = [
            {"$match": {
                "access_time": {"$gte": yesterday},
                "$or": [
                    {"success": False},
                    {"action": {"$in": ["download_denied", "preview_denied", "download_blocked", "preview_blocked"]}}
                ]
            }},
            {"$group": {
                "_id": "$user_id",
                "failed_attempts": {"$sum": 1},
                "actions": {"$push": "$action"}
            }},
            {"$match": {"failed_attempts": {"$gte": 3}}}  # 3회 이상 실패한 사용자
        ]
        
        suspicious_users = await db.file_access_logs.aggregate(suspicious_pipeline).to_list(None)
        
        # 가장 많이 접근된 파일
        popular_files_pipeline = [
            {"$match": {
                "access_time": {"$gte": yesterday},
                "success": True,
                "action": {"$in": ["download_success", "preview_success"]}
            }},
            {"$group": {
                "_id": "$file_id",
                "access_count": {"$sum": 1}
            }},
            {"$sort": {"access_count": -1}},
            {"$limit": 10}
        ]
        
        popular_files = await db.file_access_logs.aggregate(popular_files_pipeline).to_list(None)
        
        # 파일 정보 보강
        for file_stat in popular_files:
            file_info = await db.file_metadata.find_one({"id": file_stat["_id"]})
            file_stat["file_name"] = file_info.get("original_filename", "알 수 없음") if file_info else "알 수 없음"
        
        # 사용자 정보 보강
        for user_stat in suspicious_users:
            user_info = await db.users.find_one({"id": user_stat["_id"]})
            user_stat["user_name"] = user_info.get("user_name", "알 수 없음") if user_info else "알 수 없음"
        
        return {
            "period": "최근 24시간",
            "action_statistics": action_stats,
            "suspicious_activities": suspicious_users,
            "popular_files": popular_files,
            "security_recommendations": [
                "의심스러운 활동이 감지된 사용자의 계정을 점검하세요.",
                "자주 접근되는 파일의 보안 설정을 확인하세요.",
                "실패한 접근 시도가 많은 파일의 권한 설정을 재검토하세요."
            ] if suspicious_users else ["현재 특별한 보안 위험이 감지되지 않았습니다."]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"파일 보안 분석 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="파일 보안 분석 조회 중 오류가 발생했습니다.")



@api_router.get("/files/{file_id}/preview")
async def preview_file(
    file_id: str, 
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """보안 강화된 파일 미리보기 - 권한 검사 및 접근 로그 포함"""
    try:
        # 입력 검증
        if not file_id or not file_id.strip():
            raise HTTPException(status_code=400, detail="파일 ID가 필요합니다.")
        
        # 권한 검사
        if not await check_file_access_permission(current_user, file_id):
            # 권한 없는 접근 시도 로그 기록
            await log_file_access(
                user_id=current_user.id,
                file_id=file_id,
                action="preview_denied",
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent"),
                success=False,
                error_message="접근 권한 없음"
            )
            raise HTTPException(status_code=403, detail="이 파일에 접근할 권한이 없습니다.")
        
        # 파일 메타데이터 조회
        file_metadata = await db.file_metadata.find_one({"id": file_id})
        if not file_metadata:
            await log_file_access(
                user_id=current_user.id,
                file_id=file_id,
                action="preview_failed",
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent"),
                success=False,
                error_message="파일을 찾을 수 없음"
            )
            raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
        
        # 파일 경로 보안 검증
        file_path_str = file_metadata["file_path"]
        if ".." in file_path_str or file_path_str.startswith("/"):
            await log_file_access(
                user_id=current_user.id,
                file_id=file_id,
                action="preview_blocked",
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent"),
                success=False,
                error_message="잘못된 파일 경로"
            )
            raise HTTPException(status_code=400, detail="잘못된 파일 경로입니다.")
        
        file_path = Path(file_path_str)
        if not file_path.exists():
            await log_file_access(
                user_id=current_user.id,
                file_id=file_id,
                action="preview_failed",
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent"),
                success=False,
                error_message="파일이 존재하지 않음"
            )
            raise HTTPException(status_code=404, detail="파일이 존재하지 않습니다.")
        
        # 파일 크기 검사 (대용량 파일 방지)
        MAX_PREVIEW_SIZE = 100 * 1024 * 1024  # 100MB
        if file_metadata.get("file_size", 0) > MAX_PREVIEW_SIZE:
            await log_file_access(
                user_id=current_user.id,
                file_id=file_id,
                action="preview_blocked",
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent"),
                success=False,
                error_message="파일 크기 제한 초과"
            )
            raise HTTPException(status_code=413, detail="파일이 너무 커서 미리보기할 수 없습니다.")
        
        # PDF 파일 처리
        if file_metadata["file_type"] == "application/pdf":
            try:
                async with aiofiles.open(file_path, 'rb') as f:
                    content = await f.read()
                    base64_content = base64.b64encode(content).decode('utf-8')
                    
                    # 성공적인 접근 로그 기록
                    await log_file_access(
                        user_id=current_user.id,
                        file_id=file_id,
                        action="preview_success",
                        ip_address=request.client.host,
                        user_agent=request.headers.get("user-agent"),
                        success=True
                    )
                    
                    return {
                        "content": base64_content,
                        "type": "pdf",
                        "filename": file_metadata["original_filename"],
                        "watermark": {
                            "user": current_user.user_name,
                            "date": datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
                            "ip": request.client.host
                        }
                    }
            except Exception as e:
                await log_file_access(
                    user_id=current_user.id,
                    file_id=file_id,
                    action="preview_error",
                    ip_address=request.client.host,
                    user_agent=request.headers.get("user-agent"),
                    success=False,
                    error_message=f"파일 읽기 오류: {str(e)}"
                )
                raise HTTPException(status_code=500, detail="파일을 읽을 수 없습니다.")
        
        # 기타 파일 처리
        await log_file_access(
            user_id=current_user.id,
            file_id=file_id,
            action="metadata_access",
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            success=True
        )
        
        return {
            "type": "other",
            "filename": file_metadata["original_filename"],
            "size": file_metadata["file_size"],
            "file_type": file_metadata["file_type"],
            "download_url": f"/api/files/{file_id}",
            "watermark": {
                "user": current_user.user_name,
                "date": datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
                "ip": request.client.host
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        # 예상치 못한 오류 로그 기록
        await log_file_access(
            user_id=current_user.id if 'current_user' in locals() else "unknown",
            file_id=file_id,
            action="preview_error",
            ip_address=request.client.host if 'request' in locals() else "unknown",
            user_agent=request.headers.get("user-agent") if 'request' in locals() else "unknown",
            success=False,
            error_message=f"예상치 못한 오류: {str(e)}"
        )
        logging.error(f"파일 미리보기 예상치 못한 오류: {e}")
        raise HTTPException(status_code=500, detail="파일 미리보기 중 오류가 발생했습니다.")

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
        "completion_rate": round((companies_evaluated / len(companies) * 100) if companies else 0, 1),
        "score_analytics": avg_scores
    }

# Export routes for comprehensive evaluation reports
@api_router.get("/evaluations/{evaluation_id}/export")
async def export_single_evaluation(
    evaluation_id: str,
    format: str = Query(..., pattern="^(pdf|excel)$", description="Export format: pdf or excel"),
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

@api_router.get("/evaluations")
async def get_evaluations_list(
    project_id: Optional[str] = Query(None, description="프로젝트 ID 필터"),
    status: Optional[str] = Query(None, description="상태 필터"),
    evaluator_id: Optional[str] = Query(None, description="평가자 ID 필터"),
    current_user: User = Depends(get_current_user)
):
    """평가 목록 조회 - 향상된 필터링 지원"""
    try:
        query = {}
        if project_id:
            query["project_id"] = project_id
        if status:
            query["status"] = status
        if evaluator_id:
            query["evaluator_id"] = evaluator_id
            
        # 평가 시트 조회
        evaluations = await db.evaluation_sheets.find(query).to_list(1000)
        
        # 관련 데이터 조회하여 완전한 정보 제공
        result = []
        for eval_data in evaluations:
            # 프로젝트 정보 조회
            project = await db.projects.find_one({"id": eval_data.get("project_id")})
            # 회사 정보 조회
            company = await db.companies.find_one({"id": eval_data.get("company_id")})
            # 평가자 정보 조회
            evaluator = await db.users.find_one({"id": eval_data.get("evaluator_id")})
            
            result.append({
                "id": eval_data.get("id", eval_data.get("_id")),
                "project_id": eval_data.get("project_id"),
                "project_name": project.get("name") if project else "알 수 없음",
                "company_id": eval_data.get("company_id"),
                "company_name": company.get("name") if company else "알 수 없음",
                "evaluator_id": eval_data.get("evaluator_id"),
                "evaluator_name": evaluator.get("user_name") if evaluator else "알 수 없음",
                "evaluatee_id": eval_data.get("company_id"),  # 피평가자는 회사
                "status": eval_data.get("status", "pending"),
                "created_at": eval_data.get("created_at"),
                "evaluation_date": eval_data.get("submitted_at"),
                "scores": eval_data.get("scores", {}),
                "comments": eval_data.get("comments", "")
            })
        
        return result
    except Exception as e:
        logger.error(f"평가 목록 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"평가 목록 조회 실패: {str(e)}")

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

# Template routes - REMOVED: Now handled by template_endpoints.py with enhanced features

# POST template endpoint - REMOVED: Now handled by template_endpoints.py with enhanced features

# Security monitoring and management endpoints
@api_router.get("/security/health")
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

@api_router.get("/security/metrics")
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

@api_router.get("/security/threat-intelligence")
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
@api_router.get("/security/events")
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

@api_router.post("/security/validate")
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

# AI 비용 최적화 엔드포인트들
@api_router.get("/ai/cost-optimization")
async def get_ai_cost_optimization_stats(current_user: User = Depends(check_admin_or_secretary)):
    """AI 모델별 비용 최적화 통계 조회"""
    if AI_ENABLED and enhanced_ai_service:
        stats = enhanced_ai_service.get_cost_optimization_stats()
        return {"success": True, "data": stats}
    else:
        return {"success": False, "message": "AI 서비스가 비활성화되어 있습니다"}

@api_router.post("/ai/cost-estimate")
async def estimate_ai_analysis_cost(
    request: Dict[str, Any] = None,
    current_user: User = Depends(get_current_user)
):
    """AI 분석 비용 예상 계산"""
    if not AI_ENABLED or not enhanced_ai_service:
        return {"success": False, "message": "AI 서비스가 비활성화되어 있습니다"}
    
    try:
        document_text = request.get("document_text", "")
        analysis_type = request.get("analysis_type", "standard")
        budget_priority = request.get("budget_priority", "balanced")
        
        if not document_text:
            raise HTTPException(400, "document_text가 필요합니다")
        
        # 최적 모델 선택
        optimal_model = enhanced_ai_service._select_optimal_groq_model(
            document_length=len(document_text),
            analysis_type=analysis_type,
            budget_priority=budget_priority
        )
        
        # 비용 계산
        cost_info = enhanced_ai_service._calculate_token_cost(document_text, optimal_model)
        
        return {
            "success": True,
            "data": {
                "recommended_model": optimal_model,
                "document_length": len(document_text),
                "analysis_type": analysis_type,
                "budget_priority": budget_priority,
                "cost_estimate": cost_info,
                "alternatives": [
                    {
                        "model": "llama3.1-8b-instant",
                        "cost": enhanced_ai_service._calculate_token_cost(document_text, "llama3.1-8b-instant"),
                        "pros": ["최저 비용", "최고 속도"],
                        "cons": ["기본 성능"]
                    },
                    {
                        "model": "qwq-32b-preview", 
                        "cost": enhanced_ai_service._calculate_token_cost(document_text, "qwq-32b-preview"),
                        "pros": ["균형잡힌 성능", "툴 사용 강점"],
                        "cons": ["중간 비용"]
                    },
                    {
                        "model": "llama3.3-70b-versatile",
                        "cost": enhanced_ai_service._calculate_token_cost(document_text, "llama3.3-70b-versatile"),
                        "pros": ["최고 성능", "정확도 높음"],
                        "cons": ["높은 비용"]
                    }
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"AI 비용 예상 계산 오류: {e}")
        raise HTTPException(500, f"비용 계산 중 오류가 발생했습니다: {str(e)}")

@api_router.get("/ai/usage-analytics")
async def get_ai_usage_analytics(current_user: User = Depends(check_admin_or_secretary)):
    """AI 사용량 및 비용 분석"""
    if not AI_ENABLED:
        return {"success": False, "message": "AI 서비스가 비활성화되어 있습니다"}
    
    try:
        # 실제 구현시에는 데이터베이스에서 사용 내역 조회
        # 여기서는 샘플 데이터 반환
        analytics_data = {
            "current_month": {
                "total_requests": 1247,
                "total_tokens": 2856420,
                "total_cost_usd": 15.67,
                "total_cost_krw": 20371,
                "average_cost_per_request": 0.0126
            },
            "model_usage": [
                {"model": "llama3.1-8b-instant", "requests": 856, "tokens": 1234567, "cost_usd": 1.60, "percentage": 68.7},
                {"model": "qwq-32b-preview", "requests": 298, "tokens": 1105820, "cost_usd": 7.52, "percentage": 23.9},
                {"model": "llama3.3-70b-versatile", "requests": 93, "tokens": 516033, "cost_usd": 6.55, "percentage": 7.4}
            ],
            "daily_trend": [
                {"date": "2025-06-15", "requests": 45, "cost_usd": 0.67},
                {"date": "2025-06-16", "requests": 52, "cost_usd": 0.84},
                {"date": "2025-06-17", "requests": 38, "cost_usd": 0.52},
                {"date": "2025-06-18", "requests": 61, "cost_usd": 1.23},
                {"date": "2025-06-19", "requests": 49, "cost_usd": 0.78},
                {"date": "2025-06-20", "requests": 56, "cost_usd": 0.95},
                {"date": "2025-06-21", "requests": 42, "cost_usd": 0.63}
            ],
            "cost_optimization_suggestions": [
                {
                    "type": "model_switching",
                    "message": "간단한 문서 분석 856건을 llama3.1-8b로 처리하여 월 $14.07 절약 중",
                    "savings_potential": 14.07
                },
                {
                    "type": "batch_processing", 
                    "message": "유사한 문서들을 배치로 처리하면 추가로 10-15% 절약 가능",
                    "savings_potential": 2.35
                }
            ]
        }
        
        return {"success": True, "data": analytics_data}
        
    except Exception as e:
        logger.error(f"AI 사용량 분석 오류: {e}")
        raise HTTPException(500, f"사용량 분석 중 오류가 발생했습니다: {str(e)}")

# TEST ENDPOINT - Check if direct app endpoints work
@app.post("/api/test/direct")
async def test_direct_endpoint():
    """Test if direct app endpoints are accessible"""
    print("🚀 DIRECT ENDPOINT CALLED!")
    return {"status": "success", "message": "Direct endpoint working"}

# SIMPLE LOGIN TEST ENDPOINT
@app.post("/api/auth/login-simple")
async def simple_login_test(form_data: OAuth2PasswordRequestForm = Depends()):
    """Simple login test without complex error handling"""
    try:
        import bcrypt
        
        username = form_data.username.strip().lower()
        password = form_data.password
        
        # DB 조회
        user_data = await db.users.find_one({"login_id": username})
        if not user_data:
            return {"error": "user_not_found", "username": username}
        
        # 비밀번호 해시 확인
        stored_hash = user_data.get("password_hash", "")
        if not stored_hash:
            return {"error": "no_password_hash", "fields": list(user_data.keys())}
        
        # bcrypt 직접 검증
        password_valid = bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
        
        if password_valid:
            # 토큰 생성
            access_token = create_access_token(data={"sub": str(user_data["_id"])})
            return {"access_token": access_token, "token_type": "bearer", "status": "success"}
        else:
            return {"error": "invalid_password", "hash_length": len(stored_hash)}
            
    except Exception as e:
        return {"error": "exception", "message": str(e)}

# CLEAN AUTH ENDPOINT - Direct to main app to bypass router conflicts
@app.post("/api/auth/login", operation_id="login_user", response_model=Token)
async def clean_login_endpoint(form_data: OAuth2PasswordRequestForm = Depends()):
    """Clean login endpoint with enhanced validation and security"""
    
    try:
        # Input validation
        if not form_data.username or not form_data.username.strip():
            raise HTTPException(status_code=400, detail="사용자명을 입력해주세요.")
        
        if not form_data.password:
            raise HTTPException(status_code=400, detail="비밀번호를 입력해주세요.")
        
        # Rate limiting could be implemented here
        # For now, just log the attempt
        logging.info(f"Login attempt for user: {form_data.username}")
        
        # Sanitize username to prevent injection attacks
        username = form_data.username.strip().lower()
        
        # Database query with error handling
        try:
            logging.warning(f"DEBUG: Searching for user with login_id: '{username}'")
            user_data = await db.users.find_one({"login_id": username})
            logging.warning(f"DEBUG: User search result: {'Found' if user_data else 'Not found'}")
            if user_data:
                logging.warning(f"DEBUG: User fields: {list(user_data.keys())}")
        except Exception as e:
            logging.error(f"Database error during login for user {username}: {e}")
            raise HTTPException(status_code=500, detail="로그인 처리 중 데이터베이스 오류가 발생했습니다.")
        
        if not user_data:
            logging.warning(f"Login failed - user not found: {username}")
            # Don't reveal whether user exists or not for security
            raise HTTPException(status_code=401, detail="사용자명 또는 비밀번호가 올바르지 않습니다.")
        
        # Check if user account is active
        if not user_data.get("is_active", True):
            logging.warning(f"Login failed - inactive account: {username}")
            raise HTTPException(status_code=401, detail="계정이 비활성화되었습니다. 관리자에게 문의하세요.")
        
        # Verify password using bcrypt directly
        try:
            import bcrypt
            logging.warning(f"DEBUG: Attempting password verification for user: {username}")
            logging.warning(f"DEBUG: Password hash exists: {'password_hash' in user_data}")
            logging.warning(f"DEBUG: Password hash length: {len(user_data.get('password_hash', ''))}")
            
            stored_hash = user_data["password_hash"]
            password_valid = bcrypt.checkpw(form_data.password.encode('utf-8'), stored_hash.encode('utf-8'))
            
            logging.warning(f"DEBUG: Password verification result: {password_valid}")
        except Exception as e:
            logging.error(f"Password verification error for user {username}: {e}")
            raise HTTPException(status_code=500, detail="비밀번호 검증 중 오류가 발생했습니다.")
        
        if not password_valid:
            logging.warning(f"Login failed - invalid password for user: {username}")
            # Use same message as user not found for security
            raise HTTPException(status_code=401, detail="사용자명 또는 비밀번호가 올바르지 않습니다.")
        
        # Create token with error handling
        try:
            access_token = create_access_token(data={"sub": str(user_data["_id"])})
        except Exception as e:
            logging.error(f"Token creation error for user {username}: {e}")
            raise HTTPException(status_code=500, detail="인증 토큰 생성 중 오류가 발생했습니다.")
        
        # Update last login timestamp
        try:
            await db.users.update_one(
                {"_id": user_data["_id"]},
                {"$set": {"last_login": datetime.utcnow()}}
            )
        except Exception as e:
            logging.warning(f"Failed to update last login for user {username}: {e}")
            # Don't fail the login just because we can't update last login
        
        # Create user response with validation
        try:
            user_response = UserResponse(
                id=str(user_data["_id"]),
                login_id=user_data["login_id"],
                user_name=user_data["user_name"],
                email=user_data["email"],
                role=user_data["role"],
                is_active=user_data["is_active"],
                created_at=user_data.get("created_at", datetime.utcnow()),
                last_login=datetime.utcnow()
            )
        except Exception as e:
            logging.error(f"User response creation error for user {username}: {e}")
            raise HTTPException(status_code=500, detail="사용자 정보 구성 중 오류가 발생했습니다.")
        
        logging.info(f"Login successful for user: {username}")
        return Token(access_token=access_token, token_type="bearer", user=user_response)
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log unexpected errors securely (don't expose sensitive details)
        logging.error(f"Unexpected error during login: {e}")
        raise HTTPException(status_code=500, detail="로그인 처리 중 예상치 못한 오류가 발생했습니다.")

# API router will be included later with /api prefix

# Router registrations moved to centralized location below to avoid duplicates

# AI 모델 설정 라우터 추가
if AI_MODEL_SETTINGS_ENABLED:
    app.include_router(ai_model_settings_router)
    print("AI 모델 설정 기능이 활성화되었습니다.")

# 권한 관리 라우터 추가 (향상된 권한 시스템이 활성화된 경우에만)
if ENHANCED_PERMISSIONS_ENABLED:
    app.include_router(permission_admin_router)
    print("향상된 권한 관리 기능이 활성화되었습니다.")

# 향상된 템플릿 관리 라우터 추가 - MOVED to after api_router registration

# 헬스 모니터링 라우터 추가
# if enhanced_health_monitoring:
#     app.include_router(health_router)
#     print("✅ 향상된 헬스 모니터링 기능이 활성화되었습니다.")

# 평가 워크플로우 완성을 위한 추가 엔드포인트들

@api_router.post("/evaluations/create")
async def create_evaluation_assignment(
    assignment_data: dict,
    current_user: User = Depends(get_current_user)
):
    """새로운 평가 배정 생성"""
    check_admin_or_secretary(current_user)
    
    try:
        # 평가 시트 생성
        evaluation_sheet = {
            "id": str(uuid.uuid4()),
            "project_id": assignment_data["project_id"],
            "company_id": assignment_data["company_id"],
            "evaluator_id": assignment_data["evaluator_id"],
            "template_id": assignment_data.get("template_id"),
            "status": "assigned",
            "created_at": datetime.utcnow(),
            "created_by": current_user.id,
            "scores": {},
            "comments": ""
        }
        
        await db.evaluation_sheets.insert_one(evaluation_sheet)
        return {"message": "평가가 성공적으로 배정되었습니다", "evaluation_id": evaluation_sheet["id"]}
    
    except Exception as e:
        logger.error(f"평가 배정 생성 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"평가 배정 실패: {str(e)}")

@api_router.get("/evaluations/{evaluation_id}")
async def get_evaluation_detail(
    evaluation_id: str,
    current_user: User = Depends(get_current_user)
):
    """평가 상세 정보 조회"""
    try:
        evaluation = await db.evaluation_sheets.find_one({"id": evaluation_id})
        if not evaluation:
            raise HTTPException(status_code=404, detail="평가를 찾을 수 없습니다")
        
        # 권한 확인
        if current_user.role == "evaluator" and evaluation["evaluator_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="접근 권한이 없습니다")
        
        # 관련 정보 조회
        project = await db.projects.find_one({"id": evaluation["project_id"]})
        company = await db.companies.find_one({"id": evaluation["company_id"]})
        evaluator = await db.users.find_one({"id": evaluation["evaluator_id"]})
        template = await db.evaluation_templates.find_one({"id": evaluation.get("template_id")})
        
        return {
            "evaluation": evaluation,
            "project": project,
            "company": company,
            "evaluator": evaluator,
            "template": template
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"평가 상세 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"평가 상세 조회 실패: {str(e)}")

@api_router.put("/evaluations/{evaluation_id}")
async def update_evaluation(
    evaluation_id: str,
    update_data: dict,
    current_user: User = Depends(get_current_user)
):
    """평가 업데이트 (임시 저장)"""
    try:
        evaluation = await db.evaluation_sheets.find_one({"id": evaluation_id})
        if not evaluation:
            raise HTTPException(status_code=404, detail="평가를 찾을 수 없습니다")
        
        # 권한 확인
        if current_user.role == "evaluator" and evaluation["evaluator_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="접근 권한이 없습니다")
        
        # 업데이트 데이터 준비
        update_fields = {
            "scores": update_data.get("scores", evaluation["scores"]),
            "comments": update_data.get("comments", evaluation["comments"]),
            "status": update_data.get("status", "in_progress"),
            "updated_at": datetime.utcnow(),
            "updated_by": current_user.id
        }
        
        # 제출인 경우 제출 시간 기록
        if update_data.get("status") == "submitted":
            update_fields["submitted_at"] = datetime.utcnow()
        
        await db.evaluation_sheets.update_one(
            {"id": evaluation_id},
            {"$set": update_fields}
        )
        
        return {"message": "평가가 성공적으로 업데이트되었습니다"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"평가 업데이트 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"평가 업데이트 실패: {str(e)}")

@api_router.delete("/evaluations/{evaluation_id}")
async def delete_evaluation(
    evaluation_id: str,
    current_user: User = Depends(get_current_user)
):
    """평가 삭제"""
    check_admin_or_secretary(current_user)
    
    try:
        result = await db.evaluation_sheets.delete_one({"id": evaluation_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="평가를 찾을 수 없습니다")
        
        # 관련 점수 데이터도 삭제
        await db.evaluation_scores.delete_many({"sheet_id": evaluation_id})
        
        return {"message": "평가가 성공적으로 삭제되었습니다"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"평가 삭제 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"평가 삭제 실패: {str(e)}")

@api_router.get("/dashboard/statistics")
async def get_dashboard_statistics(
    current_user: User = Depends(get_current_user)
):
    """대시보드 통계 데이터 조회"""
    try:
        # 기본 통계 데이터 조회
        total_projects = await db.projects.count_documents({})
        total_companies = await db.companies.count_documents({})
        total_evaluators = await db.users.count_documents({"role": "evaluator"})
        total_evaluations = await db.evaluation_sheets.count_documents({})
        
        # 상태별 평가 집계
        pending_evaluations = await db.evaluation_sheets.count_documents({"status": "assigned"})
        in_progress_evaluations = await db.evaluation_sheets.count_documents({"status": "in_progress"})
        completed_evaluations = await db.evaluation_sheets.count_documents({"status": "submitted"})
        
        # 최근 활동
        recent_evaluations = await db.evaluation_sheets.find(
            {},
            sort=[("created_at", -1)],
            limit=5
        ).to_list(5)
        
        return {
            "overview": {
                "total_projects": total_projects,
                "total_companies": total_companies,
                "total_evaluators": total_evaluators,
                "total_evaluations": total_evaluations
            },
            "evaluation_status": {
                "pending": pending_evaluations,
                "in_progress": in_progress_evaluations,
                "completed": completed_evaluations,
                "completion_rate": round((completed_evaluations / max(total_evaluations, 1)) * 100, 1)
            },
            "recent_activity": recent_evaluations
        }
    
    except Exception as e:
        logger.error(f"대시보드 통계 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"대시보드 통계 조회 실패: {str(e)}")

# Duplicate router registrations removed - centralized below

# 배포 관리 라우터 추가
if DEPLOYMENT_MANAGER_ENABLED:
    app.include_router(deployment_router)
    print("✅ 배포 관리 기능이 활성화되었습니다.")

# WebSocket 엔드포인트 추가
try:
    from websocket_service import connection_manager, notification_service as ws_notification_service
    
    @app.websocket("/ws/{user_id}")
    async def websocket_endpoint(websocket: WebSocket, user_id: str):
        """WebSocket 연결 엔드포인트"""
        await connection_manager.connect(websocket, user_id)
        try:
            while True:
                # 클라이언트로부터 메시지 수신
                data = await websocket.receive_text()
                try:
                    message = json.loads(data)
                    
                    # 메시지 타입별 처리
                    if message.get("type") == "join_room":
                        room_id = message.get("room_id")
                        if room_id:
                            await connection_manager.join_room(websocket, room_id)
                    
                    elif message.get("type") == "leave_room":
                        room_id = message.get("room_id")
                        if room_id:
                            await connection_manager.leave_room(websocket, room_id)
                    
                    elif message.get("type") == "ping":
                        # 연결 상태 확인
                        await connection_manager.send_personal_message({
                            "type": "pong",
                            "timestamp": datetime.utcnow().isoformat()
                        }, websocket)
                    
                except json.JSONDecodeError:
                    # 잘못된 JSON 메시지 무시
                    pass
                    
        except WebSocketDisconnect:
            connection_manager.disconnect(websocket)
    
    @app.get("/api/notifications/active-connections")
    async def get_active_connections(current_user: User = Depends(get_current_user)):
        """활성 WebSocket 연결 상태 조회 (관리자 전용)"""
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="관리자만 연결 상태를 조회할 수 있습니다")
        
        return {
            "active_users": connection_manager.get_active_users(),
            "total_connections": connection_manager.get_connection_count(),
            "rooms": list(connection_manager.rooms.keys())
        }
    
    @app.post("/api/notifications/send-broadcast")
    async def send_broadcast_notification(
        message: dict,
        current_user: User = Depends(get_current_user)
    ):
        """전체 사용자에게 브로드캐스트 알림 전송 (관리자 전용)"""
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="관리자만 브로드캐스트 알림을 보낼 수 있습니다")
        
        notification_message = {
            "type": "admin_broadcast",
            "title": message.get("title", "관리자 공지"),
            "message": message.get("message", ""),
            "priority": message.get("priority", "info"),
            "timestamp": datetime.utcnow().isoformat(),
            "sender": current_user.user_name
        }
        
        await connection_manager.broadcast_to_all(notification_message)
        
        return {"message": "브로드캐스트 알림이 전송되었습니다"}
    
    print("✅ WebSocket 실시간 알림 시스템이 활성화되었습니다.")
    
except ImportError as e:
    print(f"⚠️ WebSocket 서비스를 가져올 수 없습니다: {e}")

# 기본 API 라우터 추가 (중요한 엔드포인트들)
try:
    app.include_router(api_router, prefix="/api", tags=["Main API"])
    print("✅ 기본 API 라우터가 등록되었습니다.")
except Exception as e:
    print(f"⚠️ API 라우터 등록 실패: {e}")
    print("API 라우터가 정의되지 않았을 수 있습니다. 기본 엔드포인트들은 직접 등록됩니다.")

# 향상된 템플릿 관리 라우터 추가 (prefix 없이 등록하여 우선순위 확보)
if ENHANCED_TEMPLATES_ENABLED:
    app.include_router(template_router, prefix="")
    print("✅ 향상된 템플릿 관리 기능이 활성화되었습니다 (prefix 없이 등록하여 우선순위 확보).")

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
