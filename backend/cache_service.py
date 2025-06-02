#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redis Cache Service
High-performance caching layer for the Online Evaluation System
"""

import redis.asyncio as redis
import json
import os
from typing import Any, Optional, Union
import logging
from datetime import timedelta

logger = logging.getLogger(__name__)

class CacheService:
    """Redis-based caching service for improved performance"""
    
    def __init__(self, redis_url: str = None):
        """Initialize Redis connection"""
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.redis_client = None
        self.default_ttl = 300  # 5 minutes default TTL
        
    async def connect(self):
        """Establish Redis connection"""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=20
            )
            # Test connection
            await self.redis_client.ping()
            logger.info("✅ Redis cache service connected successfully")
        except Exception as e:
            logger.warning(f"⚠️ Redis not available, falling back to no-cache mode: {e}")
            self.redis_client = None
    
    async def disconnect(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
    
    async def ping(self) -> bool:
        """Test Redis connection"""
        if not self.redis_client:
            return False
        try:
            await self.redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis ping error: {e}")
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.redis_client:
            return None
            
        try:
            value = await self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in cache with TTL"""
        if not self.redis_client:
            return False
            
        try:
            ttl = ttl or self.default_ttl
            serialized_value = json.dumps(value, default=str)
            await self.redis_client.setex(key, ttl, serialized_value)
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.redis_client:
            return False
            
        try:
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        if not self.redis_client:
            return 0
            
        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                return await self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache delete pattern error for {pattern}: {e}")
            return 0
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self.redis_client:
            return False
            
        try:
            return await self.redis_client.exists(key)
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter"""
        if not self.redis_client:
            return 0
            
        try:
            return await self.redis_client.incr(key, amount)
        except Exception as e:
            logger.error(f"Cache increment error for key {key}: {e}")
            return 0
    
    async def get_user_cache_key(self, user_id: str, suffix: str = "") -> str:
        """Generate user-specific cache key"""
        return f"user:{user_id}:{suffix}" if suffix else f"user:{user_id}"
    
    async def get_project_cache_key(self, project_id: str, suffix: str = "") -> str:
        """Generate project-specific cache key"""
        return f"project:{project_id}:{suffix}" if suffix else f"project:{project_id}"
    
    async def cache_user_data(self, user_id: str, user_data: dict, ttl: int = 600) -> bool:
        """Cache user data for 10 minutes"""
        key = await self.get_user_cache_key(user_id, "profile")
        return await self.set(key, user_data, ttl)
    
    async def get_cached_user_data(self, user_id: str) -> Optional[dict]:
        """Get cached user data"""
        key = await self.get_user_cache_key(user_id, "profile")
        return await self.get(key)
    
    async def invalidate_user_cache(self, user_id: str) -> int:
        """Invalidate all user-related cache"""
        pattern = f"user:{user_id}:*"
        return await self.delete_pattern(pattern)
    
    async def cache_dashboard_data(self, user_id: str, dashboard_data: dict, ttl: int = 300) -> bool:
        """Cache dashboard data for 5 minutes"""
        key = await self.get_user_cache_key(user_id, "dashboard")
        return await self.set(key, dashboard_data, ttl)
    
    async def get_cached_dashboard_data(self, user_id: str) -> Optional[dict]:
        """Get cached dashboard data"""
        key = await self.get_user_cache_key(user_id, "dashboard")
        return await self.get(key)

# Global cache service instance
cache_service = CacheService()
