"""
Enhanced Authentication System
Includes password reset, account lockout, MFA foundation, and session management
"""

import os
import secrets
import hashlib
import smtplib
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List, Tuple
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
import motor.motor_asyncio
import pyotp
import qrcode
import io
import base64

from security import (
    SecurityConfig, get_current_user, create_access_token, 
    verify_password, get_password_hash
)
from models import User, Token, UserResponse

logger = logging.getLogger(__name__)

class PasswordResetRequest(BaseModel):
    """Password reset request model"""
    email: str = Field(..., description="User's email address")

class PasswordReset(BaseModel):
    """Password reset model"""
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password")

class AccountLockoutStatus(BaseModel):
    """Account lockout status model"""
    is_locked: bool
    lockout_until: Optional[datetime] = None
    failed_attempts: int
    remaining_attempts: int

class MFASetupRequest(BaseModel):
    """MFA setup request model"""
    password: str = Field(..., description="Current password for verification")

class MFASetupResponse(BaseModel):
    """MFA setup response model"""
    secret: str
    qr_code: str
    backup_codes: List[str]

class MFAVerifyRequest(BaseModel):
    """MFA verification request model"""
    code: str = Field(..., description="6-digit MFA code")

class SessionInfo(BaseModel):
    """Session information model"""
    session_id: str
    user_id: str
    created_at: datetime
    last_activity: datetime
    ip_address: str
    user_agent: str
    is_active: bool

# Enhanced authentication router
auth_router = APIRouter(prefix="/auth", tags=["Enhanced Authentication"])

class AccountSecurityManager:
    """Manages account security features"""
    
    def __init__(self, database_client):
        self.db = database_client.online_evaluation
        self.security_config = SecurityConfig()
        
        # Account lockout settings
        self.max_failed_attempts = int(os.getenv("MAX_FAILED_ATTEMPTS", "5"))
        self.lockout_duration = int(os.getenv("LOCKOUT_DURATION_MINUTES", "30"))
        
        # Password reset settings
        self.reset_token_expiry = int(os.getenv("RESET_TOKEN_EXPIRY_HOURS", "24"))
        
        # Email settings
        self.smtp_server = os.getenv("SMTP_SERVER")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@onlineevaluation.com")
    
    async def track_login_attempt(self, login_id: str, ip_address: str, 
                                success: bool, user_agent: str = None) -> bool:
        """Track login attempts and handle account lockout"""
        current_time = datetime.utcnow()
        
        # Get or create login attempts record
        attempts_record = await self.db.login_attempts.find_one({"login_id": login_id})
        
        if not attempts_record:
            attempts_record = {
                "login_id": login_id,
                "failed_attempts": 0,
                "last_failed_attempt": None,
                "lockout_until": None,
                "attempt_history": []
            }
        
        # Add current attempt to history
        attempt_record = {
            "timestamp": current_time,
            "ip_address": ip_address,
            "success": success,
            "user_agent": user_agent
        }
        
        attempts_record["attempt_history"].append(attempt_record)
        
        # Keep only last 100 attempts for performance
        if len(attempts_record["attempt_history"]) > 100:
            attempts_record["attempt_history"] = attempts_record["attempt_history"][-100:]
        
        if success:
            # Reset failed attempts on successful login
            attempts_record["failed_attempts"] = 0
            attempts_record["last_failed_attempt"] = None
            attempts_record["lockout_until"] = None
        else:
            # Increment failed attempts
            attempts_record["failed_attempts"] += 1
            attempts_record["last_failed_attempt"] = current_time
            
            # Check if account should be locked
            if attempts_record["failed_attempts"] >= self.max_failed_attempts:
                lockout_until = current_time + timedelta(minutes=self.lockout_duration)
                attempts_record["lockout_until"] = lockout_until
                
                # Log security event
                logger.warning(
                    f"Account locked for user {login_id} due to {self.max_failed_attempts} "
                    f"failed attempts from IP {ip_address}"
                )
        
        # Update database
        await self.db.login_attempts.replace_one(
            {"login_id": login_id},
            attempts_record,
            upsert=True
        )
        
        return success and not self.is_account_locked(attempts_record)
    
    def is_account_locked(self, attempts_record: Dict) -> bool:
        """Check if account is currently locked"""
        if not attempts_record.get("lockout_until"):
            return False
        
        return datetime.utcnow() < attempts_record["lockout_until"]
    
    async def get_lockout_status(self, login_id: str) -> AccountLockoutStatus:
        """Get account lockout status"""
        attempts_record = await self.db.login_attempts.find_one({"login_id": login_id})
        
        if not attempts_record:
            return AccountLockoutStatus(
                is_locked=False,
                failed_attempts=0,
                remaining_attempts=self.max_failed_attempts
            )
        
        is_locked = self.is_account_locked(attempts_record)
        failed_attempts = attempts_record.get("failed_attempts", 0)
        remaining_attempts = max(0, self.max_failed_attempts - failed_attempts)
        
        return AccountLockoutStatus(
            is_locked=is_locked,
            lockout_until=attempts_record.get("lockout_until"),
            failed_attempts=failed_attempts,
            remaining_attempts=remaining_attempts
        )
    
    async def unlock_account(self, login_id: str, admin_user_id: str):
        """Manually unlock account (admin function)"""
        await self.db.login_attempts.update_one(
            {"login_id": login_id},
            {
                "$set": {
                    "failed_attempts": 0,
                    "last_failed_attempt": None,
                    "lockout_until": None
                }
            }
        )
        
        logger.info(f"Account {login_id} unlocked by admin {admin_user_id}")
    
    async def generate_password_reset_token(self, email: str) -> Optional[str]:
        """Generate password reset token"""
        # Find user by email
        user_doc = await self.db.users.find_one({"email": email})
        if not user_doc:
            # Don't reveal if email exists
            return None
        
        # Generate secure token
        reset_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=self.reset_token_expiry)
        
        # Store reset token
        await self.db.password_resets.replace_one(
            {"user_id": str(user_doc["_id"])},
            {
                "user_id": str(user_doc["_id"]),
                "email": email,
                "token": reset_token,
                "expires_at": expires_at,
                "used": False,
                "created_at": datetime.utcnow()
            },
            upsert=True
        )
        
        return reset_token
    
    async def verify_reset_token(self, token: str) -> Optional[str]:
        """Verify password reset token and return user ID"""
        reset_record = await self.db.password_resets.find_one({
            "token": token,
            "used": False,
            "expires_at": {"$gt": datetime.utcnow()}
        })
        
        if not reset_record:
            return None
        
        return reset_record["user_id"]
    
    async def reset_password(self, token: str, new_password: str) -> bool:
        """Reset password using token"""
        user_id = await self.verify_reset_token(token)
        if not user_id:
            return False
        
        # Hash new password
        password_hash = get_password_hash(new_password)
        
        # Update user password
        result = await self.db.users.update_one(
            {"_id": user_id},
            {
                "$set": {
                    "password_hash": password_hash,
                    "password_changed_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count == 0:
            return False
        
        # Mark token as used
        await self.db.password_resets.update_one(
            {"token": token},
            {"$set": {"used": True, "used_at": datetime.utcnow()}}
        )
        
        # Reset failed login attempts
        await self.db.login_attempts.update_one(
            {"login_id": user_id},
            {
                "$set": {
                    "failed_attempts": 0,
                    "last_failed_attempt": None,
                    "lockout_until": None
                }
            }
        )
        
        logger.info(f"Password reset successful for user {user_id}")
        return True
    
    async def send_password_reset_email(self, email: str, reset_token: str):
        """Send password reset email"""
        if not all([self.smtp_server, self.smtp_username, self.smtp_password]):
            logger.warning("SMTP not configured, cannot send password reset email")
            return
        
        try:
            # Create reset URL
            base_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
            reset_url = f"{base_url}/reset-password?token={reset_token}"
            
            # Create email content
            subject = "Password Reset Request - Online Evaluation System"
            html_content = f"""
            <html>
            <body>
                <h2>Password Reset Request</h2>
                <p>You have requested a password reset for your Online Evaluation System account.</p>
                <p>Click the link below to reset your password:</p>
                <p><a href="{reset_url}">Reset Password</a></p>
                <p>This link will expire in {self.reset_token_expiry} hours.</p>
                <p>If you did not request this reset, please ignore this email.</p>
                <br>
                <p>Best regards,<br>Online Evaluation System</p>
            </body>
            </html>
            """
            
            # Send email
            msg = MimeMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = email
            
            html_part = MimeText(html_content, 'html')
            msg.attach(html_part)
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Password reset email sent to {email}")
            
        except Exception as e:
            logger.error(f"Failed to send password reset email to {email}: {e}")
    
    async def setup_mfa(self, user_id: str) -> Tuple[str, str, List[str]]:
        """Setup multi-factor authentication for user"""
        # Generate secret
        secret = pyotp.random_base32()
        
        # Get user info for QR code
        user_doc = await self.db.users.find_one({"_id": user_id})
        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_email = user_doc.get("email", "user@example.com")
        
        # Generate QR code
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=user_email,
            issuer_name="Online Evaluation System"
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        qr_code_b64 = base64.b64encode(img_buffer.read()).decode()
        
        # Generate backup codes
        backup_codes = [secrets.token_hex(4) for _ in range(10)]
        
        # Store MFA setup (not activated until verified)
        await self.db.mfa_setup.replace_one(
            {"user_id": user_id},
            {
                "user_id": user_id,
                "secret": secret,
                "backup_codes": backup_codes,
                "is_active": False,
                "setup_at": datetime.utcnow()
            },
            upsert=True
        )
        
        return secret, f"data:image/png;base64,{qr_code_b64}", backup_codes
    
    async def verify_mfa_setup(self, user_id: str, code: str) -> bool:
        """Verify MFA setup with code"""
        mfa_setup = await self.db.mfa_setup.find_one({"user_id": user_id})
        if not mfa_setup:
            return False
        
        # Verify code
        totp = pyotp.TOTP(mfa_setup["secret"])
        if not totp.verify(code):
            return False
        
        # Activate MFA
        await self.db.mfa_setup.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "is_active": True,
                    "activated_at": datetime.utcnow()
                }
            }
        )
        
        logger.info(f"MFA activated for user {user_id}")
        return True
    
    async def verify_mfa_code(self, user_id: str, code: str) -> bool:
        """Verify MFA code during login"""
        mfa_setup = await self.db.mfa_setup.find_one({
            "user_id": user_id,
            "is_active": True
        })
        
        if not mfa_setup:
            return True  # MFA not setup, allow login
        
        # Check if it's a backup code
        if code in mfa_setup["backup_codes"]:
            # Remove used backup code
            await self.db.mfa_setup.update_one(
                {"user_id": user_id},
                {"$pull": {"backup_codes": code}}
            )
            logger.info(f"Backup code used for user {user_id}")
            return True
        
        # Verify TOTP code
        totp = pyotp.TOTP(mfa_setup["secret"])
        return totp.verify(code)

class SessionManager:
    """Manages user sessions"""
    
    def __init__(self, database_client):
        self.db = database_client.online_evaluation
        self.session_timeout = int(os.getenv("SESSION_TIMEOUT_HOURS", "24"))
    
    async def create_session(self, user_id: str, ip_address: str, 
                           user_agent: str) -> str:
        """Create new user session"""
        session_id = secrets.token_urlsafe(32)
        current_time = datetime.utcnow()
        
        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": current_time,
            "last_activity": current_time,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "is_active": True,
            "expires_at": current_time + timedelta(hours=self.session_timeout)
        }
        
        await self.db.user_sessions.insert_one(session_data)
        return session_id
    
    async def update_session_activity(self, session_id: str):
        """Update session last activity"""
        current_time = datetime.utcnow()
        await self.db.user_sessions.update_one(
            {"session_id": session_id, "is_active": True},
            {
                "$set": {
                    "last_activity": current_time,
                    "expires_at": current_time + timedelta(hours=self.session_timeout)
                }
            }
        )
    
    async def invalidate_session(self, session_id: str):
        """Invalidate user session"""
        await self.db.user_sessions.update_one(
            {"session_id": session_id},
            {"$set": {"is_active": False, "invalidated_at": datetime.utcnow()}}
        )
    
    async def get_user_sessions(self, user_id: str) -> List[SessionInfo]:
        """Get all active sessions for user"""
        sessions = await self.db.user_sessions.find({
            "user_id": user_id,
            "is_active": True,
            "expires_at": {"$gt": datetime.utcnow()}
        }).to_list(100)
        
        return [SessionInfo(**session) for session in sessions]
    
    async def cleanup_expired_sessions(self):
        """Cleanup expired sessions"""
        result = await self.db.user_sessions.update_many(
            {
                "expires_at": {"$lt": datetime.utcnow()},
                "is_active": True
            },
            {"$set": {"is_active": False, "expired_at": datetime.utcnow()}}
        )
        
        if result.modified_count > 0:
            logger.info(f"Cleaned up {result.modified_count} expired sessions")

# Global instances (to be initialized with database client)
security_manager = None
session_manager = None

def initialize_auth_managers(database_client):
    """Initialize authentication managers"""
    global security_manager, session_manager
    security_manager = AccountSecurityManager(database_client)
    session_manager = SessionManager(database_client)

# Enhanced authentication endpoints
@auth_router.post("/request-password-reset")
async def request_password_reset(
    request: PasswordResetRequest,
    background_tasks: BackgroundTasks
):
    """Request password reset"""
    reset_token = await security_manager.generate_password_reset_token(request.email)
    
    if reset_token:
        background_tasks.add_task(
            security_manager.send_password_reset_email,
            request.email,
            reset_token
        )
    
    # Always return success to prevent email enumeration
    return {
        "message": "If the email address exists, a password reset link has been sent."
    }

@auth_router.post("/reset-password")
async def reset_password(request: PasswordReset):
    """Reset password using token"""
    success = await security_manager.reset_password(request.token, request.new_password)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    return {"message": "Password reset successful"}

@auth_router.get("/lockout-status/{login_id}")
async def get_lockout_status(login_id: str) -> AccountLockoutStatus:
    """Get account lockout status"""
    return await security_manager.get_lockout_status(login_id)

@auth_router.post("/unlock-account/{login_id}")
async def unlock_account(
    login_id: str,
    current_user: User = Depends(get_current_user)
):
    """Unlock user account (admin only)"""
    if current_user.role not in ["admin", "secretary"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    await security_manager.unlock_account(login_id, current_user.id)
    return {"message": f"Account {login_id} unlocked successfully"}

@auth_router.post("/setup-mfa")
async def setup_mfa(
    request: MFASetupRequest,
    current_user: User = Depends(get_current_user)
) -> MFASetupResponse:
    """Setup multi-factor authentication"""
    # Verify current password
    user_doc = await security_manager.db.users.find_one({"_id": current_user.id})
    if not user_doc or not verify_password(request.password, user_doc["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid password"
        )
    
    secret, qr_code, backup_codes = await security_manager.setup_mfa(current_user.id)
    
    return MFASetupResponse(
        secret=secret,
        qr_code=qr_code,
        backup_codes=backup_codes
    )

@auth_router.post("/verify-mfa-setup")
async def verify_mfa_setup(
    request: MFAVerifyRequest,
    current_user: User = Depends(get_current_user)
):
    """Verify MFA setup"""
    success = await security_manager.verify_mfa_setup(current_user.id, request.code)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code"
        )
    
    return {"message": "MFA setup completed successfully"}

@auth_router.get("/sessions")
async def get_user_sessions(
    current_user: User = Depends(get_current_user)
) -> List[SessionInfo]:
    """Get user's active sessions"""
    return await session_manager.get_user_sessions(current_user.id)

@auth_router.delete("/sessions/{session_id}")
async def invalidate_session(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Invalidate specific session"""
    await session_manager.invalidate_session(session_id)
    return {"message": "Session invalidated successfully"}