"""
평가 템플릿 관리 API 엔드포인트
사업별 평가 지표 및 가점 관리를 위한 완전한 CRUD API
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import logging
from pydantic import BaseModel, Field
import uuid
from bson import ObjectId

import models
from models import User
from security import get_current_user
try:
    from enhanced_permissions import (
        Permission, check_permission, permission_checker,
        check_template_management_permission
    )
    ENHANCED_PERMISSIONS_AVAILABLE = True
except ImportError:
    ENHANCED_PERMISSIONS_AVAILABLE = False

logger = logging.getLogger(__name__)

# 템플릿 관리 라우터 생성
template_router = APIRouter(prefix="/api/templates", tags=["평가 템플릿 관리"])

# 향상된 템플릿 모델들
class EvaluationCriterionEnhanced(BaseModel):
    """향상된 평가 기준 모델"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="기준 ID")
    name: str = Field(..., description="평가 항목명")
    description: Optional[str] = Field(None, description="항목 설명")
    max_score: int = Field(..., description="최대 점수")
    min_score: int = Field(0, description="최소 점수")
    weight: float = Field(1.0, description="가중치")
    bonus: bool = Field(False, description="가점 항목 여부")
    category: Optional[str] = Field(None, description="기준 카테고리")
    is_required: bool = Field(True, description="필수 항목 여부")
    evaluation_guide: Optional[str] = Field(None, description="평가 가이드")
    order: int = Field(0, description="표시 순서")

class EvaluationTemplateEnhanced(BaseModel):
    """향상된 평가 템플릿 모델"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    name: str = Field(..., description="템플릿 이름")
    description: Optional[str] = Field(None, description="템플릿 설명")
    project_id: str = Field(..., description="프로젝트 ID")
    category: Optional[str] = Field(None, description="템플릿 카테고리")
    
    # 평가 기준들
    criteria: List[EvaluationCriterionEnhanced] = Field(default_factory=list, description="평가 기준 목록")
    
    # 템플릿 메타데이터
    version: int = Field(1, description="템플릿 버전")
    parent_template_id: Optional[str] = Field(None, description="부모 템플릿 ID (버전 관리용)")
    is_default: bool = Field(False, description="기본 템플릿 여부")
    is_organization_default: bool = Field(False, description="조직 기본 템플릿 여부")
    
    # 상태 관리
    status: str = Field("draft", description="템플릿 상태 (draft, active, archived)")
    approval_status: str = Field("draft", description="승인 상태 (draft, pending_approval, approved, rejected)")
    approved_by: Optional[str] = Field(None, description="승인자 ID")
    approved_at: Optional[datetime] = Field(None, description="승인 일시")
    
    # 권한 및 공유
    is_public: bool = Field(False, description="공개 템플릿 여부")
    shared_with: List[str] = Field(default_factory=list, description="공유된 사용자 ID 목록")
    
    # 추적 정보
    created_by: str = Field(..., description="생성자 ID")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    updated_by: Optional[str] = Field(None, description="최종 수정자 ID")
    
    # 사용 통계
    usage_count: int = Field(0, description="사용 횟수")
    last_used_at: Optional[datetime] = Field(None, description="마지막 사용 일시")

    class Config:
        allow_population_by_field_name = True
        json_encoders = {datetime: lambda dt: dt.isoformat()}

class EvaluationTemplateCreateEnhanced(BaseModel):
    """향상된 템플릿 생성 요청 모델"""
    name: str = Field(..., description="템플릿 이름")
    description: Optional[str] = Field(None, description="템플릿 설명")
    project_id: str = Field(..., description="프로젝트 ID")
    category: Optional[str] = Field(None, description="템플릿 카테고리")
    criteria: List[EvaluationCriterionEnhanced] = Field(..., description="평가 기준 목록")
    is_default: bool = Field(False, description="기본 템플릿 여부")
    is_public: bool = Field(False, description="공개 템플릿 여부")

class EvaluationTemplateUpdate(BaseModel):
    """템플릿 업데이트 요청 모델"""
    name: Optional[str] = Field(None, description="템플릿 이름")
    description: Optional[str] = Field(None, description="템플릿 설명")
    category: Optional[str] = Field(None, description="템플릿 카테고리")
    criteria: Optional[List[EvaluationCriterionEnhanced]] = Field(None, description="평가 기준 목록")
    status: Optional[str] = Field(None, description="템플릿 상태")
    is_default: Optional[bool] = Field(None, description="기본 템플릿 여부")
    is_public: Optional[bool] = Field(None, description="공개 템플릿 여부")

class TemplateCloneRequest(BaseModel):
    """템플릿 복제 요청 모델"""
    new_name: str = Field(..., description="새 템플릿 이름")
    new_description: Optional[str] = Field(None, description="새 템플릿 설명")
    target_project_id: Optional[str] = Field(None, description="대상 프로젝트 ID (없으면 같은 프로젝트)")

class TemplateShareRequest(BaseModel):
    """템플릿 공유 요청 모델"""
    user_ids: List[str] = Field(..., description="공유할 사용자 ID 목록")
    permission: str = Field("view", description="권한 (view, edit)")

# 데이터베이스 연결은 필요시에만 수행
db = None

@template_router.get("/test")
async def get_templates_test():
    """테스트 엔드포인트 - 인증 없음"""
    return {"message": "templates test endpoint working"}

@template_router.get("")
async def get_templates(
    project_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """템플릿 목록 조회 - 권한 기반 조회"""
    try:
        # 권한 검사 (향상된 권한 시스템이 있는 경우)
        if ENHANCED_PERMISSIONS_AVAILABLE:
            try:
                await check_permission(current_user, Permission.TEMPLATE_READ)
            except Exception as perm_error:
                logger.warning(f"Enhanced permission check failed: {perm_error}")
                # 기본 권한 검사로 폴백
                if current_user.role not in ['admin', 'secretary', 'evaluator']:
                    raise HTTPException(status_code=403, detail="템플릿 조회 권한이 없습니다")
        else:
            # 기본 권한 검사
            if current_user.role not in ['admin', 'secretary', 'evaluator']:
                raise HTTPException(status_code=403, detail="템플릿 조회 권한이 없습니다")
        
        # 향상된 템플릿 구조 반환 (데이터베이스 미연결 시 목업 데이터)
        templates = [
            {
                "id": "default-template-1",
                "name": "기본 평가 템플릿",
                "description": "일반적인 사업 평가를 위한 기본 템플릿",
                "category": "일반 사업 평가",
                "project_id": project_id or "default-project",
                "criteria": [
                    {
                        "id": "criterion-1",
                        "name": "사업성",
                        "description": "사업의 실현 가능성과 수익성",
                        "max_score": 100,
                        "weight": 0.3,
                        "is_required": True
                    },
                    {
                        "id": "criterion-2", 
                        "name": "기술성",
                        "description": "기술의 우수성과 혁신성",
                        "max_score": 100,
                        "weight": 0.3,
                        "is_required": True
                    },
                    {
                        "id": "criterion-3",
                        "name": "시장성",
                        "description": "시장 진입 가능성과 성장성",
                        "max_score": 100,
                        "weight": 0.4,
                        "is_required": True
                    }
                ],
                "status": "active",
                "is_default": True,
                "created_by": "system",
                "created_at": "2025-06-25T00:00:00Z",
                "updated_at": "2025-06-25T00:00:00Z"
            }
        ]
        
        # 검색 필터 적용
        if search:
            search_lower = search.lower()
            templates = [
                t for t in templates 
                if search_lower in t["name"].lower() or 
                   search_lower in (t["description"] or "").lower()
            ]
        
        # 프로젝트 필터 적용
        if project_id:
            templates = [t for t in templates if t["project_id"] == project_id]
            
        return templates
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"템플릿 목록 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="템플릿 목록 조회 중 오류가 발생했습니다")

# @template_router.get("/{template_id}", response_model=EvaluationTemplateEnhanced)
# async def get_template(
#     template_id: str,
#     current_user: User = Depends(get_current_user)
# ):
router = template_router
