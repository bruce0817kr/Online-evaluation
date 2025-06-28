#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simplified Prometheus Metrics Collection System
FastAPI Prometheus integration with basic metrics
"""

import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request, Response
from prometheus_client import (
    Counter, Histogram, Gauge, Info, generate_latest, 
    CONTENT_TYPE_LATEST, CollectorRegistry, REGISTRY
)
from prometheus_fastapi_instrumentator import Instrumentator, metrics
import psutil
import redis
from motor.motor_asyncio import AsyncIOMotorClient

class PrometheusMetrics:
    """Simplified Prometheus metrics collection and management"""
    
    def __init__(self, app: FastAPI, redis_client: Optional[redis.Redis] = None, 
                 mongo_client: Optional[AsyncIOMotorClient] = None):
        self.app = app
        self.redis_client = redis_client
        self.mongo_client = mongo_client
        
        # HTTP metrics
        self.http_requests_total = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status_code']
        )
        
        self.http_request_duration = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint'],
            buckets=(.005, .01, .025, .05, .075, .1, .25, .5, .75, 1.0, 2.5, 5.0, 7.5, 10.0)
        )
        
        # System metrics
        self.system_cpu_usage = Gauge('system_cpu_usage_percent', 'CPU usage percentage')
        self.system_memory_usage = Gauge('system_memory_usage_bytes', 'Memory usage in bytes')
        self.system_memory_available = Gauge('system_memory_available_bytes', 'Available memory in bytes')
        
        # Application metrics
        self.active_users = Gauge('active_users_total', 'Number of active users')
        self.active_evaluations = Gauge('active_evaluations_total', 'Number of active evaluations')
        
        # Database connection status
        self.db_connections = Gauge('database_connections_status', 'Database connection status (1=healthy, 0=unhealthy)')
        
        # Security metrics
        self.security_events = Counter(
            'security_events_total',
            'Total security events',
            ['event_type', 'severity', 'source']
        )
        self.failed_logins = Counter('failed_login_attempts_total', 'Failed login attempts', ['ip_address'])
        
        # Application info
        self.app_info = Info('application_info', 'Application information')
        self.app_info.info({
            'version': '2.0.0',
            'environment': 'development',
            'build_date': datetime.now().isoformat()
        })
        
        # Instrumentator setup
        self.instrumentator = Instrumentator(
            should_group_status_codes=False,
            should_ignore_untemplated=True,
            should_respect_env_var=True,
            should_instrument_requests_inprogress=True,
            excluded_handlers=["/metrics", "/health", "/docs", "/openapi.json"],
            inprogress_name="http_requests_inprogress",
            inprogress_labels=True,
        )
    
    def instrument_app(self):
        """Apply Prometheus instrumentation to FastAPI app"""
        self.instrumentator.instrument(self.app).expose(self.app, endpoint="/metrics")
        
        # Add custom middleware
        @self.app.middleware("http")
        async def prometheus_middleware(request: Request, call_next):
            start_time = time.time()
            
            method = request.method
            path = request.url.path
            
            try:
                response = await call_next(request)
                status_code = response.status_code
                
                # Record metrics
                duration = time.time() - start_time
                self.http_request_duration.labels(method=method, endpoint=path).observe(duration)
                self.http_requests_total.labels(method=method, endpoint=path, status_code=status_code).inc()
                
                return response
                
            except Exception as e:
                self.http_requests_total.labels(method=method, endpoint=path, status_code=500).inc()
                raise
    
    async def collect_system_metrics(self):
        """Collect basic system metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.system_cpu_usage.set(cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.system_memory_usage.set(memory.used)
            self.system_memory_available.set(memory.available)
            
        except Exception as e:
            print(f"System metrics collection error: {e}")
    
    async def collect_database_metrics(self):
        """Check database connection status"""
        if not self.mongo_client:
            self.db_connections.set(0)
            return
            
        try:
            # Simple ping to check connection
            await self.mongo_client.admin.command('ping')
            self.db_connections.set(1)
            
        except Exception as e:
            print(f"Database connection check error: {e}")
            self.db_connections.set(0)
    
    async def collect_business_metrics(self):
        """Set basic business metrics to default values"""
        try:
            # Set default values to avoid authentication issues
            self.active_users.set(0)
            self.active_evaluations.set(0)
            
        except Exception as e:
            print(f"Business metrics collection error: {e}")
    
    def record_security_event(self, event_type: str, severity: str, source: str = "application"):
        """Record security event"""
        self.security_events.labels(event_type=event_type, severity=severity, source=source).inc()
    
    def record_failed_login(self, ip_address: str):
        """Record failed login attempt"""
        self.failed_logins.labels(ip_address=ip_address).inc()
    
    async def start_background_collection(self):
        """Start background metrics collection"""
        async def collection_loop():
            while True:
                try:
                    await self.collect_system_metrics()
                    await self.collect_database_metrics()
                    await self.collect_business_metrics()
                    await asyncio.sleep(30)  # Collect every 30 seconds
                except Exception as e:
                    print(f"Metrics collection error: {e}")
                    await asyncio.sleep(60)  # Wait 1 minute on error
        
        # Start as background task
        asyncio.create_task(collection_loop())

# Global metrics instance
prometheus_metrics: Optional[PrometheusMetrics] = None

def setup_prometheus_metrics(app: FastAPI, redis_client: Optional[redis.Redis] = None, 
                           mongo_client: Optional[AsyncIOMotorClient] = None) -> PrometheusMetrics:
    """Setup Prometheus metrics"""
    global prometheus_metrics
    prometheus_metrics = PrometheusMetrics(app, redis_client, mongo_client)
    prometheus_metrics.instrument_app()
    return prometheus_metrics

def get_prometheus_metrics() -> Optional[PrometheusMetrics]:
    """Get global metrics instance"""
    return prometheus_metrics
