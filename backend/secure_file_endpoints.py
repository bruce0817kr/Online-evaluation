"""
보안 파일 서빙 API 엔드포인트
PDF 뷰어를 위한 보안 파일 접근 제어
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from typing import Optional
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

from models import User
from security import get_current_user
from enhanced_permissions import Permission, check_permission, permission_checker

logger = logging.getLogger(__name__)

# 보안 파일 라우터 생성
secure_file_router = APIRouter(prefix="/api/files", tags=["보안 파일 관리"])

# 요청 모델들
class SecurePDFViewRequest(BaseModel):
    """보안 PDF 조회 요청"""
    file_url: str = Field(..., description="파일 URL 또는 경로")
    evaluation_id: Optional[str] = Field(None, description="평가 ID")
    company_id: Optional[str] = Field(None, description="기업 ID")
    project_id: Optional[str] = Field(None, description="프로젝트 ID")

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
access_logs = []

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

async def log_file_access(user: User, file_path: str, request: Request, action: str, **kwargs):
    """파일 접근 로그 기록"""
    try:
        log_entry = FileAccessLog(
            user_id=user.id,
            file_path=file_path,
            access_time=datetime.utcnow(),
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent", ""),
            action=action,
            **kwargs
        )
        
        access_logs.append(log_entry)
        
        # 실제로는 데이터베이스에 저장
        logger.info(f"파일 접근 로그: {action}", extra={
            'user_id': user.id,
            'file_path': file_path,
            'ip_address': request.client.host,
            'action': action
        })
        
    except Exception as e:
        logger.error(f"파일 접근 로그 저장 실패: {e}")

async def check_file_access_permission(user: User, file_path: str, evaluation_id: str = None, company_id: str = None) -> bool:
    """파일 접근 권한 확인"""
    try:
        # 데이터베이스 연결
        from server import db
        
        # 1. 파일 메타데이터 조회
        file_metadata = await db.files.find_one({"file_path": file_path})
        if not file_metadata:
            logger.warning(f"파일 메타데이터를 찾을 수 없음: {file_path}")
            return False
        
        # 2. 관리자는 모든 파일 접근 가능
        if user.role == "admin":
            return True
        
        # 3. 간사는 프로젝트 내 파일 접근 가능
        if user.role == "secretary":
            # 프로젝트 권한 확인
            project_id = file_metadata.get("project_id")
            if project_id:
                has_permission = await permission_checker.has_permission(
                    user, Permission.FILE_VIEW, project_id
                )
                if has_permission:
                    return True
        
        # 4. 평가위원은 할당된 평가의 파일만 접근 가능
        if user.role == "evaluator":
            if evaluation_id:
                # 평가 할당 확인
                evaluation = await db.evaluations.find_one({"_id": evaluation_id})
                if evaluation and user.id in evaluation.get("evaluator_ids", []):
                    return True
            
            if company_id:
                # 기업 평가 할당 확인
                assignment = await db.evaluation_assignments.find_one({
                    "evaluator_id": user.id,
                    "company_id": company_id
                })
                if assignment:
                    return True
        
        # 5. 파일 소유자 확인
        if file_metadata.get("uploaded_by") == user.id:
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"파일 접근 권한 확인 오류: {e}")
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
    safe_filename = filename.encode('utf-8').decode('ascii', 'ignore')
    response.headers["Content-Disposition"] = f"inline; filename*=UTF-8''{safe_filename}"

@secure_file_router.post("/secure-pdf-view")
async def secure_pdf_view(
    request_data: SecurePDFViewRequest,
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """보안 PDF 조회 (뷰어 전용)"""
    try:
        start_time = time.time()
        
        # 권한 확인
        has_access = await check_file_access_permission(
            current_user, 
            request_data.file_url,
            request_data.evaluation_id,
            request_data.company_id
        )
        
        if not has_access:
            await log_file_access(
                current_user, request_data.file_url, request, "denied"
            )
            raise HTTPException(
                status_code=403, 
                detail="파일 접근 권한이 없습니다"
            )
        
        # 파일 경로 정리
        file_path = request_data.file_url
        if file_path.startswith('/'):
            file_path = file_path[1:]
        
        # uploads 디렉토리 기준으로 파일 경로 생성
        full_path = os.path.join("uploads", file_path)
        
        # 파일 존재 확인
        if not os.path.exists(full_path):
            logger.warning(f"파일을 찾을 수 없음: {full_path}")
            await log_file_access(
                current_user, request_data.file_url, request, "not_found"
            )
            raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")
        
        # PDF 파일인지 확인
        mime_type, _ = mimetypes.guess_type(full_path)
        if mime_type != 'application/pdf':
            await log_file_access(
                current_user, request_data.file_url, request, "invalid_type"
            )
            raise HTTPException(status_code=400, detail="PDF 파일만 조회할 수 있습니다")
        
        # 파일 정보
        file_size = os.path.getsize(full_path)
        filename = os.path.basename(full_path)
        
        # 파일 스트리밍 함수
        async def stream_pdf():
            async with aiofiles.open(full_path, 'rb') as file:
                while chunk := await file.read(8192):  # 8KB씩 읽기
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
            current_user, 
            request_data.file_url, 
            request, 
            "view",
            file_size=file_size,
            duration=duration
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"보안 PDF 조회 오류: {e}")
        await log_file_access(
            current_user, request_data.file_url, request, "error"
        )
        raise HTTPException(
            status_code=500, 
            detail="파일 조회 중 오류가 발생했습니다"
        )

@secure_file_router.get("/secure-thumbnail/{file_id}")
async def get_secure_thumbnail(
    file_id: str,
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """보안 파일 썸네일 조회"""
    try:
        # 데이터베이스 연결
        from server import db
        
        # 파일 메타데이터 조회
        file_metadata = await db.files.find_one({"_id": file_id})
        if not file_metadata:
            raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")
        
        # 권한 확인
        has_access = await check_file_access_permission(
            current_user, 
            file_metadata.get("file_path", "")
        )
        
        if not has_access:
            await log_file_access(
                current_user, file_metadata.get("file_path", ""), request, "thumbnail_denied"
            )
            raise HTTPException(status_code=403, detail="썸네일 조회 권한이 없습니다")
        
        # 썸네일 경로
        thumbnail_path = file_metadata.get("thumbnail_path")
        if not thumbnail_path or not os.path.exists(thumbnail_path):
            # 기본 PDF 아이콘 반환
            default_icon = "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjQiIGhlaWdodD0iNjQiIHZpZXdCb3g9IjAgMCA2NCA2NCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHJlY3Qgd2lkdGg9IjY0IiBoZWlnaHQ9IjY0IiByeD0iOCIgZmlsbD0iI0ZGNTc1NyIvPgo8dGV4dCB4PSIzMiIgeT0iMzgiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZpbGw9IndoaXRlIiBmb250LXNpemU9IjEyIiBmb250LWZhbWlseT0iQXJpYWwiPlBERjwvdGV4dD4KPC9zdmc+"
            return StreamingResponse(
                io.BytesIO(base64.b64decode(default_icon.split(',')[1])),
                media_type="image/svg+xml"
            )
        
        # 썸네일 파일 스트리밍
        async def stream_thumbnail():
            async with aiofiles.open(thumbnail_path, 'rb') as file:
                while chunk := await file.read(8192):
                    yield chunk
        
        mime_type, _ = mimetypes.guess_type(thumbnail_path)
        response = StreamingResponse(
            stream_thumbnail(),
            media_type=mime_type or "image/jpeg"
        )
        
        # 보안 헤더 추가
        add_security_headers(response, f"thumbnail_{file_id}")
        
        # 접근 로그 기록
        await log_file_access(
            current_user, 
            file_metadata.get("file_path", ""), 
            request, 
            "thumbnail_view"
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"썸네일 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="썸네일 조회 중 오류가 발생했습니다")

@secure_file_router.get("/access-logs")
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

@secure_file_router.post("/generate-access-token")
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

# 데이터베이스 연결
try:
    from server import db
except ImportError:
    db = None
    logger.warning("데이터베이스 연결을 찾을 수 없습니다")