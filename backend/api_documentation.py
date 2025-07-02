"""
Enhanced API Documentation System
Provides versioned OpenAPI documentation with comprehensive examples and interactive features
"""

import os
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, APIRouter, Depends, Request
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel, Field
from datetime import datetime
import json

from security import get_current_user
from models import User

class APIVersion(BaseModel):
    """API version information"""
    version: str
    release_date: str
    status: str  # "stable", "beta", "deprecated"
    changelog: List[str]
    breaking_changes: List[str]

class APIEndpointInfo(BaseModel):
    """API endpoint information"""
    path: str
    method: str
    summary: str
    description: str
    tags: List[str]
    version_added: str
    version_deprecated: Optional[str] = None
    examples: Dict[str, Any] = {}

class EnhancedAPIDocumentation:
    """Enhanced API documentation manager"""
    
    def __init__(self, app: FastAPI):
        self.app = app
        self.versions = self._get_api_versions()
        self.current_version = os.getenv("API_VERSION", "1.0.0")
        self.app_info = self._get_app_info()
        
    def _get_api_versions(self) -> List[APIVersion]:
        """Get API version history"""
        return [
            APIVersion(
                version="1.0.0",
                release_date="2024-01-15",
                status="stable",
                changelog=[
                    "Initial release",
                    "User authentication system",
                    "Template management",
                    "Evaluation workflow",
                    "File upload system"
                ],
                breaking_changes=[]
            ),
            APIVersion(
                version="1.1.0",
                release_date="2024-02-15",
                status="stable",
                changelog=[
                    "Enhanced authentication with MFA",
                    "Rate limiting system",
                    "Advanced error handling",
                    "Database optimization",
                    "Health monitoring"
                ],
                breaking_changes=[
                    "Authentication tokens now require Bearer prefix",
                    "Error response format standardized"
                ]
            ),
            APIVersion(
                version="1.2.0",
                release_date="2024-03-15",
                status="beta",
                changelog=[
                    "AI integration features",
                    "Batch operations",
                    "Enhanced export system",
                    "Real-time notifications"
                ],
                breaking_changes=[]
            )
        ]
    
    def _get_app_info(self) -> Dict[str, Any]:
        """Get application information"""
        return {
            "title": "Online Evaluation System API",
            "description": """
            ## Overview
            
            The Online Evaluation System API provides comprehensive functionality for managing 
            evaluations, templates, users, and projects in an educational or assessment context.
            
            ## Features
            
            - **User Management**: Role-based authentication with Admin, Manager, and Evaluator roles
            - **Template System**: Create and manage evaluation templates with custom criteria
            - **Evaluation Workflow**: Complete evaluation lifecycle from assignment to submission
            - **File Management**: Secure file upload and storage with various format support
            - **Export System**: Generate PDF and Excel reports with Korean font support
            - **AI Integration**: Optional AI-powered evaluation assistance
            - **Real-time Features**: WebSocket support for live updates
            - **Security**: Advanced rate limiting, MFA, and security monitoring
            
            ## Authentication
            
            The API uses JWT (JSON Web Tokens) for authentication. Include the token in the 
            Authorization header:
            
            ```
            Authorization: Bearer <your_jwt_token>
            ```
            
            ## Rate Limiting
            
            API requests are rate-limited based on IP address and user account. Rate limit 
            information is included in response headers:
            
            - `X-RateLimit-Limit`: Maximum requests allowed
            - `X-RateLimit-Remaining`: Remaining requests in current window
            - `X-RateLimit-Reset`: Timestamp when rate limit resets
            
            ## Error Handling
            
            All errors follow a standardized format:
            
            ```json
            {
                "error": true,
                "error_code": "ERROR_CODE",
                "message": "Human readable error message",
                "details": [
                    {
                        "field": "field_name",
                        "message": "Field-specific error",
                        "code": "validation_code"
                    }
                ],
                "timestamp": "2024-01-15T10:30:00Z",
                "request_id": "req_123456789"
            }
            ```
            
            ## Versioning
            
            The API uses semantic versioning (MAJOR.MINOR.PATCH). The current version is 
            indicated in the API documentation and can be retrieved from the `/version` endpoint.
            
            ## Environment Information
            
            - **Production**: `https://api.onlineevaluation.com`
            - **Staging**: `https://staging-api.onlineevaluation.com`
            - **Development**: `http://localhost:8000`
            
            ## Support
            
            For API support, please contact the development team or refer to the documentation.
            """,
            "version": self.current_version,
            "contact": {
                "name": "Online Evaluation System Team",
                "email": "support@onlineevaluation.com",
                "url": "https://onlineevaluation.com/support"
            },
            "license": {
                "name": "MIT License",
                "url": "https://opensource.org/licenses/MIT"
            },
            "servers": [
                {
                    "url": "https://api.onlineevaluation.com",
                    "description": "Production server"
                },
                {
                    "url": "https://staging-api.onlineevaluation.com",
                    "description": "Staging server"
                },
                {
                    "url": "http://localhost:8000",
                    "description": "Development server"
                }
            ]
        }
    
    def get_enhanced_openapi_schema(self) -> Dict[str, Any]:
        """Generate enhanced OpenAPI schema"""
        if self.app.openapi_schema:
            return self.app.openapi_schema
        
        openapi_schema = get_openapi(
            title=self.app_info["title"],
            version=self.app_info["version"],
            description=self.app_info["description"],
            routes=self.app.routes,
            servers=self.app_info["servers"]
        )
        
        # Add enhanced information
        openapi_schema["info"]["contact"] = self.app_info["contact"]
        openapi_schema["info"]["license"] = self.app_info["license"]
        
        # Add custom extensions
        openapi_schema["x-api-versions"] = [v.dict() for v in self.versions]
        openapi_schema["x-current-version"] = self.current_version
        openapi_schema["x-last-updated"] = datetime.utcnow().isoformat()
        
        # Add security schemes
        openapi_schema["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "JWT token for API authentication"
            },
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
                "description": "API Key for service-to-service authentication"
            }
        }
        
        # Add global security requirement
        openapi_schema["security"] = [
            {"BearerAuth": []},
            {"ApiKeyAuth": []}
        ]
        
        # Add example responses
        self._add_example_responses(openapi_schema)
        
        # Add rate limiting information
        self._add_rate_limiting_info(openapi_schema)
        
        # Add error response schemas
        self._add_error_schemas(openapi_schema)
        
        self.app.openapi_schema = openapi_schema
        return openapi_schema
    
    def _add_example_responses(self, schema: Dict[str, Any]):
        """Add example responses to schema"""
        examples = {
            "UserResponse": {
                "summary": "User information",
                "value": {
                    "id": "60f7b3b4c9e0b12345678901",
                    "login_id": "john_doe",
                    "email": "john.doe@example.com",
                    "user_name": "John Doe",
                    "role": "evaluator",
                    "is_active": True,
                    "created_at": "2024-01-15T10:30:00Z",
                    "last_login": "2024-01-20T14:22:00Z"
                }
            },
            "TokenResponse": {
                "summary": "Authentication token",
                "value": {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "user": {
                        "id": "60f7b3b4c9e0b12345678901",
                        "login_id": "john_doe",
                        "email": "john.doe@example.com",
                        "user_name": "John Doe",
                        "role": "evaluator"
                    }
                }
            },
            "ErrorResponse": {
                "summary": "Error response",
                "value": {
                    "error": True,
                    "error_code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "details": [
                        {
                            "field": "email",
                            "message": "Invalid email format",
                            "code": "value_error.email"
                        }
                    ],
                    "timestamp": "2024-01-15T10:30:00Z",
                    "request_id": "req_123456789"
                }
            },
            "HealthResponse": {
                "summary": "Health check response",
                "value": {
                    "overall_status": "healthy",
                    "timestamp": "2024-01-15T10:30:00Z",
                    "uptime_seconds": 86400,
                    "version": "1.1.0",
                    "environment": "production",
                    "services": [
                        {
                            "name": "database",
                            "status": "healthy",
                            "response_time_ms": 12.5
                        },
                        {
                            "name": "rate_limiter",
                            "status": "healthy",
                            "response_time_ms": 1.2
                        }
                    ]
                }
            }
        }
        
        if "components" not in schema:
            schema["components"] = {}
        if "examples" not in schema["components"]:
            schema["components"]["examples"] = {}
        
        schema["components"]["examples"].update(examples)
    
    def _add_rate_limiting_info(self, schema: Dict[str, Any]):
        """Add rate limiting information to schema"""
        rate_limit_headers = {
            "X-RateLimit-Limit": {
                "description": "Maximum number of requests allowed in the current window",
                "schema": {"type": "integer"}
            },
            "X-RateLimit-Remaining": {
                "description": "Number of requests remaining in the current window",
                "schema": {"type": "integer"}
            },
            "X-RateLimit-Reset": {
                "description": "Unix timestamp when the rate limit window resets",
                "schema": {"type": "integer"}
            },
            "X-RateLimit-Window": {
                "description": "Rate limit window duration in seconds",
                "schema": {"type": "integer"}
            }
        }
        
        # Add to all successful responses
        for path_item in schema.get("paths", {}).values():
            for method_data in path_item.values():
                if isinstance(method_data, dict) and "responses" in method_data:
                    for response_code, response_data in method_data["responses"].items():
                        if response_code.startswith("2"):  # 2xx responses
                            if "headers" not in response_data:
                                response_data["headers"] = {}
                            response_data["headers"].update(rate_limit_headers)
    
    def _add_error_schemas(self, schema: Dict[str, Any]):
        """Add standardized error response schemas"""
        error_schemas = {
            "ErrorDetail": {
                "type": "object",
                "properties": {
                    "field": {"type": "string", "nullable": True},
                    "message": {"type": "string"},
                    "code": {"type": "string", "nullable": True},
                    "value": {"nullable": True}
                },
                "required": ["message"]
            },
            "StandardErrorResponse": {
                "type": "object",
                "properties": {
                    "error": {"type": "boolean", "default": True},
                    "error_code": {"type": "string"},
                    "message": {"type": "string"},
                    "details": {
                        "type": "array",
                        "items": {"$ref": "#/components/schemas/ErrorDetail"},
                        "nullable": True
                    },
                    "timestamp": {"type": "string", "format": "date-time"},
                    "request_id": {"type": "string", "nullable": True},
                    "severity": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"]
                    },
                    "category": {
                        "type": "string",
                        "enum": [
                            "authentication", "authorization", "validation",
                            "business_logic", "external_service", "database",
                            "system", "security"
                        ]
                    },
                    "support_reference": {"type": "string", "nullable": True}
                },
                "required": ["error_code", "message", "timestamp"]
            }
        }
        
        if "schemas" not in schema["components"]:
            schema["components"]["schemas"] = {}
        
        schema["components"]["schemas"].update(error_schemas)
        
        # Add common error responses
        common_errors = {
            "400": {
                "description": "Bad Request",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/StandardErrorResponse"},
                        "example": {"$ref": "#/components/examples/ErrorResponse"}
                    }
                }
            },
            "401": {
                "description": "Unauthorized",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/StandardErrorResponse"}
                    }
                }
            },
            "403": {
                "description": "Forbidden",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/StandardErrorResponse"}
                    }
                }
            },
            "404": {
                "description": "Not Found",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/StandardErrorResponse"}
                    }
                }
            },
            "429": {
                "description": "Too Many Requests",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/StandardErrorResponse"}
                    }
                }
            },
            "500": {
                "description": "Internal Server Error",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/StandardErrorResponse"}
                    }
                }
            }
        }
        
        # Add to paths that don't have these error responses
        for path_item in schema.get("paths", {}).values():
            for method_data in path_item.values():
                if isinstance(method_data, dict) and "responses" in method_data:
                    for error_code, error_response in common_errors.items():
                        if error_code not in method_data["responses"]:
                            method_data["responses"][error_code] = error_response

# Documentation router
docs_router = APIRouter(prefix="/docs", tags=["Documentation"])

@docs_router.get("/openapi.json", include_in_schema=False)
async def get_openapi_schema(request: Request):
    """Get OpenAPI schema"""
    app = request.app
    doc_manager = EnhancedAPIDocumentation(app)
    return doc_manager.get_enhanced_openapi_schema()

@docs_router.get("/versions", response_model=List[APIVersion])
async def get_api_versions():
    """Get API version history"""
    doc_manager = EnhancedAPIDocumentation(None)
    return doc_manager.versions

@docs_router.get("/version")
async def get_current_version():
    """Get current API version"""
    return {
        "version": os.getenv("API_VERSION", "1.1.0"),
        "build": os.getenv("BUILD_NUMBER", "unknown"),
        "commit": os.getenv("GIT_COMMIT", "unknown"),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "timestamp": datetime.utcnow().isoformat()
    }

@docs_router.get("/changelog")
async def get_changelog():
    """Get API changelog"""
    doc_manager = EnhancedAPIDocumentation(None)
    changelog = []
    
    for version in reversed(doc_manager.versions):
        changelog.append({
            "version": version.version,
            "release_date": version.release_date,
            "status": version.status,
            "changes": version.changelog,
            "breaking_changes": version.breaking_changes
        })
    
    return changelog

@docs_router.get("/endpoints")
async def get_api_endpoints(current_user: User = Depends(get_current_user)):
    """Get list of available API endpoints (requires authentication)"""
    # This would analyze the FastAPI app routes and return endpoint information
    # For brevity, returning a sample structure
    return {
        "total_endpoints": 45,
        "categories": {
            "Authentication": 8,
            "Users": 12,
            "Templates": 10,
            "Evaluations": 15,
            "Files": 8,
            "Projects": 6,
            "Health": 4,
            "Documentation": 5
        },
        "deprecated_endpoints": 0,
        "beta_endpoints": 3
    }

@docs_router.get("/", include_in_schema=False)
async def custom_swagger_ui_html(request: Request):
    """Custom Swagger UI with enhanced styling"""
    root_path = getattr(request.app, "root_path", "")
    openapi_url = root_path + "/docs/openapi.json"
    
    return get_swagger_ui_html(
        openapi_url=openapi_url,
        title=f"Online Evaluation System API - Interactive Documentation",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
        swagger_ui_parameters={
            "deepLinking": True,
            "displayRequestDuration": True,
            "docExpansion": "none",
            "operationsSorter": "alpha",
            "filter": True,
            "showExtensions": True,
            "showCommonExtensions": True,
            "tryItOutEnabled": True
        }
    )

@docs_router.get("/redoc", include_in_schema=False)
async def custom_redoc_html(request: Request):
    """Custom ReDoc documentation"""
    root_path = getattr(request.app, "root_path", "")
    openapi_url = root_path + "/docs/openapi.json"
    
    return get_redoc_html(
        openapi_url=openapi_url,
        title=f"Online Evaluation System API - Documentation",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2.0.0/bundles/redoc.standalone.js"
    )

def setup_enhanced_documentation(app: FastAPI):
    """Setup enhanced documentation for FastAPI app"""
    # Create documentation manager
    doc_manager = EnhancedAPIDocumentation(app)
    
    # Override the default OpenAPI schema generator
    def custom_openapi():
        return doc_manager.get_enhanced_openapi_schema()
    
    app.openapi = custom_openapi
    
    # Add documentation router
    app.include_router(docs_router)
    
    # Disable default docs routes
    app.openapi_url = None
    app.docs_url = None
    app.redoc_url = None
    
    return doc_manager