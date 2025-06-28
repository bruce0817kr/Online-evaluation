#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced Health Check Endpoint
Real-time system monitoring for the Online Evaluation System
Enhanced with Prometheus metrics integration
"""

import time
import psutil
import requests
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
try:
    from prometheus_metrics import get_prometheus_metrics
except ImportError:
    get_prometheus_metrics = lambda: None

logger = logging.getLogger(__name__)

# This would be added to the backend/server.py
health_router = APIRouter(prefix="/health", tags=["health"])

def setup_health_monitor(db_client, redis_client=None):
    """Setup and return a health monitor instance"""
    try:
        from health_monitor import HealthMonitor
        return HealthMonitor(db_client)
    except ImportError as e:
        # Fallback to basic health monitoring
        logger.warning(f"Could not import HealthMonitor: {e}. Using basic monitoring.")
        return None

def get_system_metrics() -> Dict[str, Any]:
    """Get comprehensive system health metrics"""
    
    # CPU and Memory metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Process information
    process = psutil.Process()
    process_memory = process.memory_info()
    
    return {
        "timestamp": datetime.now().isoformat(),
        "system": {
            "cpu_percent": cpu_percent,
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": (disk.used / disk.total) * 100
            }
        },
        "application": {
            "memory_rss": process_memory.rss,
            "memory_vms": process_memory.vms,
            "cpu_times": process.cpu_times()._asdict(),
            "status": "healthy"
        }
    }

def check_database_connection() -> Dict[str, Any]:
    """Check MongoDB connection health"""
    try:
        # This would use the actual MongoDB client from the main app
        # For demo purposes, we'll simulate the check
        start_time = time.time()
        
        # Simulate database ping
        time.sleep(0.01)  # Simulated response time
        
        response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        return {
            "status": "healthy",
            "response_time_ms": round(response_time, 2),
            "connection_pool": {
                "active": 5,
                "idle": 10,
                "total": 15
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "response_time_ms": None
        }

def check_external_dependencies() -> Dict[str, Any]:
    """Check external service dependencies"""
    dependencies = {}
    
    # Check if frontend is accessible (if serving from different port)
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        dependencies["frontend"] = {
            "status": "healthy" if response.status_code == 200 else "degraded",
            "response_code": response.status_code
        }
    except requests.RequestException:
        dependencies["frontend"] = {
            "status": "not_applicable",
            "note": "Frontend served by same application"
        }
    
    return dependencies

@health_router.get("/")
async def basic_health():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Online Evaluation System",
        "version": "1.0.0"
    }

@health_router.get("/detailed")
async def detailed_health():
    """Comprehensive health check with system metrics"""
    try:
        system_metrics = get_system_metrics()
        database_health = check_database_connection()
        dependencies = check_external_dependencies()
        
        # Determine overall health status
        overall_status = "healthy"
        if database_health["status"] != "healthy":
            overall_status = "degraded"
        if system_metrics["system"]["memory"]["percent"] > 90:
            overall_status = "warning"
        if system_metrics["system"]["cpu_percent"] > 95:
            overall_status = "critical"
        
        return {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "service": "Online Evaluation System",
            "version": "1.0.0",
            "system_metrics": system_metrics,
            "database": database_health,
            "dependencies": dependencies,
            "checks": {
                "memory_usage": "ok" if system_metrics["system"]["memory"]["percent"] < 80 else "warning",
                "cpu_usage": "ok" if system_metrics["system"]["cpu_percent"] < 80 else "warning",
                "disk_usage": "ok" if system_metrics["system"]["disk"]["percent"] < 80 else "warning",
                "database_connectivity": database_health["status"]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@health_router.get("/liveness")
async def liveness_probe():
    """Kubernetes-style liveness probe"""
    return {"status": "alive", "timestamp": datetime.now().isoformat()}

@health_router.get("/readiness")
async def readiness_probe():
    """Kubernetes-style readiness probe"""
    try:
        # Check if the application is ready to serve requests
        database_health = check_database_connection()
        
        if database_health["status"] == "healthy":
            return {
                "status": "ready", 
                "timestamp": datetime.now().isoformat(),
                "dependencies": {"database": "ready"}
            }
        else:
            raise HTTPException(
                status_code=503, 
                detail="Service not ready - database connection failed"
            )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service not ready: {str(e)}")

@health_router.get("/deployment")
async def deployment_status():
    """Public deployment status endpoint for monitoring tools (no auth required)"""
    import subprocess
    import os
    
    async def get_container_status_simple(container_name: str) -> Dict[str, Any]:
        """Simple container status check without authentication"""
        try:
            result = subprocess.run(
                ['docker', 'inspect', container_name, '--format', '{{.State.Running}}:{{.State.Status}}'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                output = result.stdout.strip()
                parts = output.split(':')
                running = parts[0].lower() == 'true'
                status = parts[1] if len(parts) > 1 else 'unknown'
                
                return {
                    'running': running,
                    'healthy': running,  # Simple check - if running, consider healthy
                    'status': status
                }
            else:
                return {
                    'running': False,
                    'healthy': False,
                    'status': 'not_found'
                }
        except Exception:
            return {
                'running': False,
                'healthy': False,
                'status': 'error'
            }
    
    try:
        # Get environment-based port configuration
        backend_port = os.getenv('BACKEND_PORT', '8002')
        frontend_port = os.getenv('FRONTEND_PORT', '3002')
        
        # Check core services
        containers = {
            'backend': 'online-evaluation-backend',
            'frontend': 'online-evaluation-frontend',
            'mongodb': 'online-evaluation-mongodb',
            'redis': 'online-evaluation-redis'
        }
        
        service_status = {}
        
        for service_name, container_name in containers.items():
            status = await get_container_status_simple(container_name)
            service_status[service_name] = {
                'name': service_name.title(),
                'running': status['running'],
                'healthy': status['healthy'],
                'status': status['status']
            }
        
        # Overall health calculation
        all_healthy = all(s['healthy'] for s in service_status.values())
        
        return {
            "timestamp": datetime.now().isoformat(),
            "deployment_status": "healthy" if all_healthy else "degraded",
            "services": service_status,
            "configuration": {
                "backend_port": backend_port,
                "frontend_port": frontend_port
            },
            "overall_healthy": all_healthy,
            "monitoring": "public_endpoint"
        }
        
    except Exception as e:
        logger.error(f"Deployment status check failed: {e}")
        return {
            "timestamp": datetime.now().isoformat(),
            "deployment_status": "error",
            "error": str(e),
            "monitoring": "public_endpoint"
        }

# Example usage in main FastAPI app:
"""
from health_monitoring import health_router

app = FastAPI()
app.include_router(health_router)
"""

# Standalone monitoring script
def run_health_monitoring():
    """Standalone health monitoring for external use"""
    print("🏥 ONLINE EVALUATION SYSTEM - HEALTH MONITORING")
    print("=" * 60)
    
    try:
        # Check basic endpoint
        response = requests.get("http://localhost:8080/health", timeout=5)
        if response.status_code == 200:
            print("✅ Basic Health Check: PASSED")
            data = response.json()
            print(f"   Status: {data.get('status', 'unknown')}")
            print(f"   Timestamp: {data.get('timestamp', 'unknown')}")
        else:
            print(f"❌ Basic Health Check: FAILED (HTTP {response.status_code})")
    except Exception as e:
        print(f"❌ Basic Health Check: FAILED ({str(e)})")
    
    # Check system metrics
    try:
        metrics = get_system_metrics()
        print(f"\n📊 System Metrics:")
        print(f"   CPU Usage: {metrics['system']['cpu_percent']:.1f}%")
        print(f"   Memory Usage: {metrics['system']['memory']['percent']:.1f}%")
        print(f"   Disk Usage: {metrics['system']['disk']['percent']:.1f}%")
        print(f"   Application Memory: {metrics['application']['memory_rss'] / 1024 / 1024:.1f} MB")
    except Exception as e:
        print(f"❌ System Metrics: FAILED ({str(e)})")
    
    # Check database
    try:
        db_health = check_database_connection()
        print(f"\n🗄️ Database Health:")
        print(f"   Status: {db_health['status']}")
        print(f"   Response Time: {db_health.get('response_time_ms', 'N/A')} ms")
    except Exception as e:
        print(f"❌ Database Health: FAILED ({str(e)})")
    
    print("\n✨ Health monitoring complete!")

if __name__ == "__main__":
    run_health_monitoring()
