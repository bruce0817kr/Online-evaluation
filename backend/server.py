from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
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

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT settings
SECRET_KEY = "your-secret-key-here-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Create the main app without a prefix
app = FastAPI(title="온라인 평가 시스템")

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
    files: List[str] = []  # file paths
    created_at: datetime = Field(default_factory=datetime.utcnow)

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
    status: str  # draft, submitted
    deadline: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    submitted_at: Optional[datetime] = None

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

# Project routes
@api_router.get("/projects", response_model=List[Project])
async def get_projects(current_user: User = Depends(get_current_user)):
    projects = await db.projects.find({"is_active": True}).to_list(1000)
    return [Project(**project) for project in projects]

@api_router.post("/projects", response_model=Project)
async def create_project(project_data: ProjectCreate, current_user: User = Depends(get_current_user)):
    check_admin_or_secretary(current_user)
    
    deadline_dt = datetime.fromisoformat(project_data.deadline.replace('Z', '+00:00'))
    project = Project(
        name=project_data.name,
        description=project_data.description,
        deadline=deadline_dt,
        created_by=current_user.id
    )
    
    await db.projects.insert_one(project.dict())
    return project

# Company routes
@api_router.get("/companies", response_model=List[Company])
async def get_companies(project_id: Optional[str] = None, current_user: User = Depends(get_current_user)):
    query = {}
    if project_id:
        query["project_id"] = project_id
    
    companies = await db.companies.find(query).to_list(1000)
    return [Company(**company) for company in companies]

@api_router.post("/companies", response_model=Company)
async def create_company(company_data: CompanyCreate, current_user: User = Depends(get_current_user)):
    check_admin_or_secretary(current_user)
    
    company = Company(**company_data.dict())
    await db.companies.insert_one(company.dict())
    return company

# Evaluation Template routes
@api_router.get("/templates", response_model=List[EvaluationTemplate])
async def get_templates(project_id: Optional[str] = None, current_user: User = Depends(get_current_user)):
    query = {}
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

# Assignment routes
@api_router.post("/assignments")
async def create_assignments(assignment_data: AssignmentCreate, current_user: User = Depends(get_current_user)):
    check_admin_or_secretary(current_user)
    
    deadline = None
    if assignment_data.deadline:
        deadline = datetime.fromisoformat(assignment_data.deadline.replace('Z', '+00:00'))
    
    created_sheets = []
    
    # Create evaluation sheets for each evaluator-company combination
    for evaluator_id in assignment_data.evaluator_ids:
        for company_id in assignment_data.company_ids:
            # Get company to find project_id
            company_data = await db.companies.find_one({"id": company_id})
            if not company_data:
                continue
                
            # Check if assignment already exists
            existing_sheet = await db.evaluation_sheets.find_one({
                "evaluator_id": evaluator_id,
                "company_id": company_id,
                "template_id": assignment_data.template_id
            })
            
            if not existing_sheet:
                sheet = EvaluationSheet(
                    evaluator_id=evaluator_id,
                    company_id=company_id,
                    project_id=company_data["project_id"],
                    template_id=assignment_data.template_id,
                    status="draft",
                    deadline=deadline
                )
                
                await db.evaluation_sheets.insert_one(sheet.dict())
                created_sheets.append(sheet)
    
    return {"message": f"{len(created_sheets)}개의 평가가 할당되었습니다", "count": len(created_sheets)}

# File upload routes
@api_router.post("/upload")
async def upload_file(
    company_id: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    check_admin_or_secretary(current_user)
    
    # Create uploads directory if it doesn't exist
    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)
    
    # Save file
    file_path = upload_dir / f"{company_id}_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Update company's files list
    await db.companies.update_one(
        {"id": company_id},
        {"$push": {"files": str(file_path)}}
    )
    
    return {"filename": file.filename, "path": str(file_path)}

# Evaluation routes
@api_router.get("/evaluation/{sheet_id}")
async def get_evaluation_sheet(sheet_id: str, current_user: User = Depends(get_current_user)):
    sheet_data = await db.evaluation_sheets.find_one({"id": sheet_id})
    if not sheet_data:
        raise HTTPException(status_code=404, detail="평가지를 찾을 수 없습니다")
    
    sheet = EvaluationSheet(**sheet_data)
    
    # Check permissions
    if current_user.role == "evaluator" and sheet.evaluator_id != current_user.id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다")
    
    # Get related data
    company_data = await db.companies.find_one({"id": sheet.company_id})
    project_data = await db.projects.find_one({"id": sheet.project_id})
    template_data = await db.evaluation_templates.find_one({"id": sheet.template_id})
    
    # Get existing scores
    scores = await db.evaluation_scores.find({"sheet_id": sheet_id}).to_list(1000)
    
    return {
        "sheet": sheet,
        "company": Company(**company_data) if company_data else None,
        "project": Project(**project_data) if project_data else None,
        "template": EvaluationTemplate(**template_data) if template_data else None,
        "scores": [EvaluationScore(**score) for score in scores]
    }

@api_router.post("/evaluation/submit")
async def submit_evaluation(submission: EvaluationSubmission, current_user: User = Depends(get_current_user)):
    sheet_data = await db.evaluation_sheets.find_one({"id": submission.sheet_id})
    if not sheet_data:
        raise HTTPException(status_code=404, detail="평가지를 찾을 수 없습니다")
    
    sheet = EvaluationSheet(**sheet_data)
    
    # Check permissions
    if current_user.role == "evaluator" and sheet.evaluator_id != current_user.id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다")
    
    # Delete existing scores
    await db.evaluation_scores.delete_many({"sheet_id": submission.sheet_id})
    
    # Save new scores
    for score_data in submission.scores:
        score = EvaluationScore(
            sheet_id=submission.sheet_id,
            item_id=score_data["item_id"],
            score=score_data["score"],
            opinion=score_data.get("opinion", "")
        )
        await db.evaluation_scores.insert_one(score.dict())
    
    # Update sheet status
    await db.evaluation_sheets.update_one(
        {"id": submission.sheet_id},
        {"$set": {"status": "submitted", "submitted_at": datetime.utcnow()}}
    )
    
    return {"message": "평가가 성공적으로 제출되었습니다"}

@api_router.post("/evaluation/save")
async def save_evaluation(submission: EvaluationSubmission, current_user: User = Depends(get_current_user)):
    sheet_data = await db.evaluation_sheets.find_one({"id": submission.sheet_id})
    if not sheet_data:
        raise HTTPException(status_code=404, detail="평가지를 찾을 수 없습니다")
    
    sheet = EvaluationSheet(**sheet_data)
    
    # Check permissions
    if current_user.role == "evaluator" and sheet.evaluator_id != current_user.id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다")
    
    # Delete existing scores
    await db.evaluation_scores.delete_many({"sheet_id": submission.sheet_id})
    
    # Save new scores
    for score_data in submission.scores:
        score = EvaluationScore(
            sheet_id=submission.sheet_id,
            item_id=score_data["item_id"],
            score=score_data["score"],
            opinion=score_data.get("opinion", "")
        )
        await db.evaluation_scores.insert_one(score.dict())
    
    return {"message": "평가가 임시저장되었습니다"}

# Dashboard routes
@api_router.get("/dashboard/evaluator")
async def get_evaluator_dashboard(current_user: User = Depends(get_current_user)):
    if current_user.role != "evaluator":
        raise HTTPException(status_code=403, detail="평가위원만 접근할 수 있습니다")
    
    # Get assigned evaluation sheets
    sheets = await db.evaluation_sheets.find({"evaluator_id": current_user.id}).to_list(1000)
    
    # Get company and project details for each sheet
    result = []
    for sheet_data in sheets:
        sheet = EvaluationSheet(**sheet_data)
        company_data = await db.companies.find_one({"id": sheet.company_id})
        project_data = await db.projects.find_one({"id": sheet.project_id})
        template_data = await db.evaluation_templates.find_one({"id": sheet.template_id})
        
        if company_data and project_data and template_data:
            result.append({
                "sheet": sheet,
                "company": Company(**company_data),
                "project": Project(**project_data),
                "template": EvaluationTemplate(**template_data)
            })
    
    return result

@api_router.get("/dashboard/admin")
async def get_admin_dashboard(current_user: User = Depends(get_current_user)):
    if current_user.role not in ["admin", "secretary"]:
        raise HTTPException(status_code=403, detail="관리자 또는 간사만 접근할 수 있습니다")
    
    # Get statistics
    projects_count = await db.projects.count_documents({"is_active": True})
    companies_count = await db.companies.count_documents({})
    evaluators_count = await db.users.count_documents({"role": "evaluator", "is_active": True})
    
    # Get evaluation progress
    total_sheets = await db.evaluation_sheets.count_documents({})
    completed_sheets = await db.evaluation_sheets.count_documents({"status": "submitted"})
    
    # Get recent projects
    recent_projects = await db.projects.find({"is_active": True}).sort("created_at", -1).limit(5).to_list(5)
    
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
    
    for user_data in default_users:
        hashed_password = get_password_hash(user_data["password"])
        user = User(
            login_id=user_data["login_id"],
            password_hash=hashed_password,
            user_name=user_data["user_name"],
            email=user_data["email"],
            role=user_data["role"]
        )
        await db.users.insert_one(user.dict())
    
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

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()