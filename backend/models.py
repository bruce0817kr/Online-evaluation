from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

# Temporary fix for missing email-validator - using str instead of EmailStr
try:
    from pydantic import EmailStr
except ImportError:
    EmailStr = str  # Fallback to str if email-validator is not installed

class Token(BaseModel):
    access_token: str
    token_type: str
    user: Optional['UserResponse'] # Use forward reference for UserResponse

class UserBase(BaseModel):
    login_id: str = Field(..., description="User's login ID")
    email: str = Field(..., description="User's email address")  # Changed from EmailStr to str
    user_name: str = Field(..., description="User's full name")
    phone: Optional[str] = Field(None, description="User's phone number")
    role: str = Field(..., description="User's role (admin, secretary, evaluator)")
    is_active: bool = Field(True, description="Whether the user account is active")
    
class UserCreate(UserBase):
    password: str = Field(..., description="User's password (plain text)")

class User(UserBase):
    id: Optional[str] = Field(default=None, alias="_id", description="User's unique ID")
    password_hash: str = Field(..., description="User's hashed password")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of user creation")
    last_login: Optional[datetime] = Field(None, description="Timestamp of last login")
    
    class Config:
        validate_by_name = True # Pydantic V2 (renamed from allow_population_by_field_name)
        allow_population_by_field_name = True  # For backward compatibility
        json_encoders = {datetime: lambda dt: dt.isoformat()}
        from_attributes = True # For Pydantic V2 (renamed from orm_mode)
    
    @classmethod
    def from_mongo(cls, data: dict):
        """MongoDB 문서를 User 객체로 변환"""
        if data and "_id" in data:
            data = data.copy()  # Create a copy to avoid modifying the original
            data["id"] = str(data.pop("_id"))  # Convert ObjectId to string and remove _id
        return cls(**data) if data else None
    
    def to_mongo(self) -> dict:
        """User 객체를 MongoDB 문서로 변환"""
        data = self.dict(by_alias=True, exclude_unset=True)
        if "id" in data and data["id"]:
            data["_id"] = data.pop("id")
        return data

# UserInDB can be an alias for User as it contains all necessary fields including password_hash
UserInDB = User

class UserResponse(UserBase):
    id: str = Field(..., description="User's unique ID")
    created_at: datetime = Field(..., description="Timestamp of user creation")
    last_login: Optional[datetime] = Field(None, description="Timestamp of last login")

    class Config:
        from_attributes = True # For Pydantic V2

class SecretarySignupRequest(BaseModel):
    name: str
    phone: str
    email: str  # Changed from EmailStr to str
    reason: Optional[str] = None

class SecretaryApproval(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    name: str
    phone: str
    email: str  # Changed from EmailStr to str
    reason: Optional[str] = None
    status: str = Field("pending", description="Approval status: pending, approved, rejected")
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None # Admin user ID

    class Config:
        allow_population_by_field_name = True
        json_encoders = {datetime: lambda dt: dt.isoformat()}

class EvaluatorCreate(BaseModel):
    user_name: str
    phone: str
    email: str  # Changed from EmailStr to str
    # Add other fields as necessary based on usage in server.py

class ProjectBase(BaseModel):
    name: str = Field(..., description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class ProjectCreate(ProjectBase):
    deadline: Optional[datetime] = Field(None, description="Project deadline")

class Project(ProjectBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    deadline: Optional[datetime] = Field(None, description="Project deadline")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None # User ID

    class Config:
        allow_population_by_field_name = True
        json_encoders = {datetime: lambda dt: dt.isoformat()}
        
# Update Company model to include project_id field
class CompanyBase(BaseModel):
    name: str = Field(..., description="Company name")
    registration_number: Optional[str] = Field(None, description="Company registration number")
    address: Optional[str] = Field(None, description="Company address")
    project_id: str = Field(..., description="Project ID this company belongs to")  # Added project_id field

class CompanyCreate(CompanyBase):
    pass

class Company(CompanyBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        json_encoders = {datetime: lambda dt: dt.isoformat()}

# Add FileMetadata model for file upload functionality
class FileMetadata(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    filename: str = Field(..., description="Stored filename")
    original_filename: str = Field(..., description="Original filename")
    file_path: str = Field(..., description="File storage path")
    file_size: int = Field(..., description="File size in bytes")
    file_type: str = Field(..., description="File MIME type")
    uploaded_by: str = Field(..., description="User ID who uploaded the file")
    company_id: str = Field(..., description="Company ID this file belongs to")
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        json_encoders = {datetime: lambda dt: dt.isoformat()}

# Add EvaluationTemplateCreate model for template creation
class EvaluationTemplateCreate(BaseModel):
    name: str = Field(..., description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    project_id: str = Field(..., description="Project ID this template belongs to")
    items: List[Dict[str, Any]] = Field(default_factory=list, description="Evaluation criteria items")

# Add other models as identified from server.py's usage and errors
# For example: EvaluationSheet, EvaluationItem, Submission, etc.

class EvaluationSheet(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    project_id: str
    evaluator_id: str
    company_id: str
    status: str = Field("pending") # pending, in_progress, submitted, reviewed
    # ... other fields

class EvaluationItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sheet_id: str
    criteria: str
    score: Optional[int] = None
    comment: Optional[str] = None
    # ... other fields

class Submission(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sheet_id: str
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    # ... other fields

class FileUploadResponse(BaseModel):
    filename: str
    file_id: str
    file_url: str
    content_type: str
    size: int

class Notification(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    message: str
    type: str = Field("info") # info, warning, error, success
    is_read: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CacheStatus(BaseModel):
    status: str
    keys_count: Optional[int] = None
    memory_usage: Optional[str] = None

class SystemLoad(BaseModel):
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    
class ServiceStatus(BaseModel):
    name: str
    status: str # e.g., "healthy", "unhealthy", "degraded"
    details: Optional[str] = None
    
class HealthCheckResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
    services: List[ServiceStatus]
    system_load: Optional[SystemLoad] = None
    cache_status: Optional[CacheStatus] = None
    
class ExportRequest(BaseModel):
    project_id: str
    format: str = Field("excel", description="Export format: excel, csv, pdf")
    data_scope: str = Field("all", description="all, summary, detailed_scores")

class ExportStatusResponse(BaseModel):
    task_id: str
    status: str # pending, processing, completed, failed
    file_url: Optional[str] = None
    error_message: Optional[str] = None
    
class AdminDashboardData(BaseModel):
    total_users: int
    active_users: int
    pending_secretaries: int
    total_projects: int
    ongoing_projects: int
    completed_projects: int
    # Add more fields as needed
    
class UserActivityLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    action: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: Optional[Dict[str, Any]] = None
    
class SystemConfiguration(BaseModel):
    setting_name: str
    setting_value: Any
    description: Optional[str] = None
    
class BackupStatus(BaseModel):
    last_backup_time: Optional[datetime] = None
    status: str # e.g., "success", "failed", "in_progress"
    next_backup_scheduled: Optional[datetime] = None
    
class AdvancedSearchQuery(BaseModel):
    keywords: str
    search_in: List[str] # e.g., ["projects", "users", "evaluations"]
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    filters: Optional[Dict[str, Any]] = None # e.g., {"role": "evaluator", "project_status": "completed"}

class AdvancedSearchResult(BaseModel):
    type: str # "project", "user", "evaluation"
    id: str
    summary: str
    score: Optional[float] = None # Relevance score
    # ... other common fields or a union of result types
    
class BulkUserImportRow(BaseModel):
    login_id: str
    user_name: str
    email: str  # Changed from EmailStr to str
    phone: Optional[str] = None
    role: str
    password: Optional[str] = None # If provided, will be used. Otherwise, auto-generated.

class BulkUserImportRequest(BaseModel):
    users: List[BulkUserImportRow]

class BulkUserImportResult(BaseModel):
    success_count: int
    failed_count: int
    errors: List[Dict[str, Any]] # e.g., {"row_index": 1, "login_id": "test", "error": "Duplicate login_id"}

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

class PasswordResetRequest(BaseModel):
    email: str  # Changed from EmailStr to str

class TwoFactorAuthSetupResponse(BaseModel):
    qr_code_url: Optional[str] = None # For TOTP
    secret_key: Optional[str] = None # For TOTP
    backup_codes: Optional[List[str]] = None
    status: str # e.g., "enabled", "disabled", "setup_required"

class TwoFactorAuthVerifyRequest(BaseModel):
    token: str # TOTP token or backup code
    
class APIToken(BaseModel): # For machine-to-machine communication if needed
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str # The user this token belongs to
    token_hash: str
    prefix: str # First few chars of the token, for display
    scopes: List[str] = Field(default_factory=list) # e.g., ["read:projects", "write:evaluations"]
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    description: Optional[str] = None
    
class APITokenCreateRequest(BaseModel):
    description: Optional[str] = None
    scopes: List[str] = Field(default_factory=list)
    expires_in_days: Optional[int] = None # e.g., 30, 90, or None for no expiry

class APITokenCreateResponse(BaseModel):
    plain_token: str # The actual token, show only once
    token_info: APIToken # The stored token metadata (without plain_token)

class EvaluationCriteria(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    max_score: int
    category: Optional[str] = None # e.g., "Technical", "Financial"
    is_active: bool = True

# Update EvaluationTemplate model to include more fields
class EvaluationTemplate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    name: str = Field(..., description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    project_id: str = Field(..., description="Project ID this template belongs to")
    items: List[Dict[str, Any]] = Field(default_factory=list, description="Evaluation criteria items")
    created_by: str = Field(..., description="User ID who created the template")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_default: bool = Field(False, description="Whether this is a default template")
    status: str = Field("draft", description="Template status: draft, active, archived")

    class Config:
        allow_population_by_field_name = True
        json_encoders = {datetime: lambda dt: dt.isoformat()}

class EvaluationCriterionEnhanced(BaseModel):
    """향상된 평가 기준 모델 (사업별 지표 및 가점 관리용)"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="기준 ID")
    name: str = Field(..., description="평가 항목명")
    description: Optional[str] = Field(None, description="항목 설명")
    max_score: int = Field(..., description="최대 점수")
    min_score: int = Field(0, description="최소 점수")
    weight: float = Field(1.0, description="가중치")
    bonus: bool = Field(False, description="가점 항목 여부")
    category: Optional[str] = Field(None, description="기준 카테고리 (기술성, 사업성, 혁신성 등)")
    is_required: bool = Field(True, description="필수 항목 여부")
    evaluation_guide: Optional[str] = Field(None, description="평가 가이드라인")
    order: int = Field(0, description="표시 순서")

class EvaluationTemplateEnhanced(BaseModel):
    """향상된 평가 템플릿 모델 (사업별 지표 및 가점 관리용)"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    name: str = Field(..., description="템플릿 이름")
    description: Optional[str] = Field(None, description="템플릿 설명")
    project_id: str = Field(..., description="프로젝트 ID")
    category: Optional[str] = Field(None, description="템플릿 카테고리 (스타트업, 혁신기술, R&D 등)")
    
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

# Add Assignment models for evaluation assignment functionality
class AssignmentCreate(BaseModel):
    evaluator_ids: List[str] = Field(..., description="List of evaluator user IDs")
    company_ids: List[str] = Field(..., description="List of company IDs")
    template_id: str = Field(..., description="Evaluation template ID")
    deadline: Optional[datetime] = Field(None, description="Assignment deadline")

class BatchAssignmentCreate(BaseModel):
    assignments: List[AssignmentCreate] = Field(..., description="List of assignments to create")

class EvaluationScore(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    sheet_id: str = Field(..., description="Evaluation sheet ID")
    item_id: str = Field(..., description="Evaluation item ID")
    score: int = Field(..., description="Score value")
    opinion: Optional[str] = Field(None, description="Evaluator's opinion/comment")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        json_encoders = {datetime: lambda dt: dt.isoformat()}

class EvaluationSubmission(BaseModel):
    sheet_id: str = Field(..., description="Evaluation sheet ID")
    scores: List[Dict[str, Any]] = Field(..., description="List of scores with item_id, score, and opinion")
    overall_comment: Optional[str] = Field(None, description="Overall evaluation comment")
    
class AssignedEvaluation(BaseModel): # Represents an evaluation assigned to an evaluator for a company in a project
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    company_id: str
    evaluator_id: str
    template_id: str # EvaluationTemplate ID
    status: str = Field("pending") # pending, in_progress, submitted, reviewed
    due_date: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    scores: Optional[Dict[str, int]] = None # {criteria_id: score}
    comments: Optional[Dict[str, str]] = None # {criteria_id: comment}
    overall_comment: Optional[str] = None
    
class ProjectStatistics(BaseModel):
    project_id: str
    total_assigned_evaluations: int
    completed_evaluations: int
    average_score: Optional[float] = None
    # Add more stats as needed
    
class UserProfile(UserResponse): # Extends UserResponse with more details
    profile_picture_url: Optional[str] = None
    bio: Optional[str] = None
    department: Optional[str] = None
    # Add other profile fields
    
class AuditLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None # Can be system action
    action: str # e.g., "USER_LOGIN", "PROJECT_CREATE", "EVALUATION_SUBMIT"
    target_type: Optional[str] = None # e.g., "User", "Project", "Evaluation"
    target_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None # e.g., {"ip_address": "1.2.3.4", "old_value": "X", "new_value": "Y"}
    status: str = Field("success") # success, failure
    
class Report(BaseModel): # For generating various reports
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    report_type: str # e.g., "PROJECT_SUMMARY", "EVALUATOR_PERFORMANCE"
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    generated_by: str # User ID
    filters: Optional[Dict[str, Any]] = None
    data: Any # The actual report data, could be complex
    file_url: Optional[str] = None # If report is generated as a file
    
class Message(BaseModel): # For simple API responses
    message: str
    details: Optional[Any] = None
    
class ErrorDetail(BaseModel):
    loc: Optional[List[str]] = None
    msg: str
    type: str

class HTTPValidationError(BaseModel):
    detail: List[ErrorDetail]

class SystemStats(BaseModel):
    uptime_seconds: float
    cpu_load_avg: List[float] # 1, 5, 15 min avg
    memory_usage_mb: float
    disk_space_free_gb: float
    active_connections: int
    db_ping_ms: Optional[float] = None
    cache_ping_ms: Optional[float] = None
    
class Feedback(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None # Anonymous feedback possible
    email: Optional[str] = None # If user provides it  # Changed from EmailStr to str
    feedback_type: str # e.g., "bug_report", "feature_request", "general"
    subject: str
    message: str
    page_url: Optional[str] = None # URL where feedback was submitted
    user_agent: Optional[str] = None
    status: str = Field("new") # new, acknowledged, in_progress, resolved, closed
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
class Announcement(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
    audience: List[str] = Field(default_factory=lambda: ["all"]) # "all", "admin", "secretary", "evaluator"
    start_date: datetime
    end_date: Optional[datetime] = None
    is_active: bool = True
    created_by: str # User ID
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserPreferences(BaseModel):
    user_id: str
    theme: str = Field("light") # "light", "dark"
    language: str = Field("ko") # "ko", "en"
    notifications_enabled: bool = True
    email_notifications: Dict[str, bool] = Field(default_factory=lambda: {
        "project_updates": True,
        "evaluation_assignments": True,
        "system_announcements": True
    })
    # Add more preferences as needed
    
class LoginActivity(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    ip_address: str
    user_agent: str
    status: str # "success", "failure_password", "failure_user_not_found", "failure_2fa"
    
class DataExportJob(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    export_type: str # e.g., "all_user_data", "project_archive"
    format: str # "json", "csv", "zip"
    status: str = Field("pending") # pending, processing, completed, failed
    file_url: Optional[str] = None
    error_message: Optional[str] = None
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

class DataImportJob(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    import_type: str # e.g., "bulk_users", "project_data"
    source_file_url: str
    status: str = Field("pending") # pending, processing, completed, failed, partial_success
    results: Optional[Dict[str, Any]] = None # e.g., {"created": 10, "updated": 5, "failed": 2, "errors": [...]}
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

class WebSocketMessage(BaseModel):
    type: str # e.g., "notification", "progress_update", "chat_message"
    payload: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ChatRoom(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    participant_ids: List[str] # User IDs
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_message_at: Optional[datetime] = None

class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    room_id: str
    sender_id: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    is_read_by: List[str] = Field(default_factory=list) # User IDs who have read the message
    
class SearchFilter(BaseModel):
    field: str
    operator: str # eq, ne, gt, lt, gte, lte, contains, starts_with, ends_with
    value: Any

class SearchSort(BaseModel):
    field: str
    direction: str = Field("asc") # asc, desc

class PaginatedRequest(BaseModel):
    page: int = Field(1, ge=1)
    per_page: int = Field(10, ge=1, le=100)
    filters: Optional[List[SearchFilter]] = None
    sort_by: Optional[List[SearchSort]] = None

class PaginatedResponse(BaseModel):
    total_items: int
    total_pages: int
    page: int
    per_page: int
    items: List[Any] # Should be parameterized with the actual item type, e.g., List[UserResponse]
    
# Example of a paginated response for users
class PaginatedUserResponse(PaginatedResponse):
    items: List[UserResponse]

class PaginatedProjectResponse(PaginatedResponse):
    items: List[Project]
    
# Add more specific paginated responses as needed

# Evaluation related models for the new evaluation system

class EvaluationCriterion(BaseModel):
    """평가 항목 (기준) 모델"""
    name: str = Field(..., description="평가 항목명")
    max_score: int = Field(..., description="최대 점수")
    bonus: bool = Field(False, description="가점 항목 여부")
    description: Optional[str] = Field(None, description="항목 설명")

class EvaluationBase(BaseModel):
    """평가 프로젝트 기본 모델"""
    title: str = Field(..., description="평가 제목")
    description: Optional[str] = Field("", description="평가 설명")
    companies: List[str] = Field(..., description="대상 기업 목록")
    criteria: List[EvaluationCriterion] = Field(..., description="평가 항목 리스트")
    status: str = Field("draft", description="평가 상태 (draft, active, completed)")

class EvaluationCreate(EvaluationBase):
    """평가 생성 요청 모델"""
    pass

class Evaluation(EvaluationBase):
    """평가 프로젝트 모델"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    created_by: str = Field(..., description="생성자 사용자 ID")
    assigned_evaluators: List[str] = Field(default_factory=list, description="배정된 평가위원 ID 목록")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        validate_by_name = True
        allow_population_by_field_name = True
        json_encoders = {datetime: lambda dt: dt.isoformat()}
        from_attributes = True

    @classmethod
    def from_mongo(cls, data: dict):
        """MongoDB 문서를 Evaluation 객체로 변환"""
        if data and "_id" in data:
            data = data.copy()
            data["id"] = str(data.pop("_id"))
        return cls(**data) if data else None

class ScoreSubmission(BaseModel):
    """평가 점수 제출 모델"""
    evaluation_id: str = Field(..., description="평가 ID")
    company_id: str = Field(..., description="기업 ID (또는 기업명)")
    evaluator_id: str = Field(..., description="평가위원 ID")
    scores: Dict[str, int] = Field(..., description="항목별 점수 (항목명: 점수)")
    comment: Optional[str] = Field("", description="평가 코멘트")
    total_score: int = Field(0, description="총점")
    submitted_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        validate_by_name = True
        allow_population_by_field_name = True
        json_encoders = {datetime: lambda dt: dt.isoformat()}

class ScoreSubmissionCreate(BaseModel):
    """점수 제출 요청 모델"""
    companyId: str = Field(..., alias="company_id", description="기업 ID")
    scores: Dict[str, int] = Field(..., description="항목별 점수")
    comment: Optional[str] = Field("", description="평가 코멘트")

    class Config:
        allow_population_by_field_name = True

# AI 공급자 관리 모델들
class AIProviderConfig(BaseModel):
    """AI 공급자 설정 모델"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    provider_name: str = Field(..., description="AI 공급자명 (openai, anthropic, google, groq)")
    display_name: str = Field(..., description="표시할 공급자명")
    api_key: str = Field(..., description="API 키 (암호화 저장)")
    api_endpoint: Optional[str] = Field(None, description="커스텀 API 엔드포인트")
    is_active: bool = Field(True, description="활성화 여부")
    priority: int = Field(1, description="우선순위 (1이 가장 높음)")
    max_tokens: Optional[int] = Field(None, description="최대 토큰 수")
    temperature: float = Field(0.3, description="기본 temperature 설정")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(..., description="설정한 관리자 ID")
    
    class Config:
        allow_population_by_field_name = True
        json_encoders = {datetime: lambda dt: dt.isoformat()}
        from_attributes = True
    
    @classmethod
    def from_mongo(cls, data: dict):
        """MongoDB 문서를 AIProviderConfig 객체로 변환"""
        if data and "_id" in data:
            data = data.copy()
            data["id"] = str(data.pop("_id"))
        return cls(**data) if data else None
    
    def to_mongo(self) -> dict:
        """AIProviderConfig 객체를 MongoDB 문서로 변환"""
        data = self.dict(by_alias=True, exclude_unset=True)
        if "id" in data and data["id"]:
            data["_id"] = data.pop("id")
        return data

class AIModelConfig(BaseModel):
    """AI 모델 설정 모델"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    provider_id: str = Field(..., description="AI 공급자 ID")
    model_name: str = Field(..., description="모델명 (gpt-4, claude-3-haiku, gemini-pro)")
    display_name: str = Field(..., description="표시할 모델명")
    model_type: str = Field(..., description="모델 타입 (chat, completion, embedding)")
    is_default: bool = Field(False, description="기본 모델 여부")
    is_active: bool = Field(True, description="활성화 여부")
    max_tokens: Optional[int] = Field(None, description="최대 토큰 수")
    cost_per_1k_tokens: Optional[float] = Field(None, description="1K 토큰당 비용")
    capabilities: List[str] = Field(default_factory=list, description="지원 기능 목록")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        allow_population_by_field_name = True
        json_encoders = {datetime: lambda dt: dt.isoformat()}

class AIProviderConfigCreate(BaseModel):
    """AI 공급자 설정 생성 요청 모델"""
    provider_name: str = Field(..., description="AI 공급자명")
    display_name: str = Field(..., description="표시할 공급자명")
    api_key: str = Field(..., description="API 키")
    api_endpoint: Optional[str] = Field(None, description="커스텀 API 엔드포인트")
    is_active: bool = Field(True, description="활성화 여부")
    priority: int = Field(1, description="우선순위")
    max_tokens: Optional[int] = Field(None, description="최대 토큰 수")
    temperature: float = Field(0.3, description="기본 temperature 설정")

class AIProviderConfigUpdate(BaseModel):
    """AI 공급자 설정 업데이트 요청 모델"""
    display_name: Optional[str] = Field(None, description="표시할 공급자명")
    api_key: Optional[str] = Field(None, description="API 키")
    api_endpoint: Optional[str] = Field(None, description="커스텀 API 엔드포인트")
    is_active: Optional[bool] = Field(None, description="활성화 여부")
    priority: Optional[int] = Field(None, description="우선순위")
    max_tokens: Optional[int] = Field(None, description="최대 토큰 수")
    temperature: Optional[float] = Field(None, description="기본 temperature 설정")

class AIServiceStatus(BaseModel):
    """AI 서비스 상태 모델"""
    provider_statuses: List[Dict[str, Any]] = Field(default_factory=list, description="공급자별 상태")
    active_providers: int = Field(0, description="활성화된 공급자 수")
    total_providers: int = Field(0, description="전체 공급자 수")
    default_provider: Optional[str] = Field(None, description="기본 공급자")
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class AIAnalysisJob(BaseModel):
    """AI 분석 작업 모델"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    user_id: str = Field(..., description="요청자 ID")
    job_type: str = Field(..., description="작업 타입 (document_analysis, score_suggestion, plagiarism_check)")
    input_data: Dict[str, Any] = Field(..., description="입력 데이터")
    status: str = Field("pending", description="작업 상태 (pending, processing, completed, failed)")
    provider_used: Optional[str] = Field(None, description="사용된 AI 공급자")
    model_used: Optional[str] = Field(None, description="사용된 모델")
    result_data: Optional[Dict[str, Any]] = Field(None, description="결과 데이터")
    error_message: Optional[str] = Field(None, description="오류 메시지")
    processing_time: Optional[float] = Field(None, description="처리 시간(초)")
    tokens_used: Optional[int] = Field(None, description="사용된 토큰 수")
    cost: Optional[float] = Field(None, description="비용")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(None, description="완료 시간")
    
    class Config:
        allow_population_by_field_name = True
        json_encoders = {datetime: lambda dt: dt.isoformat()}

class AIUsageStatistics(BaseModel):
    """AI 사용 통계 모델"""
    period: str = Field(..., description="기간 (daily, weekly, monthly)")
    date: datetime = Field(..., description="날짜")
    provider_usage: Dict[str, int] = Field(default_factory=dict, description="공급자별 사용 횟수")
    total_requests: int = Field(0, description="총 요청 수")
    total_tokens: int = Field(0, description="총 토큰 사용량")
    total_cost: float = Field(0.0, description="총 비용")
    success_rate: float = Field(0.0, description="성공률")
    average_response_time: float = Field(0.0, description="평균 응답 시간")

class AIProviderTestRequest(BaseModel):
    """AI 공급자 테스트 요청 모델"""
    provider_name: str = Field(..., description="테스트할 공급자명")
    api_key: str = Field(..., description="테스트할 API 키")
    test_prompt: str = Field("Hello, this is a test message.", description="테스트 프롬프트")
