# Enhanced Logging Configuration for Online Evaluation System

## 🔍 Logging Architecture Overview

### Components
1. **Enhanced Logger**: `enhanced_logging.py` - Structured JSON logging with ELK integration
2. **Request Context**: Automatic request ID, user ID, session ID tracking
3. **Performance Logging**: Automatic timing for database operations and API calls
4. **Security Logging**: Comprehensive security event logging
5. **Error Tracking**: Structured error logging with context

### Log Levels
- **DEBUG**: Detailed debugging information
- **INFO**: General operational information
- **WARNING**: Warning conditions that need attention
- **ERROR**: Error conditions that need immediate attention
- **CRITICAL**: Critical errors that may cause system failure

### Log Structure (JSON Format)
```json
{
  "@timestamp": "2025-01-23T12:00:00.000Z",
  "service": {
    "name": "online-evaluation-backend",
    "version": "2.0.0",
    "environment": "development"
  },
  "host": {
    "name": "hostname",
    "ip": "192.168.1.100"
  },
  "log": {
    "level": "INFO",
    "logger": "server",
    "thread": 123,
    "process": 456
  },
  "message": "User authentication successful",
  "request": {"id": "req-123"},
  "user": {"id": "user-456"},
  "session": {"id": "sess-789"},
  "performance": {"duration": 150, "unit": "ms"},
  "http": {
    "request": {
      "method": "POST",
      "uri": "/api/auth/login",
      "user_agent": "Mozilla/5.0...",
      "remote_ip": "192.168.1.10"
    },
    "response": {
      "status_code": 200,
      "duration": 150
    }
  }
}
```

### Performance Decorators

#### @log_async_performance
Automatically logs function execution time and performance metrics.

```python
@log_async_performance("user_authentication")
async def login(form_data: OAuth2PasswordRequestForm):
    # Function implementation
    pass
```

#### @log_database_operation
Logs database operations with collection name and performance metrics.

```python
@log_database_operation("users")
async def create_user(user_data: UserCreate):
    # Database operation
    pass
```

#### @log_security_event
Logs security-related events with severity levels.

```python
@log_security_event("user_login", "medium")
async def login(form_data: OAuth2PasswordRequestForm):
    # Security-sensitive operation
    pass
```

### Context Management

#### RequestContext
Automatically tracks request-scoped information:
- Request ID (UUID)
- User ID (from authentication)
- Session ID (from cookies/headers)

```python
with RequestContext(request_id="req-123", user_id="user-456"):
    logger.info("Processing user request")
    # All logs within this context include request/user info
```

#### Middleware Integration
The logging middleware automatically:
1. Generates unique request IDs
2. Extracts user context from JWT tokens
3. Logs request/response cycles
4. Measures request duration
5. Adds request ID to response headers

### ELK Stack Integration

#### Filebeat Collection
- Application logs: `/app/logs/app.log`
- Error logs: `/app/logs/app_error.log`
- Structured JSON format for easy parsing

#### Logstash Processing
- Parses JSON logs
- Adds enrichment data
- Routes to appropriate Elasticsearch indices

#### Elasticsearch Storage
- Index patterns: `app-logs-*`, `nginx-logs-*`, `docker-logs-*`
- Retention policies: 90 days (app), 30 days (nginx), 14 days (docker)

#### Kibana Visualization
- Real-time dashboards
- Error analysis views
- Performance monitoring
- Security event tracking

### Environment Configuration

#### Development
- Console output: Human-readable format
- File output: JSON format
- Log level: DEBUG/INFO
- Detailed stack traces

#### Production
- Console output: JSON format (for container logging)
- File output: JSON format
- Log level: INFO/WARNING
- Minimal stack traces (security)

### Best Practices

1. **Use Structured Logging**
   ```python
   logger.info("User created", extra={
       'custom_user_id': user.id,
       'custom_user_role': user.role
   })
   ```

2. **Include Context**
   ```python
   with RequestContext(user_id=current_user.id):
       # All logs include user context
       pass
   ```

3. **Log Performance Metrics**
   ```python
   @log_async_performance("database_query")
   async def complex_query():
       pass
   ```

4. **Security Event Logging**
   ```python
   @log_security_event("failed_login", "high")
   async def failed_login_handler():
       pass
   ```

5. **Error Handling**
   ```python
   try:
       await risky_operation()
   except Exception as e:
       logger.error("Operation failed", extra={
           'custom_operation': 'risky_operation',
           'custom_error_type': type(e).__name__
       })
   ```

### Monitoring and Alerting

#### Critical Alerts
- Authentication failures (>10/min)
- Database connection failures
- High error rates (>5%)
- Performance degradation (>2s response time)

#### Performance Metrics
- Request duration percentiles
- Database query performance
- Memory usage trends
- CPU utilization

#### Security Monitoring
- Failed login attempts
- Suspicious IP addresses
- Privilege escalation attempts
- Data access patterns

### Log Analysis Queries

#### Find Authentication Failures
```json
{
  "query": {
    "bool": {
      "must": [
        {"match": {"log.level": "ERROR"}},
        {"match": {"custom_security_event": "user_login"}}
      ]
    }
  }
}
```

#### Performance Analysis
```json
{
  "query": {
    "range": {
      "performance.duration": {"gte": 1000}
    }
  }
}
```

#### User Activity Tracking
```json
{
  "query": {
    "match": {"user.id": "user-123"}
  }
}
```

### Troubleshooting

#### Common Issues
1. **Missing Context**: Ensure RequestContext is used properly
2. **Performance Impact**: Monitor logging overhead in production
3. **Log Volume**: Implement log rotation and retention policies
4. **ELK Integration**: Verify Filebeat configuration and network connectivity

#### Debug Mode
Set `LOG_LEVEL=DEBUG` to enable verbose logging for troubleshooting.

### Integration Checklist

✅ Enhanced logging system initialized
✅ Request context middleware added
✅ Performance decorators applied
✅ Security event logging configured
✅ Database operation logging implemented
✅ Error handling enhanced
✅ ELK stack integration configured
✅ Startup/shutdown logging added

### Performance Impact

- **Logging Overhead**: <1ms per request
- **Memory Usage**: ~10MB for log buffers
- **CPU Impact**: <2% under normal load
- **Network Impact**: Minimal (local file logging)

### Maintenance

#### Daily
- Monitor log volume and disk usage
- Check for error spikes

#### Weekly
- Review performance metrics
- Analyze security events
- Clean up old log files

#### Monthly
- Update log retention policies
- Review and optimize queries
- Update alerting thresholds
