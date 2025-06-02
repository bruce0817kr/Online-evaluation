#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Health Monitoring System
Comprehensive health checks for production deployment
"""

import psutil
import asyncio
import time
from typing import Dict, List, Any
from datetime import datetime, timedelta
import logging
import json
from motor.motor_asyncio import AsyncIOMotorClient
import os

logger = logging.getLogger(__name__)

class HealthMonitor:
    """Comprehensive health monitoring for the Online Evaluation System"""
    
    def __init__(self, db_client: AsyncIOMotorClient = None):
        self.db_client = db_client
        self.start_time = time.time()
        self.health_checks = {}
        
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get comprehensive system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            
            # Network metrics (if available)
            try:
                network = psutil.net_io_counters()
                network_stats = {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                }
            except:
                network_stats = {"error": "Network stats unavailable"}
            
            # System uptime
            uptime_seconds = time.time() - self.start_time
            
            return {
                "cpu": {
                    "usage_percent": round(cpu_percent, 2),
                    "count": cpu_count,
                    "status": "healthy" if cpu_percent < 80 else "warning" if cpu_percent < 95 else "critical"
                },
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "used_gb": round(memory.used / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "usage_percent": round(memory.percent, 2),
                    "status": "healthy" if memory.percent < 80 else "warning" if memory.percent < 95 else "critical"
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "used_gb": round(disk.used / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "usage_percent": round((disk.used / disk.total) * 100, 2),
                    "status": "healthy" if (disk.used / disk.total) < 0.8 else "warning" if (disk.used / disk.total) < 0.95 else "critical"
                },
                "network": network_stats,
                "uptime": {
                    "seconds": round(uptime_seconds, 2),
                    "formatted": str(timedelta(seconds=int(uptime_seconds)))
                }
            }
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {"error": str(e)}
    
    async def check_database_health(self) -> Dict[str, Any]:
        """Check MongoDB database health"""
        if not self.db_client:
            return {"status": "error", "message": "No database client available"}
        
        try:
            start_time = time.time()
            
            # Test connection
            await self.db_client.admin.command('ping')
            connection_time = round((time.time() - start_time) * 1000, 2)
            
            # Get database stats
            stats = await self.db_client.admin.command('serverStatus')
            
            # Get collection counts
            db = self.db_client[os.getenv('DB_NAME', 'online_evaluation')]
            collections = await db.list_collection_names()
            
            collection_stats = {}
            for collection_name in collections:
                try:
                    count = await db[collection_name].count_documents({})
                    collection_stats[collection_name] = count
                except Exception as e:
                    collection_stats[collection_name] = f"Error: {str(e)}"
            
            return {
                "status": "healthy",
                "connection_time_ms": connection_time,
                "server_version": stats.get('version', 'unknown'),
                "uptime_seconds": stats.get('uptime', 0),
                "collections": collection_stats,
                "active_connections": stats.get('connections', {}).get('current', 0),
                "available_connections": stats.get('connections', {}).get('available', 0),
                "total_connections": stats.get('connections', {}).get('totalCreated', 0)
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "connection_time_ms": None
            }
    
    async def check_application_health(self) -> Dict[str, Any]:
        """Check application-specific health indicators"""
        try:
            health_data = {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "version": "1.0.0",
                "environment": os.getenv('ENVIRONMENT', 'development')
            }
            
            # Check critical services
            checks = {
                "database": await self.check_database_health(),
                "file_system": await self._check_file_system(),
                "memory_usage": await self._check_memory_usage(),
                "response_time": await self._check_response_time()
            }
            
            # Determine overall health
            overall_status = "healthy"
            for check_name, check_result in checks.items():
                if isinstance(check_result, dict):
                    if check_result.get('status') == 'error':
                        overall_status = "error"
                        break
                    elif check_result.get('status') == 'warning':
                        overall_status = "warning"
            
            health_data.update({
                "overall_status": overall_status,
                "checks": checks
            })
            
            return health_data
            
        except Exception as e:
            logger.error(f"Application health check failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _check_file_system(self) -> Dict[str, Any]:
        """Check file system health"""
        try:
            # Check if upload directories exist and are writable
            upload_dirs = ['uploads', 'exports', 'temp']
            dir_status = {}
            
            for dir_name in upload_dirs:
                dir_path = f"./{dir_name}"
                if os.path.exists(dir_path):
                    if os.access(dir_path, os.W_OK):
                        dir_status[dir_name] = "writable"
                    else:
                        dir_status[dir_name] = "read_only"
                else:
                    dir_status[dir_name] = "missing"
            
            return {
                "status": "healthy",
                "directories": dir_status
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def _check_memory_usage(self) -> Dict[str, Any]:
        """Check application memory usage"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()
            
            status = "healthy"
            if memory_percent > 80:
                status = "warning"
            if memory_percent > 95:
                status = "critical"
            
            return {
                "status": status,
                "memory_mb": round(memory_info.rss / (1024 * 1024), 2),
                "memory_percent": round(memory_percent, 2)
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def _check_response_time(self) -> Dict[str, Any]:
        """Check average response time"""
        try:
            # Simulate a simple operation time check
            start_time = time.time()
            await asyncio.sleep(0.001)  # Minimal async operation
            response_time = (time.time() - start_time) * 1000
            
            status = "healthy"
            if response_time > 100:
                status = "warning"
            if response_time > 500:
                status = "critical"
            
            return {
                "status": status,
                "average_response_time_ms": round(response_time, 2)
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def get_liveness_probe(self) -> Dict[str, Any]:
        """Kubernetes-style liveness probe"""
        try:
            # Basic health check - is the application running?
            return {
                "status": "alive",
                "timestamp": datetime.utcnow().isoformat(),
                "uptime_seconds": round(time.time() - self.start_time, 2)
            }
        except Exception as e:
            return {
                "status": "dead",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_readiness_probe(self) -> Dict[str, Any]:
        """Kubernetes-style readiness probe"""
        try:
            # Check if application is ready to serve requests
            db_health = await self.check_database_health()
            
            if db_health.get('status') == 'healthy':
                return {
                    "status": "ready",
                    "timestamp": datetime.utcnow().isoformat(),
                    "database": "connected"
                }
            else:
                return {
                    "status": "not_ready",
                    "timestamp": datetime.utcnow().isoformat(),
                    "database": "disconnected",
                    "reason": db_health.get('message', 'Database check failed')
                }
        except Exception as e:
            return {
                "status": "not_ready",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_comprehensive_health_report(self) -> Dict[str, Any]:
        """Get complete health report including all metrics"""
        try:
            system_metrics = await self.get_system_metrics()
            app_health = await self.check_application_health()
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "overall_status": app_health.get('overall_status', 'unknown'),
                "system_metrics": system_metrics,
                "application_health": app_health,
                "liveness": await self.get_liveness_probe(),
                "readiness": await self.get_readiness_probe()
            }
        except Exception as e:
            logger.error(f"Comprehensive health report failed: {e}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "overall_status": "error",
                "error": str(e)
            }
