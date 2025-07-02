"""
Advanced Error Handling and Custom Exception System
Provides structured error responses, logging, and monitoring
"""

import os
import sys
import traceback
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException
import motor.motor_asyncio

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Error categories for better classification"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    VALIDATION = "validation"
    BUSINESS_LOGIC = "business_logic"
    EXTERNAL_SERVICE = "external_service"
    DATABASE = "database"
    SYSTEM = "system"
    SECURITY = "security"

class ErrorDetail(BaseModel):
    """Detailed error information"""
    field: Optional[str] = None
    message: str
    code: Optional[str] = None
    value: Optional[Any] = None

class StandardErrorResponse(BaseModel):
    """Standardized error response format"""
    error: bool = True
    error_code: str
    message: str
    details: Optional[List[ErrorDetail]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    category: ErrorCategory = ErrorCategory.SYSTEM
    support_reference: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class CustomAPIException(HTTPException):
    """Custom API exception with enhanced error information"""
    
    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        details: Optional[List[ErrorDetail]] = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        headers: Optional[Dict[str, str]] = None,
        log_error: bool = True
    ):
        super().__init__(status_code=status_code, detail=message, headers=headers)
        self.error_code = error_code
        self.message = message
        self.details = details or []
        self.severity = severity
        self.category = category
        
        if log_error:
            self._log_error()
    
    def _log_error(self):
        """Log error based on severity"""
        log_message = f"API Error [{self.error_code}]: {self.message}"
        
        if self.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message)
        elif self.severity == ErrorSeverity.HIGH:
            logger.error(log_message)
        elif self.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message)
        else:
            logger.info(log_message)

class BusinessLogicError(CustomAPIException):
    """Business logic validation errors"""
    
    def __init__(self, message: str, error_code: str = "BUSINESS_LOGIC_ERROR", **kwargs):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code=error_code,
            message=message,
            category=ErrorCategory.BUSINESS_LOGIC,
            **kwargs
        )

class DatabaseError(CustomAPIException):
    """Database operation errors"""
    
    def __init__(self, message: str, error_code: str = "DATABASE_ERROR", **kwargs):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=error_code,
            message=message,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.DATABASE,
            **kwargs
        )

class AuthenticationError(CustomAPIException):
    """Authentication errors"""
    
    def __init__(self, message: str = "Authentication failed", error_code: str = "AUTH_FAILED", **kwargs):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code=error_code,
            message=message,
            category=ErrorCategory.AUTHENTICATION,
            headers={"WWW-Authenticate": "Bearer"},
            **kwargs
        )

class AuthorizationError(CustomAPIException):
    """Authorization errors"""
    
    def __init__(self, message: str = "Insufficient permissions", error_code: str = "INSUFFICIENT_PERMISSIONS", **kwargs):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code=error_code,
            message=message,
            category=ErrorCategory.AUTHORIZATION,
            **kwargs
        )

class ValidationError(CustomAPIException):
    """Input validation errors"""
    
    def __init__(self, message: str, details: List[ErrorDetail] = None, error_code: str = "VALIDATION_ERROR", **kwargs):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code=error_code,
            message=message,
            details=details,
            category=ErrorCategory.VALIDATION,
            **kwargs
        )

class ExternalServiceError(CustomAPIException):
    """External service integration errors"""
    
    def __init__(self, service_name: str, message: str = None, error_code: str = "EXTERNAL_SERVICE_ERROR", **kwargs):
        if not message:
            message = f"External service {service_name} is currently unavailable"
        
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code=error_code,
            message=message,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.EXTERNAL_SERVICE,
            **kwargs
        )

class SecurityError(CustomAPIException):
    """Security-related errors"""
    
    def __init__(self, message: str, error_code: str = "SECURITY_VIOLATION", **kwargs):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code=error_code,
            message=message,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.SECURITY,
            **kwargs
        )

class ErrorLogger:
    """Enhanced error logging and monitoring"""
    
    def __init__(self, database_client=None):
        self.db = database_client.online_evaluation if database_client else None
        self.error_stats = {
            "total_errors": 0,
            "error_counts": {},
            "category_counts": {},
            "severity_counts": {}
        }
    
    async def log_error(self, error: CustomAPIException, request: Request = None, 
                       request_id: str = None, user_id: str = None):
        """Log error with full context"""
        error_record = {
            "error_code": error.error_code,
            "message": error.message,
            "status_code": error.status_code,
            "severity": error.severity.value,
            "category": error.category.value,
            "details": [detail.dict() for detail in error.details] if error.details else [],
            "timestamp": datetime.utcnow(),
            "request_id": request_id,
            "user_id": user_id
        }
        
        # Add request context if available
        if request:
            error_record.update({
                "method": request.method,
                "url": str(request.url),
                "headers": dict(request.headers),
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent")
            })
        
        # Log to database if available
        if self.db:
            try:
                await self.db.error_logs.insert_one(error_record)
            except Exception as e:
                logger.error(f"Failed to log error to database: {e}")
        
        # Update statistics
        self._update_error_stats(error)
        
        # Log to file
        self._log_to_file(error_record)
    
    def _update_error_stats(self, error: CustomAPIException):
        """Update error statistics"""
        self.error_stats["total_errors"] += 1
        
        # Count by error code
        code = error.error_code
        self.error_stats["error_counts"][code] = self.error_stats["error_counts"].get(code, 0) + 1
        
        # Count by category
        category = error.category.value
        self.error_stats["category_counts"][category] = self.error_stats["category_counts"].get(category, 0) + 1
        
        # Count by severity
        severity = error.severity.value
        self.error_stats["severity_counts"][severity] = self.error_stats["severity_counts"].get(severity, 0) + 1
    
    def _log_to_file(self, error_record: Dict[str, Any]):
        """Log error to file"""
        log_level = {
            ErrorSeverity.LOW.value: logging.INFO,
            ErrorSeverity.MEDIUM.value: logging.WARNING,
            ErrorSeverity.HIGH.value: logging.ERROR,
            ErrorSeverity.CRITICAL.value: logging.CRITICAL
        }.get(error_record["severity"], logging.ERROR)
        
        logger.log(
            log_level,
            f"Error [{error_record['error_code']}]: {error_record['message']} "
            f"| Status: {error_record['status_code']} "
            f"| Category: {error_record['category']} "
            f"| Request: {error_record.get('method', 'N/A')} {error_record.get('url', 'N/A')}"
        )
    
    async def get_error_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get error statistics for the specified time period"""
        if not self.db:
            return self.error_stats
        
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        try:
            # Aggregate errors by category
            category_pipeline = [
                {"$match": {"timestamp": {"$gte": start_time}}},
                {"$group": {"_id": "$category", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            
            # Aggregate errors by severity
            severity_pipeline = [
                {"$match": {"timestamp": {"$gte": start_time}}},
                {"$group": {"_id": "$severity", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            
            # Get top error codes
            error_codes_pipeline = [
                {"$match": {"timestamp": {"$gte": start_time}}},
                {"$group": {"_id": "$error_code", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 10}
            ]
            
            category_stats = await self.db.error_logs.aggregate(category_pipeline).to_list(None)
            severity_stats = await self.db.error_logs.aggregate(severity_pipeline).to_list(None)
            error_code_stats = await self.db.error_logs.aggregate(error_codes_pipeline).to_list(None)
            
            return {
                "time_period_hours": hours,
                "categories": {item["_id"]: item["count"] for item in category_stats},
                "severities": {item["_id"]: item["count"] for item in severity_stats},
                "top_error_codes": {item["_id"]: item["count"] for item in error_code_stats},
                "total_errors": sum(item["count"] for item in category_stats)
            }
        
        except Exception as e:
            logger.error(f"Failed to get error statistics: {e}")
            return self.error_stats

# Global error logger instance
error_logger = ErrorLogger()

def initialize_error_logger(database_client):
    """Initialize error logger with database client"""
    global error_logger
    error_logger = ErrorLogger(database_client)

class ErrorHandlers:
    """Collection of error handlers for FastAPI"""
    
    @staticmethod
    def get_request_id(request: Request) -> str:
        """Generate or get request ID"""
        return request.headers.get("X-Request-ID", f"req_{datetime.utcnow().timestamp()}")
    
    @staticmethod
    async def custom_api_exception_handler(request: Request, exc: CustomAPIException) -> JSONResponse:
        """Handle custom API exceptions"""
        request_id = ErrorHandlers.get_request_id(request)
        
        # Log error
        await error_logger.log_error(exc, request, request_id)
        
        # Create response
        error_response = StandardErrorResponse(
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details,
            request_id=request_id,
            severity=exc.severity,
            category=exc.category,
            support_reference=f"REF-{request_id[-8:]}"
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.dict(),
            headers=exc.headers
        )
    
    @staticmethod
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        """Handle standard HTTP exceptions"""
        request_id = ErrorHandlers.get_request_id(request)
        
        # Convert to custom exception
        custom_exc = CustomAPIException(
            status_code=exc.status_code,
            error_code=f"HTTP_{exc.status_code}",
            message=str(exc.detail),
            severity=ErrorSeverity.MEDIUM if exc.status_code < 500 else ErrorSeverity.HIGH
        )
        
        await error_logger.log_error(custom_exc, request, request_id)
        
        error_response = StandardErrorResponse(
            error_code=custom_exc.error_code,
            message=custom_exc.message,
            request_id=request_id,
            severity=custom_exc.severity,
            category=custom_exc.category
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.dict(),
            headers=getattr(exc, 'headers', None)
        )
    
    @staticmethod
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """Handle request validation errors"""
        request_id = ErrorHandlers.get_request_id(request)
        
        # Convert validation errors to ErrorDetail objects
        details = []
        for error in exc.errors():
            details.append(ErrorDetail(
                field=".".join(str(loc) for loc in error["loc"]),
                message=error["msg"],
                code=error["type"],
                value=error.get("input")
            ))
        
        custom_exc = ValidationError(
            message="Request validation failed",
            details=details,
            error_code="VALIDATION_ERROR"
        )
        
        await error_logger.log_error(custom_exc, request, request_id)
        
        error_response = StandardErrorResponse(
            error_code=custom_exc.error_code,
            message=custom_exc.message,
            details=custom_exc.details,
            request_id=request_id,
            severity=custom_exc.severity,
            category=custom_exc.category
        )
        
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response.dict()
        )
    
    @staticmethod
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle unexpected exceptions"""
        request_id = ErrorHandlers.get_request_id(request)
        
        # Log full traceback for debugging
        error_traceback = traceback.format_exc()
        logger.critical(f"Unhandled exception [{request_id}]: {str(exc)}\n{error_traceback}")
        
        # Create custom exception
        custom_exc = CustomAPIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred. Please try again later.",
            severity=ErrorSeverity.CRITICAL,
            category=ErrorCategory.SYSTEM
        )
        
        await error_logger.log_error(custom_exc, request, request_id)
        
        # Don't expose internal error details in production
        message = custom_exc.message
        if os.getenv("ENVIRONMENT") == "development":
            message = f"{message} Debug: {str(exc)}"
        
        error_response = StandardErrorResponse(
            error_code=custom_exc.error_code,
            message=message,
            request_id=request_id,
            severity=custom_exc.severity,
            category=custom_exc.category,
            support_reference=f"REF-{request_id[-8:]}"
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.dict()
        )

def setup_error_handlers(app):
    """Setup all error handlers for the FastAPI app"""
    app.add_exception_handler(CustomAPIException, ErrorHandlers.custom_api_exception_handler)
    app.add_exception_handler(HTTPException, ErrorHandlers.http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, ErrorHandlers.http_exception_handler)
    app.add_exception_handler(RequestValidationError, ErrorHandlers.validation_exception_handler)
    app.add_exception_handler(Exception, ErrorHandlers.general_exception_handler)

# Utility functions for common error scenarios
def raise_authentication_error(message: str = "Authentication required"):
    """Raise authentication error"""
    raise AuthenticationError(message)

def raise_authorization_error(message: str = "Insufficient permissions"):
    """Raise authorization error"""
    raise AuthorizationError(message)

def raise_validation_error(message: str, field: str = None, value: Any = None):
    """Raise validation error"""
    details = []
    if field:
        details.append(ErrorDetail(field=field, message=message, value=value))
    raise ValidationError(message, details)

def raise_business_logic_error(message: str, error_code: str = "BUSINESS_LOGIC_ERROR"):
    """Raise business logic error"""
    raise BusinessLogicError(message, error_code)

def raise_database_error(message: str = "Database operation failed"):
    """Raise database error"""
    raise DatabaseError(message)

def raise_external_service_error(service_name: str, message: str = None):
    """Raise external service error"""
    raise ExternalServiceError(service_name, message)

def raise_security_error(message: str):
    """Raise security error"""
    raise SecurityError(message)