"""
Advanced Rate Limiting System for Online Evaluation API
Implements token bucket algorithm with Redis backend for distributed rate limiting
"""

import time
import json
import logging
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import redis.asyncio as redis
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

class RateLimitType(Enum):
    """Types of rate limits"""
    PER_IP = "per_ip"
    PER_USER = "per_user"
    PER_ENDPOINT = "per_endpoint"
    GLOBAL = "global"

@dataclass
class RateLimitRule:
    """Rate limit rule configuration"""
    limit: int  # Number of requests
    window: int  # Time window in seconds
    burst_limit: Optional[int] = None  # Burst allowance
    penalty_duration: int = 300  # Penalty duration in seconds for violations

@dataclass
class RateLimitStatus:
    """Current rate limit status"""
    requests_made: int
    limit: int
    window_start: float
    window_end: float
    remaining: int
    reset_time: float
    is_limited: bool
    penalty_until: Optional[float] = None

class AdvancedRateLimiter:
    """Advanced rate limiter with multiple strategies and monitoring"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/1"):
        self.redis_client = None
        self.redis_url = redis_url
        self.local_cache = {}  # Fallback for when Redis is unavailable
        self.monitoring_data = {
            "total_requests": 0,
            "blocked_requests": 0,
            "violations": []
        }
        
        # Default rate limit rules
        self.default_rules = {
            RateLimitType.PER_IP: {
                "general": RateLimitRule(limit=100, window=60),  # 100 requests per minute
                "login": RateLimitRule(limit=5, window=300, penalty_duration=900),  # 5 login attempts per 5 minutes
                "upload": RateLimitRule(limit=10, window=60),  # 10 uploads per minute
                "api": RateLimitRule(limit=60, window=60),  # 60 API calls per minute
                "strict": RateLimitRule(limit=20, window=60, penalty_duration=300)  # Strict endpoints
            },
            RateLimitType.PER_USER: {
                "general": RateLimitRule(limit=1000, window=3600),  # 1000 requests per hour
                "evaluator": RateLimitRule(limit=500, window=3600),  # Evaluators get less quota
                "admin": RateLimitRule(limit=2000, window=3600)  # Admins get more quota
            },
            RateLimitType.PER_ENDPOINT: {
                "bulk_operations": RateLimitRule(limit=5, window=300),  # 5 bulk operations per 5 minutes
                "export": RateLimitRule(limit=10, window=600),  # 10 exports per 10 minutes
                "ai_requests": RateLimitRule(limit=50, window=3600)  # 50 AI requests per hour
            },
            RateLimitType.GLOBAL: {
                "system": RateLimitRule(limit=10000, window=60)  # 10k requests per minute system-wide
            }
        }
    
    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            await self.redis_client.ping()
            logger.info("Redis connection established for rate limiting")
        except Exception as e:
            logger.warning(f"Redis connection failed, using local cache: {e}")
            self.redis_client = None
    
    async def cleanup(self):
        """Cleanup Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
    
    def get_client_identifier(self, request: Request) -> str:
        """Get client identifier for rate limiting"""
        # Try to get real IP from headers (for proxy setups)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def get_user_identifier(self, request: Request) -> Optional[str]:
        """Get user identifier from request"""
        # Extract from JWT token if present
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                # This would need to be integrated with your JWT decode logic
                # For now, return a placeholder
                return "user_from_jwt"
            except Exception:
                pass
        return None
    
    def get_rate_limit_key(self, limit_type: RateLimitType, identifier: str, 
                          endpoint: str = None, rule_name: str = "general") -> str:
        """Generate rate limit key for storage"""
        parts = ["rate_limit", limit_type.value, rule_name]
        if endpoint:
            parts.append(endpoint.replace("/", "_"))
        parts.append(identifier)
        return ":".join(parts)
    
    def get_applicable_rules(self, request: Request) -> List[Tuple[str, RateLimitRule]]:
        """Get all applicable rate limit rules for a request"""
        rules = []
        path = request.url.path
        
        # IP-based rules
        client_ip = self.get_client_identifier(request)
        
        # Determine rule type based on endpoint
        if "/auth/login" in path:
            rules.append((
                self.get_rate_limit_key(RateLimitType.PER_IP, client_ip, rule_name="login"),
                self.default_rules[RateLimitType.PER_IP]["login"]
            ))
        elif "/files/" in path or "/upload" in path:
            rules.append((
                self.get_rate_limit_key(RateLimitType.PER_IP, client_ip, rule_name="upload"),
                self.default_rules[RateLimitType.PER_IP]["upload"]
            ))
        elif "/admin/" in path:
            rules.append((
                self.get_rate_limit_key(RateLimitType.PER_IP, client_ip, rule_name="strict"),
                self.default_rules[RateLimitType.PER_IP]["strict"]
            ))
        else:
            rules.append((
                self.get_rate_limit_key(RateLimitType.PER_IP, client_ip, rule_name="api"),
                self.default_rules[RateLimitType.PER_IP]["api"]
            ))
        
        # User-based rules
        user_id = self.get_user_identifier(request)
        if user_id:
            rules.append((
                self.get_rate_limit_key(RateLimitType.PER_USER, user_id),
                self.default_rules[RateLimitType.PER_USER]["general"]
            ))
        
        # Endpoint-specific rules
        if "/export" in path:
            rules.append((
                self.get_rate_limit_key(RateLimitType.PER_ENDPOINT, client_ip, 
                                      endpoint=path, rule_name="export"),
                self.default_rules[RateLimitType.PER_ENDPOINT]["export"]
            ))
        elif "/bulk" in path:
            rules.append((
                self.get_rate_limit_key(RateLimitType.PER_ENDPOINT, client_ip, 
                                      endpoint=path, rule_name="bulk_operations"),
                self.default_rules[RateLimitType.PER_ENDPOINT]["bulk_operations"]
            ))
        
        # Global rate limit
        rules.append((
            self.get_rate_limit_key(RateLimitType.GLOBAL, "system"),
            self.default_rules[RateLimitType.GLOBAL]["system"]
        ))
        
        return rules
    
    async def check_rate_limit(self, key: str, rule: RateLimitRule) -> RateLimitStatus:
        """Check rate limit for a specific key and rule"""
        current_time = time.time()
        
        try:
            if self.redis_client:
                return await self._check_rate_limit_redis(key, rule, current_time)
            else:
                return self._check_rate_limit_local(key, rule, current_time)
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # Fail open - allow request but log the error
            return RateLimitStatus(
                requests_made=0, limit=rule.limit, window_start=current_time,
                window_end=current_time + rule.window, remaining=rule.limit,
                reset_time=current_time + rule.window, is_limited=False
            )
    
    async def _check_rate_limit_redis(self, key: str, rule: RateLimitRule, 
                                    current_time: float) -> RateLimitStatus:
        """Check rate limit using Redis backend"""
        window_start = current_time - rule.window
        
        # Use Redis pipeline for atomic operations
        async with self.redis_client.pipeline() as pipe:
            # Remove expired entries
            await pipe.zremrangebyscore(key, 0, window_start)
            # Count current requests
            await pipe.zcard(key)
            # Add current request
            await pipe.zadd(key, {str(current_time): current_time})
            # Set expiration
            await pipe.expire(key, rule.window + 60)  # Add buffer for cleanup
            
            results = await pipe.execute()
            current_count = results[1] + 1  # Include the request we just added
        
        # Check for penalty
        penalty_key = f"{key}:penalty"
        penalty_until = await self.redis_client.get(penalty_key)
        if penalty_until and float(penalty_until) > current_time:
            return RateLimitStatus(
                requests_made=current_count, limit=rule.limit,
                window_start=window_start, window_end=current_time + rule.window,
                remaining=0, reset_time=float(penalty_until),
                is_limited=True, penalty_until=float(penalty_until)
            )
        
        is_limited = current_count > rule.limit
        remaining = max(0, rule.limit - current_count)
        
        # Apply penalty if limit exceeded
        if is_limited:
            penalty_end = current_time + rule.penalty_duration
            await self.redis_client.setex(penalty_key, rule.penalty_duration, penalty_end)
        
        return RateLimitStatus(
            requests_made=current_count, limit=rule.limit,
            window_start=window_start, window_end=current_time + rule.window,
            remaining=remaining, reset_time=current_time + rule.window,
            is_limited=is_limited
        )
    
    def _check_rate_limit_local(self, key: str, rule: RateLimitRule, 
                               current_time: float) -> RateLimitStatus:
        """Check rate limit using local cache (fallback)"""
        if key not in self.local_cache:
            self.local_cache[key] = []
        
        # Clean expired entries
        window_start = current_time - rule.window
        self.local_cache[key] = [
            timestamp for timestamp in self.local_cache[key] 
            if timestamp > window_start
        ]
        
        # Add current request
        self.local_cache[key].append(current_time)
        current_count = len(self.local_cache[key])
        
        is_limited = current_count > rule.limit
        remaining = max(0, rule.limit - current_count)
        
        return RateLimitStatus(
            requests_made=current_count, limit=rule.limit,
            window_start=window_start, window_end=current_time + rule.window,
            remaining=remaining, reset_time=current_time + rule.window,
            is_limited=is_limited
        )
    
    async def is_request_allowed(self, request: Request) -> Tuple[bool, Dict[str, any]]:
        """Check if request is allowed under all applicable rate limits"""
        rules = self.get_applicable_rules(request)
        self.monitoring_data["total_requests"] += 1
        
        violated_rules = []
        headers = {}
        
        for key, rule in rules:
            status = await self.check_rate_limit(key, rule)
            
            # Add rate limit headers
            headers.update({
                "X-RateLimit-Limit": str(rule.limit),
                "X-RateLimit-Remaining": str(status.remaining),
                "X-RateLimit-Reset": str(int(status.reset_time)),
                "X-RateLimit-Window": str(rule.window)
            })
            
            if status.is_limited:
                violated_rules.append({
                    "key": key,
                    "rule": asdict(rule),
                    "status": asdict(status)
                })
        
        if violated_rules:
            self.monitoring_data["blocked_requests"] += 1
            self.monitoring_data["violations"].append({
                "timestamp": datetime.utcnow().isoformat(),
                "client_ip": self.get_client_identifier(request),
                "path": request.url.path,
                "violated_rules": violated_rules
            })
            
            # Keep only last 1000 violations for memory management
            if len(self.monitoring_data["violations"]) > 1000:
                self.monitoring_data["violations"] = self.monitoring_data["violations"][-1000:]
            
            return False, headers
        
        return True, headers
    
    def get_monitoring_stats(self) -> Dict[str, any]:
        """Get rate limiting monitoring statistics"""
        return {
            "total_requests": self.monitoring_data["total_requests"],
            "blocked_requests": self.monitoring_data["blocked_requests"],
            "block_rate": (
                self.monitoring_data["blocked_requests"] / max(1, self.monitoring_data["total_requests"])
            ) * 100,
            "recent_violations": self.monitoring_data["violations"][-50:],  # Last 50 violations
            "redis_connected": self.redis_client is not None
        }
    
    async def clear_rate_limit(self, identifier: str, limit_type: RateLimitType, 
                             rule_name: str = "general"):
        """Clear rate limit for a specific identifier (admin function)"""
        key = self.get_rate_limit_key(limit_type, identifier, rule_name=rule_name)
        
        if self.redis_client:
            await self.redis_client.delete(key)
            await self.redis_client.delete(f"{key}:penalty")
        else:
            self.local_cache.pop(key, None)
        
        logger.info(f"Cleared rate limit for key: {key}")

# Global rate limiter instance
rate_limiter = AdvancedRateLimiter()

class RateLimitMiddleware:
    """Middleware for applying rate limits"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        
        # Skip rate limiting for certain paths
        skip_paths = ["/health", "/metrics", "/docs", "/redoc", "/openapi.json"]
        if any(request.url.path.startswith(path) for path in skip_paths):
            await self.app(scope, receive, send)
            return
        
        # Check rate limits
        allowed, headers = await rate_limiter.is_request_allowed(request)
        
        if not allowed:
            response = JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": "Too many requests. Please try again later.",
                    "retry_after": headers.get("X-RateLimit-Reset", 60)
                },
                headers=headers
            )
            await response(scope, receive, send)
            return
        
        # Add rate limit headers to successful responses
        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                for key, value in headers.items():
                    message["headers"].append([key.encode(), str(value).encode()])
            await send(message)
        
        await self.app(scope, receive, send_with_headers)