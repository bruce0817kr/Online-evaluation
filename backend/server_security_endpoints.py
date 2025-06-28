# Security monitoring and management endpoints
@app.get("/api/security/health")
async def security_health_check():
    """Public endpoint to check security system health"""
    try:
        # Check Redis connection
        redis_status = "healthy"
        try:
            if security_monitor.redis_client:
                security_monitor.redis_client.ping()
        except:
            redis_status = "unavailable"
        
        # Check MongoDB connection
        mongo_status = "healthy"
        try:
            if security_monitor.mongo_client:
                security_monitor.mongo_client.admin.command('ping')
        except:
            mongo_status = "unavailable"
        
        return {
            "status": "healthy",
            "components": {
                "security_monitor": "active",
                "redis": redis_status,
                "mongodb": mongo_status,
                "rate_limiting": "active",
                "threat_detection": "active"
            },
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        return {
            "status": "degraded",
            "error": str(e),
            "timestamp": datetime.utcnow()
        }

@app.get("/api/security/metrics")
async def get_security_metrics(
    hours: int = Query(24, ge=1, le=168),  # 1 hour to 1 week
    current_user: User = Depends(get_current_user)
):
    """Get security metrics for the specified time period (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    metrics = await security_monitor.get_security_metrics(hours)
    return {"metrics": metrics, "generated_at": datetime.utcnow()}

@app.get("/api/security/threat-intelligence")
async def get_threat_intelligence_report(current_user: User = Depends(get_current_user)):
    """Get comprehensive threat intelligence report (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    report = await security_monitor.get_threat_intelligence_report()
    return {"report": report}

if __name__ == "__main__":
    import uvicorn
    
    # Production-ready server configuration
    config = {
        "host": "0.0.0.0",
        "port": int(os.getenv("PORT", 8080)),
        "log_level": os.getenv("LOG_LEVEL", "info").lower(),
        "access_log": True,
        "use_colors": False,
        "server_header": False,  # Hide server information
        "date_header": False,    # Don't include date header
    }
    
    # Add SSL configuration for production
    if os.getenv("ENVIRONMENT") == "production":
        config.update({
            "ssl_keyfile": os.getenv("SSL_KEY_FILE"),
            "ssl_certfile": os.getenv("SSL_CERT_FILE"),
            "ssl_ca_certs": os.getenv("SSL_CA_CERTS"),
        })
    
    logger.info(f"🚀 Starting Online Evaluation System on {config['host']}:{config['port']}")
    uvicorn.run(app, **config)
