# 📋 온라인 평가 시스템 종합 수정 계획서

## 🎯 프로젝트 현황 요약

### ✅ 완료된 작업
- Docker Compose 설정 수정 (포트 매핑, 빌드 타겟)
- 프로젝트 구조 및 아키텍처 분석
- 보안 취약점 식별 및 개선 계획 수립
- 지식 그래프 구축 (18개 엔티티, 24개 관계)

### ⚠️ 핵심 문제점
1. **백엔드 인증 시스템**: MongoDB `_id` vs `id` 필드 불일치
2. **패스워드 보안**: bcrypt 해시 검증 실패
3. **미완성 기능**: 평가 시스템, 내보내기, 실시간 알림
4. **보안 미흡**: JWT, CSRF, XSS 방지 미비
5. **프론트엔드**: 컴포넌트 구조 개선 필요

---

## 🔧 모듈별 상세 수정 계획

### 1. 백엔드 인증 시스템 수정 (우선순위: 🔴 최고)

#### 1.1 User 모델 필드 일관성 수정
**파일**: `backend/models.py`
**문제**: MongoDB `_id` vs 코드 내 `id` 불일치

```python
# 현재 문제 코드
class User(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")  # 불일치 문제

# 수정 방안
class User(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        
    @classmethod
    def from_mongo(cls, data: dict):
        """MongoDB 문서를 User 객체로 변환"""
        if data.get("_id"):
            data["id"] = str(data["_id"])
        return cls(**data)
```

#### 1.2 인증 로직 수정
**파일**: `backend/server.py`
**수정 범위**: 로그인, 회원가입, 사용자 조회 함수

```python
# login_user 함수 수정
@app.post("/api/login")
async def login_user(login_data: LoginData):
    try:
        # MongoDB 쿼리 시 _id 사용
        user_data = await db.users.find_one({"username": login_data.username})
        if not user_data:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # User 객체 생성 시 변환
        user = User.from_mongo(user_data)
        
        # 패스워드 검증
        if not verify_password(login_data.password, user_data.get("password")):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # JWT 토큰 생성 시 user.id 사용
        token = create_access_token(data={"sub": user.id, "username": user.username})
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "role": user.role
            }
        }
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")
```

#### 1.3 패스워드 해시 시스템 수정
**파일**: `backend/security.py`

```python
import bcrypt
from passlib.context import CryptContext

# 새로운 패스워드 컨텍스트
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """패스워드 해시 생성"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """패스워드 검증"""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        # 기존 bcrypt 해시와의 호환성
        try:
            return bcrypt.checkpw(
                plain_password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except Exception:
            return False
```

---

### 2. 보안 강화 (우선순위: 🔴 최고)

#### 2.1 JWT 토큰 보안 강화
**파일**: `backend/auth.py` (신규 생성)

```python
from datetime import datetime, timedelta
from jose import JWTError, jwt
import secrets

# 보안 강화된 JWT 설정
SECRET_KEY = secrets.token_urlsafe(32)  # 환경변수로 관리
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

class TokenManager:
    def __init__(self):
        self.blacklisted_tokens = set()
    
    def create_access_token(self, data: dict, expires_delta: timedelta = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "iat": datetime.utcnow()})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str):
        if token in self.blacklisted_tokens:
            raise JWTError("Token has been revoked")
        
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            raise JWTError("Could not validate credentials")
```

#### 2.2 CSRF 보호
**파일**: `backend/middleware.py` (신규 생성)

```python
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer
import secrets

class CSRFProtection:
    def __init__(self):
        self.csrf_tokens = {}
    
    def generate_csrf_token(self, session_id: str) -> str:
        token = secrets.token_urlsafe(32)
        self.csrf_tokens[session_id] = token
        return token
    
    def verify_csrf_token(self, session_id: str, token: str) -> bool:
        return self.csrf_tokens.get(session_id) == token

@app.middleware("http")
async def csrf_middleware(request: Request, call_next):
    if request.method in ["POST", "PUT", "DELETE"]:
        csrf_token = request.headers.get("X-CSRF-Token")
        if not csrf_token:
            raise HTTPException(status_code=403, detail="CSRF token missing")
        # CSRF 토큰 검증 로직
    
    response = await call_next(request)
    return response
```

#### 2.3 입력 검증 및 데이터 무결성
**파일**: `backend/validators.py` (신규 생성)

```python
from pydantic import BaseModel, validator, Field
import re

class SecureUserInput(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=128)
    email: str = Field(..., regex=r'^[^@]+@[^@]+\.[^@]+$')
    
    @validator('username')
    def validate_username(cls, v):
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username can only contain letters, numbers, and underscores')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v
```

---

### 3. 미완성 기능 구현 (우선순위: 🟡 중간)

#### 3.1 평가 시스템 구현
**파일**: `backend/evaluation.py` (신규 생성)

```python
from typing import List, Dict, Any
from datetime import datetime
from enum import Enum

class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    ESSAY = "essay"

class EvaluationSystem:
    def __init__(self, db):
        self.db = db
    
    async def create_evaluation(self, evaluation_data: dict) -> str:
        """평가 생성"""
        evaluation = {
            "title": evaluation_data["title"],
            "description": evaluation_data.get("description", ""),
            "questions": evaluation_data["questions"],
            "time_limit": evaluation_data.get("time_limit", 60),
            "created_at": datetime.utcnow(),
            "created_by": evaluation_data["created_by"],
            "status": "draft"
        }
        
        result = await self.db.evaluations.insert_one(evaluation)
        return str(result.inserted_id)
    
    async def submit_answer(self, evaluation_id: str, user_id: str, answers: Dict[str, Any]):
        """답안 제출"""
        submission = {
            "evaluation_id": evaluation_id,
            "user_id": user_id,
            "answers": answers,
            "submitted_at": datetime.utcnow(),
            "score": await self.calculate_score(evaluation_id, answers)
        }
        
        await self.db.submissions.insert_one(submission)
        return submission["score"]
    
    async def calculate_score(self, evaluation_id: str, answers: Dict[str, Any]) -> float:
        """점수 계산"""
        evaluation = await self.db.evaluations.find_one({"_id": evaluation_id})
        total_points = 0
        earned_points = 0
        
        for question in evaluation["questions"]:
            question_id = str(question["_id"])
            total_points += question.get("points", 1)
            
            if question_id in answers:
                if question["type"] == QuestionType.MULTIPLE_CHOICE:
                    if answers[question_id] == question["correct_answer"]:
                        earned_points += question.get("points", 1)
        
        return (earned_points / total_points) * 100 if total_points > 0 else 0
```

#### 3.2 실시간 알림 시스템
**파일**: `backend/notifications.py` (신규 생성)

```python
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
import json

class NotificationManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
    
    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                await connection.send_text(json.dumps(message))
    
    async def broadcast(self, message: dict):
        for user_connections in self.active_connections.values():
            for connection in user_connections:
                await connection.send_text(json.dumps(message))

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await notification_manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            # 메시지 처리 로직
    except WebSocketDisconnect:
        notification_manager.disconnect(websocket, user_id)
```

#### 3.3 데이터 내보내기 기능
**파일**: `backend/export.py` (신규 생성)

```python
import pandas as pd
from io import StringIO, BytesIO
import xlsxwriter
from typing import List, Dict

class ExportService:
    def __init__(self, db):
        self.db = db
    
    async def export_evaluation_results(self, evaluation_id: str, format: str = "xlsx"):
        """평가 결과 내보내기"""
        # 평가 데이터 조회
        evaluation = await self.db.evaluations.find_one({"_id": evaluation_id})
        submissions = await self.db.submissions.find({"evaluation_id": evaluation_id}).to_list(None)
        
        # 데이터 가공
        export_data = []
        for submission in submissions:
            user = await self.db.users.find_one({"_id": submission["user_id"]})
            export_data.append({
                "사용자명": user.get("username", ""),
                "이메일": user.get("email", ""),
                "점수": submission.get("score", 0),
                "제출시간": submission.get("submitted_at", ""),
                "소요시간": self.calculate_duration(submission)
            })
        
        if format == "xlsx":
            return await self.create_excel_file(export_data, evaluation["title"])
        elif format == "csv":
            return await self.create_csv_file(export_data)
        else:
            raise ValueError("Unsupported format")
    
    async def create_excel_file(self, data: List[Dict], title: str) -> bytes:
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet(title[:31])  # Excel 시트명 제한
        
        # 헤더 작성
        headers = list(data[0].keys()) if data else []
        for col, header in enumerate(headers):
            worksheet.write(0, col, header)
        
        # 데이터 작성
        for row, record in enumerate(data, 1):
            for col, header in enumerate(headers):
                worksheet.write(row, col, record.get(header, ""))
        
        workbook.close()
        output.seek(0)
        return output.read()
```

---

### 4. 프론트엔드 개선 (우선순위: 🟡 중간)

#### 4.1 컴포넌트 구조 개선
**파일**: `frontend/src/components/` (구조 개선)

```typescript
// components/common/Layout.tsx
import React from 'react';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { Footer } from './Footer';

interface LayoutProps {
  children: React.ReactNode;
  user?: User;
}

export const Layout: React.FC<LayoutProps> = ({ children, user }) => {
  return (
    <div className="min-h-screen bg-gray-50">
      <Header user={user} />
      <div className="flex">
        <Sidebar user={user} />
        <main className="flex-1 p-6">
          {children}
        </main>
      </div>
      <Footer />
    </div>
  );
};

// components/auth/AuthGuard.tsx
import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';

interface AuthGuardProps {
  children: React.ReactNode;
  requiredRole?: string;
}

export const AuthGuard: React.FC<AuthGuardProps> = ({ children, requiredRole }) => {
  const { user, loading } = useAuth();
  
  if (loading) return <div>Loading...</div>;
  
  if (!user) return <Navigate to="/login" replace />;
  
  if (requiredRole && user.role !== requiredRole) {
    return <Navigate to="/unauthorized" replace />;
  }
  
  return <>{children}</>;
};
```

#### 4.2 상태 관리 개선
**파일**: `frontend/src/store/` (새로운 상태 관리)

```typescript
// store/authSlice.ts
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { authAPI } from '../services/api';

interface AuthState {
  user: User | null;
  token: string | null;
  loading: boolean;
  error: string | null;
}

export const loginAsync = createAsyncThunk(
  'auth/login',
  async (credentials: LoginCredentials, { rejectWithValue }) => {
    try {
      const response = await authAPI.login(credentials);
      localStorage.setItem('token', response.access_token);
      return response;
    } catch (error) {
      return rejectWithValue(error.response.data);
    }
  }
);

const authSlice = createSlice({
  name: 'auth',
  initialState: {
    user: null,
    token: localStorage.getItem('token'),
    loading: false,
    error: null
  } as AuthState,
  reducers: {
    logout: (state) => {
      state.user = null;
      state.token = null;
      localStorage.removeItem('token');
    },
    clearError: (state) => {
      state.error = null;
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(loginAsync.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(loginAsync.fulfilled, (state, action) => {
        state.loading = false;
        state.user = action.payload.user;
        state.token = action.payload.access_token;
      })
      .addCase(loginAsync.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });
  }
});

export const { logout, clearError } = authSlice.actions;
export default authSlice.reducer;
```

#### 4.3 API 클라이언트 개선
**파일**: `frontend/src/services/api.ts`

```typescript
import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';

class APIClient {
  private client: AxiosInstance;
  
  constructor() {
    this.client = axios.create({
      baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
      timeout: 10000,
    });
    
    this.setupInterceptors();
  }
  
  private setupInterceptors() {
    // 요청 인터셉터
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        
        // CSRF 토큰 추가
        const csrfToken = this.getCSRFToken();
        if (csrfToken) {
          config.headers['X-CSRF-Token'] = csrfToken;
        }
        
        return config;
      },
      (error) => Promise.reject(error)
    );
    
    // 응답 인터셉터
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }
  
  private getCSRFToken(): string | null {
    return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || null;
  }
  
  // API 메소드들
  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.get(url, config);
    return response.data;
  }
  
  async post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.post(url, data, config);
    return response.data;
  }
}

export const apiClient = new APIClient();

// 인증 API
export const authAPI = {
  login: (credentials: LoginCredentials) => 
    apiClient.post<LoginResponse>('/api/login', credentials),
  
  register: (userData: RegisterData) => 
    apiClient.post<User>('/api/register', userData),
  
  logout: () => 
    apiClient.post('/api/logout'),
  
  getCurrentUser: () => 
    apiClient.get<User>('/api/me')
};
```

---

### 5. 데이터베이스 최적화 (우선순위: 🟢 낮음)

#### 5.1 인덱스 생성
**파일**: `scripts/create_indexes.py`

```python
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def create_indexes():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.evaluation_system
    
    # 사용자 컬렉션 인덱스
    await db.users.create_index([("username", 1)], unique=True)
    await db.users.create_index([("email", 1)], unique=True)
    
    # 평가 컬렉션 인덱스
    await db.evaluations.create_index([("created_by", 1)])
    await db.evaluations.create_index([("created_at", -1)])
    await db.evaluations.create_index([("status", 1)])
    
    # 제출 컬렉션 인덱스
    await db.submissions.create_index([("evaluation_id", 1, "user_id", 1)], unique=True)
    await db.submissions.create_index([("submitted_at", -1)])
    
    print("Indexes created successfully")

if __name__ == "__main__":
    asyncio.run(create_indexes())
```

---

## 📅 구현 일정

### Phase 1: 핵심 오류 수정 (1-2일)
1. User 모델 id 필드 일관성 수정
2. 패스워드 해시 시스템 수정
3. 로그인/인증 로직 수정
4. 기본 보안 강화 (JWT, CSRF)

### Phase 2: 기능 완성 (3-4일)
1. 평가 시스템 구현
2. 데이터 내보내기 기능
3. 실시간 알림 시스템
4. 프론트엔드 컴포넌트 개선

### Phase 3: 최적화 및 배포 (1-2일)
1. 데이터베이스 인덱스 최적화
2. 성능 튜닝
3. 통합 테스트
4. 배포 자동화

---

## 🧪 테스트 계획

### 단위 테스트
- 인증 시스템 테스트
- 평가 시스템 테스트
- 데이터 검증 테스트

### 통합 테스트
- API 엔드포인트 테스트
- 데이터베이스 연동 테스트
- 실시간 알림 테스트

### E2E 테스트
- 사용자 워크플로우 테스트
- 보안 테스트
- 성능 테스트

---

## 📈 성공 지표

1. **기능성**: 모든 핵심 기능 정상 동작
2. **보안**: OWASP Top 10 준수
3. **성능**: 응답시간 < 2초
4. **안정성**: 99% 가용성
5. **사용성**: 직관적인 사용자 인터페이스

이 계획서를 바탕으로 단계별로 수정 작업을 진행하시겠습니까?
