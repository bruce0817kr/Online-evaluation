#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
간단한 온라인 평가 시스템 백엔드 서버
최소한의 기능으로 동작하는 버전
"""

import os
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
from typing import Optional
import hashlib
import jwt

# 설정
SECRET_KEY = "your-super-secret-jwt-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# FastAPI 앱 생성
app = FastAPI(
    title="온라인 평가 시스템",
    description="간단한 온라인 평가 시스템 API",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# OAuth2 설정
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

# 데이터베이스 연결
try:
    mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017/online_evaluation")
    client = AsyncIOMotorClient(mongo_url)
    db = client.get_default_database()
    print(f"✅ MongoDB 연결: {mongo_url}")
except Exception as e:
    print(f"❌ MongoDB 연결 실패: {e}")
    db = None

# 모델 정의
class User(BaseModel):
    username: str
    email: Optional[str] = None
    role: str = "evaluator"

class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserLogin(BaseModel):
    username: str
    password: str

# 유틸리티 함수
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호 검증"""
    return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password

def get_password_hash(password: str) -> str:
    """비밀번호 해시"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """JWT 토큰 생성"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_user(username: str) -> Optional[UserInDB]:
    """사용자 조회"""
    if not db:
        # 데모 사용자 (데이터베이스 없을 때)
        demo_users = {
            "admin": UserInDB(
                username="admin", 
                email="admin@example.com", 
                role="admin",
                hashed_password=get_password_hash("admin123")
            ),
            "secretary": UserInDB(
                username="secretary", 
                email="secretary@example.com", 
                role="secretary",
                hashed_password=get_password_hash("secretary123")
            ),
            "evaluator": UserInDB(
                username="evaluator", 
                email="evaluator@example.com", 
                role="evaluator",
                hashed_password=get_password_hash("evaluator123")
            )
        }
        return demo_users.get(username)
    
    try:
        user_data = await db.users.find_one({"username": username})
        if user_data:
            return UserInDB(**user_data)
    except Exception as e:
        print(f"사용자 조회 오류: {e}")
    return None

async def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """사용자 인증"""
    user = await get_user(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """현재 사용자 조회"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    user = await get_user(username=username)
    if user is None:
        raise credentials_exception
    return User(username=user.username, email=user.email, role=user.role)

# API 엔드포인트
@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "온라인 평가 시스템 API", 
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "connected" if db else "disconnected"
    }

@app.post("/api/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """로그인"""
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/auth/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """현재 사용자 정보"""
    return current_user

@app.get("/api/users")
async def get_users(current_user: User = Depends(get_current_user)):
    """사용자 목록 (관리자 전용)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다")
    
    # 데모 데이터
    return [
        {"username": "admin", "email": "admin@example.com", "role": "admin"},
        {"username": "secretary", "email": "secretary@example.com", "role": "secretary"},
        {"username": "evaluator", "email": "evaluator@example.com", "role": "evaluator"}
    ]

@app.get("/api/templates")
async def get_templates(current_user: User = Depends(get_current_user)):
    """템플릿 목록"""
    # 데모 데이터
    return [
        {
            "id": "1",
            "name": "기본 평가 템플릿",
            "description": "기본적인 평가 항목들",
            "created_at": "2025-06-24T00:00:00Z"
        }
    ]

@app.get("/api/evaluations")
async def get_evaluations(current_user: User = Depends(get_current_user)):
    """평가 목록"""
    # 데모 데이터
    return [
        {
            "id": "1",
            "title": "샘플 평가",
            "status": "completed",
            "created_at": "2025-06-24T00:00:00Z"
        }
    ]

if __name__ == "__main__":
    port = int(os.getenv("BACKEND_PORT", 8081))
    print(f"🚀 서버 시작: http://localhost:{port}")
    print(f"📖 API 문서: http://localhost:{port}/docs")
    print(f"🔑 로그인 정보: admin/admin123, secretary/secretary123, evaluator/evaluator123")
    
    uvicorn.run(
        "simple_server:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )