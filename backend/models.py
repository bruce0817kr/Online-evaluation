from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

class Token(BaseModel):
    access_token: str
    token_type: str
    user: Optional['UserResponse'] # Use forward reference for UserResponse

class UserBase(BaseModel):
    login_id: str = Field(..., description="User's login ID")
    email: EmailStr = Field(..., description="User's email address")
    user_name: str = Field(..., description="User's full name")
    phone: Optional[str] = Field(None, description="User's phone number")
    role: str = Field(..., description="User's role (admin, secretary, evaluator)")
    is_active: bool = Field(True, description="Whether the user account is active")
    
class UserCreate(UserBase):
    password: str = Field(..., description="User's password (plain text)")

class User(UserBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id", description="User's unique ID")
    password_hash: str = Field(..., description="User's hashed password")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of user creation")
    last_login: Optional[datetime] = Field(None, description="Timestamp of last login")
    
    class Config:
        validate_by_name = True # Pydantic V2 (renamed from allow_population_by_field_name)
        json_encoders = {datetime: lambda dt: dt.isoformat()}
        from_attributes = True # For Pydantic V2 (renamed from orm_mode)

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
    email: EmailStr
    reason: Optional[str] = None

class SecretaryApproval(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    name: str
    phone: str
    email: EmailStr
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
    email: EmailStr
    # Add other fields as necessary based on usage in server.py

class ProjectBase(BaseModel):
    name: str = Field(..., description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class ProjectCreate(ProjectBase):
    pass

class Project(ProjectBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None # User ID

    class Config:
        allow_population_by_field_name = True
        json_encoders = {datetime: lambda dt: dt.isoformat()}
        
class CompanyBase(BaseModel):
    name: str = Field(..., description="Company name")
    registration_number: Optional[str] = Field(None, description="Company registration number")
    address: Optional[str] = Field(None, description="Company address")

class CompanyCreate(CompanyBase):
    pass

class Company(CompanyBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        json_encoders = {datetime: lambda dt: dt.isoformat()}

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
    email: EmailStr
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
    email: EmailStr

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

class EvaluationTemplate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    criteria_ids: List[str] # List of EvaluationCriteria IDs
    created_by: str # User ID
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_default: bool = False
    
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
    email: Optional[EmailStr] = None # If user provides it
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
