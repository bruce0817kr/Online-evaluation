"""
향상된 권한 관리 시스템
세밀한 권한 제어 및 프로젝트별/기능별 권한 관리
"""

from enum import Enum
from typing import List, Dict, Set, Optional, Any
from fastapi import HTTPException, Depends, status
from functools import wraps
import logging
from datetime import datetime

from models import User
from security import get_current_user

logger = logging.getLogger(__name__)

class Permission(str, Enum):
    """시스템 권한 정의"""
    
    # 사용자 관리
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_MANAGE_ROLES = "user:manage_roles"
    
    # 프로젝트 관리
    PROJECT_CREATE = "project:create"
    PROJECT_READ = "project:read"
    PROJECT_UPDATE = "project:update"
    PROJECT_DELETE = "project:delete"
    PROJECT_MANAGE_MEMBERS = "project:manage_members"
    
    # 평가 템플릿 관리
    TEMPLATE_CREATE = "template:create"
    TEMPLATE_READ = "template:read"
    TEMPLATE_UPDATE = "template:update"
    TEMPLATE_DELETE = "template:delete"
    TEMPLATE_ASSIGN = "template:assign"
    
    # 회사/기업 관리
    COMPANY_CREATE = "company:create"
    COMPANY_READ = "company:read"
    COMPANY_UPDATE = "company:update"
    COMPANY_DELETE = "company:delete"
    
    # 평가 관리
    EVALUATION_CREATE = "evaluation:create"
    EVALUATION_READ = "evaluation:read"
    EVALUATION_UPDATE = "evaluation:update"
    EVALUATION_DELETE = "evaluation:delete"
    EVALUATION_SUBMIT = "evaluation:submit"
    EVALUATION_REVIEW = "evaluation:review"
    EVALUATION_ASSIGN = "evaluation:assign"
    
    # 파일 관리
    FILE_UPLOAD = "file:upload"
    FILE_READ = "file:read"
    FILE_DELETE = "file:delete"
    FILE_DOWNLOAD = "file:download"
    
    # AI 기능
    AI_PROVIDER_MANAGE = "ai:provider_manage"
    AI_ANALYSIS_EXECUTE = "ai:analysis_execute"
    AI_ANALYSIS_VIEW = "ai:analysis_view"
    AI_SETTINGS_MANAGE = "ai:settings_manage"
    
    # 시스템 관리
    SYSTEM_CONFIG = "system:config"
    SYSTEM_MONITORING = "system:monitoring"
    SYSTEM_BACKUP = "system:backup"
    
    # 보고서 및 내보내기
    REPORT_GENERATE = "report:generate"
    REPORT_EXPORT = "report:export"
    REPORT_VIEW = "report:view"

class Role(str, Enum):
    """시스템 역할 정의"""
    ADMIN = "admin"
    SECRETARY = "secretary"  
    EVALUATOR = "evaluator"
    VIEWER = "viewer"  # 읽기 전용 사용자

class ProjectRole(str, Enum):
    """프로젝트별 역할 정의"""
    PROJECT_ADMIN = "project_admin"
    PROJECT_MANAGER = "project_manager"
    PROJECT_EVALUATOR = "project_evaluator"
    PROJECT_VIEWER = "project_viewer"

# 역할별 기본 권한 매핑
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.ADMIN: {
        # 전체 권한
        Permission.USER_CREATE, Permission.USER_READ, Permission.USER_UPDATE, 
        Permission.USER_DELETE, Permission.USER_MANAGE_ROLES,
        Permission.PROJECT_CREATE, Permission.PROJECT_READ, Permission.PROJECT_UPDATE,
        Permission.PROJECT_DELETE, Permission.PROJECT_MANAGE_MEMBERS,
        Permission.TEMPLATE_CREATE, Permission.TEMPLATE_READ, Permission.TEMPLATE_UPDATE,
        Permission.TEMPLATE_DELETE, Permission.TEMPLATE_ASSIGN,
        Permission.COMPANY_CREATE, Permission.COMPANY_READ, Permission.COMPANY_UPDATE,
        Permission.COMPANY_DELETE,
        Permission.EVALUATION_CREATE, Permission.EVALUATION_READ, Permission.EVALUATION_UPDATE,
        Permission.EVALUATION_DELETE, Permission.EVALUATION_REVIEW, Permission.EVALUATION_ASSIGN,
        Permission.FILE_UPLOAD, Permission.FILE_READ, Permission.FILE_DELETE, Permission.FILE_DOWNLOAD,
        Permission.AI_PROVIDER_MANAGE, Permission.AI_ANALYSIS_EXECUTE, Permission.AI_ANALYSIS_VIEW,
        Permission.AI_SETTINGS_MANAGE,
        Permission.SYSTEM_CONFIG, Permission.SYSTEM_MONITORING, Permission.SYSTEM_BACKUP,
        Permission.REPORT_GENERATE, Permission.REPORT_EXPORT, Permission.REPORT_VIEW
    },
    
    Role.SECRETARY: {
        # 간사 권한 - 관리 업무 중심
        Permission.USER_READ,
        Permission.PROJECT_CREATE, Permission.PROJECT_READ, Permission.PROJECT_UPDATE,
        Permission.PROJECT_MANAGE_MEMBERS,
        Permission.TEMPLATE_CREATE, Permission.TEMPLATE_READ, Permission.TEMPLATE_UPDATE,
        Permission.TEMPLATE_ASSIGN,
        Permission.COMPANY_CREATE, Permission.COMPANY_READ, Permission.COMPANY_UPDATE,
        Permission.EVALUATION_CREATE, Permission.EVALUATION_READ, Permission.EVALUATION_ASSIGN,
        Permission.EVALUATION_REVIEW,
        Permission.FILE_UPLOAD, Permission.FILE_READ, Permission.FILE_DOWNLOAD,
        Permission.AI_ANALYSIS_EXECUTE, Permission.AI_ANALYSIS_VIEW,
        Permission.REPORT_GENERATE, Permission.REPORT_EXPORT, Permission.REPORT_VIEW
    },
    
    Role.EVALUATOR: {
        # 평가위원 권한 - 평가 활동 중심
        Permission.PROJECT_READ,
        Permission.TEMPLATE_READ,
        Permission.COMPANY_READ,
        Permission.EVALUATION_READ, Permission.EVALUATION_SUBMIT,
        Permission.FILE_READ, Permission.FILE_DOWNLOAD,
        Permission.AI_ANALYSIS_VIEW,
        Permission.REPORT_VIEW
    },
    
    Role.VIEWER: {
        # 읽기 전용 권한
        Permission.PROJECT_READ,
        Permission.TEMPLATE_READ,
        Permission.COMPANY_READ,
        Permission.EVALUATION_READ,
        Permission.FILE_READ,
        Permission.REPORT_VIEW
    }
}

# 프로젝트 역할별 추가 권한
PROJECT_ROLE_PERMISSIONS: Dict[ProjectRole, Set[Permission]] = {
    ProjectRole.PROJECT_ADMIN: {
        Permission.PROJECT_UPDATE, Permission.PROJECT_DELETE, Permission.PROJECT_MANAGE_MEMBERS,
        Permission.TEMPLATE_CREATE, Permission.TEMPLATE_UPDATE, Permission.TEMPLATE_DELETE,
        Permission.EVALUATION_CREATE, Permission.EVALUATION_ASSIGN, Permission.EVALUATION_REVIEW,
        Permission.AI_ANALYSIS_EXECUTE
    },
    
    ProjectRole.PROJECT_MANAGER: {
        Permission.PROJECT_UPDATE, Permission.PROJECT_MANAGE_MEMBERS,
        Permission.TEMPLATE_UPDATE, Permission.EVALUATION_ASSIGN, Permission.EVALUATION_REVIEW,
        Permission.AI_ANALYSIS_EXECUTE
    },
    
    ProjectRole.PROJECT_EVALUATOR: {
        Permission.EVALUATION_SUBMIT, Permission.AI_ANALYSIS_VIEW
    },
    
    ProjectRole.PROJECT_VIEWER: {
        Permission.PROJECT_READ, Permission.EVALUATION_READ
    }
}

class PermissionChecker:
    """권한 검사 클래스"""
    
    def __init__(self, db_client=None):
        self._db = None
        self.user_permissions_collection = None
        self.project_members_collection = None
        if db_client:
            self._db = db_client.online_evaluation
            self.user_permissions_collection = self._db.user_permissions
            self.project_members_collection = self._db.project_members
    
    @property
    def db(self):
        return self._db
    
    @db.setter
    def db(self, value):
        self._db = value
        if value is not None:
            self.user_permissions_collection = value.user_permissions
            self.project_members_collection = value.project_members
    
    async def get_user_permissions(self, user: User, project_id: Optional[str] = None) -> Set[Permission]:
        """사용자의 전체 권한 조회"""
        permissions = set()
        
        # 기본 역할 권한
        if user.role in ROLE_PERMISSIONS:
            permissions.update(ROLE_PERMISSIONS[Role(user.role)])
        
        # 프로젝트별 권한 추가
        if project_id and self._db is not None:
            project_permissions = await self._get_project_permissions(user.id, project_id)
            permissions.update(project_permissions)
        
        # 사용자별 커스텀 권한 추가
        if self._db is not None:
            custom_permissions = await self._get_custom_permissions(user.id)
            permissions.update(custom_permissions)
        
        return permissions
    
    async def _get_project_permissions(self, user_id: str, project_id: str) -> Set[Permission]:
        """프로젝트별 권한 조회"""
        try:
            member = await self.project_members_collection.find_one({
                "user_id": user_id,
                "project_id": project_id,
                "is_active": True
            })
            
            if member and member.get("project_role"):
                project_role = ProjectRole(member["project_role"])
                return PROJECT_ROLE_PERMISSIONS.get(project_role, set())
            
        except Exception as e:
            logger.error(f"프로젝트 권한 조회 오류: {e}")
        
        return set()
    
    async def _get_custom_permissions(self, user_id: str) -> Set[Permission]:
        """사용자별 커스텀 권한 조회"""
        try:
            user_perms = await self.user_permissions_collection.find_one({
                "user_id": user_id,
                "is_active": True
            })
            
            if user_perms:
                return set(Permission(p) for p in user_perms.get("permissions", []))
            
        except Exception as e:
            logger.error(f"커스텀 권한 조회 오류: {e}")
        
        return set()
    
    async def has_permission(self, user: User, permission: Permission, project_id: Optional[str] = None) -> bool:
        """권한 확인"""
        user_permissions = await self.get_user_permissions(user, project_id)
        return permission in user_permissions
    
    async def has_any_permission(self, user: User, permissions: List[Permission], project_id: Optional[str] = None) -> bool:
        """여러 권한 중 하나라도 있는지 확인"""
        user_permissions = await self.get_user_permissions(user, project_id)
        return any(perm in user_permissions for perm in permissions)
    
    async def has_all_permissions(self, user: User, permissions: List[Permission], project_id: Optional[str] = None) -> bool:
        """모든 권한을 가지고 있는지 확인"""
        user_permissions = await self.get_user_permissions(user, project_id)
        return all(perm in user_permissions for perm in permissions)

# 전역 권한 검사 인스턴스
permission_checker = PermissionChecker()

def require_permission(permission: Permission, project_id_param: Optional[str] = None):
    """권한 필요 데코레이터"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 현재 사용자 추출
            current_user = None
            project_id = None
            
            # 함수 매개변수에서 current_user 찾기
            for arg in args:
                if isinstance(arg, User):
                    current_user = arg
                    break
            
            # kwargs에서 current_user 찾기
            if not current_user:
                current_user = kwargs.get('current_user')
            
            # project_id 추출
            if project_id_param:
                project_id = kwargs.get(project_id_param)
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="인증이 필요합니다"
                )
            
            # 권한 확인
            has_perm = await permission_checker.has_permission(current_user, permission, project_id)
            if not has_perm:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"권한이 부족합니다. {permission.value} 권한이 필요합니다"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_any_permission(permissions: List[Permission], project_id_param: Optional[str] = None):
    """여러 권한 중 하나 필요 데코레이터"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = None
            project_id = None
            
            # current_user 추출
            for arg in args:
                if isinstance(arg, User):
                    current_user = arg
                    break
            
            if not current_user:
                current_user = kwargs.get('current_user')
            
            # project_id 추출
            if project_id_param:
                project_id = kwargs.get(project_id_param)
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="인증이 필요합니다"
                )
            
            # 권한 확인
            has_perm = await permission_checker.has_any_permission(current_user, permissions, project_id)
            if not has_perm:
                perm_names = [p.value for p in permissions]
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"권한이 부족합니다. 다음 권한 중 하나가 필요합니다: {', '.join(perm_names)}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# 편의 함수들
async def check_permission(permission: Permission, current_user: User = Depends(get_current_user), project_id: Optional[str] = None):
    """권한 확인 의존성 함수"""
    has_perm = await permission_checker.has_permission(current_user, permission, project_id)
    if not has_perm:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"권한이 부족합니다. {permission.value} 권한이 필요합니다"
        )
    return current_user

async def check_template_management_permission(current_user: User = Depends(get_current_user)):
    """템플릿 관리 권한 확인"""
    return await check_permission(Permission.TEMPLATE_UPDATE, current_user)

async def check_ai_execution_permission(current_user: User = Depends(get_current_user)):
    """AI 분석 실행 권한 확인"""
    return await check_permission(Permission.AI_ANALYSIS_EXECUTE, current_user)

async def check_project_management_permission(current_user: User = Depends(get_current_user)):
    """프로젝트 관리 권한 확인"""
    return await check_permission(Permission.PROJECT_UPDATE, current_user)

async def check_evaluation_assignment_permission(current_user: User = Depends(get_current_user)):
    """평가 배정 권한 확인"""
    return await check_permission(Permission.EVALUATION_ASSIGN, current_user)

# 프로젝트 멤버 관리 함수들
async def add_project_member(user_id: str, project_id: str, project_role: ProjectRole):
    """프로젝트 멤버 추가"""
    if permission_checker._db is None:
        logger.warning("데이터베이스가 연결되지 않았습니다")
        return
    
    try:
        member_data = {
            "user_id": user_id,
            "project_id": project_id,
            "project_role": project_role.value,
            "is_active": True,
            "added_at": datetime.utcnow()
        }
        
        # 기존 멤버 확인
        existing = await permission_checker.project_members_collection.find_one({
            "user_id": user_id,
            "project_id": project_id
        })
        
        if existing:
            # 업데이트
            await permission_checker.project_members_collection.update_one(
                {"user_id": user_id, "project_id": project_id},
                {"$set": {"project_role": project_role.value, "is_active": True, "updated_at": datetime.utcnow()}}
            )
        else:
            # 새로 추가
            await permission_checker.project_members_collection.insert_one(member_data)
        
        logger.info(f"프로젝트 멤버 추가: {user_id} -> {project_id} ({project_role.value})")
        
    except Exception as e:
        logger.error(f"프로젝트 멤버 추가 오류: {e}")

async def remove_project_member(user_id: str, project_id: str):
    """프로젝트 멤버 제거"""
    if permission_checker._db is None:
        return
    
    try:
        await permission_checker.project_members_collection.update_one(
            {"user_id": user_id, "project_id": project_id},
            {"$set": {"is_active": False, "removed_at": datetime.utcnow()}}
        )
        
        logger.info(f"프로젝트 멤버 제거: {user_id} from {project_id}")
        
    except Exception as e:
        logger.error(f"프로젝트 멤버 제거 오류: {e}")

async def grant_custom_permission(user_id: str, permission: Permission):
    """사용자에게 커스텀 권한 부여"""
    if permission_checker._db is None:
        return
    
    try:
        # 기존 권한 조회
        user_perms = await permission_checker.user_permissions_collection.find_one({
            "user_id": user_id
        })
        
        if user_perms:
            # 기존 권한에 추가
            permissions = set(user_perms.get("permissions", []))
            permissions.add(permission.value)
            
            await permission_checker.user_permissions_collection.update_one(
                {"user_id": user_id},
                {"$set": {"permissions": list(permissions), "updated_at": datetime.utcnow()}}
            )
        else:
            # 새로운 권한 문서 생성
            perm_data = {
                "user_id": user_id,
                "permissions": [permission.value],
                "is_active": True,
                "created_at": datetime.utcnow()
            }
            
            await permission_checker.user_permissions_collection.insert_one(perm_data)
        
        logger.info(f"커스텀 권한 부여: {user_id} -> {permission.value}")
        
    except Exception as e:
        logger.error(f"커스텀 권한 부여 오류: {e}")

async def revoke_custom_permission(user_id: str, permission: Permission):
    """사용자의 커스텀 권한 철회"""
    if permission_checker._db is None:
        return
    
    try:
        user_perms = await permission_checker.user_permissions_collection.find_one({
            "user_id": user_id
        })
        
        if user_perms:
            permissions = set(user_perms.get("permissions", []))
            permissions.discard(permission.value)
            
            await permission_checker.user_permissions_collection.update_one(
                {"user_id": user_id},
                {"$set": {"permissions": list(permissions), "updated_at": datetime.utcnow()}}
            )
        
        logger.info(f"커스텀 권한 철회: {user_id} -> {permission.value}")
        
    except Exception as e:
        logger.error(f"커스텀 권한 철회 오류: {e}")