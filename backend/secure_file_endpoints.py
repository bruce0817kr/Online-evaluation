"""
보안 파일 서빙 API 엔드포인트
PDF 뷰어를 위한 보안 파일 접근 제어
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from typing import Optional, Any
import logging
from pydantic import BaseModel, Field
import os
import aiofiles
import mimetypes
import hashlib
import time
from datetime import datetime, timedelta
import io
import base64
import uuid # Added for log_file_access

from models import User
from security import get_current_user
from enhanced_permissions import Permission, check_permission, permission_checker

logger = logging.getLogger(__name__)

# Dependency to get the database connection
async def get_db():
    from server import db
    return db

# 보안 파일 라우터 생성
secure_file_router = APIRouter(prefix="/api/files", tags=["보안 파일 관리"])

# 요청 모델들
class SecurePDFViewRequest(BaseModel):
    """보안 PDF 조회 요청"""
    file_id: str = Field(..., description="파일 ID")

class FileAccessLog(BaseModel):
    """파일 접근 로그"""
    user_id: str
    file_path: str
    access_time: datetime
    ip_address: str
    user_agent: str
    action: str  # "view", "download", "denied"
    file_size: Optional[int] = None
    duration: Optional[int] = None  # 조회 시간 (초)

# 접근 로그 저장소 (실제로는 데이터베이스에 저장)
# access_logs = [] # Removed as logging directly to DB

# 파일 접근 토큰 캐시 (실제로는 Redis 등 사용)
access_tokens = {}

def generate_access_token(user_id: str, file_path: str) -> str:
    """임시 파일 접근 토큰 생성"""
    timestamp = str(int(time.time()))
    data = f"{user_id}:{file_path}:{timestamp}"
    token = hashlib.sha256(data.encode()).hexdigest()
    
    # 5분간 유효한 토큰
    access_tokens[token] = {
        "user_id": user_id,
        "file_path": file_path,
        "expires_at": datetime.utcnow() + timedelta(minutes=5)
    }
    
    return token

def validate_access_token(token: str) -> Optional[dict]:
    """접근 토큰 검증"""
    if token not in access_tokens:
        return None
    
    token_data = access_tokens[token]
    if datetime.utcnow() > token_data["expires_at"]:
        del access_tokens[token]
        return None
    
    return token_data



logger = logging.getLogger(__name__)

# 보안 파일 라우터 생성
secure_file_router = APIRouter(prefix="/api/files", tags=["보안 파일 관리"])

# 요청 모델들
class SecurePDFViewRequest(BaseModel):
    """보안 PDF 조회 요청"""
    file_id: str = Field(..., description="파일 ID")

class FileAccessLog(BaseModel):
    """파일 접근 로그"""
    user_id: str
    file_path: str
    access_time: datetime
    ip_address: str
    user_agent: str
    action: str  # "view", "download", "denied"
    file_size: Optional[int] = None
    duration: Optional[int] = None  # 조회 시간 (초)

# 접근 로그 저장소 (실제로는 데이터베이스에 저장)
# access_logs = [] # Removed as logging directly to DB

# 파일 접근 토큰 캐시 (실제로는 Redis 등 사용)
access_tokens = {}

def generate_access_token(user_id: str, file_path: str) -> str:
    """임시 파일 접근 토큰 생성"""
    timestamp = str(int(time.time()))
    data = f"{user_id}:{file_path}:{timestamp}"
    token = hashlib.sha256(data.encode()).hexdigest()
    
    # 5분간 유효한 토큰
    access_tokens[token] = {
        "user_id": user_id,
        "file_path": file_path,
        "expires_at": datetime.utcnow() + timedelta(minutes=5)
    }
    
    return token

def validate_access_token(token: str) -> Optional[dict]:
    """접근 토큰 검증"""
    if token not in access_tokens:
        return None
    
    token_data = access_tokens[token]
    if datetime.utcnow() > token_data["expires_at"]:
        del access_tokens[token]
        return None
    
    return token_data

async def log_file_access(db: Any, user_id: str, file_id: str, action: str, ip_address: str = None, user_agent: str = None, success: bool = True, error_message: str = None):
    """파일 접근 로그 기록"""
    try:
        access_log = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "file_id": file_id,
            "action": action,
            "access_time": datetime.utcnow(),
            "ip_address": ip_address or "unknown",
            "user_agent": user_agent or "unknown",
            "success": success,
            "error_message": error_message
        }
        
        # 데이터베이스에 영구 저장
        await db.file_access_logs.insert_one(access_log)
        
        # 보안 로그에도 기록
        log_message = f"파일 접근: 사용자={user_id}, 파일={file_id}, 작업={action}, 성공={success}"
        if error_message:
            log_message += f", 오류={error_message}"
        logger.info(log_message)
        
    except Exception as e:
        logger.error(f"파일 접근 로그 기록 실패: {e}")

async def check_file_access_permission(db: Any, current_user: User, file_id: str) -> bool:
    """파일 접근 권한 검사"""
    try:
        file_metadata = await db.file_metadata.find_one({"id": file_id})
        if not file_metadata:
            return False
        
        # 관리자와 간사는 모든 파일 접근 가능
        if current_user.role in ["admin", "secretary"]:
            return True
        
        # 평가위원은 자신이 담당하는 평가의 파일만 접근 가능
        if current_user.role == "evaluator":
            # 파일이 속한 회사의 평가를 담당하는지 확인
            evaluation = await db.evaluation_sheets.find_one({"company_id": file_metadata["company_id"],"evaluator_id": current_user.id})
            return evaluation is not None
        
        # 기본적으로 접근 거부
        return False
        
    except Exception as e:
        logger.error(f"파일 권한 검사 오류: {e}")
        return False

def add_security_headers(response, filename: str):
    """보안 헤더 추가"""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, private"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    response.headers["Content-Security-Policy"] = "default-src 'none'; script-src 'none'; object-src 'none';"
    
    # 파일 이름을 안전하게 인코딩
    import urllib.parse
    safe_filename = urllib.parse.quote(filename)
    response.headers["Content-Disposition"] = f"inline; filename*=UTF-8''{safe_filename}"

@secure_file_router.post("/secure-pdf-view/{file_id}", operation_id="secure_pdf_view_post")
async def secure_pdf_view(
    file_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Any = Depends(get_db)
):
    """보안 PDF 조회 (뷰어 전용)"""
    try:
        start_time = time.time()
        
        # 파일 메타데이터 조회
        file_metadata = await db.file_metadata.find_one({"id": file_id})
        if not file_metadata:
            await log_file_access(
                db, # Pass db here
                user_id=current_user.id,
                file_id=file_id,
                action="preview_denied",
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent"),
                success=False,
                error_message="접근 권한 없음"
            )
            raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")

        # 권한 확인
        has_access = await check_file_access_permission(
            current_user, 
            file_id
        )
        
        if not has_access:
            await log_file_access(
                db, # Pass db here
                user_id=current_user.id,
                file_id=file_id,
                action="preview_denied",
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent"),
                success=False,
                error_message="접근 권한 없음"
            )
            raise HTTPException(
                status_code=403, 
                detail="파일 접근 권한이 없습니다"
            )
        
        # 파일 경로 정리
        file_path_str = file_metadata["file_path"]
        if ".." in file_path_str or file_path_str.startswith("/"):
            await log_file_access(
                db, # Pass db here
                user_id=current_user.id,
                file_id=file_id,
                action="preview_blocked",
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent"),
                success=False,
                error_message="잘못된 파일 경로"
            )
            raise HTTPException(status_code=400, detail="잘못된 파일 경로입니다.")
        
        full_path = os.path.join("uploads", file_path_str)
        
        # 파일 존재 확인
        if not os.path.exists(full_path):
            logger.warning(f"파일을 찾을 수 없음: {full_path}")
            await log_file_access(
                user_id=current_user.id,
                file_id=file_id,
                action="preview_failed",
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent"),
                success=False,
                error_message="파일이 존재하지 않음"
            )
            raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")
        
        # PDF 파일인지 확인
        mime_type, _ = mimetypes.guess_type(full_path)
        if mime_type != 'application/pdf':
            await log_file_access(
                user_id=current_user.id,
                file_id=file_id,
                action="preview_failed",
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent"),
                success=False,
                error_message="PDF 파일만 조회할 수 있습니다"
            )
            raise HTTPException(status_code=400, detail="PDF 파일만 조회할 수 있습니다")
        
        # 파일 정보
        file_size = os.path.getsize(full_path)
        filename = file_metadata["original_filename"]
        
        # 파일 스트리밍 함수
        async def stream_pdf():
            async with aiofiles.open(full_path, 'rb') as file:
                while chunk := await file.read(8192):
                    yield chunk
        
        # 응답 생성
        response = StreamingResponse(
            stream_pdf(),
            media_type="application/pdf",
            headers={
                "Content-Length": str(file_size),
                "Accept-Ranges": "bytes"
            }
        )
        
        # 보안 헤더 추가
        add_security_headers(response, filename)
        
        # 접근 로그 기록
        duration = int(time.time() - start_time)
        await log_file_access(
            user_id=current_user.id,
            file_id=file_id,
            action="preview_success",
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            success=True
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"보안 PDF 조회 오류: {e}")
        await log_file_access(
            user_id=current_user.id if 'current_user' in locals() else "unknown",
            file_id=file_id,
            action="preview_error",
            ip_address=request.client.host if 'request' in locals() else "unknown",
            user_agent=request.headers.get("user-agent") if 'request' in locals() else "unknown",
            success=False,
            error_message=f"예상치 못한 오류: {str(e)}"
        )
        raise HTTPException(
            status_code=500, 
            detail="파일 조회 중 오류가 발생했습니다"
        )

@secure_file_router.get("/access-logs", operation_id="get_secure_file_access_logs")
async def get_file_access_logs(
    current_user: User = Depends(get_current_user),
    limit: int = 100
):
    """파일 접근 로그 조회 (관리자 전용)"""
    try:
        # 관리자 권한 확인
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="관리자만 접근 로그를 조회할 수 있습니다")
        
        # 최근 로그 반환
        recent_logs = access_logs[-limit:] if len(access_logs) > limit else access_logs
        
        return {
            "success": True,
            "logs": [log.dict() for log in reversed(recent_logs)],
            "total": len(access_logs)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"접근 로그 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="접근 로그 조회 중 오류가 발생했습니다")

@secure_file_router.post("/generate-access-token", operation_id="generate_secure_file_access_token")
async def generate_file_access_token(
    file_path: str,
    current_user: User = Depends(get_current_user)
):
    """임시 파일 접근 토큰 생성"""
    try:
        # 권한 확인
        has_access = await check_file_access_permission(current_user, file_path)
        if not has_access:
            raise HTTPException(status_code=403, detail="파일 접근 권한이 없습니다")
        
        # 토큰 생성
        token = generate_access_token(current_user.id, file_path)
        
        return {
            "success": True,
            "access_token": token,
            "expires_in": 300  # 5분
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"접근 토큰 생성 오류: {e}")
        raise HTTPException(status_code=500, detail="접근 토큰 생성 중 오류가 발생했습니다")

