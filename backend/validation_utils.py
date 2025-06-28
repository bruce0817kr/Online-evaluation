"""
Validation utilities for input validation and error handling
"""
import re
from typing import Any, Dict, List, Optional
from fastapi import HTTPException
from pydantic import BaseModel, ValidationError
import logging

logger = logging.getLogger(__name__)

class ValidationResult:
    """Result of validation with detailed error information"""
    def __init__(self, is_valid: bool = True, errors: List[Dict[str, Any]] = None):
        self.is_valid = is_valid
        self.errors = errors or []
    
    def add_error(self, field: str, message: str, code: str = "validation_error"):
        """Add validation error"""
        self.is_valid = False
        self.errors.append({
            "field": field,
            "message": message,
            "code": code
        })
    
    def raise_if_invalid(self, status_code: int = 422):
        """Raise HTTPException if validation failed"""
        if not self.is_valid:
            error_details = {
                "message": "입력 데이터가 올바르지 않습니다.",
                "errors": self.errors
            }
            raise HTTPException(status_code=status_code, detail=error_details)

def validate_email(email: str) -> bool:
    """Validate email format"""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email) is not None

def validate_phone(phone: str) -> bool:
    """Validate Korean phone number format"""
    # Remove all non-digits
    digits_only = re.sub(r'\D', '', phone)
    
    # Check if it's a valid Korean phone number
    if len(digits_only) == 11 and digits_only.startswith('010'):
        return True
    elif len(digits_only) == 10 and digits_only.startswith(('02', '031', '032', '033', '041', '042', '043', '044', '051', '052', '053', '054', '055', '061', '062', '063', '064')):
        return True
    
    return False

def validate_password_strength(password: str) -> ValidationResult:
    """Validate password strength"""
    result = ValidationResult()
    
    if len(password) < 8:
        result.add_error("password", "비밀번호는 최소 8자 이상이어야 합니다.", "password_too_short")
    
    if len(password) > 128:
        result.add_error("password", "비밀번호는 128자를 초과할 수 없습니다.", "password_too_long")
    
    if not re.search(r'[A-Za-z]', password):
        result.add_error("password", "비밀번호에는 영문자가 포함되어야 합니다.", "password_missing_letter")
    
    if not re.search(r'\d', password):
        result.add_error("password", "비밀번호에는 숫자가 포함되어야 합니다.", "password_missing_number")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        result.add_error("password", "비밀번호에는 특수문자가 포함되어야 합니다.", "password_missing_special")
    
    return result

def validate_user_role(role: str) -> bool:
    """Validate user role"""
    valid_roles = {"admin", "secretary", "evaluator"}
    return role in valid_roles

def validate_file_size(size: int, max_size: int = 50 * 1024 * 1024) -> ValidationResult:
    """Validate file size (default max: 50MB)"""
    result = ValidationResult()
    
    if size <= 0:
        result.add_error("file", "파일이 비어있습니다.", "file_empty")
    elif size > max_size:
        max_mb = max_size / (1024 * 1024)
        result.add_error("file", f"파일 크기가 {max_mb:.1f}MB를 초과합니다.", "file_too_large")
    
    return result

def validate_file_extension(filename: str, allowed_extensions: set = None) -> ValidationResult:
    """Validate file extension"""
    result = ValidationResult()
    
    if allowed_extensions is None:
        allowed_extensions = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.txt', '.png', '.jpg', '.jpeg'}
    
    if not filename:
        result.add_error("filename", "파일명이 없습니다.", "filename_missing")
        return result
    
    file_extension = filename.lower().split('.')[-1] if '.' in filename else ''
    if not file_extension:
        result.add_error("filename", "파일 확장자가 없습니다.", "extension_missing")
    elif f'.{file_extension}' not in allowed_extensions:
        allowed_str = ', '.join(sorted(allowed_extensions))
        result.add_error("filename", f"지원하지 않는 파일 형식입니다. 허용된 형식: {allowed_str}", "extension_not_allowed")
    
    return result

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent directory traversal and other security issues"""
    if not filename:
        return "unnamed_file"
    
    # Remove path separators and dangerous characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    filename = re.sub(r'\.\.+', '.', filename)  # Remove multiple dots
    filename = filename.strip('. ')  # Remove leading/trailing dots and spaces
    
    # Ensure filename is not empty after sanitization
    if not filename:
        return "unnamed_file"
    
    return filename

def validate_object_id(obj_id: str, field_name: str = "id") -> ValidationResult:
    """Validate ObjectId format (24 character hex string)"""
    result = ValidationResult()
    
    if not obj_id:
        result.add_error(field_name, f"{field_name}가 제공되지 않았습니다.", "missing_id")
    elif not isinstance(obj_id, str):
        result.add_error(field_name, f"{field_name}는 문자열이어야 합니다.", "invalid_id_type")
    elif len(obj_id) != 24 or not re.match(r'^[a-fA-F0-9]{24}$', obj_id):
        result.add_error(field_name, f"올바르지 않은 {field_name} 형식입니다.", "invalid_id_format")
    
    return result

def validate_pagination(skip: int = 0, limit: int = 100) -> ValidationResult:
    """Validate pagination parameters"""
    result = ValidationResult()
    
    if skip < 0:
        result.add_error("skip", "skip 값은 0 이상이어야 합니다.", "invalid_skip")
    
    if limit < 1:
        result.add_error("limit", "limit 값은 1 이상이어야 합니다.", "invalid_limit")
    elif limit > 1000:
        result.add_error("limit", "limit 값은 1000을 초과할 수 없습니다.", "limit_too_large")
    
    return result

def validate_date_range(start_date: Optional[str], end_date: Optional[str]) -> ValidationResult:
    """Validate date range"""
    result = ValidationResult()
    
    if start_date and end_date:
        try:
            from datetime import datetime
            start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            
            if start > end:
                result.add_error("date_range", "시작 날짜는 종료 날짜보다 빨라야 합니다.", "invalid_date_range")
        except ValueError:
            result.add_error("date_format", "날짜 형식이 올바르지 않습니다.", "invalid_date_format")
    
    return result

def validate_pydantic_model(data: Dict[str, Any], model_class: BaseModel) -> ValidationResult:
    """Validate data against Pydantic model"""
    result = ValidationResult()
    
    try:
        model_class(**data)
    except ValidationError as e:
        for error in e.errors():
            field = '.'.join(str(loc) for loc in error['loc'])
            message = error['msg']
            result.add_error(field, message, error['type'])
    except Exception as e:
        result.add_error("validation", f"검증 중 오류가 발생했습니다: {str(e)}", "validation_error")
    
    return result

class DatabaseError(Exception):
    """Custom exception for database-related errors"""
    def __init__(self, message: str, operation: str = "", collection: str = ""):
        self.message = message
        self.operation = operation
        self.collection = collection
        super().__init__(self.message)

def handle_database_error(func):
    """Decorator to handle database errors gracefully"""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Database error in {func.__name__}: {e}")
            
            # Map specific database errors to user-friendly messages
            if "connection" in str(e).lower():
                raise HTTPException(status_code=503, detail="데이터베이스 연결에 문제가 있습니다.")
            elif "duplicate" in str(e).lower():
                raise HTTPException(status_code=409, detail="이미 존재하는 데이터입니다.")
            elif "not found" in str(e).lower():
                raise HTTPException(status_code=404, detail="요청한 데이터를 찾을 수 없습니다.")
            else:
                raise HTTPException(status_code=500, detail="데이터베이스 오류가 발생했습니다.")
    
    return wrapper

def validate_search_query(query: str, max_length: int = 100) -> ValidationResult:
    """Validate search query"""
    result = ValidationResult()
    
    if len(query) > max_length:
        result.add_error("search", f"검색어는 {max_length}자를 초과할 수 없습니다.", "search_too_long")
    
    # Check for potentially dangerous patterns
    dangerous_patterns = ['<script', 'javascript:', 'data:', 'vbscript:']
    query_lower = query.lower()
    for pattern in dangerous_patterns:
        if pattern in query_lower:
            result.add_error("search", "허용되지 않는 검색어가 포함되어 있습니다.", "search_dangerous")
            break
    
    return result

# Common validation combinations
def validate_user_input(user_data: Dict[str, Any]) -> ValidationResult:
    """Comprehensive user input validation"""
    result = ValidationResult()
    
    # Email validation
    if 'email' in user_data:
        if not validate_email(user_data['email']):
            result.add_error("email", "올바른 이메일 형식이 아닙니다.", "invalid_email")
    
    # Phone validation
    if 'phone' in user_data:
        if not validate_phone(user_data['phone']):
            result.add_error("phone", "올바른 전화번호 형식이 아닙니다.", "invalid_phone")
    
    # Role validation
    if 'role' in user_data:
        if not validate_user_role(user_data['role']):
            result.add_error("role", "올바르지 않은 사용자 권한입니다.", "invalid_role")
    
    # Password validation
    if 'password' in user_data:
        password_result = validate_password_strength(user_data['password'])
        if not password_result.is_valid:
            result.errors.extend(password_result.errors)
            result.is_valid = False
    
    return result