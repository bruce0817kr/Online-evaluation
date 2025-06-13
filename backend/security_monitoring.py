"""
Comprehensive Security Monitoring and Logging System
Enhanced security monitoring, logging, and alerting for Online Evaluation System
"""

import os
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import ipaddress
from collections import defaultdict, deque
import time

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import redis
import pymongo
from pymongo import MongoClient

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('security.log'),
        logging.StreamHandler()
    ]
)

class SecurityEventType(Enum):
    """Security event types for monitoring"""
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SQL_INJECTION_ATTEMPT = "sql_injection_attempt"
    XSS_ATTEMPT = "xss_attempt"
    FILE_UPLOAD_VIOLATION = "file_upload_violation"
    DATA_BREACH_ATTEMPT = "data_breach_attempt"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    BRUTE_FORCE_ATTACK = "brute_force_attack"
    DDoS_ATTEMPT = "ddos_attempt"
    MALWARE_DETECTED = "malware_detected"
    COMPLIANCE_VIOLATION = "compliance_violation"

class SecuritySeverity(Enum):
    """Security event severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SecurityEvent:
    """Security event data structure"""
    event_id: str
    event_type: SecurityEventType
    severity: SecuritySeverity
    timestamp: datetime
    user_id: Optional[str]
    ip_address: str
    user_agent: str
    endpoint: str
    method: str
    payload: Optional[Dict[str, Any]]
    response_code: int
    description: str
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'severity': self.severity.value,
            'timestamp': self.timestamp.isoformat(),
            'user_id': self.user_id,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'endpoint': self.endpoint,
            'method': self.method,
            'payload': self.payload,
            'response_code': self.response_code,
            'description': self.description,
            'metadata': self.metadata or {}
        }

class SecurityMonitor:
    """Comprehensive security monitoring system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.redis_client = None
        self.mongo_client = None
        self.failed_login_attempts = defaultdict(deque)
        self.suspicious_ips = set()
        self.blocked_ips = set()
        self.rate_limits = defaultdict(deque)
        
        # Configuration
        self.max_login_attempts = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
        self.login_window_minutes = int(os.getenv("LOGIN_WINDOW_MINUTES", "15"))
        self.rate_limit_requests = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
        self.rate_limit_window = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
        self.enable_ip_blocking = os.getenv("ENABLE_IP_BLOCKING", "true").lower() == "true"
        self.enable_real_time_alerts = os.getenv("ENABLE_REAL_TIME_ALERTS", "true").lower() == "true"
        
        # Initialize connections
        self._initialize_connections()
        
    def _initialize_connections(self):
        """Initialize Redis and MongoDB connections"""
        try:
            # Redis for real-time data
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            self.redis_client = redis.from_url(redis_url)
            self.redis_client.ping()
            self.logger.info("Connected to Redis for security monitoring")
        except Exception as e:
                        self.logger.error(f"Failed to connect to Redis: {e}")
            
        try:
            # MongoDB for persistent storage
            mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
            self.mongo_client = MongoClient(mongo_url)
            self.security_db = self.mongo_client.security_monitoring
            self.events_collection = self.security_db.security_events
            
            # Create indexes for performance
            self.events_collection.create_index([("timestamp", -1)])
            self.events_collection.create_index([("event_type", 1)])
            self.events_collection.create_index([("severity", 1)])
            self.events_collection.create_index([("ip_address", 1)])
            self.events_collection.create_index([("user_id", 1)])
            
            self.logger.info("Connected to MongoDB for security event storage")
        except Exception as e:
            self.logger.error(f"Failed to connect to MongoDB: {e}")
    
    def generate_event_id(self) -> str:
        """Generate unique event ID"""
        timestamp = str(time.time())
        unique_string = f"{timestamp}-{os.urandom(8).hex()}"
        return hashlib.sha256(unique_string.encode()).hexdigest()[:16]
    
    async def log_security_event(self, event: SecurityEvent):
        """Log security event to multiple destinations"""
        try:
            # Structured logging
            self.logger.info(
                f"SECURITY_EVENT: {event.event_type.value} | "
                f"Severity: {event.severity.value} | "
                f"IP: {event.ip_address} | "
                f"User: {event.user_id} | "
                f"Endpoint: {event.endpoint} | "
                f"Description: {event.description}"
            )
            
            # Store in Redis for real-time monitoring
            if self.redis_client:
                event_data = event.to_dict()
                await self._store_in_redis(event_data)
            
            # Store in MongoDB for persistence
            if self.mongo_client:
                await self._store_in_mongodb(event)
            
            # Real-time alerting for critical events
            if event.severity in [SecuritySeverity.HIGH, SecuritySeverity.CRITICAL]:
                await self._send_real_time_alert(event)
                
            # Update threat intelligence
            await self._update_threat_intelligence(event)
            
        except Exception as e:
            self.logger.error(f"Failed to log security event: {e}")
    
    async def _store_in_redis(self, event_data: Dict[str, Any]):
        """Store event in Redis for real-time access"""
        try:
            # Store latest events (last 1000)
            await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: self.redis_client.lpush("security_events", json.dumps(event_data))
            )
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.redis_client.ltrim("security_events", 0, 999)
            )
            
            # Store by event type for quick filtering
            event_type_key = f"events:{event_data['event_type']}"
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.redis_client.lpush(event_type_key, json.dumps(event_data))
            )
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.redis_client.ltrim(event_type_key, 0, 99)
            )
            
        except Exception as e:
            self.logger.error(f"Failed to store event in Redis: {e}")
    
    async def _store_in_mongodb(self, event: SecurityEvent):
        """Store event in MongoDB for persistence"""
        try:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.events_collection.insert_one(event.to_dict())
            )
        except Exception as e:
            self.logger.error(f"Failed to store event in MongoDB: {e}")
    
    async def _send_real_time_alert(self, event: SecurityEvent):
        """Send real-time alerts for critical security events"""
        if not self.enable_real_time_alerts:
            return
            
        try:
            alert_data = {
                'alert_type': 'security_critical',
                'event_id': event.event_id,
                'severity': event.severity.value,
                'event_type': event.event_type.value,
                'timestamp': event.timestamp.isoformat(),
                'ip_address': event.ip_address,
                'description': event.description,
                'requires_immediate_action': event.severity == SecuritySeverity.CRITICAL
            }
            
            # Store alert in Redis for real-time consumption
            if self.redis_client:
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.redis_client.publish("security_alerts", json.dumps(alert_data))
                )
            
            # Log critical alert
            self.logger.critical(f"CRITICAL SECURITY ALERT: {event.description}")
            
        except Exception as e:
            self.logger.error(f"Failed to send real-time alert: {e}")
    
    async def _update_threat_intelligence(self, event: SecurityEvent):
        """Update threat intelligence based on security events"""
        try:
            current_time = datetime.utcnow()
            
            # Track failed login attempts
            if event.event_type == SecurityEventType.LOGIN_FAILURE:
                self._track_failed_login(event.ip_address, current_time)
            
            # Track suspicious activity patterns
            if event.event_type in [
                SecurityEventType.SQL_INJECTION_ATTEMPT,
                SecurityEventType.XSS_ATTEMPT,
                SecurityEventType.UNAUTHORIZED_ACCESS
            ]:
                self._mark_ip_suspicious(event.ip_address)
            
            # Update rate limiting data
            self._update_rate_limit_data(event.ip_address, current_time)
            
        except Exception as e:
            self.logger.error(f"Failed to update threat intelligence: {e}")
    
    def _track_failed_login(self, ip_address: str, timestamp: datetime):
        """Track failed login attempts for brute force detection"""
        window_start = timestamp - timedelta(minutes=self.login_window_minutes)
        
        # Remove old attempts
        while (self.failed_login_attempts[ip_address] and 
               self.failed_login_attempts[ip_address][0] < window_start):
            self.failed_login_attempts[ip_address].popleft()
        
        # Add current attempt
        self.failed_login_attempts[ip_address].append(timestamp)
        
        # Check if threshold exceeded
        if len(self.failed_login_attempts[ip_address]) >= self.max_login_attempts:
            self._mark_ip_suspicious(ip_address)
            if self.enable_ip_blocking:
                self.blocked_ips.add(ip_address)
                self.logger.warning(f"IP {ip_address} blocked due to excessive failed login attempts")
    
    def _mark_ip_suspicious(self, ip_address: str):
        """Mark IP as suspicious"""
        self.suspicious_ips.add(ip_address)
        self.logger.warning(f"IP {ip_address} marked as suspicious")
    
    def _update_rate_limit_data(self, ip_address: str, timestamp: datetime):
        """Update rate limiting data"""
        window_start = timestamp - timedelta(seconds=self.rate_limit_window)
        
        # Remove old requests
        while (self.rate_limits[ip_address] and 
               self.rate_limits[ip_address][0] < window_start):
            self.rate_limits[ip_address].popleft()
        
        # Add current request
        self.rate_limits[ip_address].append(timestamp)
    
    def is_ip_blocked(self, ip_address: str) -> bool:
        """Check if IP is blocked"""
        return ip_address in self.blocked_ips
    
    def is_ip_suspicious(self, ip_address: str) -> bool:
        """Check if IP is suspicious"""
        return ip_address in self.suspicious_ips
    
    def is_rate_limited(self, ip_address: str) -> bool:
        """Check if IP is rate limited"""
        current_time = datetime.utcnow()
        self._update_rate_limit_data(ip_address, current_time)
        return len(self.rate_limits[ip_address]) > self.rate_limit_requests
    
    async def get_security_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """Get security metrics for the specified time period"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            
            if not self.mongo_client:
                return {"error": "MongoDB not available"}
            
            # Query security events
            pipeline = [
                {"$match": {"timestamp": {"$gte": start_time.isoformat(), "$lte": end_time.isoformat()}}},
                {"$group": {
                    "_id": {
                        "event_type": "$event_type",
                        "severity": "$severity"
                    },
                    "count": {"$sum": 1}
                }}
            ]
            
            results = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: list(self.events_collection.aggregate(pipeline))
            )
            
            # Process results
            metrics = {
                "time_period": f"Last {hours} hours",
                "total_events": sum(result["count"] for result in results),
                "events_by_type": defaultdict(int),
                "events_by_severity": defaultdict(int),
                "suspicious_ips": len(self.suspicious_ips),
                "blocked_ips": len(self.blocked_ips)
            }
            
            for result in results:
                event_type = result["_id"]["event_type"]
                severity = result["_id"]["severity"]
                count = result["count"]
                
                metrics["events_by_type"][event_type] += count
                metrics["events_by_severity"][severity] += count
            
            return dict(metrics)
            
        except Exception as e:
            self.logger.error(f"Failed to get security metrics: {e}")
            return {"error": str(e)}
    
    async def get_threat_intelligence_report(self) -> Dict[str, Any]:
        """Generate threat intelligence report"""
        try:
            current_time = datetime.utcnow()
            
            # Top suspicious IPs
            top_suspicious_ips = []
            for ip in list(self.suspicious_ips)[:10]:
                if self.mongo_client:
                    # Get event count for this IP
                    event_count = await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: self.events_collection.count_documents({"ip_address": ip})
                    )
                    top_suspicious_ips.append({"ip": ip, "events": event_count})
            
            # Rate limiting statistics
            rate_limit_stats = {
                "total_ips_tracked": len(self.rate_limits),
                "currently_rate_limited": sum(1 for ip in self.rate_limits.keys() 
                                            if self.is_rate_limited(ip))
            }
            
            # Failed login statistics
            failed_login_stats = {
                "ips_with_failed_logins": len(self.failed_login_attempts),
                "total_failed_attempts": sum(len(attempts) for attempts in self.failed_login_attempts.values())
            }
            
            report = {
                "generated_at": current_time.isoformat(),
                "summary": {
                    "suspicious_ips": len(self.suspicious_ips),
                    "blocked_ips": len(self.blocked_ips),
                    "monitored_ips": len(self.rate_limits)
                },
                "top_suspicious_ips": top_suspicious_ips,
                "rate_limiting": rate_limit_stats,
                "failed_logins": failed_login_stats,
                "recommendations": self._generate_security_recommendations()
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Failed to generate threat intelligence report: {e}")
            return {"error": str(e)}
    
    def _generate_security_recommendations(self) -> List[str]:
        """Generate security recommendations based on current threat data"""
        recommendations = []
        
        if len(self.suspicious_ips) > 10:
            recommendations.append("High number of suspicious IPs detected. Consider reviewing firewall rules.")
        
        if len(self.blocked_ips) > 5:
            recommendations.append("Multiple IPs have been blocked. Review security policies and consider geographic restrictions.")
        
        if any(len(attempts) > self.max_login_attempts * 2 for attempts in self.failed_login_attempts.values()):
            recommendations.append("Severe brute force attacks detected. Consider implementing CAPTCHA or account lockouts.")
        
        total_rate_limited = sum(1 for ip in self.rate_limits.keys() if self.is_rate_limited(ip))
        if total_rate_limited > 20:
            recommendations.append("High number of rate-limited IPs. Consider reviewing rate limiting thresholds.")
        
        if not recommendations:
            recommendations.append("Security posture is stable. Continue monitoring for threats.")
        
        return recommendations

class SecurityMiddleware(BaseHTTPMiddleware):
    """Enhanced security middleware with comprehensive monitoring"""
    
    def __init__(self, app, security_monitor: SecurityMonitor):
        super().__init__(app)
        self.security_monitor = security_monitor
        self.logger = logging.getLogger(__name__)
    
    async def dispatch(self, request: Request, call_next):
        """Process request through security middleware"""
        start_time = time.time()
        client_ip = self._get_client_ip(request)
        
        try:
            # Check if IP is blocked
            if self.security_monitor.is_ip_blocked(client_ip):
                await self._log_blocked_request(request, client_ip)
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
            
            # Check rate limiting
            if self.security_monitor.is_rate_limited(client_ip):
                await self._log_rate_limit_exceeded(request, client_ip)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded"
                )
            
            # Security checks
            await self._perform_security_checks(request, client_ip)
            
            # Process request
            response = await call_next(request)
            
            # Log successful request if from suspicious IP
            if self.security_monitor.is_ip_suspicious(client_ip):
                await self._log_suspicious_access(request, client_ip, response.status_code)
            
            return response
            
        except HTTPException as e:
            # Log security exceptions
            await self._log_security_exception(request, client_ip, e)
            raise
        except Exception as e:
            # Log unexpected errors
            await self._log_unexpected_error(request, client_ip, e)
            raise
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address"""
        # Check for forwarded headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    async def _perform_security_checks(self, request: Request, client_ip: str):
        """Perform various security checks on the request"""
        
        # Check for SQL injection patterns
        if await self._check_sql_injection(request):
            await self.security_monitor.log_security_event(SecurityEvent(
                event_id=self.security_monitor.generate_event_id(),
                event_type=SecurityEventType.SQL_INJECTION_ATTEMPT,
                severity=SecuritySeverity.HIGH,
                timestamp=datetime.utcnow(),
                user_id=None,
                ip_address=client_ip,
                user_agent=request.headers.get("User-Agent", ""),
                endpoint=str(request.url),
                method=request.method,
                payload=None,
                response_code=0,
                description=f"SQL injection attempt detected from {client_ip}"
            ))
        
        # Check for XSS patterns
        if await self._check_xss_attempt(request):
            await self.security_monitor.log_security_event(SecurityEvent(
                event_id=self.security_monitor.generate_event_id(),
                event_type=SecurityEventType.XSS_ATTEMPT,
                severity=SecuritySeverity.HIGH,
                timestamp=datetime.utcnow(),
                user_id=None,
                ip_address=client_ip,
                user_agent=request.headers.get("User-Agent", ""),
                endpoint=str(request.url),
                method=request.method,
                payload=None,
                response_code=0,
                description=f"XSS attempt detected from {client_ip}"
            ))
    
    async def _check_sql_injection(self, request: Request) -> bool:
        """Check for SQL injection patterns"""
        sql_patterns = [
            r"union.*select", r"drop.*table", r"insert.*into",
            r"delete.*from", r"update.*set", r"exec.*\(",
            r"'.*or.*'.*=.*'", r"'.*and.*'.*=.*'"
        ]
        
        # Check URL parameters
        query_string = str(request.url.query).lower()
        for pattern in sql_patterns:
            if pattern in query_string:
                return True
        
        # Check request body if present
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                body_str = body.decode('utf-8').lower()
                for pattern in sql_patterns:
                    if pattern in body_str:
                        return True
            except:
                pass
        
        return False
    
    async def _check_xss_attempt(self, request: Request) -> bool:
        """Check for XSS attack patterns"""
        xss_patterns = [
            r"<script", r"javascript:", r"onload=", r"onerror=",
            r"<iframe", r"<object", r"<embed"
        ]
        
        # Check URL parameters
        query_string = str(request.url.query).lower()
        for pattern in xss_patterns:
            if pattern in query_string:
                return True
        
        # Check request body if present
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                body_str = body.decode('utf-8').lower()
                for pattern in xss_patterns:
                    if pattern in body_str:
                        return True
            except:
                pass
        
        return False
    
    async def _log_blocked_request(self, request: Request, client_ip: str):
        """Log blocked request"""
        await self.security_monitor.log_security_event(SecurityEvent(
            event_id=self.security_monitor.generate_event_id(),
            event_type=SecurityEventType.UNAUTHORIZED_ACCESS,
            severity=SecuritySeverity.HIGH,
            timestamp=datetime.utcnow(),
            user_id=None,
            ip_address=client_ip,
            user_agent=request.headers.get("User-Agent", ""),
            endpoint=str(request.url),
            method=request.method,
            payload=None,
            response_code=403,
            description=f"Blocked IP {client_ip} attempted access"
        ))
    
    async def _log_rate_limit_exceeded(self, request: Request, client_ip: str):
        """Log rate limit exceeded"""
        await self.security_monitor.log_security_event(SecurityEvent(
            event_id=self.security_monitor.generate_event_id(),
            event_type=SecurityEventType.RATE_LIMIT_EXCEEDED,
            severity=SecuritySeverity.MEDIUM,
            timestamp=datetime.utcnow(),
            user_id=None,
            ip_address=client_ip,
            user_agent=request.headers.get("User-Agent", ""),
            endpoint=str(request.url),
            method=request.method,
            payload=None,
            response_code=429,
            description=f"Rate limit exceeded for IP {client_ip}"
        ))
    
    async def _log_suspicious_access(self, request: Request, client_ip: str, status_code: int):
        """Log access from suspicious IP"""
        await self.security_monitor.log_security_event(SecurityEvent(
            event_id=self.security_monitor.generate_event_id(),
            event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
            severity=SecuritySeverity.MEDIUM,
            timestamp=datetime.utcnow(),
            user_id=None,
            ip_address=client_ip,
            user_agent=request.headers.get("User-Agent", ""),
            endpoint=str(request.url),
            method=request.method,
            payload=None,
            response_code=status_code,
            description=f"Suspicious IP {client_ip} accessed {request.url}"
        ))
    
    async def _log_security_exception(self, request: Request, client_ip: str, exception: HTTPException):
        """Log security-related exceptions"""
        severity = SecuritySeverity.HIGH if exception.status_code == 403 else SecuritySeverity.MEDIUM
        
        await self.security_monitor.log_security_event(SecurityEvent(
            event_id=self.security_monitor.generate_event_id(),
            event_type=SecurityEventType.UNAUTHORIZED_ACCESS,
            severity=severity,
            timestamp=datetime.utcnow(),
            user_id=None,
            ip_address=client_ip,
            user_agent=request.headers.get("User-Agent", ""),
            endpoint=str(request.url),
            method=request.method,
            payload=None,
            response_code=exception.status_code,
            description=f"Security exception: {exception.detail}"
        ))
    
    async def _log_unexpected_error(self, request: Request, client_ip: str, error: Exception):
        """Log unexpected errors"""
        await self.security_monitor.log_security_event(SecurityEvent(
            event_id=self.security_monitor.generate_event_id(),
            event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
            severity=SecuritySeverity.LOW,
            timestamp=datetime.utcnow(),
            user_id=None,
            ip_address=client_ip,
            user_agent=request.headers.get("User-Agent", ""),
            endpoint=str(request.url),
            method=request.method,
            payload=None,
            response_code=500,
            description=f"Unexpected error: {str(error)}"
        ))

# Global security monitor instance
security_monitor = SecurityMonitor()
