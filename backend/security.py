"""
Security configuration and utilities for Online Evaluation System
Implements security best practices for FastAPI applications
"""

import os
import secrets
import hashlib
import re
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone # Ensure timezone is imported
from fastapi import HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from jose import JWTError, jwt
import logging # Add logging import

# from . import models # Assuming models.py is in the same directory
import models # Use absolute import
# from .config import settings # Assuming a config.py with settings
import config # Use absolute import, assuming config.py with a settings object

# Assuming your models are in backend.models
# and you will have a crud.py for database operations
# and a database.py for session management (get_db)
# from . import crud  # Placeholder for CRUD operations
# from .database import get_db # Placeholder for DB session dependency
from fastapi import Depends

logger = logging.getLogger(__name__)

class SecurityConfig:
    """Security configuration settings"""
    
    def __init__(self):
        # JWT Configuration
        self.JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", self._generate_secret_key())
        self.JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
        self.JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        self.JWT_REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))
        
        # Password Security
        self.PASSWORD_MIN_LENGTH = int(os.getenv("PASSWORD_MIN_LENGTH", "8"))
        self.PASSWORD_REQUIRE_UPPERCASE = os.getenv("PASSWORD_REQUIRE_UPPERCASE", "true").lower() == "true"
        self.PASSWORD_REQUIRE_LOWERCASE = os.getenv("PASSWORD_REQUIRE_LOWERCASE", "true").lower() == "true"
        self.PASSWORD_REQUIRE_NUMBERS = os.getenv("PASSWORD_REQUIRE_NUMBERS", "true").lower() == "true"
        self.PASSWORD_REQUIRE_SPECIAL_CHARS = os.getenv("PASSWORD_REQUIRE_SPECIAL_CHARS", "true").lower() == "true"
        
        # Rate Limiting
        self.RATE_LIMIT_REQUESTS_PER_MINUTE = int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "60"))
        self.RATE_LIMIT_BURST = int(os.getenv("RATE_LIMIT_BURST", "10"))
        
        # File Upload Security
        self.MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
        self.ALLOWED_FILE_TYPES = os.getenv("ALLOWED_FILE_TYPES", "pdf,doc,docx,xls,xlsx,ppt,pptx,jpg,jpeg,png,gif").split(",")
        
        # Security Headers
        self.SECURITY_HEADERS_ENABLED = os.getenv("SECURITY_HEADERS_ENABLED", "true").lower() == "true"
        self.CONTENT_SECURITY_POLICY = os.getenv("CONTENT_SECURITY_POLICY", 
            "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'")
        
        # CORS Configuration
        self.CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3001").split(",")
        self.CORS_ALLOW_CREDENTIALS = os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"
    
    def _generate_secret_key(self) -> str:
        """Generate a secure secret key"""
        return secrets.token_urlsafe(32)

# Global security configuration
security_config = SecurityConfig()

# Password context with improved settings
# Renaming to imported_pwd_context to avoid conflict if server.py also defines pwd_context
imported_pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Increased rounds for better security
)

# OAuth2 scheme
oauth2_scheme = HTTPBearer()

class JWTManager:
    """Manages JWT creation and verification."""
    def __init__(self, config: SecurityConfig):
        self.config = config

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.config.JWT_SECRET_KEY, algorithm=self.config.JWT_ALGORITHM)
        return encoded_jwt

    def verify_token(self, token: str, credentials_exception: HTTPException) -> dict:
        try:
            payload = jwt.decode(token, self.config.JWT_SECRET_KEY, algorithms=[self.config.JWT_ALGORITHM])
            return payload
        except JWTError as e:
            logger.error(f"JWTError during token verification: {e}")
            raise credentials_exception

# Instantiate JWTManager
jwt_manager = JWTManager(security_config)

# Top-level functions for server.py to import
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates a new access token.
    """
    return jwt_manager.create_access_token(data, expires_delta)

def get_password_hash(password: str) -> str:
    """
    Hashes a password using the configured context.
    """
    return imported_pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain password against a hashed password.
    """
    return imported_pwd_context.verify(plain_password, hashed_password)

# Placeholder for get_db dependency - replace with your actual implementation
def get_db():
    # This is a placeholder. Replace with your actual database session provider.
    # Example:
    # try:
    #     db = SessionLocal()
    #     yield db
    # finally:
    #     db.close()
    # yield None # Returning None for now as it's a placeholder
    # For Motor, db connection is typically managed differently, often via a global client
    # or passed through app state. For now, this dependency can be removed or adapted.
    pass

# Placeholder for CRUD function - replace with your actual implementation
# This would typically be in a crud.py file
class PlaceholderCRUD:
    @staticmethod
    def get_user_by_login_id(db: Any, login_id: str) -> Optional[models.User]: # Changed Session to Any
        # This is a placeholder. Replace with your actual database query.
        # Example: return db.query(models.DBUser).filter(models.DBUser.login_id == login_id).first()
        print(f"PlaceholderCRUD: Attempting to get user by login_id: {login_id}")
        # Simulate finding a user for now for dependency structure
        if login_id == "admin": # Or any other logic for testing
             return models.User(id="fake-admin-id", login_id="admin", email="admin@example.com", role="admin", name="Admin User", is_active=True, hashed_password="hashed_password_admin")
        return None

crud_user = PlaceholderCRUD() # Instantiate the placeholder

async def get_current_user(
    token: HTTPAuthorizationCredentials = Depends(oauth2_scheme), 
    # db: Session = Depends(get_db) # Placeholder, to be replaced with Motor client
) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt_manager.verify_token(token.credentials, credentials_exception)
        login_id: str = payload.get("sub")
        if login_id is None:
            logger.warning("Token payload missing 'sub' (login_id)")
            raise credentials_exception
    except JWTError as e: # Catching JWTError from jwt_manager.verify_token if it raises it directly
        logger.error(f"JWTError in get_current_user: {e}")
        raise credentials_exception
    
    # user = crud.get_user_by_login_id(db=db, login_id=login_id) # Replace with actual CRUD
    user = crud_user.get_user_by_login_id(db=None, login_id=login_id) # Using placeholder, db removed for now
    if user is None:
        logger.warning(f"User not found for login_id: {login_id} from token")
        raise credentials_exception
    if not user.is_active:
        logger.warning(f"User {login_id} is inactive")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return user

async def get_current_user_optional(
    token: Optional[HTTPAuthorizationCredentials] = Depends(oauth2_scheme), 
    # db: Session = Depends(get_db) # Placeholder, to be replaced with Motor client
) -> Optional[models.User]:
    if token is None or token.credentials is None: # Check if token was provided
        return None
    try:
        payload = jwt_manager.verify_token(token.credentials, HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")) # Temp exception
        login_id: str = payload.get("sub")
        if login_id is None:
            return None
        # user = crud.get_user_by_login_id(db=db, login_id=login_id) # Replace with actual CRUD
        user = crud_user.get_user_by_login_id(db=None, login_id=login_id) # Using placeholder, db removed for now
        if user is None or not user.is_active:
            return None
        return user
    except JWTError: # If token is invalid
        return None
    except HTTPException: # If token is invalid (from verify_token)
        return None


async def check_admin_or_secretary(
    current_user: models.User = Depends(get_current_user)
) -> models.User:
    if current_user.role not in ["admin", "secretary"]:
        logger.warning(f"User {current_user.login_id} with role {current_user.role} attempted admin/secretary action.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Admin or Secretary role required.",
        )
    return current_user

class PasswordValidator:
    """Password validation utility"""
    
    @staticmethod
    def validate_password(password: str) -> tuple[bool, List[str]]:
        """
        Validate password against security requirements
        Returns (is_valid, list_of_errors)
        """
        errors = []
        
        if len(password) < security_config.PASSWORD_MIN_LENGTH:
            errors.append(f"Password must be at least {security_config.PASSWORD_MIN_LENGTH} characters long")
        
        if security_config.PASSWORD_REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if security_config.PASSWORD_REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if security_config.PASSWORD_REQUIRE_NUMBERS and not re.search(r'\d', password):
            errors.append("Password must contain at least one number")
        
        if security_config.PASSWORD_REQUIRE_SPECIAL_CHARS and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        # Check for common weak passwords
        weak_passwords = ['password', '123456', 'qwerty', 'admin', 'root']
        if password.lower() in weak_passwords:
            errors.append("Password is too common and easily guessable")
        
        return len(errors) == 0, errors

class InputValidator:
    """Input validation utility"""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validate phone number format (Korean format)"""
        pattern = r'^01[0-9]-\d{4}-\d{4}$'
        return re.match(pattern, phone) is not None
    
    @staticmethod
    def sanitize_string(input_string: str, max_length: int = 255) -> str:
        """Sanitize string input"""
        if not isinstance(input_string, str):
            raise ValueError("Input must be a string")
        
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\']', '', input_string)
        
        # Limit length
        sanitized = sanitized[:max_length]
        
        # Strip whitespace
        sanitized = sanitized.strip()
        
        return sanitized
    
    @staticmethod
    def validate_file_type(filename: str) -> bool:
        """Validate file type based on extension"""
        if not filename:
            return False
        
        extension = filename.lower().split('.')[-1]
        return extension in security_config.ALLOWED_FILE_TYPES
    
    @staticmethod
    def validate_file_size(file_size: int) -> bool:
        """Validate file size"""
        max_size_bytes = security_config.MAX_FILE_SIZE_MB * 1024 * 1024
        return file_size <= max_size_bytes

class SecurityHeaders:
    """Security headers utility"""
    
    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """Get security headers for HTTP responses"""
        if not security_config.SECURITY_HEADERS_ENABLED:
            return {}
        
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": security_config.CONTENT_SECURITY_POLICY,
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=(), payment=(), usb=(), magnetometer=(), gyroscope=(), accelerometer=()"
        }

class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self.clients = {}
        self.cleanup_interval = 300  # 5 minutes
        self.last_cleanup = datetime.utcnow()
    
    def is_allowed(self, client_id: str) -> bool:
        """Check if client is allowed to make request"""
        now = datetime.utcnow()
        
        # Cleanup old entries
        if (now - self.last_cleanup).seconds > self.cleanup_interval:
            self._cleanup()
        
        if client_id not in self.clients:
            self.clients[client_id] = {
                'requests': [],
                'burst_count': 0,
                'burst_start': now
            }
        
        client_data = self.clients[client_id]
        
        # Remove old requests (older than 1 minute)
        minute_ago = now - timedelta(minutes=1)
        client_data['requests'] = [req_time for req_time in client_data['requests'] if req_time > minute_ago]
        
        # Check burst limit
        if (now - client_data['burst_start']).seconds < 10:  # 10 second window
            if client_data['burst_count'] >= security_config.RATE_LIMIT_BURST:
                return False
            client_data['burst_count'] += 1
        else:
            client_data['burst_count'] = 1
            client_data['burst_start'] = now
        
        # Check per-minute limit
        if len(client_data['requests']) >= security_config.RATE_LIMIT_REQUESTS_PER_MINUTE:
            return False
        
        client_data['requests'].append(now)
        return True
    
    def _cleanup(self):
        """Cleanup old client data"""
        now = datetime.utcnow()
        cutoff = now - timedelta(minutes=5)
        
        clients_to_remove = []
        for client_id, client_data in self.clients.items():
            if client_data['requests'] and max(client_data['requests']) < cutoff:
                clients_to_remove.append(client_id)
        
        for client_id in clients_to_remove:
            del self.clients[client_id]
        
        self.last_cleanup = now

# Global rate limiter instance
rate_limiter = RateLimiter()

class SecurityUtils:
    """General security utilities"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        return imported_pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return imported_pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate a secure random token"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def hash_file_content(content: bytes) -> str:
        """Generate hash of file content for integrity checking"""
        return hashlib.sha256(content).hexdigest()
    
    @staticmethod
    def get_client_ip(request: Request) -> str:
        """Get client IP address from request"""
        # Check for forwarded headers (when behind proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"

# Enhanced JWT Bearer security scheme
class JWTBearer(HTTPBearer):
    """Enhanced JWT Bearer authentication"""
    
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)
    
    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication scheme."
                )
            
            payload = JWTManager.verify_token(credentials.credentials)
            request.state.user = payload
            return credentials.credentials
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization code."
            )

# Global JWT bearer instance
jwt_bearer = JWTBearer()
