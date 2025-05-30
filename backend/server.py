from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import FileResponse, StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
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
import shutil
import re
import asyncio
import aiofiles
import io
import base64
from concurrent.futures import ThreadPoolExecutor
import json

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

# JWT settings
SECRET_KEY = "your-secret-key-here-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Create the main app without a prefix
app = FastAPI(title="온라인 평가 시스템", version="2.0.0")

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
    contact_person: str
    phone: str
    email: str
    project_id: str
    files: List[Dict[str, Any]] = []  # Enhanced file metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    evaluation_status: str = "pending"  # pending, in_progress, completed

class CompanyCreate(BaseModel):
    name: str
    business_number: str
    address: str
    contact_person: str
    phone: str
    email: str
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
    password = clean_phone[-8:]  # last 8 digits of phone
    
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
    upload_dir.mkdir(exist_ok=True)
    
    # Generate unique filename
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
async def preview_file(file_id: str, current_user: User = Depends(get_current_user)):
    """Get file content for inline preview"""
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
@api_router.get("/health")
async def health_check():
    try:
        # Check database connection
        await db.admin.command('ping')
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow(),
            "database": "connected",
            "version": "2.0.0"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow(),
            "database": "disconnected",
            "error": str(e)
        }

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

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    logger.info("온라인 평가 시스템 v2.0.0 시작됨")
    logger.info(f"MongoDB 연결: {mongo_url}")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
    executor.shutdown(wait=True)
    logger.info("시스템 종료됨")