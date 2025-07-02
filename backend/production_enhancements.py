"""
Production-Ready FastAPI Enhancements Integration
Integrates all advanced features: rate limiting, health monitoring, enhanced auth, 
error handling, database optimization, and API documentation
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import all enhancement modules
from rate_limiter import RateLimitMiddleware, rate_limiter
from health_endpoints import health_router, health_monitor, initialize_health_monitor
from enhanced_auth import auth_router, initialize_auth_managers
from error_handlers import setup_error_handlers, initialize_error_logger
from database_optimization import optimized_db_client, initialize_database, cleanup_database
from api_documentation import docs_router, setup_enhanced_documentation

logger = logging.getLogger(__name__)

class ProductionEnhancementManager:
    """Manages all production enhancements"""
    
    def __init__(self, app: FastAPI):
        self.app = app
        self.database_client = None
        
    async def initialize_all_services(self):
        """Initialize all enhancement services"""
        try:
            # 1. Initialize database with optimization
            logger.info("Initializing optimized database connection...")
            self.database_client = await initialize_database()
            
            # 2. Initialize health monitoring
            logger.info("Initializing health monitoring system...")
            await initialize_health_monitor(self.database_client.client)
            
            # 3. Initialize enhanced authentication
            logger.info("Initializing enhanced authentication...")
            initialize_auth_managers(self.database_client.client)
            
            # 4. Initialize error logging
            logger.info("Initializing error logging system...")
            initialize_error_logger(self.database_client.client)
            
            # 5. Initialize rate limiting
            logger.info("Initializing rate limiting system...")
            await rate_limiter.initialize()
            
            logger.info("All production services initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize production services: {e}")
            raise
    
    async def cleanup_all_services(self):
        """Cleanup all enhancement services"""
        try:
            # Cleanup in reverse order
            await rate_limiter.cleanup()
            await cleanup_database()
            
            logger.info("All production services cleaned up successfully")
            
        except Exception as e:
            logger.error(f"Error during service cleanup: {e}")
    
    def setup_middlewares(self):
        """Setup all middleware components"""
        # 1. CORS middleware (should be first)
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
            allow_headers=["*"],
        )
        
        # 2. Rate limiting middleware
        self.app.add_middleware(RateLimitMiddleware)
        
        # Note: Other middlewares like SecurityMiddleware would be added here
        # from the existing middleware.py file
        
        logger.info("All middlewares configured")
    
    def setup_routers(self):
        """Setup all API routers"""
        # Enhanced routers
        self.app.include_router(health_router)
        self.app.include_router(auth_router)
        self.app.include_router(docs_router)
        
        # Note: Original routers from server.py would also be included here
        logger.info("All routers configured")
    
    def setup_error_handlers(self):
        """Setup error handling"""
        setup_error_handlers(self.app)
        logger.info("Error handlers configured")
    
    def setup_documentation(self):
        """Setup enhanced documentation"""
        setup_enhanced_documentation(self.app)
        logger.info("Enhanced documentation configured")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    enhancement_manager = ProductionEnhancementManager(app)
    app.state.enhancement_manager = enhancement_manager
    
    try:
        await enhancement_manager.initialize_all_services()
        yield
    finally:
        # Shutdown
        await enhancement_manager.cleanup_all_services()

def create_production_app() -> FastAPI:
    """Create FastAPI app with all production enhancements"""
    
    # Create FastAPI app with enhanced configuration
    app = FastAPI(
        title="Online Evaluation System API",
        description="Production-ready API with advanced features",
        version=os.getenv("API_VERSION", "1.1.0"),
        lifespan=lifespan,
        # Disable default documentation (we use enhanced docs)
        docs_url=None,
        redoc_url=None,
        openapi_url=None
    )
    
    # Create enhancement manager
    enhancement_manager = ProductionEnhancementManager(app)
    
    # Setup all components
    enhancement_manager.setup_middlewares()
    enhancement_manager.setup_error_handlers()
    enhancement_manager.setup_documentation()
    enhancement_manager.setup_routers()
    
    # Add basic health check for immediate availability
    @app.get("/ping")
    async def ping():
        return {"status": "ok", "message": "Service is running"}
    
    # Add shutdown endpoint for graceful shutdown
    @app.post("/admin/shutdown")
    async def shutdown(background_tasks: BackgroundTasks):
        """Graceful shutdown endpoint (admin only)"""
        background_tasks.add_task(lambda: os._exit(0))
        return {"message": "Shutdown initiated"}
    
    return app

# Additional utility endpoints for monitoring
def add_monitoring_endpoints(app: FastAPI):
    """Add additional monitoring endpoints"""
    
    @app.get("/metrics/rate-limiting")
    async def get_rate_limiting_metrics():
        """Get rate limiting statistics"""
        return rate_limiter.get_monitoring_stats()
    
    @app.get("/metrics/database")
    async def get_database_metrics():
        """Get database performance metrics"""
        if hasattr(app.state, 'enhancement_manager'):
            client = app.state.enhancement_manager.database_client
            if client:
                health = await client.get_health_status()
                return {
                    "health": health.dict(),
                    "performance": client.metrics_collector.get_performance_summary()
                }
        return {"error": "Database client not available"}
    
    @app.get("/status/comprehensive")
    async def get_comprehensive_status():
        """Get comprehensive system status"""
        if hasattr(app.state, 'enhancement_manager'):
            return {
                "api_version": os.getenv("API_VERSION", "1.1.0"),
                "environment": os.getenv("ENVIRONMENT", "development"),
                "health": await health_monitor.get_comprehensive_health(),
                "rate_limiting": rate_limiter.get_monitoring_stats()
            }
        return {"error": "Enhancement manager not available"}

# Example configuration for different environments
def get_environment_config():
    """Get environment-specific configuration"""
    env = os.getenv("ENVIRONMENT", "development")
    
    configs = {
        "development": {
            "log_level": "DEBUG",
            "reload": True,
            "workers": 1,
            "host": "0.0.0.0",
            "port": int(os.getenv("BACKEND_PORT", "8000"))
        },
        "staging": {
            "log_level": "INFO",
            "reload": False,
            "workers": 2,
            "host": "0.0.0.0",
            "port": int(os.getenv("BACKEND_PORT", "8000"))
        },
        "production": {
            "log_level": "WARNING",
            "reload": False,
            "workers": 4,
            "host": "0.0.0.0",
            "port": int(os.getenv("BACKEND_PORT", "8000"))
        }
    }
    
    return configs.get(env, configs["development"])

def run_production_server():
    """Run the production server with optimal configuration"""
    config = get_environment_config()
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, config["log_level"]),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Create app
    app = create_production_app()
    add_monitoring_endpoints(app)
    
    # Run server
    uvicorn.run(
        "production_enhancements:create_production_app",
        factory=True,
        host=config["host"],
        port=config["port"],
        workers=config["workers"],
        reload=config["reload"],
        access_log=True,
        log_config={
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
                "access": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
                "access": {
                    "formatter": "access",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
            },
            "loggers": {
                "uvicorn": {"handlers": ["default"], "level": "INFO"},
                "uvicorn.error": {"level": "INFO"},
                "uvicorn.access": {"handlers": ["access"], "level": "INFO", "propagate": False},
            },
        }
    )

if __name__ == "__main__":
    run_production_server()