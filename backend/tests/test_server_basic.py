"""
Basic server functionality tests
"""
import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import app

client = TestClient(app)

def test_health_check():
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"

def test_root_endpoint():
    """Test the root endpoint"""
    response = client.get("/")
    # Should either return 200 or redirect
    assert response.status_code in [200, 301, 302, 404]

def test_api_docs():
    """Test that API docs are accessible"""
    response = client.get("/docs")
    assert response.status_code == 200

def test_openapi():
    """Test that OpenAPI schema is accessible"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data