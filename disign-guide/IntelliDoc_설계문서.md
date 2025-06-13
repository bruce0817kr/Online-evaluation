# IntelliDoc 설계문서 (AI 코더 최적화)

## 1. 시스템 아키텍처 설계

### 1.1 전체 아키텍처 다이어그램
```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │  Auth    │ │Document  │ │  OCR/LLM │ │  Export  │          │
│  │Component │ │ Upload   │ │  Process │ │  Module  │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API Gateway (FastAPI)                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │   Auth   │ │Document  │ │Processing│ │  Export  │          │
│  │  Router  │ │  Router  │ │  Router  │ │  Router  │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
└─────────────────────────────────────────────────────────────────┘
                                │
         ┌──────────────────────┼──────────────────────┐
         ▼                      ▼                      ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Auth Service   │    │Document Service │    │Process Service  │
│  - JWT Token    │    │  - Upload       │    │  - OCR Engine   │
│  - RBAC         │    │  - Storage      │    │  - LLM Engine   │
│  - User Mgmt    │    │  - Metadata     │    │  - Queue Mgmt   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                      │                      │
         └──────────────────────┼──────────────────────┘
                                ▼
         ┌──────────────────────────────────────────────┐
         │           Data Layer                         │
         │  ┌────────────┐  ┌────────────┐            │
         │  │PostgreSQL  │  │   Redis    │            │
         │  │(Metadata)  │  │(Cache/Queue)│           │
         │  └────────────┘  └────────────┘            │
         └──────────────────────────────────────────────┘
```

### 1.2 컴포넌트 간 통신 설계
```yaml
통신 프로토콜:
  - Frontend ↔ Backend: REST API (HTTPS)
  - Backend Services: 내부 함수 호출
  - Backend ↔ Redis: Redis Protocol
  - Backend ↔ PostgreSQL: psycopg2
  - Celery Workers: AMQP over Redis

데이터 형식:
  - API Request/Response: JSON
  - 파일 업로드: multipart/form-data
  - 내부 통신: Python 객체/Dict
  - 캐시 데이터: JSON 직렬화
```

## 2. 데이터베이스 설계

### 2.1 ER 다이어그램 (주요 테이블)
```sql
-- 사용자 테이블
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    CONSTRAINT check_role CHECK (role IN ('admin', 'user', 'viewer'))
);

-- 문서 테이블
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    original_filename VARCHAR(255) NOT NULL,
    storage_path VARCHAR(500) NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    page_count INTEGER,
    status VARCHAR(20) NOT NULL DEFAULT 'UPLOADED',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    CONSTRAINT check_status CHECK (status IN ('UPLOADED', 'PROCESSING', 'COMPLETED', 'ERROR'))
);

-- OCR 결과 테이블
CREATE TABLE ocr_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id),
    engine VARCHAR(50) NOT NULL,
    page_number INTEGER NOT NULL,
    text_content TEXT,
    confidence_score DECIMAL(3,2),
    processing_time INTEGER, -- milliseconds
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- LLM 결과 테이블
CREATE TABLE llm_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id),
    engine VARCHAR(50) NOT NULL,
    task_type VARCHAR(50) NOT NULL,
    result JSONB NOT NULL,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    processing_time INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 처리 작업 테이블
CREATE TABLE processing_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id),
    job_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    celery_task_id VARCHAR(255),
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    CONSTRAINT check_job_type CHECK (job_type IN ('OCR', 'LLM', 'EXPORT'))
);

-- 인덱스 생성
CREATE INDEX idx_documents_user_id ON documents(user_id);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_ocr_results_document_id ON ocr_results(document_id);
CREATE INDEX idx_llm_results_document_id ON llm_results(document_id);
CREATE INDEX idx_processing_jobs_document_id ON processing_jobs(document_id);
CREATE INDEX idx_processing_jobs_status ON processing_jobs(status);
```

### 2.2 데이터 모델 설계 (SQLAlchemy)
```python
# shared/models.py
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, JSON, DECIMAL
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default='user')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default='NOW()')
    updated_at = Column(DateTime(timezone=True), onupdate='NOW()')
    
    # Relationships
    documents = relationship("Document", back_populates="user")

class Document(Base):
    __tablename__ = 'documents'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    original_filename = Column(String(255), nullable=False)
    storage_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    page_count = Column(Integer)
    status = Column(String(20), nullable=False, default='UPLOADED')
    created_at = Column(DateTime(timezone=True), server_default='NOW()')
    updated_at = Column(DateTime(timezone=True), onupdate='NOW()')
    
    # Relationships
    user = relationship("User", back_populates="documents")
    ocr_results = relationship("OCRResult", back_populates="document")
    llm_results = relationship("LLMResult", back_populates="document")
    processing_jobs = relationship("ProcessingJob", back_populates="document")
```

## 3. API 설계

### 3.1 RESTful API 엔드포인트
```yaml
# 인증 API
POST   /api/v1/auth/login          # 로그인
POST   /api/v1/auth/refresh        # 토큰 갱신
POST   /api/v1/auth/logout         # 로그아웃
GET    /api/v1/auth/me             # 현재 사용자 정보

# 사용자 관리 API
GET    /api/v1/users               # 사용자 목록 (admin)
POST   /api/v1/users               # 사용자 생성 (admin)
GET    /api/v1/users/{id}          # 사용자 상세
PUT    /api/v1/users/{id}          # 사용자 수정
DELETE /api/v1/users/{id}          # 사용자 삭제 (admin)

# 문서 관리 API
POST   /api/v1/documents/upload    # 문서 업로드
GET    /api/v1/documents           # 문서 목록
GET    /api/v1/documents/{id}      # 문서 상세
DELETE /api/v1/documents/{id}      # 문서 삭제

# 처리 API
POST   /api/v1/documents/{id}/ocr  # OCR 처리 시작
GET    /api/v1/documents/{id}/ocr/status  # OCR 상태 조회
GET    /api/v1/documents/{id}/ocr/result  # OCR 결과 조회

POST   /api/v1/documents/{id}/llm  # LLM 처리 시작
GET    /api/v1/documents/{id}/llm/status  # LLM 상태 조회
GET    /api/v1/documents/{id}/llm/result  # LLM 결과 조회

# 내보내기 API
GET    /api/v1/documents/{id}/export  # 문서 내보내기
POST   /api/v1/documents/batch/export # 배치 내보내기

# 템플릿 API
GET    /api/v1/templates           # 템플릿 목록
POST   /api/v1/templates           # 템플릿 생성
GET    /api/v1/templates/{id}      # 템플릿 상세
PUT    /api/v1/templates/{id}      # 템플릿 수정
DELETE /api/v1/templates/{id}      # 템플릿 삭제
```

### 3.2 API 스키마 정의 (Pydantic)
```python
# shared/schemas.py
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

# 인증 스키마
class UserLogin(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

# 사용자 스키마
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    role: str = Field(default="user", regex="^(admin|user|viewer)$")

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    
    @validator('password')
    def validate_password(cls, v):
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        return v

class UserResponse(UserBase):
    id: UUID
    is_active: bool
    created_at: datetime
    
    class Config:
        orm_mode = True

# 문서 스키마
class DocumentUpload(BaseModel):
    metadata: Optional[Dict[str, Any]] = None

class DocumentResponse(BaseModel):
    id: UUID
    original_filename: str
    file_size: int
    mime_type: str
    status: str
    page_count: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        orm_mode = True

# OCR 스키마
class OCRRequest(BaseModel):
    engine: str = Field(default="tesseract", regex="^(tesseract|google_vision|aws_textract)$")
    options: Optional[Dict[str, Any]] = None

class OCRResult(BaseModel):
    page_number: int
    text: str
    confidence: float = Field(..., ge=0, le=1)
    
# LLM 스키마
class LLMRequest(BaseModel):
    engine: str = Field(default="openai", regex="^(openai|ollama|claude)$")
    model: Optional[str] = None
    tasks: List[Dict[str, Any]]

class LLMResult(BaseModel):
    task_type: str
    result: Dict[str, Any]
    processing_time: int
```

## 4. 핵심 모듈 상세 설계

### 4.1 인증 모듈 (auth)
```python
# auth/service.py
import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
from shared.config import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRATION
from shared.models import User
from shared.database import get_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self):
        self.secret_key = JWT_SECRET_KEY
        self.algorithm = JWT_ALGORITHM
        self.access_token_expire = timedelta(minutes=JWT_EXPIRATION)
        
    def create_access_token(self, data: dict) -> str:
        """JWT 액세스 토큰 생성"""
        to_encode = data.copy()
        expire = datetime.utcnow() + self.access_token_expire
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> dict:
        """JWT 토큰 검증 및 디코드"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.PyJWTError:
            raise ValueError("Invalid token")
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """비밀번호 검증"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """비밀번호 해시 생성"""
        return pwd_context.hash(password)
    
    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """사용자 인증"""
        db = next(get_db())
        user = db.query(User).filter(User.username == username).first()
        if not user or not self.verify_password(password, user.password_hash):
            return None
        return user

# auth/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from auth.service import AuthService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """현재 사용자 정보 반환"""
    auth_service = AuthService()
    try:
        payload = auth_service.verify_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    db = next(get_db())
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

def require_role(allowed_roles: List[str]):
    """역할 기반 접근 제어 데코레이터"""
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker
```

### 4.2 파일 관리 모듈 (file_manager)
```python
# file_manager/service.py
import os
import hashlib
from typing import List, BinaryIO
from uuid import UUID
import aiofiles
from fastapi import UploadFile, HTTPException
from shared.config import UPLOAD_DIR, MAX_FILE_SIZE, ALLOWED_EXTENSIONS
from shared.models import Document
from shared.database import get_db

class FileService:
    def __init__(self):
        self.upload_dir = UPLOAD_DIR
        self.max_file_size = MAX_FILE_SIZE
        self.allowed_extensions = ALLOWED_EXTENSIONS
        
    def validate_file(self, file: UploadFile) -> None:
        """파일 유효성 검증"""
        # 파일 크기 검증
        if file.size > self.max_file_size:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum allowed size of {self.max_file_size} bytes"
            )
        
        # 파일 확장자 검증
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in self.allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type {ext} is not allowed"
            )
    
    async def save_file(self, file: UploadFile, user_id: UUID) -> str:
        """파일 저장 및 경로 반환"""
        self.validate_file(file)
        
        # 안전한 파일명 생성
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        file_hash = hashlib.md5(file.filename.encode()).hexdigest()[:8]
        safe_filename = f"{user_id}_{timestamp}_{file_hash}{os.path.splitext(file.filename)[1]}"
        
        # 사용자별 디렉토리 생성
        user_dir = os.path.join(self.upload_dir, str(user_id))
        os.makedirs(user_dir, exist_ok=True)
        
        # 파일 저장
        file_path = os.path.join(user_dir, safe_filename)
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        return file_path
    
    def extract_metadata(self, file_path: str) -> dict:
        """파일 메타데이터 추출"""
        metadata = {
            'file_size': os.path.getsize(file_path),
            'mime_type': self.get_mime_type(file_path),
        }
        
        # PDF 메타데이터 추출
        if file_path.endswith('.pdf'):
            metadata.update(self.extract_pdf_metadata(file_path))
        
        return metadata
    
    def get_mime_type(self, file_path: str) -> str:
        """MIME 타입 추출"""
        import magic
        mime = magic.Magic(mime=True)
        return mime.from_file(file_path)
    
    def extract_pdf_metadata(self, file_path: str) -> dict:
        """PDF 메타데이터 추출"""
        import PyPDF2
        metadata = {}
        
        try:
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                metadata['page_count'] = len(pdf_reader.pages)
                
                if pdf_reader.metadata:
                    metadata['author'] = pdf_reader.metadata.get('/Author', '')
                    metadata['title'] = pdf_reader.metadata.get('/Title', '')
                    metadata['subject'] = pdf_reader.metadata.get('/Subject', '')
        except Exception as e:
            print(f"Error extracting PDF metadata: {e}")
        
        return metadata

# file_manager/queue.py
from celery import Celery
from shared.config import REDIS_URL

celery_app = Celery('intellidoc', broker=REDIS_URL, backend=REDIS_URL)

@celery_app.task
def process_document_task(document_id: str, processing_type: str):
    """문서 처리 비동기 작업"""
    try:
        if processing_type == 'OCR':
            process_ocr(document_id)
        elif processing_type == 'LLM':
            process_llm(document_id)
        else:
            raise ValueError(f"Unknown processing type: {processing_type}")
    except Exception as e:
        # 에러 로깅 및 상태 업데이트
        update_document_status(document_id, 'ERROR', str(e))
        raise
```

### 4.3 OCR 엔진 모듈 (ocr_engines)
```python
# ocr_engines/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseOCREngine(ABC):
    """OCR 엔진 추상 클래스"""
    
    @abstractmethod
    def __init__(self, config: Dict[str, Any]):
        """엔진 초기화"""
        self.config = config
    
    @abstractmethod
    def extract_text(self, image_path: str) -> Dict[str, Any]:
        """텍스트 추출"""
        pass
    
    @abstractmethod
    def extract_structured_data(self, image_path: str) -> List[Dict[str, Any]]:
        """구조화된 데이터 추출 (테이블, 양식 등)"""
        pass
    
    @abstractmethod
    def get_confidence_score(self) -> float:
        """신뢰도 점수 반환"""
        pass

# ocr_engines/tesseract.py
import pytesseract
from PIL import Image
import cv2
import numpy as np

class TesseractEngine(BaseOCREngine):
    """Tesseract OCR 엔진 구현"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.language = config.get('language', 'kor+eng')
        self.confidence_threshold = config.get('confidence_threshold', 0.6)
        
    def preprocess_image(self, image_path: str) -> np.ndarray:
        """이미지 전처리"""
        # 이미지 읽기
        image = cv2.imread(image_path)
        
        # 그레이스케일 변환
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 노이즈 제거
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # 대비 향상
        enhanced = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8)).apply(denoised)
        
        # 이진화
        _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        return binary
    
    def extract_text(self, image_path: str) -> Dict[str, Any]:
        """텍스트 추출"""
        # 이미지 전처리
        processed_image = self.preprocess_image(image_path)
        
        # OCR 수행
        custom_config = f'--oem 3 --psm 6 -l {self.language}'
        data = pytesseract.image_to_data(processed_image, config=custom_config, output_type=pytesseract.Output.DICT)
        
        # 텍스트 조합
        text = ' '.join([word for word, conf in zip(data['text'], data['conf']) 
                        if int(conf) > self.confidence_threshold * 100 and word.strip()])
        
        # 평균 신뢰도 계산
        confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        return {
            'text': text,
            'confidence': avg_confidence / 100,
            'language': self.language,
            'word_count': len(text.split())
        }
    
    def extract_structured_data(self, image_path: str) -> List[Dict[str, Any]]:
        """테이블 구조 추출"""
        # 이미지 전처리
        processed_image = self.preprocess_image(image_path)
        
        # 테이블 감지 (간단한 구현)
        # 실제로는 더 복잡한 테이블 감지 알고리즘 필요
        tables = []
        
        # Hough 변환으로 라인 감지
        edges = cv2.Canny(processed_image, 50, 150, apertureSize=3)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, minLineLength=100, maxLineGap=10)
        
        # 테이블 영역 추출 로직 (간략화)
        # 실제 구현에서는 라인 교차점을 찾아 셀 영역 정의
        
        return tables
    
    def get_confidence_score(self) -> float:
        """마지막 처리의 신뢰도 반환"""
        return self.last_confidence if hasattr(self, 'last_confidence') else 0.0

# ocr_engines/postprocessor.py
import re
from typing import List, Dict

class KoreanPostProcessor:
    """한국어 OCR 후처리"""
    
    def __init__(self):
        # 자주 틀리는 한글 매핑
        self.common_mistakes = {
            '대헌': '대한',
            '인국': '한국',
            '서을': '서울',
            # ... 더 많은 매핑
        }
        
        # 한글 자모 분리/결합을 위한 상수
        self.CHOSUNG = list('ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ')
        self.JUNGSUNG = list('ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ')
        self.JONGSUNG = list(' ㄱㄲㄳㄴㄵㄶㄷㄹㄺㄻㄼㄽㄾㄿㅀㅁㅂㅄㅅㅆㅇㅈㅊㅋㅌㅍㅎ')
    
    def correct_korean_typos(self, text: str) -> str:
        """한글 오타 수정"""
        corrected = text
        
        # 일반적인 오타 수정
        for mistake, correct in self.common_mistakes.items():
            corrected = corrected.replace(mistake, correct)
        
        # 분리된 자모 결합
        corrected = self.combine_separated_jamo(corrected)
        
        return corrected
    
    def fix_spacing(self, text: str) -> str:
        """띄어쓰기 교정"""
        # 조사 앞 띄어쓰기 제거
        particles = ['은', '는', '이', '가', '을', '를', '의', '에', '에서', '로', '으로']
        for particle in particles:
            text = re.sub(f' {particle}(?=\\s|$)', particle, text)
        
        # 숫자와 단위 사이 띄어쓰기
        text = re.sub(r'(\d+)([가-힣]+)', r'\1 \2', text)
        
        return text
    
    def normalize_special_chars(self, text: str) -> str:
        """특수문자 정규화"""
        # 전각 문자를 반각으로
        text = text.replace('．', '.').replace('，', ',').replace('！', '!')
        
        # 중복된 공백 제거
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def process(self, text: str) -> str:
        """전체 후처리 파이프라인"""
        text = self.correct_korean_typos(text)
        text = self.fix_spacing(text)
        text = self.normalize_special_chars(text)
        return text
```

### 4.4 LLM 처리 모듈 (llm_processors)
```python
# llm_processors/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseLLMProcessor(ABC):
    """LLM 프로세서 추상 클래스"""
    
    @abstractmethod
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    @abstractmethod
    def analyze_document(self, text: str, prompt: str) -> Dict[str, Any]:
        """문서 분석"""
        pass
    
    @abstractmethod
    def extract_structured_data(self, text: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """구조화된 데이터 추출"""
        pass
    
    @abstractmethod
    def summarize(self, text: str, max_length: int = 500) -> str:
        """문서 요약"""
        pass

# llm_processors/openai_processor.py
import openai
from typing import Dict, Any
import json

class OpenAIProcessor(BaseLLMProcessor):
    """OpenAI LLM 프로세서"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        openai.api_key = config.get('api_key')
        self.model = config.get('model', 'gpt-4')
        self.temperature = config.get('temperature', 0.3)
        
    def analyze_document(self, text: str, prompt: str) -> Dict[str, Any]:
        """문서 분석"""
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a document analysis assistant."},
                    {"role": "user", "content": f"{prompt}\n\nDocument:\n{text}"}
                ],
                temperature=self.temperature
            )
            
            return {
                'result': response.choices[0].message['content'],
                'usage': response['usage'],
                'model': self.model
            }
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    def extract_structured_data(self, text: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """구조화된 데이터 추출"""
        prompt = f"""
        Extract the following information from the document and return as JSON:
        Schema: {json.dumps(schema, ensure_ascii=False)}
        
        Return only valid JSON without any additional text.
        """
        
        response = self.analyze_document(text, prompt)
        
        try:
            return json.loads(response['result'])
        except json.JSONDecodeError:
            # JSON 파싱 실패 시 재시도 또는 에러 처리
            raise ValueError("Failed to parse JSON response from LLM")
    
    def summarize(self, text: str, max_length: int = 500) -> str:
        """문서 요약"""
        prompt = f"Summarize the following document in {max_length} characters or less in Korean:"
        response = self.analyze_document(text, prompt)
        return response['result']

# llm_processors/prompts.py
class PromptManager:
    """프롬프트 템플릿 관리"""
    
    def __init__(self):
        self.templates = {
            'summarize': """
다음 문서를 {max_length}자 이내로 요약해주세요.
주요 내용과 핵심 정보를 포함해야 합니다.

문서:
{text}
""",
            'extract_info': """
다음 문서에서 아래 정보를 추출해주세요:
{fields}

추출 형식은 JSON으로 해주세요.

문서:
{text}
""",
            'classify': """
다음 문서를 아래 카테고리 중 하나로 분류해주세요:
{categories}

문서:
{text}

카테고리:
""",
            'sentiment': """
다음 문서의 감정을 분석해주세요.
긍정적, 부정적, 중립적 중 하나를 선택하고 점수(0-1)를 매겨주세요.

문서:
{text}
"""
        }
    
    def get_prompt(self, template_name: str, **kwargs) -> str:
        """프롬프트 템플릿 렌더링"""
        template = self.templates.get(template_name)
        if not template:
            raise ValueError(f"Unknown template: {template_name}")
        
        return template.format(**kwargs)
    
    def add_template(self, name: str, template: str):
        """새 템플릿 추가"""
        self.templates[name] = template
```

### 4.5 데이터 처리 모듈 (data_processor)
```python
# data_processor/service.py
from typing import Dict, Any, List
import json
from shared.models import Document, OCRResult, LLMResult

class DataProcessorService:
    """데이터 처리 및 구조화 서비스"""
    
    def merge_results(self, document_id: str) -> Dict[str, Any]:
        """OCR과 LLM 결과 병합"""
        # DB에서 결과 조회
        ocr_results = self.get_ocr_results(document_id)
        llm_results = self.get_llm_results(document_id)
        
        # 결과 병합
        merged = {
            'document_id': document_id,
            'text': self.combine_ocr_text(ocr_results),
            'pages': len(ocr_results),
            'analysis': {}
        }
        
        # LLM 결과 추가
        for llm_result in llm_results:
            task_type = llm_result.task_type
            merged['analysis'][task_type] = llm_result.result
        
        return merged
    
    def combine_ocr_text(self, ocr_results: List[OCRResult]) -> str:
        """여러 페이지의 OCR 텍스트 결합"""
        # 페이지 번호순으로 정렬
        sorted_results = sorted(ocr_results, key=lambda x: x.page_number)
        
        # 텍스트 결합
        combined_text = '\n\n'.join([result.text_content for result in sorted_results])
        
        return combined_text
    
    def validate_data(self, data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """데이터 유효성 검증"""
        # JSON Schema 검증 또는 커스텀 검증 로직
        # 간단한 구현 예시
        for field, rules in schema.items():
            if rules.get('required') and field not in data:
                return False
            
            if field in data:
                value = data[field]
                if 'type' in rules:
                    expected_type = rules['type']
                    if expected_type == 'string' and not isinstance(value, str):
                        return False
                    elif expected_type == 'number' and not isinstance(value, (int, float)):
                        return False
                    elif expected_type == 'array' and not isinstance(value, list):
                        return False
        
        return True
    
    def normalize_korean_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """한국어 데이터 정규화"""
        normalized = data.copy()
        
        # 전화번호 정규화
        if 'phone' in normalized:
            normalized['phone'] = self.normalize_phone_number(normalized['phone'])
        
        # 주소 정규화
        if 'address' in normalized:
            normalized['address'] = self.normalize_address(normalized['address'])
        
        # 날짜 정규화
        if 'date' in normalized:
            normalized['date'] = self.normalize_date(normalized['date'])
        
        return normalized
    
    def normalize_phone_number(self, phone: str) -> str:
        """전화번호 정규화"""
        import re
        # 숫자만 추출
        numbers = re.sub(r'[^0-9]', '', phone)
        
        # 형식 적용
        if len(numbers) == 11:  # 휴대폰
            return f"{numbers[:3]}-{numbers[3:7]}-{numbers[7:]}"
        elif len(numbers) == 10:  # 서울
            return f"{numbers[:2]}-{numbers[2:6]}-{numbers[6:]}"
        else:
            return numbers
    
    def normalize_address(self, address: str) -> str:
        """주소 정규화"""
        # 도로명 주소 패턴 정규화
        # 구 주소를 도로명 주소로 변환 (외부 API 활용 가능)
        return address.strip()
    
    def normalize_date(self, date_str: str) -> str:
        """날짜 형식 정규화"""
        import re
        from datetime import datetime
        
        # 다양한 날짜 형식 처리
        patterns = [
            (r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일', '%Y-%m-%d'),
            (r'(\d{4})-(\d{1,2})-(\d{1,2})', '%Y-%m-%d'),
            (r'(\d{4})\.(\d{1,2})\.(\d{1,2})', '%Y-%m-%d'),
        ]
        
        for pattern, format_str in patterns:
            match = re.match(pattern, date_str)
            if match:
                year, month, day = match.groups()
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        return date_str
```

### 4.6 내보내기 모듈 (export)
```python
# export/service.py
import io
import json
from typing import List, Dict, Any
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

class ExportService:
    """데이터 내보내기 서비스"""
    
    def export_to_excel(self, data: List[Dict[str, Any]], template: str = None) -> bytes:
        """Excel 파일로 내보내기"""
        wb = Workbook()
        ws = wb.active
        ws.title = "IntelliDoc Export"
        
        # 헤더 스타일
        header_font = Font(bold=True, size=12)
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center")
        
        if template == "structured":
            # 구조화된 데이터 출력
            headers = ["문서 ID", "파일명", "상태", "추출 텍스트", "요약", "분류", "생성일"]
            ws.append(headers)
            
            # 헤더 스타일 적용
            for col in range(1, len(headers) + 1):
                cell = ws.cell(row=1, column=col)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = header_alignment
            
            # 데이터 추가
            for item in data:
                row = [
                    str(item.get('document_id', '')),
                    item.get('filename', ''),
                    item.get('status', ''),
                    item.get('text', '')[:100] + '...' if item.get('text') else '',
                    item.get('summary', ''),
                    item.get('category', ''),
                    str(item.get('created_at', ''))
                ]
                ws.append(row)
        else:
            # 기본 출력
            if data:
                headers = list(data[0].keys())
                ws.append(headers)
                
                for item in data:
                    ws.append([str(item.get(key, '')) for key in headers])
        
        # 열 너비 자동 조정
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
        
        # 바이트 스트림으로 저장
        excel_file = io.BytesIO()
        wb.save(excel_file)
        excel_file.seek(0)
        
        return excel_file.getvalue()
    
    def export_to_csv(self, data: List[Dict[str, Any]]) -> bytes:
        """CSV 파일로 내보내기"""
        if not data:
            return b""
        
        df = pd.DataFrame(data)
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')  # BOM 추가로 한글 깨짐 방지
        
        return csv_buffer.getvalue().encode('utf-8-sig')
    
    def export_to_pdf(self, data: List[Dict[str, Any]], title: str = "IntelliDoc Report") -> bytes:
        """PDF 보고서로 내보내기"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        
        # 제목
        title_style = styles['Title']
        elements.append(Paragraph(title, title_style))
        elements.append(Paragraph("<br/><br/>", styles['Normal']))
        
        # 요약 정보
        summary_data = [
            ['총 문서 수', str(len(data))],
            ['처리 완료', str(sum(1 for d in data if d.get('status') == 'COMPLETED'))],
            ['처리 중', str(sum(1 for d in data if d.get('status') == 'PROCESSING'))],
            ['오류', str(sum(1 for d in data if d.get('status') == 'ERROR'))]
        ]
        
        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(summary_table)
        elements.append(Paragraph("<br/><br/>", styles['Normal']))
        
        # 상세 데이터 테이블
        if data:
            detail_headers = ['문서 ID', '파일명', '상태', '생성일']
            detail_data = [detail_headers]
            
            for item in data[:20]:  # 최대 20개만 표시
                row = [
                    str(item.get('document_id', ''))[:8] + '...',
                    item.get('filename', '')[:30] + '...' if len(item.get('filename', '')) > 30 else item.get('filename', ''),
                    item.get('status', ''),
                    str(item.get('created_at', ''))[:10]
                ]
                detail_data.append(row)
            
            detail_table = Table(detail_data)
            detail_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(detail_table)
        
        # PDF 생성
        doc.build(elements)
        buffer.seek(0)
        
        return buffer.getvalue()
    
    def export_to_json(self, data: List[Dict[str, Any]]) -> bytes:
        """JSON 형식으로 내보내기"""
        return json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')

# export/templates.py
class TemplateManager:
    """내보내기 템플릿 관리"""
    
    def __init__(self):
        self.templates = {
            'invoice': {
                'name': '청구서',
                'fields': ['invoice_number', 'date', 'vendor', 'amount', 'items'],
                'format': 'structured'
            },
            'contract': {
                'name': '계약서',
                'fields': ['contract_number', 'parties', 'date', 'terms', 'amount'],
                'format': 'structured'
            },
            'receipt': {
                'name': '영수증',
                'fields': ['receipt_number', 'date', 'vendor', 'amount', 'items'],
                'format': 'structured'
            }
        }
    
    def get_template(self, template_name: str) -> Dict[str, Any]:
        """템플릿 가져오기"""
        return self.templates.get(template_name, {})
    
    def apply_template(self, data: Dict[str, Any], template_name: str) -> Dict[str, Any]:
        """템플릿 적용"""
        template = self.get_template(template_name)
        if not template:
            return data
        
        result = {}
        for field in template['fields']:
            result[field] = data.get(field, '')
        
        return result
```

## 5. 프론트엔드 설계

### 5.1 컴포넌트 구조
```typescript
// src/types/index.ts
export interface User {
  id: string;
  username: string;
  email: string;
  role: 'admin' | 'user' | 'viewer';
  isActive: boolean;
  createdAt: Date;
}

export interface Document {
  id: string;
  originalFilename: string;
  fileSize: number;
  mimeType: string;
  status: 'UPLOADED' | 'PROCESSING' | 'COMPLETED' | 'ERROR';
  pageCount?: number;
  createdAt: Date;
  updatedAt?: Date;
}

export interface OCRResult {
  pageNumber: number;
  text: string;
  confidence: number;
}

export interface LLMResult {
  taskType: string;
  result: any;
  processingTime: number;
}

// src/api/client.ts
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 요청 인터셉터 - 토큰 추가
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// 응답 인터셉터 - 토큰 갱신
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        const response = await apiClient.post('/auth/refresh', {
          refresh_token: refreshToken,
        });
        
        const { access_token } = response.data;
        localStorage.setItem('access_token', access_token);
        
        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        // 리프레시 실패 - 로그아웃 처리
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);

// src/store/slices/authSlice.ts
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { apiClient } from '../../api/client';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;
}

const initialState: AuthState = {
  user: null,
  isAuthenticated: false,
  loading: false,
  error: null,
};

export const login = createAsyncThunk(
  'auth/login',
  async (credentials: { username: string; password: string }) => {
    const response = await apiClient.post('/auth/login', credentials);
    const { access_token, refresh_token } = response.data;
    
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);
    
    // 사용자 정보 가져오기
    const userResponse = await apiClient.get('/auth/me');
    return userResponse.data;
  }
);

export const logout = createAsyncThunk('auth/logout', async () => {
  await apiClient.post('/auth/logout');
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
});

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(login.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(login.fulfilled, (state, action) => {
        state.loading = false;
        state.isAuthenticated = true;
        state.user = action.payload;
      })
      .addCase(login.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Login failed';
      })
      .addCase(logout.fulfilled, (state) => {
        state.user = null;
        state.isAuthenticated = false;
      });
  },
});

export const { clearError } = authSlice.actions;
export default authSlice.reducer;

// src/components/DocumentUpload/DocumentUpload.tsx
import React, { useState, useCallback } from 'react';
import { Upload, message } from 'antd';
import { InboxOutlined } from '@ant-design/icons';
import type { UploadProps } from 'antd';
import { apiClient } from '../../api/client';

const { Dragger } = Upload;

export const DocumentUpload: React.FC = () => {
  const [uploading, setUploading] = useState(false);

  const uploadProps: UploadProps = {
    name: 'file',
    multiple: true,
    maxCount: 10,
    beforeUpload: (file) => {
      const isValidType = [
        'application/pdf',
        'image/jpeg',
        'image/png',
        'image/tiff',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      ].includes(file.type);

      if (!isValidType) {
        message.error(`${file.name} is not a valid file type`);
        return false;
      }

      const isLt100M = file.size / 1024 / 1024 < 100;
      if (!isLt100M) {
        message.error('File must be smaller than 100MB!');
        return false;
      }

      return true;
    },
    customRequest: async ({ file, onSuccess, onError, onProgress }) => {
      const formData = new FormData();
      formData.append('file', file as File);

      try {
        setUploading(true);
        const response = await apiClient.post('/documents/upload', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          onUploadProgress: (progressEvent) => {
            const percent = (progressEvent.loaded / progressEvent.total!) * 100;
            onProgress?.({ percent });
          },
        });

        onSuccess?.(response.data);
        message.success(`${(file as File).name} uploaded successfully`);
      } catch (error) {
        onError?.(error as Error);
        message.error(`${(file as File).name} upload failed`);
      } finally {
        setUploading(false);
      }
    },
  };

  return (
    <div style={{ padding: '24px' }}>
      <h2>문서 업로드</h2>
      <Dragger {...uploadProps}>
        <p className="ant-upload-drag-icon">
          <InboxOutlined />
        </p>
        <p className="ant-upload-text">
          클릭하거나 파일을 이곳으로 드래그하세요
        </p>
        <p className="ant-upload-hint">
          PDF, 이미지(JPG, PNG, TIFF), Word 문서를 지원합니다.
          최대 10개 파일, 각 100MB까지 업로드 가능합니다.
        </p>
      </Dragger>
    </div>
  );
};
```

## 6. 테스트 설계

### 6.1 단위 테스트
```python
# tests/test_auth_service.py
import pytest
from auth.service import AuthService
from shared.models import User

class TestAuthService:
    @pytest.fixture
    def auth_service(self):
        return AuthService()
    
    def test_password_hashing(self, auth_service):
        """비밀번호 해싱 테스트"""
        password = "TestPassword123!"
        hashed = auth_service.get_password_hash(password)
        
        assert hashed != password
        assert auth_service.verify_password(password, hashed)
        assert not auth_service.verify_password("WrongPassword", hashed)
    
    def test_token_creation(self, auth_service):
        """JWT 토큰 생성 테스트"""
        user_data = {"sub": "user123", "role": "user"}
        token = auth_service.create_access_token(user_data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # 토큰 검증
        decoded = auth_service.verify_token(token)
        assert decoded["sub"] == "user123"
        assert decoded["role"] == "user"

# tests/test_ocr_engine.py
import pytest
from ocr_engines.tesseract import TesseractEngine
import numpy as np

class TestTesseractEngine:
    @pytest.fixture
    def engine(self):
        config = {"language": "kor+eng", "confidence_threshold": 0.6}
        return TesseractEngine(config)
    
    def test_image_preprocessing(self, engine):
        """이미지 전처리 테스트"""
        # 테스트 이미지 생성
        test_image_path = "tests/fixtures/test_image.jpg"
        processed = engine.preprocess_image(test_image_path)
        
        assert isinstance(processed, np.ndarray)
        assert len(processed.shape) == 2  # 그레이스케일
        assert processed.dtype == np.uint8
    
    @pytest.mark.integration
    def test_text_extraction(self, engine):
        """텍스트 추출 통합 테스트"""
        test_image_path = "tests/fixtures/korean_text.jpg"
        result = engine.extract_text(test_image_path)
        
        assert "text" in result
        assert "confidence" in result
        assert 0 <= result["confidence"] <= 1
        assert result["language"] == "kor+eng"
```

### 6.2 통합 테스트
```python
# tests/test_api_integration.py
import pytest
from fastapi.testclient import TestClient
from web_api.main import app

class TestDocumentAPI:
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self, client):
        """인증 헤더 생성"""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "testpass123"}
        )
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_document_upload_workflow(self, client, auth_headers):
        """문서 업로드 전체 워크플로우 테스트"""
        # 1. 문서 업로드
        with open("tests/fixtures/test.pdf", "rb") as f:
            response = client.post(
                "/api/v1/documents/upload",
                files={"file": ("test.pdf", f, "application/pdf")},
                headers=auth_headers
            )
        
        assert response.status_code == 201
        document_id = response.json()["document_id"]
        
        # 2. OCR 처리 시작
        response = client.post(
            f"/api/v1/documents/{document_id}/ocr",
            json={"engine": "tesseract"},
            headers=auth_headers
        )
        
        assert response.status_code == 202
        
        # 3. 처리 상태 확인
        response = client.get(
            f"/api/v1/documents/{document_id}/ocr/status",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert response.json()["status"] in ["PENDING", "PROCESSING", "COMPLETED"]
```

### 6.3 성능 테스트
```python
# tests/test_performance.py
import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
import requests

class TestPerformance:
    @pytest.mark.performance
    def test_concurrent_uploads(self):
        """동시 업로드 성능 테스트"""
        base_url = "http://localhost:8000/api/v1"
        concurrent_users = 10
        
        def upload_file(user_id):
            start_time = time.time()
            
            # 로그인
            response = requests.post(
                f"{base_url}/auth/login",
                json={"username": f"user{user_id}", "password": "password"}
            )
            token = response.json()["access_token"]
            
            # 파일 업로드
            with open("tests/fixtures/test.pdf", "rb") as f:
                response = requests.post(
                    f"{base_url}/documents/upload",
                    files={"file": f},
                    headers={"Authorization": f"Bearer {token}"}
                )
            
            elapsed = time.time() - start_time
            return elapsed, response.status_code
        
        # 동시 실행
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(upload_file, i) for i in range(concurrent_users)]
            results = [f.result() for f in futures]
        
        # 결과 분석
        times = [r[0] for r in results]
        statuses = [r[1] for r in results]
        
        assert all(status == 201 for status in statuses)
        assert max(times) < 10  # 최대 10초 이내
        print(f"Average upload time: {sum(times) / len(times):.2f}s")
```

## 7. 배포 설계

### 7.1 Docker 구성
```dockerfile
# backend/Dockerfile
FROM python:3.9-slim

WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    tesseract-ocr \
    tesseract-ocr-kor \
    tesseract-ocr-eng \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 환경 변수
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 포트 노출
EXPOSE 8000

# 시작 명령
CMD ["uvicorn", "web_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 7.2 Docker Compose 설정
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:13-alpine
    environment:
      POSTGRES_USER: intellidoc
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: intellidoc
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U intellidoc"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:6-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build: ./backend
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      - DATABASE_URL=postgresql://intellidoc:${DB_PASSWORD}@postgres:5432/intellidoc
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
      - document_storage:/app/storage

  worker:
    build: ./backend
    command: celery -A celery_app worker --loglevel=info
    depends_on:
      - backend
    environment:
      - DATABASE_URL=postgresql://intellidoc:${DB_PASSWORD}@postgres:5432/intellidoc
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./backend:/app
      - document_storage:/app/storage

  frontend:
    build: ./frontend
    depends_on:
      - backend
    ports:
      - "3000:80"
    environment:
      - REACT_APP_API_URL=http://backend:8000/api/v1

volumes:
  postgres_data:
  redis_data:
  document_storage:
```

### 7.3 Kubernetes 배포 (선택적)
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: intellidoc-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: intellidoc-backend
  template:
    metadata:
      labels:
        app: intellidoc-backend
    spec:
      containers:
      - name: backend
        image: intellidoc-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: intellidoc-secrets
              key: database-url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: intellidoc-backend
spec:
  selector:
    app: intellidoc-backend
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP
```

## 8. 모니터링 및 로깅 설계

### 8.1 Prometheus 메트릭
```python
# shared/metrics.py
from prometheus_client import Counter, Histogram, Gauge
import time
from functools import wraps

# 메트릭 정의
document_upload_counter = Counter(
    'intellidoc_document_uploads_total',
    'Total number of document uploads',
    ['status']
)

ocr_processing_time = Histogram(
    'intellidoc_ocr_processing_seconds',
    'Time spent processing OCR',
    ['engine']
)

active_processing_jobs = Gauge(
    'intellidoc_active_processing_jobs',
    'Number of active processing jobs',
    ['job_type']
)

def track_processing_time(job_type):
    """처리 시간 추적 데코레이터"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            active_processing_jobs.labels(job_type=job_type).inc()
            
            try:
                result = func(*args, **kwargs)
                status = 'success'
            except Exception as e:
                status = 'error'
                raise
            finally:
                duration = time.time() - start_time
                active_processing_jobs.labels(job_type=job_type).dec()
                
                if job_type == 'ocr':
                    engine = kwargs.get('engine', 'unknown')
                    ocr_processing_time.labels(engine=engine).observe(duration)
            
            return result
        return wrapper
    return decorator
```

### 8.2 구조화된 로깅
```python
# shared/logger.py
import logging
import json
from datetime import datetime
from contextvars import ContextVar

# 요청 ID 컨텍스트 변수
request_id_var: ContextVar[str] = ContextVar('request_id', default='')

class JSONFormatter(logging.Formatter):
    """JSON 형식 로그 포맷터"""
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'request_id': request_id_var.get(),
        }
        
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # 추가 컨텍스트 정보
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'document_id'):
            log_data['document_id'] = record.document_id
        
        return json.dumps(log_data)

def setup_logger(name: str) -> logging.Logger:
    """로거 설정"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)
    
    return logger

# 사용 예시
logger = setup_logger('intellidoc')

def log_document_processing(document_id: str, user_id: str):
    """문서 처리 로깅 예시"""
    logger.info(
        "Document processing started",
        extra={
            'user_id': user_id,
            'document_id': document_id
        }
    )
```

## 9. 보안 설계

### 9.1 보안 미들웨어
```python
# web_api/middleware.py
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import time
import hashlib
from collections import defaultdict

class SecurityMiddleware(BaseHTTPMiddleware):
    """보안 관련 미들웨어"""
    
    def __init__(self, app, rate_limit: int = 100):
        super().__init__(app)
        self.rate_limit = rate_limit
        self.request_counts = defaultdict(lambda: defaultdict(int))
    
    async def dispatch(self, request: Request, call_next):
        # 1. Rate Limiting
        client_ip = request.client.host
        current_minute = int(time.time() / 60)
        
        self.request_counts[client_ip][current_minute] += 1
        
        if self.request_counts[client_ip][current_minute] > self.rate_limit:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        # 2. Security Headers
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response

class InputValidationMiddleware(BaseHTTPMiddleware):
    """입력 검증 미들웨어"""
    
    async def dispatch(self, request: Request, call_next):
        # SQL 인젝션 패턴 검사
        if request.method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
            body_str = body.decode('utf-8')
            
            # 간단한 SQL 인젝션 패턴 검사
            sql_patterns = ["';", '";', '--', '/*', '*/', 'xp_', 'sp_']
            for pattern in sql_patterns:
                if pattern in body_str.lower():
                    raise HTTPException(
                        status_code=400,
                        detail="Potentially malicious input detected"
                    )
        
        response = await call_next(request)
        return response
```

### 9.2 파일 업로드 보안
```python
# file_manager/security.py
import magic
import hashlib
from typing import BinaryIO

class FileSecurityChecker:
    """파일 보안 검사"""
    
    def __init__(self):
        self.allowed_mime_types = {
            'application/pdf',
            'image/jpeg',
            'image/png',
            'image/tiff',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        }
        
        # 위험한 파일 시그니처
        self.dangerous_signatures = {
            b'MZ': 'Windows executable',
            b'\x7fELF': 'Linux executable',
            b'#!/': 'Script file',
        }
    
    def check_file_safety(self, file_path: str) -> bool:
        """파일 안전성 검사"""
        # 1. MIME 타입 검사
        mime = magic.Magic(mime=True)
        file_mime = mime.from_file(file_path)
        
        if file_mime not in self.allowed_mime_types:
            raise ValueError(f"File type {file_mime} is not allowed")
        
        # 2. 파일 시그니처 검사
        with open(file_path, 'rb') as f:
            header = f.read(16)
            
            for signature, file_type in self.dangerous_signatures.items():
                if header.startswith(signature):
                    raise ValueError(f"Dangerous file type detected: {file_type}")
        
        # 3. 파일 해시 계산 (중복 검사용)
        file_hash = self.calculate_file_hash(file_path)
        
        return True
    
    def calculate_file_hash(self, file_path: str) -> str:
        """파일 해시 계산"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def sanitize_filename(self, filename: str) -> str:
        """파일명 정제"""
        import re
        # 위험한 문자 제거
        sanitized = re.sub(r'[^\w\s.-]', '', filename)
        # 경로 순회 방지
        sanitized = sanitized.replace('..', '')
        # 최대 길이 제한
        return sanitized[:255]
```

## 10. AI 코더를 위한 구현 가이드

### 10.1 개발 순서
1. **환경 설정**
   - Python 가상환경 생성
   - 의존성 설치
   - 환경변수 설정

2. **데이터베이스 구축**
   - PostgreSQL 설치/설정
   - 스키마 생성
   - 초기 데이터 입력

3. **백엔드 구현 순서**
   - 공통 모듈 (models, schemas, config)
   - 인증 모듈
   - 파일 관리 모듈
   - OCR 엔진 (Tesseract부터)
   - LLM 프로세서 (OpenAI부터)
   - API 라우터
   - Celery 작업 설정

4. **프론트엔드 구현 순서**
   - 프로젝트 설정 (React + TypeScript)
   - 라우팅 설정
   - 인증 컴포넌트
   - 문서 업로드 컴포넌트
   - 문서 목록/상세 컴포넌트
   - 처리 상태 표시 컴포넌트

5. **테스트 및 배포**
   - 단위 테스트 작���
   - 통합 테스트
   - Docker 이미지 빌드
   - 배포 및 모니터링

### 10.2 주의사항
- 모든 함수에 타입 힌트와 docstring 필수
- 에러 처리 철저히 구현
- 로깅을 통한 디버깅 정보 제공
- 성능 병목 지점 프로파일링
- 보안 체크리스트 준수

---

**작성일**: 2025년 1월
**버전**: 1.0
**문서 상태**: AI 코더 개발용 최종본