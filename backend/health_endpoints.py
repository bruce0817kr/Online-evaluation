"""
Comprehensive Health Check and Monitoring Endpoints
Provides detailed system health information for monitoring and alerting
"""

import os
import time
import psutil
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel
import motor.motor_asyncio
from pathlib import Path

from security import get_current_user, check_admin_or_secretary
from models import User
from rate_limiter import rate_limiter

logger = logging.getLogger(__name__)

class HealthStatus(BaseModel):
    """Health status model"""
    status: str  # "healthy", "degraded", "unhealthy"
    timestamp: datetime
    response_time_ms: float
    details: Dict[str, Any] = {}

class SystemMetrics(BaseModel):
    """System metrics model"""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    load_average: List[float]
    uptime_seconds: float
    active_connections: int

class DatabaseHealth(BaseModel):
    """Database health model"""
    status: str
    response_time_ms: float
    connections: Optional[int] = None
    collections_count: Optional[int] = None
    last_operation: Optional[datetime] = None

class ServiceHealth(BaseModel):
    """Individual service health"""
    name: str
    status: str
    response_time_ms: float
    last_check: datetime
    details: Dict[str, Any] = {}

class ApplicationHealth(BaseModel):
    """Complete application health"""
    overall_status: str
    timestamp: datetime
    uptime_seconds: float
    version: str
    environment: str
    services: List[ServiceHealth]
    system_metrics: SystemMetrics
    database: DatabaseHealth
    rate_limiting: Dict[str, Any]

# Health check router
health_router = APIRouter(prefix="/health", tags=["Health"])

class HealthMonitor:
    """Health monitoring service"""
    
    def __init__(self):
        self.start_time = time.time()
        self.health_history = []
        self.alert_thresholds = {
            "cpu_percent": 80.0,
            "memory_percent": 85.0,
            "disk_percent": 90.0,
            "response_time_ms": 1000.0
        }
        self.database_client = None
    
    def set_database_client(self, client):
        """Set database client for health checks"""
        self.database_client = client
    
    async def check_database_health(self) -> DatabaseHealth:
        """Check database connectivity and performance"""
        start_time = time.time()
        
        try:
            if not self.database_client:
                return DatabaseHealth(
                    status="unhealthy",
                    response_time_ms=0,
                    details={"error": "Database client not initialized"}
                )
            
            # Test basic connectivity
            db = self.database_client.online_evaluation
            await db.command("ping")
            
            # Get collection count
            collections = await db.list_collection_names()
            collections_count = len(collections)
            
            response_time = (time.time() - start_time) * 1000
            
            # Check if response time is acceptable
            status = "healthy" if response_time < self.alert_thresholds["response_time_ms"] else "degraded"
            
            return DatabaseHealth(
                status=status,
                response_time_ms=response_time,
                collections_count=collections_count,
                last_operation=datetime.utcnow()
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Database health check failed: {e}")
            
            return DatabaseHealth(
                status="unhealthy",
                response_time_ms=response_time,
                details={"error": str(e)}
            )
    
    def get_system_metrics(self) -> SystemMetrics:
        """Get current system metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
            uptime = time.time() - self.start_time
            
            # Get network connections count
            try:
                connections = len(psutil.net_connections())
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                connections = 0
            
            return SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                disk_percent=disk.percent,
                load_average=list(load_avg),
                uptime_seconds=uptime,
                active_connections=connections
            )
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return SystemMetrics(
                cpu_percent=0,
                memory_percent=0,
                disk_percent=0,
                load_average=[0, 0, 0],
                uptime_seconds=time.time() - self.start_time,
                active_connections=0
            )
    
    async def check_service_health(self, service_name: str, check_func) -> ServiceHealth:
        """Check individual service health"""
        start_time = time.time()
        
        try:
            result = await check_func() if asyncio.iscoroutinefunction(check_func) else check_func()
            response_time = (time.time() - start_time) * 1000
            
            return ServiceHealth(
                name=service_name,
                status="healthy",
                response_time_ms=response_time,
                last_check=datetime.utcnow(),
                details=result if isinstance(result, dict) else {}
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Service {service_name} health check failed: {e}")
            
            return ServiceHealth(
                name=service_name,
                status="unhealthy",
                response_time_ms=response_time,
                last_check=datetime.utcnow(),
                details={"error": str(e)}
            )
    
    async def get_comprehensive_health(self) -> ApplicationHealth:
        """Get comprehensive application health status"""
        # Get system metrics
        system_metrics = self.get_system_metrics()
        
        # Check database
        database_health = await self.check_database_health()
        
        # Check individual services
        services = []
        
        # Rate limiter service
        rate_limiter_health = await self.check_service_health(
            "rate_limiter",
            lambda: rate_limiter.get_monitoring_stats()
        )
        services.append(rate_limiter_health)
        
        # File system service
        file_system_health = await self.check_service_health(
            "file_system",
            self._check_file_system
        )
        services.append(file_system_health)
        
        # External API service (if any)
        external_api_health = await self.check_service_health(
            "external_apis",
            self._check_external_apis
        )
        services.append(external_api_health)
        
        # Determine overall status
        overall_status = self._determine_overall_status(
            system_metrics, database_health, services
        )
        
        return ApplicationHealth(
            overall_status=overall_status,
            timestamp=datetime.utcnow(),
            uptime_seconds=time.time() - self.start_time,
            version=os.getenv("APP_VERSION", "1.0.0"),
            environment=os.getenv("ENVIRONMENT", "development"),
            services=services,
            system_metrics=system_metrics,
            database=database_health,
            rate_limiting=rate_limiter.get_monitoring_stats()
        )
    
    def _check_file_system(self) -> Dict[str, Any]:
        """Check file system health"""
        upload_dir = Path(os.getenv("UPLOAD_DIR", "./uploads"))
        
        # Check if upload directory exists and is writable
        if not upload_dir.exists():
            upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Test write access
        test_file = upload_dir / ".health_check"
        try:
            test_file.write_text("health check")
            test_file.unlink()
            writable = True
        except Exception:
            writable = False
        
        # Get directory size
        try:
            total_size = sum(f.stat().st_size for f in upload_dir.rglob('*') if f.is_file())
        except Exception:
            total_size = 0
        
        return {
            "upload_dir_exists": upload_dir.exists(),
            "upload_dir_writable": writable,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2)
        }
    
    async def _check_external_apis(self) -> Dict[str, Any]:
        """Check external API connectivity"""
        # Placeholder for external API health checks
        # Add actual checks for any external services you use
        return {
            "ai_services": "not_configured",
            "email_service": "not_configured",
            "cloud_storage": "not_configured"
        }
    
    def _determine_overall_status(self, system_metrics: SystemMetrics, 
                                database_health: DatabaseHealth, 
                                services: List[ServiceHealth]) -> str:
        """Determine overall application health status"""
        # Check critical thresholds
        if (system_metrics.cpu_percent > self.alert_thresholds["cpu_percent"] or
            system_metrics.memory_percent > self.alert_thresholds["memory_percent"] or
            system_metrics.disk_percent > self.alert_thresholds["disk_percent"]):
            return "degraded"
        
        # Check database health
        if database_health.status == "unhealthy":
            return "unhealthy"
        
        # Check service health
        unhealthy_services = [s for s in services if s.status == "unhealthy"]
        if unhealthy_services:
            return "unhealthy"
        
        degraded_services = [s for s in services if s.status == "degraded"]
        if degraded_services or database_health.status == "degraded":
            return "degraded"
        
        return "healthy"
    
    def record_health_check(self, health: ApplicationHealth):
        """Record health check result for history"""
        self.health_history.append({
            "timestamp": health.timestamp,
            "status": health.overall_status,
            "response_time": max(s.response_time_ms for s in health.services),
            "cpu_percent": health.system_metrics.cpu_percent,
            "memory_percent": health.system_metrics.memory_percent
        })
        
        # Keep only last 1000 records
        if len(self.health_history) > 1000:
            self.health_history = self.health_history[-1000:]

# Global health monitor instance
health_monitor = HealthMonitor()

@health_router.get("/", response_model=HealthStatus)
async def basic_health_check():
    """Basic health check endpoint"""
    start_time = time.time()
    
    # Quick health check
    response_time = (time.time() - start_time) * 1000
    
    return HealthStatus(
        status="healthy",
        timestamp=datetime.utcnow(),
        response_time_ms=response_time,
        details={"message": "Service is operational"}
    )

@health_router.get("/ping")
async def ping():
    """Simple ping endpoint for load balancers"""
    return PlainTextResponse("pong")

@health_router.get("/ready")
async def readiness_check():
    """Readiness check for Kubernetes/container orchestration"""
    try:
        # Check if database is ready
        database_health = await health_monitor.check_database_health()
        
        if database_health.status == "unhealthy":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database not ready"
            )
        
        return {"status": "ready", "timestamp": datetime.utcnow()}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service not ready: {str(e)}"
        )

@health_router.get("/live")
async def liveness_check():
    """Liveness check for Kubernetes/container orchestration"""
    # Simple liveness check - if we can respond, we're alive
    return {"status": "alive", "timestamp": datetime.utcnow()}

@health_router.get("/detailed", response_model=ApplicationHealth)
async def detailed_health_check(current_user: User = Depends(get_current_user)):
    """Detailed health check (requires authentication)"""
    health = await health_monitor.get_comprehensive_health()
    health_monitor.record_health_check(health)
    return health

@health_router.get("/metrics")
async def prometheus_metrics(current_user: User = Depends(check_admin_or_secretary)):
    """Prometheus-compatible metrics endpoint"""
    try:
        health = await health_monitor.get_comprehensive_health()
        system_metrics = health.system_metrics
        
        metrics = [
            f"# HELP app_up Application up status",
            f"# TYPE app_up gauge",
            f'app_up{{environment="{health.environment}",version="{health.version}"}} {1 if health.overall_status != "unhealthy" else 0}',
            "",
            f"# HELP app_uptime_seconds Application uptime in seconds",
            f"# TYPE app_uptime_seconds counter",
            f'app_uptime_seconds {{environment="{health.environment}"}} {health.uptime_seconds}',
            "",
            f"# HELP system_cpu_percent CPU usage percentage",
            f"# TYPE system_cpu_percent gauge",
            f'system_cpu_percent {{environment="{health.environment}"}} {system_metrics.cpu_percent}',
            "",
            f"# HELP system_memory_percent Memory usage percentage",
            f"# TYPE system_memory_percent gauge",
            f'system_memory_percent {{environment="{health.environment}"}} {system_metrics.memory_percent}',
            "",
            f"# HELP system_disk_percent Disk usage percentage",
            f"# TYPE system_disk_percent gauge",
            f'system_disk_percent {{environment="{health.environment}"}} {system_metrics.disk_percent}',
            "",
            f"# HELP database_response_time_ms Database response time in milliseconds",
            f"# TYPE database_response_time_ms gauge",
            f'database_response_time_ms {{environment="{health.environment}"}} {health.database.response_time_ms}',
            "",
            f"# HELP rate_limit_total_requests Total number of requests processed by rate limiter",
            f"# TYPE rate_limit_total_requests counter",
            f'rate_limit_total_requests {{environment="{health.environment}"}} {health.rate_limiting["total_requests"]}',
            "",
            f"# HELP rate_limit_blocked_requests Total number of requests blocked by rate limiter",
            f"# TYPE rate_limit_blocked_requests counter",
            f'rate_limit_blocked_requests {{environment="{health.environment}"}} {health.rate_limiting["blocked_requests"]}',
        ]
        
        return PlainTextResponse("\n".join(metrics))
    
    except Exception as e:
        logger.error(f"Failed to generate metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate metrics"
        )

@health_router.get("/history")
async def health_history(
    limit: int = 100,
    current_user: User = Depends(check_admin_or_secretary)
):
    """Get health check history"""
    history = health_monitor.health_history[-limit:]
    return {
        "total_records": len(health_monitor.health_history),
        "returned_records": len(history),
        "history": history
    }

@health_router.post("/alerts/test")
async def test_alert_system(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(check_admin_or_secretary)
):
    """Test alert system (admin only)"""
    # This would integrate with your alerting system
    background_tasks.add_task(_send_test_alert, current_user.login_id)
    return {"message": "Test alert scheduled"}

async def _send_test_alert(user_id: str):
    """Send test alert (placeholder)"""
    logger.info(f"Test alert sent by user: {user_id}")
    # Implement actual alerting logic here (email, Slack, etc.)

# Startup event to initialize health monitor
async def initialize_health_monitor(database_client):
    """Initialize health monitor with database client"""
    health_monitor.set_database_client(database_client)
    await rate_limiter.initialize()
    logger.info("Health monitoring system initialized")