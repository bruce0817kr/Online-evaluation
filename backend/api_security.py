"""
Advanced API Security Validation and Protection
Enhanced input validation, output sanitization, and API protection for Online Evaluation System
"""

import re
import html
import json
import hashlib
import os
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import bleach
from pydantic import BaseModel, Field
from pydantic.functional_validators import field_validator
from fastapi import HTTPException, status, Request, UploadFile
import mimetypes
from urllib.parse import urlparse, parse_qs

# Optional magic import for file type detection
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    magic = None

class ValidationError(Exception):
    """Custom validation error"""
    pass

class SecurityLevel(Enum):
    """Security validation levels"""
    BASIC = "basic"
    STANDARD = "standard"
    STRICT = "strict"
    PARANOID = "paranoid"

@dataclass
class ValidationConfig:
    """Security validation configuration"""
    security_level: SecurityLevel = SecurityLevel.STANDARD
    max_string_length: int = 1000
    max_file_size_mb: int = 50
    allowed_file_extensions: List[str] = None
    allowed_mime_types: List[str] = None
    enable_html_sanitization: bool = True
    enable_sql_injection_detection: bool = True
    enable_xss_detection: bool = True
    enable_path_traversal_detection: bool = True
    enable_command_injection_detection: bool = True
    max_nested_depth: int = 10
    rate_limit_per_minute: int = 60
    
    def __post_init__(self):
        if self.allowed_file_extensions is None:
            self.allowed_file_extensions = [
                'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
                'jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg',
                'txt', 'csv', 'json'
            ]
        
        if self.allowed_mime_types is None:
            self.allowed_mime_types = [
                'application/pdf',
                'application/msword',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'application/vnd.ms-excel',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'application/vnd.ms-powerpoint',
                'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                'image/jpeg', 'image/png', 'image/gif', 'image/bmp', 'image/svg+xml',
                'text/plain', 'text/csv', 'application/json'
            ]

class SecurityValidator:
    """Comprehensive security validation system"""
    
    def __init__(self, config: ValidationConfig = None):
        self.config = config or ValidationConfig()
        
        # Initialize magic checker if available
        if MAGIC_AVAILABLE:
            try:
                self.magic_checker = magic.Magic(mime=True)
            except Exception:
                self.magic_checker = None
        else:
            self.magic_checker = None
        
        # Malicious patterns for detection
        self.sql_injection_patterns = [
            r"(?i)(union.*select|drop.*table|insert.*into|delete.*from|update.*set)",
            r"(?i)(exec\s*\(|sp_|xp_)",
            r"(?i)('.*or.*'.*=.*'|'.*and.*'.*=.*')",
            r"(?i)(--|\#|\/\*|\*\/)",
            r"(?i)(waitfor\s+delay|benchmark\s*\()",
            r"(?i)(load_file\s*\(|into\s+outfile)",
        ]
        
        self.xss_patterns = [
            r"(?i)(<script[^>]*>|</script>)",
            r"(?i)(javascript\s*:|vbscript\s*:|data\s*:)",
            r"(?i)(on\w+\s*=|expression\s*\()",
            r"(?i)(<iframe[^>]*>|<object[^>]*>|<embed[^>]*>)",
            r"(?i)(<link[^>]*>|<meta[^>]*>)",
            r"(?i)(document\.|window\.|eval\s*\()",
        ]
        
        self.path_traversal_patterns = [
            r"(\.\./|\.\.\\)",
            r"(%2e%2e%2f|%2e%2e%5c)",
            r"(\.\.%2f|\.\.%5c)",
            r"(%252e%252e%252f|%252e%252e%255c)",
        ]
        
        self.command_injection_patterns = [
            r"(;|\||&|`|\$\()",
            r"(\|\s*|\&\&|\|\|)",
            r"(`.*`|\$\{.*\})",
            r"(nc\s|netcat\s|curl\s|wget\s)",
            r"(chmod\s|chown\s|rm\s|mv\s)",
        ]
    
    def validate_string_input(self, value: str, field_name: str = "input") -> str:
        """Comprehensive string validation and sanitization"""
        if not isinstance(value, str):
            raise ValidationError(f"{field_name} must be a string")
        
        # Length validation
        if len(value) > self.config.max_string_length:
            raise ValidationError(f"{field_name} exceeds maximum length of {self.config.max_string_length}")
        
        # Security pattern detection
        if self.config.enable_sql_injection_detection:
            self._check_sql_injection(value, field_name)
        
        if self.config.enable_xss_detection:
            self._check_xss_attempt(value, field_name)
        
        if self.config.enable_path_traversal_detection:
            self._check_path_traversal(value, field_name)
        
        if self.config.enable_command_injection_detection:
            self._check_command_injection(value, field_name)
        
        # HTML sanitization
        if self.config.enable_html_sanitization:
            value = self._sanitize_html(value)
        
        # Additional encoding/escaping based on security level
        if self.config.security_level in [SecurityLevel.STRICT, SecurityLevel.PARANOID]:
            value = html.escape(value)
        
        return value
    
    def validate_numeric_input(self, value: Union[int, float], field_name: str = "input", 
                             min_value: Optional[Union[int, float]] = None,
                             max_value: Optional[Union[int, float]] = None) -> Union[int, float]:
        """Numeric input validation"""
        if not isinstance(value, (int, float)):
            raise ValidationError(f"{field_name} must be a number")
        
        if min_value is not None and value < min_value:
            raise ValidationError(f"{field_name} must be at least {min_value}")
        
        if max_value is not None and value > max_value:
            raise ValidationError(f"{field_name} must be at most {max_value}")
        
        return value
    
    def validate_email(self, email: str) -> str:
        """Email validation with security checks"""
        if not isinstance(email, str):
            raise ValidationError("Email must be a string")
        
        # Basic email pattern
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValidationError("Invalid email format")
        
        # Security checks
        email = self.validate_string_input(email, "email")
        
        # Additional email-specific security checks
        if len(email) > 254:  # RFC 5321 limit
            raise ValidationError("Email address too long")
        
        local_part, domain = email.split('@')
        if len(local_part) > 64:  # RFC 5321 limit
            raise ValidationError("Email local part too long")
        
        return email.lower()
    
    def validate_url(self, url: str, allowed_schemes: List[str] = None) -> str:
        """URL validation with security checks"""
        if not isinstance(url, str):
            raise ValidationError("URL must be a string")
        
        if allowed_schemes is None:
            allowed_schemes = ['http', 'https']
        
        try:
            parsed = urlparse(url)
            
            if parsed.scheme not in allowed_schemes:
                raise ValidationError(f"URL scheme must be one of: {allowed_schemes}")
            
            if not parsed.netloc:
                raise ValidationError("URL must have a valid domain")
            
            # Security checks
            url = self.validate_string_input(url, "url")
            
            # Check for suspicious patterns
            if any(pattern in url.lower() for pattern in ['localhost', '127.0.0.1', '0.0.0.0', '::1']):
                if self.config.security_level in [SecurityLevel.STRICT, SecurityLevel.PARANOID]:
                    raise ValidationError("Local URLs not allowed")
            
            return url
            
        except Exception as e:
            raise ValidationError(f"Invalid URL: {str(e)}")
    
    def validate_file_upload(self, file: UploadFile, field_name: str = "file") -> UploadFile:
        """Comprehensive file upload validation"""
        if not file or not file.filename:
            raise ValidationError(f"{field_name} is required")
        
        # File size validation
        file_size = 0
        if hasattr(file, 'size') and file.size:
            file_size = file.size
        elif hasattr(file, 'file'):
            # Get file size by seeking to end
            file.file.seek(0, 2)
            file_size = file.file.tell()
            file.file.seek(0)
        
        max_size_bytes = self.config.max_file_size_mb * 1024 * 1024
        if file_size > max_size_bytes:
            raise ValidationError(f"File size exceeds {self.config.max_file_size_mb}MB limit")
        
        # File extension validation
        file_extension = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
        if file_extension not in self.config.allowed_file_extensions:
            raise ValidationError(f"File extension '{file_extension}' not allowed")
          # MIME type validation
        try:
            # Read a small chunk to determine MIME type
            file_content = file.file.read(1024)
            file.file.seek(0)
            
            # Use magic library if available, otherwise fall back to mimetypes
            if self.magic_checker:
                detected_mime = self.magic_checker.from_buffer(file_content)
            else:
                # Fallback to mimetypes module and file extension
                detected_mime, _ = mimetypes.guess_type(file.filename)
                if not detected_mime:
                    # Basic type detection based on file extension
                    ext_to_mime = {
                        'pdf': 'application/pdf',
                        'doc': 'application/msword',
                        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                        'txt': 'text/plain',
                        'jpg': 'image/jpeg',
                        'jpeg': 'image/jpeg',
                        'png': 'image/png',
                        'gif': 'image/gif'
                    }
                    file_ext = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
                    detected_mime = ext_to_mime.get(file_ext, 'application/octet-stream')
            
            if detected_mime not in self.config.allowed_mime_types:
                raise ValidationError(f"File type '{detected_mime}' not allowed")
            
            # Additional security checks for specific file types
            self._check_file_security(file_content, detected_mime, file.filename)
            
        except Exception as e:
            raise ValidationError(f"File validation failed: {str(e)}")
        
        return file
    
    def validate_json_input(self, data: Dict[str, Any], max_depth: int = None) -> Dict[str, Any]:
        """JSON input validation with depth and structure checks"""
        if max_depth is None:
            max_depth = self.config.max_nested_depth
        
        def check_depth(obj, current_depth=0):
            if current_depth > max_depth:
                raise ValidationError(f"JSON nesting depth exceeds {max_depth}")
            
            if isinstance(obj, dict):
                for key, value in obj.items():
                    # Validate keys
                    self.validate_string_input(str(key), f"JSON key")
                    check_depth(value, current_depth + 1)
            elif isinstance(obj, list):
                for item in obj:
                    check_depth(item, current_depth + 1)
            elif isinstance(obj, str):
                self.validate_string_input(obj, "JSON string value")
        
        check_depth(data)
        return data
    
    def validate_api_request(self, request: Request) -> Dict[str, Any]:
        """Comprehensive API request validation"""
        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'security_flags': []
        }
        
        try:
            # Validate request headers
            self._validate_request_headers(request, validation_results)
            
            # Validate request parameters
            self._validate_request_params(request, validation_results)
            
            # Validate request size
            self._validate_request_size(request, validation_results)
            
            # Rate limiting check
            self._check_rate_limiting(request, validation_results)
            
        except Exception as e:
            validation_results['valid'] = False
            validation_results['errors'].append(f"Request validation failed: {str(e)}")
        
        return validation_results
    
    def _check_sql_injection(self, value: str, field_name: str):
        """Check for SQL injection patterns"""
        for pattern in self.sql_injection_patterns:
            if re.search(pattern, value):
                raise ValidationError(f"Potential SQL injection detected in {field_name}")
    
    def _check_xss_attempt(self, value: str, field_name: str):
        """Check for XSS attack patterns"""
        for pattern in self.xss_patterns:
            if re.search(pattern, value):
                raise ValidationError(f"Potential XSS attack detected in {field_name}")
    
    def _check_path_traversal(self, value: str, field_name: str):
        """Check for path traversal patterns"""
        for pattern in self.path_traversal_patterns:
            if re.search(pattern, value):
                raise ValidationError(f"Potential path traversal detected in {field_name}")
    
    def _check_command_injection(self, value: str, field_name: str):
        """Check for command injection patterns"""
        for pattern in self.command_injection_patterns:
            if re.search(pattern, value):
                raise ValidationError(f"Potential command injection detected in {field_name}")
    
    def _sanitize_html(self, value: str) -> str:
        """Sanitize HTML content"""
        # Allow minimal safe HTML tags
        allowed_tags = ['b', 'i', 'u', 'em', 'strong', 'p', 'br']
        allowed_attributes = {}
        
        if self.config.security_level == SecurityLevel.PARANOID:
            # Strip all HTML in paranoid mode
            return bleach.clean(value, tags=[], attributes={}, strip=True)
        
        return bleach.clean(value, tags=allowed_tags, attributes=allowed_attributes, strip=True)
    
    def _check_file_security(self, file_content: bytes, mime_type: str, filename: str):
        """Additional security checks for uploaded files"""
        
        # Check for embedded scripts in images
        if mime_type.startswith('image/'):
            suspicious_patterns = [b'<script', b'javascript:', b'<?php', b'<%', b'<html']
            for pattern in suspicious_patterns:
                if pattern in file_content.lower():
                    raise ValidationError("Suspicious content detected in image file")
        
        # Check for malicious file signatures
        known_malicious_signatures = [
            b'\x4d\x5a',  # PE executable
            b'\x7f\x45\x4c\x46',  # ELF executable
            b'\xca\xfe\xba\xbe',  # Java class file
        ]
        
        for signature in known_malicious_signatures:
            if file_content.startswith(signature):
                raise ValidationError("Potentially malicious file detected")
        
        # Check filename for suspicious patterns
        suspicious_filename_patterns = [
            r'\.exe$', r'\.bat$', r'\.cmd$', r'\.scr$', r'\.com$', r'\.pif$',
            r'\.php$', r'\.asp$', r'\.jsp$', r'\.py$', r'\.rb$', r'\.pl$'
        ]
        
        for pattern in suspicious_filename_patterns:
            if re.search(pattern, filename, re.IGNORECASE):
                if self.config.security_level in [SecurityLevel.STRICT, SecurityLevel.PARANOID]:
                    raise ValidationError(f"File type not allowed: {filename}")
    
    def _validate_request_headers(self, request: Request, results: Dict[str, Any]):
        """Validate request headers for security"""
        headers = dict(request.headers)
        
        # Check for suspicious user agents
        user_agent = headers.get('user-agent', '').lower()
        suspicious_ua_patterns = [
            'sqlmap', 'nikto', 'nmap', 'masscan', 'burp', 'owasp',
            'havij', 'hydra', 'john', 'metasploit'
        ]
        
        for pattern in suspicious_ua_patterns:
            if pattern in user_agent:
                results['security_flags'].append(f"Suspicious user agent: {pattern}")
        
        # Validate content-type for POST/PUT requests
        if request.method in ['POST', 'PUT', 'PATCH']:
            content_type = headers.get('content-type', '')
            if not content_type:
                results['warnings'].append("Missing content-type header")
    
    def _validate_request_params(self, request: Request, results: Dict[str, Any]):
        """Validate request parameters"""
        # Check query parameters
        query_params = dict(request.query_params)
        for key, value in query_params.items():
            try:
                self.validate_string_input(key, f"query parameter key")
                self.validate_string_input(value, f"query parameter {key}")
            except ValidationError as e:
                results['errors'].append(str(e))
                results['valid'] = False
    
    def _validate_request_size(self, request: Request, results: Dict[str, Any]):
        """Validate request size"""
        content_length = request.headers.get('content-length')
        if content_length:
            try:
                size = int(content_length)
                max_size = 10 * 1024 * 1024  # 10MB default
                if size > max_size:
                    results['errors'].append(f"Request size {size} exceeds maximum {max_size}")
                    results['valid'] = False
            except ValueError:
                results['warnings'].append("Invalid content-length header")
    
    def _check_rate_limiting(self, request: Request, results: Dict[str, Any]):
        """Check rate limiting for the request"""
        # This would integrate with your rate limiting system
        # For now, just add it as a validation step
        results['warnings'].append("Rate limiting check not implemented yet")

class SecureRequestValidator(BaseModel):
    """Pydantic models for secure request validation"""
    
    def validate_all_strings(cls, values):
        """Validate all string fields in the model"""
        validator = SecurityValidator()
        for field_name, value in values.items():
            if isinstance(value, str):
                try:
                    values[field_name] = validator.validate_string_input(value, field_name)
                except ValidationError as e:
                    raise ValueError(str(e))
        return values

# Predefined validation schemas for common use cases
class UserRegistrationValidator(SecureRequestValidator):
    """Secure user registration validation"""
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., max_length=254)
    password: str = Field(..., min_length=8, max_length=128)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    
    @field_validator('email')
    @classmethod
    def validate_email_security(cls, v):
        validator = SecurityValidator()
        return validator.validate_email(v)
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if not re.match(r'^[a-zA-Z0-9_.-]+$', v):
            raise ValueError('Username can only contain letters, numbers, dots, hyphens, and underscores')
        return v

class LoginValidator(SecureRequestValidator):
    """Secure login validation"""
    username: str = Field(..., max_length=100)
    password: str = Field(..., max_length=128)

class QuestionValidator(SecureRequestValidator):
    """Secure question validation"""
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=2000)
    type: str = Field(..., pattern=r'^(multiple_choice|true_false|short_answer|essay)$')
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    points: int = Field(..., ge=1, le=100)

class FileUploadValidator(SecureRequestValidator):
    """Secure file upload validation"""
    filename: str = Field(..., max_length=255)
    description: Optional[str] = Field(None, max_length=500)

# Global security validator instance
security_validator = SecurityValidator()
