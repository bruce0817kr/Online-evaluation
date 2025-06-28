"""
권한 관리 API 엔드포인트 (관리자 전용)
사용자 권한, 프로젝트 멤버십, 역할 관리를 위한 REST API
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import logging
from pydantic import BaseModel, Field

from models import User
from security import get_current_user
from enhanced_permissions import (
    Permission, Role, ProjectRole, PermissionChecker, 
    permission_checker, add_project_member, remove_project_member,
    grant_custom_permission, revoke_custom_permission,
    ROLE_PERMISSIONS, PROJECT_ROLE_PERMISSIONS
)

logger = logging.getLogger(__name__)

# 권한 관리 라우터 생성
permission_admin_router = APIRouter(prefix="/api/admin/permissions", tags=["권한 관리"])

# Pydantic 모델들
class UserPermissionsResponse(BaseModel):
    user_id: str
    user_name: str
    role: str
    permissions: List[str]
    project_memberships: List[Dict[str, Any]]
    custom_permissions: List[str]

class ProjectMemberCreate(BaseModel):
    user_id: str = Field(..., description="사용자 ID")
    project_role: ProjectRole = Field(..., description="프로젝트 역할")

class ProjectMemberUpdate(BaseModel):
    project_role: ProjectRole = Field(..., description="새로운 프로젝트 역할")

class CustomPermissionRequest(BaseModel):
    user_id: str = Field(..., description="사용자 ID")
    permission: Permission = Field(..., description="권한")

class RoleUpdateRequest(BaseModel):
    user_id: str = Field(..., description="사용자 ID")
    new_role: Role = Field(..., description="새로운 역할")

class PermissionCheckRequest(BaseModel):
    user_id: str = Field(..., description="사용자 ID")
    permission: Permission = Field(..., description="확인할 권한")
    project_id: Optional[str] = Field(None, description="프로젝트 ID (선택사항)")

# 데이터베이스 연결 (순환 임포트 방지)
try:
    import motor.motor_asyncio
    import os
    mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017/online_evaluation")
    client = motor.motor_asyncio.AsyncIOMotorClient(mongo_url)
    db = client.get_default_database()
    permission_checker._setup_database(client) if hasattr(permission_checker, '_setup_database') else None
except ImportError:
    db = None
    client = None
    print("Warning: 데이터베이스 연결을 찾을 수 없습니다")

def check_admin_permission(current_user: User = Depends(get_current_user)):
    """관리자 권한 확인"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다"
        )
    return current_user

@permission_admin_router.get("/overview")
async def get_permissions_overview(current_user: User = Depends(check_admin_permission)):
    """권한 시스템 개요 조회"""
    try:
        overview = {
            "total_permissions": len(Permission),
            "total_roles": len(Role),
            "total_project_roles": len(ProjectRole),
            "available_permissions": [p.value for p in Permission],
            "available_roles": [r.value for r in Role],
            "available_project_roles": [pr.value for pr in ProjectRole],
            "role_permission_matrix": {
                role.value: [p.value for p in permissions] 
                for role, permissions in ROLE_PERMISSIONS.items()
            },
            "project_role_permission_matrix": {
                role.value: [p.value for p in permissions]
                for role, permissions in PROJECT_ROLE_PERMISSIONS.items()
            }
        }
        
        return {
            "success": True,
            "overview": overview
        }
        
    except Exception as e:
        logger.error(f"권한 개요 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="권한 개요 조회 중 오류가 발생했습니다")

@permission_admin_router.get("/users/{user_id}", response_model=UserPermissionsResponse)
async def get_user_permissions(
    user_id: str,
    project_id: Optional[str] = Query(None, description="특정 프로젝트 권한 조회"),
    current_user: User = Depends(check_admin_permission)
):
    """사용자 권한 상세 조회"""
    try:
        # 사용자 정보 조회
        user_doc = await db.users.find_one({"_id": user_id})
        if not user_doc:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        user = User.from_mongo(user_doc)
        
        # 사용자 권한 조회
        permissions = await permission_checker.get_user_permissions(user, project_id)
        
        # 프로젝트 멤버십 조회
        project_memberships = []
        if db:
            memberships = await db.project_members.find({
                "user_id": user_id,
                "is_active": True
            }).to_list(length=None)
            
            for membership in memberships:
                project_doc = await db.projects.find_one({"_id": membership["project_id"]})
                project_memberships.append({
                    "project_id": membership["project_id"],
                    "project_name": project_doc.get("name", "Unknown") if project_doc else "Unknown",
                    "project_role": membership["project_role"],
                    "added_at": membership.get("added_at", "Unknown")
                })
        
        # 커스텀 권한 조회
        custom_permissions = []
        if db:
            user_perms = await db.user_permissions.find_one({
                "user_id": user_id,
                "is_active": True
            })
            if user_perms:
                custom_permissions = user_perms.get("permissions", [])
        
        return UserPermissionsResponse(
            user_id=user_id,
            user_name=user.user_name,
            role=user.role,
            permissions=[p.value for p in permissions],
            project_memberships=project_memberships,
            custom_permissions=custom_permissions
        )
        
    except Exception as e:
        logger.error(f"사용자 권한 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="사용자 권한 조회 중 오류가 발생했습니다")

@permission_admin_router.post("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    request: RoleUpdateRequest,
    current_user: User = Depends(check_admin_permission)
):
    """사용자 역할 변경"""
    try:
        # 사용자 존재 확인
        user_doc = await db.users.find_one({"_id": user_id})
        if not user_doc:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        # 역할 업데이트
        await db.users.update_one(
            {"_id": user_id},
            {
                "$set": {
                    "role": request.new_role.value,
                    "updated_at": datetime.utcnow(),
                    "updated_by": current_user.id
                }
            }
        )
        
        logger.info(f"사용자 역할 변경: {user_id} -> {request.new_role.value}", extra={
            'admin_id': current_user.id,
            'target_user_id': user_id,
            'new_role': request.new_role.value
        })
        
        return {
            "success": True,
            "message": f"사용자 역할이 {request.new_role.value}로 변경되었습니다"
        }
        
    except Exception as e:
        logger.error(f"사용자 역할 변경 오류: {e}")
        raise HTTPException(status_code=500, detail="역할 변경 중 오류가 발생했습니다")

@permission_admin_router.post("/projects/{project_id}/members")
async def add_project_member_endpoint(
    project_id: str,
    request: ProjectMemberCreate,
    current_user: User = Depends(check_admin_permission)
):
    """프로젝트 멤버 추가"""
    try:
        # 프로젝트 존재 확인
        project_doc = await db.projects.find_one({"_id": project_id})
        if not project_doc:
            raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")
        
        # 사용자 존재 확인
        user_doc = await db.users.find_one({"_id": request.user_id})
        if not user_doc:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        # 프로젝트 멤버 추가
        await add_project_member(request.user_id, project_id, request.project_role)
        
        logger.info(f"프로젝트 멤버 추가: {request.user_id} -> {project_id} ({request.project_role.value})", extra={
            'admin_id': current_user.id,
            'project_id': project_id,
            'user_id': request.user_id,
            'project_role': request.project_role.value
        })
        
        return {
            "success": True,
            "message": "프로젝트 멤버가 추가되었습니다"
        }
        
    except Exception as e:
        logger.error(f"프로젝트 멤버 추가 오류: {e}")
        raise HTTPException(status_code=500, detail="프로젝트 멤버 추가 중 오류가 발생했습니다")

@permission_admin_router.put("/projects/{project_id}/members/{user_id}")
async def update_project_member_role(
    project_id: str,
    user_id: str,
    request: ProjectMemberUpdate,
    current_user: User = Depends(check_admin_permission)
):
    """프로젝트 멤버 역할 변경"""
    try:
        # 기존 멤버십 확인
        member = await db.project_members.find_one({
            "user_id": user_id,
            "project_id": project_id,
            "is_active": True
        })
        
        if not member:
            raise HTTPException(status_code=404, detail="프로젝트 멤버를 찾을 수 없습니다")
        
        # 역할 업데이트
        await db.project_members.update_one(
            {"user_id": user_id, "project_id": project_id},
            {
                "$set": {
                    "project_role": request.project_role.value,
                    "updated_at": datetime.utcnow(),
                    "updated_by": current_user.id
                }
            }
        )
        
        logger.info(f"프로젝트 멤버 역할 변경: {user_id} in {project_id} -> {request.project_role.value}", extra={
            'admin_id': current_user.id,
            'project_id': project_id,
            'user_id': user_id,
            'new_role': request.project_role.value
        })
        
        return {
            "success": True,
            "message": "프로젝트 멤버 역할이 변경되었습니다"
        }
        
    except Exception as e:
        logger.error(f"프로젝트 멤버 역할 변경 오류: {e}")
        raise HTTPException(status_code=500, detail="멤버 역할 변경 중 오류가 발생했습니다")

@permission_admin_router.delete("/projects/{project_id}/members/{user_id}")
async def remove_project_member_endpoint(
    project_id: str,
    user_id: str,
    current_user: User = Depends(check_admin_permission)
):
    """프로젝트 멤버 제거"""
    try:
        # 멤버 존재 확인
        member = await db.project_members.find_one({
            "user_id": user_id,
            "project_id": project_id,
            "is_active": True
        })
        
        if not member:
            raise HTTPException(status_code=404, detail="프로젝트 멤버를 찾을 수 없습니다")
        
        # 멤버 제거
        await remove_project_member(user_id, project_id)
        
        logger.info(f"프로젝트 멤버 제거: {user_id} from {project_id}", extra={
            'admin_id': current_user.id,
            'project_id': project_id,
            'user_id': user_id
        })
        
        return {
            "success": True,
            "message": "프로젝트 멤버가 제거되었습니다"
        }
        
    except Exception as e:
        logger.error(f"프로젝트 멤버 제거 오류: {e}")
        raise HTTPException(status_code=500, detail="프로젝트 멤버 제거 중 오류가 발생했습니다")

@permission_admin_router.post("/users/custom-permissions/grant")
async def grant_custom_permission_endpoint(
    request: CustomPermissionRequest,
    current_user: User = Depends(check_admin_permission)
):
    """사용자에게 커스텀 권한 부여"""
    try:
        # 사용자 존재 확인
        user_doc = await db.users.find_one({"_id": request.user_id})
        if not user_doc:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        # 권한 부여
        await grant_custom_permission(request.user_id, request.permission)
        
        logger.info(f"커스텀 권한 부여: {request.user_id} -> {request.permission.value}", extra={
            'admin_id': current_user.id,
            'user_id': request.user_id,
            'permission': request.permission.value
        })
        
        return {
            "success": True,
            "message": f"{request.permission.value} 권한이 부여되었습니다"
        }
        
    except Exception as e:
        logger.error(f"커스텀 권한 부여 오류: {e}")
        raise HTTPException(status_code=500, detail="권한 부여 중 오류가 발생했습니다")

@permission_admin_router.post("/users/custom-permissions/revoke")
async def revoke_custom_permission_endpoint(
    request: CustomPermissionRequest,
    current_user: User = Depends(check_admin_permission)
):
    """사용자의 커스텀 권한 철회"""
    try:
        # 사용자 존재 확인
        user_doc = await db.users.find_one({"_id": request.user_id})
        if not user_doc:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        # 권한 철회
        await revoke_custom_permission(request.user_id, request.permission)
        
        logger.info(f"커스텀 권한 철회: {request.user_id} -> {request.permission.value}", extra={
            'admin_id': current_user.id,
            'user_id': request.user_id,
            'permission': request.permission.value
        })
        
        return {
            "success": True,
            "message": f"{request.permission.value} 권한이 철회되었습니다"
        }
        
    except Exception as e:
        logger.error(f"커스텀 권한 철회 오류: {e}")
        raise HTTPException(status_code=500, detail="권한 철회 중 오류가 발생했습니다")

@permission_admin_router.post("/check")
async def check_user_permission(
    request: PermissionCheckRequest,
    current_user: User = Depends(check_admin_permission)
):
    """사용자 권한 확인"""
    try:
        # 사용자 조회
        user_doc = await db.users.find_one({"_id": request.user_id})
        if not user_doc:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        user = User.from_mongo(user_doc)
        
        # 권한 확인
        has_permission = await permission_checker.has_permission(
            user, request.permission, request.project_id
        )
        
        return {
            "success": True,
            "user_id": request.user_id,
            "permission": request.permission.value,
            "project_id": request.project_id,
            "has_permission": has_permission
        }
        
    except Exception as e:
        logger.error(f"권한 확인 오류: {e}")
        raise HTTPException(status_code=500, detail="권한 확인 중 오류가 발생했습니다")

@permission_admin_router.get("/projects/{project_id}/members")
async def get_project_members(
    project_id: str,
    current_user: User = Depends(check_admin_permission)
):
    """프로젝트 멤버 목록 조회"""
    try:
        # 프로젝트 존재 확인
        project_doc = await db.projects.find_one({"_id": project_id})
        if not project_doc:
            raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")
        
        # 프로젝트 멤버 조회
        members = await db.project_members.find({
            "project_id": project_id,
            "is_active": True
        }).to_list(length=None)
        
        # 사용자 정보와 함께 반환
        member_list = []
        for member in members:
            user_doc = await db.users.find_one({"_id": member["user_id"]})
            if user_doc:
                member_list.append({
                    "user_id": member["user_id"],
                    "user_name": user_doc.get("user_name", "Unknown"),
                    "email": user_doc.get("email", "Unknown"),
                    "project_role": member["project_role"],
                    "added_at": member.get("added_at"),
                    "updated_at": member.get("updated_at")
                })
        
        return {
            "success": True,
            "project_id": project_id,
            "project_name": project_doc.get("name", "Unknown"),
            "members": member_list,
            "total_members": len(member_list)
        }
        
    except Exception as e:
        logger.error(f"프로젝트 멤버 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="프로젝트 멤버 조회 중 오류가 발생했습니다")

@permission_admin_router.get("/users")
async def get_users_with_permissions(
    role: Optional[str] = Query(None, description="역할로 필터링"),
    has_permission: Optional[str] = Query(None, description="권한으로 필터링"),
    current_user: User = Depends(check_admin_permission)
):
    """권한 정보가 포함된 사용자 목록 조회"""
    try:
        # 사용자 조회 조건
        filter_conditions = {}
        if role:
            filter_conditions["role"] = role
        
        users = await db.users.find(filter_conditions).to_list(length=None)
        
        user_list = []
        for user_doc in users:
            user = User.from_mongo(user_doc)
            
            # 권한 조회
            permissions = await permission_checker.get_user_permissions(user)
            
            # 특정 권한 필터링
            if has_permission and Permission(has_permission) not in permissions:
                continue
            
            user_list.append({
                "user_id": user.id,
                "user_name": user.user_name,
                "email": user.email,
                "role": user.role,
                "is_active": user.is_active,
                "permissions_count": len(permissions),
                "created_at": user.created_at,
                "last_login": user.last_login
            })
        
        return {
            "success": True,
            "users": user_list,
            "total_users": len(user_list),
            "filters": {
                "role": role,
                "has_permission": has_permission
            }
        }
        
    except Exception as e:
        logger.error(f"사용자 목록 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="사용자 목록 조회 중 오류가 발생했습니다")