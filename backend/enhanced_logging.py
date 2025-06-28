#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Logging System for Online Evaluation System
Comprehensive structured logging with ELK stack integration
"""

import logging
import logging.config
import json
import sys
import os
import traceback
from datetime import datetime
from typing import Any, Dict, Optional
from functools import wraps
import time
import asyncio
from contextvars import ContextVar
import uuid
from pathlib import Path

# Context variables for request tracking
request_id_context: ContextVar[str] = ContextVar('request_id', default='')
user_id_context: ContextVar[str] = ContextVar('user_id', default='')
session_id_context: ContextVar[str] = ContextVar('session_id', default='')

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging compatible with ELK stack"""
    
    def __init__(self, service_name: str = "online-evaluation-backend"):
        super().__init__()
        self.service_name = service_name
        self.hostname = os.uname().nodename if hasattr(os, 'uname') else 'unknown'
        
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        
        # Base log structure
        log_entry = {
            "@timestamp": datetime.utcnow().isoformat() + "Z",
            "service": {
                "name": self.service_name,
                "version": os.getenv("APP_VERSION", "2.0.0"),
                "environment": os.getenv("ENVIRONMENT", "development")
            },
            "host": {
                "name": self.hostname,
                "ip": self._get_host_ip()
            },
            "log": {
                "level": record.levelname,
                "logger": record.name,
                "thread": record.thread,
                "process": record.process
            },
            "message": record.getMessage()
        }
        
        # Add request context if available
        try:
            request_id = request_id_context.get()
            user_id = user_id_context.get()
            session_id = session_id_context.get()
            
            if request_id:
                log_entry["request"] = {"id": request_id}
            if user_id:
                log_entry["user"] = {"id": user_id}
            if session_id:
                log_entry["session"] = {"id": session_id}
        except LookupError:
            pass
        
        # Add exception information if present
        if record.exc_info:
            log_entry["error"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "stack_trace": self.formatException(record.exc_info)
            }
        
        # Add custom fields from record
        for key, value in record.__dict__.items():
            if key.startswith('custom_'):
                field_name = key[7:]  # Remove 'custom_' prefix
                log_entry[field_name] = value
        
        # Add performance metrics if available
        if hasattr(record, 'duration'):
            log_entry["performance"] = {
                "duration": record.duration,
                "unit": "ms"
            }
        
        # Add HTTP request information if available
        if hasattr(record, 'http_method'):
            log_entry["http"] = {
                "request": {
                    "method": record.http_method,
                    "uri": getattr(record, 'http_uri', ''),
                    "user_agent": getattr(record, 'http_user_agent', ''),
                    "remote_ip": getattr(record, 'http_remote_ip', '')
                },
                "response": {
                    "status_code": getattr(record, 'http_status_code', 0),
                    "duration": getattr(record, 'http_duration', 0)
                }
            }
        
        # Add database operation information if available
        if hasattr(record, 'db_operation'):
            log_entry["database"] = {
                "operation": record.db_operation,
                "collection": getattr(record, 'db_collection', ''),
                "duration": getattr(record, 'db_duration', 0),
                "records_affected": getattr(record, 'db_records_affected', 0)
            }
        
        # Add security event information if available
        if hasattr(record, 'security_event'):
            log_entry["security"] = {
                "event": record.security_event,
                "severity": getattr(record, 'security_severity', 'low'),
                "source_ip": getattr(record, 'security_source_ip', ''),
                "action": getattr(record, 'security_action', '')
            }
        
        return json.dumps(log_entry, ensure_ascii=False)
    
    def _get_host_ip(self) -> str:
        """Get host IP address"""
        try:
            import socket
            hostname = socket.gethostname()
            return socket.gethostbyname(hostname)
        except Exception:
            return "unknown"

class ContextualLogger:
    """Logger with automatic context injection"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def _add_context(self, extra: Dict[str, Any] = None) -> Dict[str, Any]:
        """Add request context to log extra data"""
        if extra is None:
            extra = {}
        
        try:
            request_id = request_id_context.get()
            user_id = user_id_context.get()
            session_id = session_id_context.get()
            
            if request_id and 'custom_request_id' not in extra:
                extra['custom_request_id'] = request_id
            if user_id and 'custom_user_id' not in extra:
                extra['custom_user_id'] = user_id
            if session_id and 'custom_session_id' not in extra:
                extra['custom_session_id'] = session_id
        except LookupError:
            pass
        
        return extra
    
    def debug(self, msg: str, **kwargs):
        extra = self._add_context(kwargs.get('extra'))
        self.logger.debug(msg, extra=extra)
    
    def info(self, msg: str, **kwargs):
        extra = self._add_context(kwargs.get('extra'))
        self.logger.info(msg, extra=extra)
    
    def warning(self, msg: str, **kwargs):
        extra = self._add_context(kwargs.get('extra'))
        self.logger.warning(msg, extra=extra)
    
    def error(self, msg: str, **kwargs):
        extra = self._add_context(kwargs.get('extra'))
        self.logger.error(msg, extra=extra, exc_info=kwargs.get('exc_info', True))
    
    def critical(self, msg: str, **kwargs):
        extra = self._add_context(kwargs.get('extra'))
        self.logger.critical(msg, extra=extra, exc_info=kwargs.get('exc_info', True))

def setup_logging(
    service_name: str = "online-evaluation-backend",
    log_level: str = None,
    log_file: str = None
) -> None:
    """Setup comprehensive logging configuration"""
    
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    if log_file is None:
        log_file = os.getenv("LOG_FILE", "/app/logs/app.log")
    
    # Ensure log directory exists
    log_dir = Path(log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # JSON formatter for structured logging
    json_formatter = JSONFormatter(service_name)
    
    # Console formatter for development
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if log_level == "DEBUG" else logging.INFO)
    
    # Use JSON format in production, console format in development
    if os.getenv("ENVIRONMENT", "development") == "production":
        console_handler.setFormatter(json_formatter)
    else:
        console_handler.setFormatter(console_formatter)
    
    root_logger.addHandler(console_handler)
    
    # File handler for application logs
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(getattr(logging, log_level))
    file_handler.setFormatter(json_formatter)
    root_logger.addHandler(file_handler)
    
    # Separate error log file
    error_log_file = str(log_file).replace('.log', '_error.log')
    error_handler = logging.FileHandler(error_log_file, encoding='utf-8')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(json_formatter)
    root_logger.addHandler(error_handler)
    
    # Configure specific loggers
    configure_logger_levels()
    
    # Log configuration completion
    logger = ContextualLogger(__name__)
    logger.info(f"Logging system initialized", extra={
        'custom_log_level': log_level,
        'custom_log_file': log_file,
        'custom_service_name': service_name
    })

def configure_logger_levels():
    """Configure specific logger levels"""
    
    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("motor").setLevel(logging.WARNING)
    logging.getLogger("pymongo").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    
    # Application-specific loggers
    logging.getLogger("auth").setLevel(logging.INFO)
    logging.getLogger("database").setLevel(logging.INFO)
    logging.getLogger("security").setLevel(logging.INFO)
    logging.getLogger("performance").setLevel(logging.INFO)

# Context managers for request tracking
class RequestContext:
    """Context manager for request-scoped logging"""
    
    def __init__(self, request_id: str = None, user_id: str = None, session_id: str = None):
        self.request_id = request_id or str(uuid.uuid4())
        self.user_id = user_id
        self.session_id = session_id
        self.start_time = time.time()
        
        # Store previous context values
        self._previous_request_id = None
        self._previous_user_id = None
        self._previous_session_id = None
    
    def __enter__(self):
        # Store previous values
        try:
            self._previous_request_id = request_id_context.get()
        except LookupError:
            pass
        
        try:
            self._previous_user_id = user_id_context.get()
        except LookupError:
            pass
        
        try:
            self._previous_session_id = session_id_context.get()
        except LookupError:
            pass
        
        # Set new context values
        request_id_context.set(self.request_id)
        if self.user_id:
            user_id_context.set(self.user_id)
        if self.session_id:
            session_id_context.set(self.session_id)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Calculate request duration
        duration = (time.time() - self.start_time) * 1000  # Convert to milliseconds
        
        # Log request completion
        logger = ContextualLogger(__name__)
        if exc_type:
            logger.error(f"Request completed with error", extra={
                'custom_duration': duration,
                'custom_error_type': exc_type.__name__ if exc_type else None
            })
        else:
            logger.info(f"Request completed successfully", extra={
                'custom_duration': duration
            })
        
        # Restore previous context values
        if self._previous_request_id is not None:
            request_id_context.set(self._previous_request_id)
        if self._previous_user_id is not None:
            user_id_context.set(self._previous_user_id)
        if self._previous_session_id is not None:
            session_id_context.set(self._previous_session_id)

# Decorators for automatic logging
def log_async_performance(operation_name: str = None):
    """Decorator to log async function performance"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            start_time = time.time()
            
            logger = ContextualLogger(func.__module__)
            logger.debug(f"Starting {op_name}")
            
            try:
                result = await func(*args, **kwargs)
                duration = (time.time() - start_time) * 1000
                
                logger.info(f"Completed {op_name}", extra={
                    'custom_operation': op_name,
                    'custom_duration': duration,
                    'custom_status': 'success'
                })
                
                return result
            
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                
                logger.error(f"Failed {op_name}: {str(e)}", extra={
                    'custom_operation': op_name,
                    'custom_duration': duration,
                    'custom_status': 'error',
                    'custom_error_type': type(e).__name__
                })
                
                raise
        
        return wrapper
    return decorator

def log_database_operation(collection_name: str = None):
    """Decorator to log database operations"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            operation_name = func.__name__
            
            logger = ContextualLogger("database")
            logger.debug(f"Database operation: {operation_name}", extra={
                'custom_db_operation': operation_name,
                'custom_db_collection': collection_name or 'unknown'
            })
            
            try:
                result = await func(*args, **kwargs)
                duration = (time.time() - start_time) * 1000
                
                # Try to determine records affected
                records_affected = 0
                if hasattr(result, 'matched_count'):
                    records_affected = result.matched_count
                elif hasattr(result, 'inserted_id'):
                    records_affected = 1
                elif isinstance(result, list):
                    records_affected = len(result)
                
                logger.info(f"Database operation completed: {operation_name}", extra={
                    'custom_db_operation': operation_name,
                    'custom_db_collection': collection_name or 'unknown',
                    'custom_db_duration': duration,
                    'custom_db_records_affected': records_affected
                })
                
                return result
            
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                
                logger.error(f"Database operation failed: {operation_name}: {str(e)}", extra={
                    'custom_db_operation': operation_name,
                    'custom_db_collection': collection_name or 'unknown',
                    'custom_db_duration': duration,
                    'custom_error_type': type(e).__name__
                })
                
                raise
        
        return wrapper
    return decorator

def log_security_event(event_type: str, severity: str = 'medium'):
    """Decorator to log security events"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            logger = ContextualLogger("security")
            
            try:
                result = await func(*args, **kwargs)
                
                logger.info(f"Security event: {event_type}", extra={
                    'custom_security_event': event_type,
                    'custom_security_severity': severity,
                    'custom_security_action': 'allowed'
                })
                
                return result
            
            except Exception as e:
                logger.warning(f"Security event blocked: {event_type}: {str(e)}", extra={
                    'custom_security_event': event_type,
                    'custom_security_severity': 'high',
                    'custom_security_action': 'blocked',
                    'custom_error_type': type(e).__name__
                })
                
                raise
        
        return wrapper
    return decorator

# Utility functions
def get_logger(name: str) -> ContextualLogger:
    """Get a contextual logger instance"""
    return ContextualLogger(name)

def log_startup_info():
    """Log application startup information"""
    logger = get_logger(__name__)
    
    startup_info = {
        'custom_version': os.getenv("APP_VERSION", "2.0.0"),
        'custom_environment': os.getenv("ENVIRONMENT", "development"),
        'custom_python_version': sys.version,
        'custom_startup_time': datetime.utcnow().isoformat()
    }
    
    logger.info("Application starting up", extra=startup_info)

def log_shutdown_info():
    """Log application shutdown information"""
    logger = get_logger(__name__)
    
    logger.info("Application shutting down", extra={
        'custom_shutdown_time': datetime.utcnow().isoformat()
    })

# Export main components
__all__ = [
    'setup_logging',
    'get_logger',
    'RequestContext',
    'log_async_performance',
    'log_database_operation',
    'log_security_event',
    'log_startup_info',
    'log_shutdown_info',
    'request_id_context',
    'user_id_context',
    'session_id_context'
]
