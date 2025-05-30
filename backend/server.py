from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
import shutil

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
    role: str  # admin, secretary, evaluator
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

class UserCreate(BaseModel):
    login_id: str
    password: str
    user_name: str
    email: str
    role: str

class UserResponse(BaseModel):
    id: str
    login_id: str
    user_name: str
    email: str
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

class EvaluationItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    max_score: int
    project_id: str

class EvaluationSheet(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    evaluator_id: str
    company_id: str
    project_id: str
    status: str  # draft, submitted
    created_at: datetime = Field(default_factory=datetime.utcnow)
    submitted_at: Optional[datetime] = None

class EvaluationScore(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sheet_id: str
    item_id: str
    score: int
    opinion: str

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
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="관리자만 사용자를 생성할 수 있습니다")
    
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
        role=user_data.role
    )
    
    await db.users.insert_one(user.dict())
    return UserResponse(**user.dict())

# Project routes
@api_router.get("/projects", response_model=List[Project])
async def get_projects(current_user: User = Depends(get_current_user)):
    projects = await db.projects.find({"is_active": True}).to_list(1000)
    return [Project(**project) for project in projects]

@api_router.post("/projects", response_model=Project)
async def create_project(
    name: str = Form(...),
    description: str = Form(...),
    deadline: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "secretary"]:
        raise HTTPException(status_code=403, detail="권한이 없습니다")
    
    deadline_dt = datetime.fromisoformat(deadline)
    project = Project(
        name=name,
        description=description,
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
async def create_company(
    name: str = Form(...),
    business_number: str = Form(...),
    address: str = Form(...),
    contact_person: str = Form(...),
    phone: str = Form(...),
    email: str = Form(...),
    project_id: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "secretary"]:
        raise HTTPException(status_code=403, detail="권한이 없습니다")
    
    company = Company(
        name=name,
        business_number=business_number,
        address=address,
        contact_person=contact_person,
        phone=phone,
        email=email,
        project_id=project_id
    )
    
    await db.companies.insert_one(company.dict())
    return company

# File upload routes
@api_router.post("/upload")
async def upload_file(
    company_id: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "secretary"]:
        raise HTTPException(status_code=403, detail="권한이 없습니다")
    
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
        
        if company_data and project_data:
            result.append({
                "sheet": sheet,
                "company": Company(**company_data),
                "project": Project(**project_data)
            })
    
    return result

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