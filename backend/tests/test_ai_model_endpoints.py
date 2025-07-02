"""
Integration Tests for AI Model Management API Endpoints
Tests the FastAPI endpoints with real HTTP requests
"""

import pytest
import asyncio
import json
from httpx import AsyncClient
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from server import app
from ai_model_settings_endpoints import (
    CreateModelRequest, UpdateModelRequest, ModelRecommendationRequest
)
from ai_model_management import AIModelConfig, ModelProvider, ModelStatus, TaskType

class TestAIModelEndpoints:
    """Integration tests for AI Model API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def admin_headers(self):
        """Mock headers for admin user"""
        # In real implementation, this would be a valid JWT token
        return {"Authorization": "Bearer admin-token"}
    
    @pytest.fixture
    def secretary_headers(self):
        """Mock headers for secretary user"""
        return {"Authorization": "Bearer secretary-token"}
    
    @pytest.fixture
    def evaluator_headers(self):
        """Mock headers for evaluator user"""
        return {"Authorization": "Bearer evaluator-token"}
    
    @pytest.fixture
    def sample_model_data(self):
        """Sample model data for testing"""
        return {
            "model_id": "test-model",
            "provider": "openai",
            "model_name": "gpt-4",
            "display_name": "Test GPT-4",
            "api_endpoint": "https://api.openai.com/v1",
            "parameters": {"temperature": 0.7},
            "cost_per_token": 0.00003,
            "max_tokens": 8192,
            "context_window": 8192,
            "capabilities": ["text-generation", "analysis"],
            "quality_score": 0.95,
            "speed_score": 0.7,
            "cost_score": 0.3,
            "reliability_score": 0.9,
            "is_default": False
        }
    
    @patch('ai_model_management.ai_model_service')
    def test_get_available_models_success(self, mock_service, client, admin_headers):
        """Test getting available models successfully"""
        # Mock service response
        mock_models = [
            AIModelConfig(
                model_id="gpt-4",
                provider=ModelProvider.OPENAI,
                model_name="gpt-4",
                display_name="GPT-4",
                status=ModelStatus.ACTIVE
            ),
            AIModelConfig(
                model_id="claude-3",
                provider=ModelProvider.ANTHROPIC,
                model_name="claude-3-opus",
                display_name="Claude 3 Opus",
                status=ModelStatus.INACTIVE
            )
        ]
        mock_service.get_available_models = AsyncMock(return_value=mock_models)
        
        # Test request
        response = client.get("/api/ai-models/available", headers=admin_headers)
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["model_id"] == "gpt-4"
        assert data[1]["model_id"] == "claude-3"
    
    @patch('ai_model_management.ai_model_service')
    def test_get_available_models_active_only(self, mock_service, client, admin_headers):
        """Test getting only active models"""
        mock_models = [
            AIModelConfig(
                model_id="gpt-4",
                provider=ModelProvider.OPENAI,
                model_name="gpt-4",
                display_name="GPT-4",
                status=ModelStatus.ACTIVE
            )
        ]
        mock_service.get_available_models = AsyncMock(return_value=mock_models)
        
        # Test request for active only
        response = client.get("/api/ai-models/available?include_inactive=false", headers=admin_headers)
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "active"
        
        mock_service.get_available_models.assert_called_with(include_inactive=False)
    
    @patch('ai_model_management.ai_model_service')
    def test_create_model_success(self, mock_service, client, admin_headers, sample_model_data):
        """Test creating a new model successfully"""
        # Mock service response
        created_model = AIModelConfig(**sample_model_data)
        mock_service.create_model_config = AsyncMock(return_value=created_model)
        
        # Test request
        response = client.post("/api/ai-models/create", 
                             headers=admin_headers, 
                             json=sample_model_data)
        
        # Assertions
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "Model created successfully"
        assert data["model"]["model_id"] == "test-model"
        
        mock_service.create_model_config.assert_called_once()
    
    @patch('ai_model_management.ai_model_service')
    def test_create_model_duplicate_error(self, mock_service, client, admin_headers, sample_model_data):
        """Test creating a duplicate model returns error"""
        # Mock service error
        mock_service.create_model_config = AsyncMock(side_effect=ValueError("Model already exists"))
        
        # Test request
        response = client.post("/api/ai-models/create", 
                             headers=admin_headers, 
                             json=sample_model_data)
        
        # Assertions
        assert response.status_code == 400
        data = response.json()
        assert "already exists" in data["detail"]
    
    def test_create_model_invalid_data(self, client, admin_headers):
        """Test creating model with invalid data"""
        invalid_data = {
            "model_id": "INVALID-ID",  # Should be lowercase
            "provider": "invalid_provider",
            "model_name": "",  # Required field
            "display_name": "Test"
        }
        
        response = client.post("/api/ai-models/create", 
                             headers=admin_headers, 
                             json=invalid_data)
        
        # Should return validation error
        assert response.status_code == 422
    
    @patch('ai_model_management.ai_model_service')
    def test_update_model_success(self, mock_service, client, admin_headers):
        """Test updating a model successfully"""
        # Mock service response
        updated_model = AIModelConfig(
            model_id="test-model",
            provider=ModelProvider.OPENAI,
            model_name="gpt-4",
            display_name="Updated GPT-4",
            cost_per_token=0.00004
        )
        mock_service.update_model_config = AsyncMock(return_value=updated_model)
        
        update_data = {
            "display_name": "Updated GPT-4",
            "cost_per_token": 0.00004
        }
        
        # Test request
        response = client.put("/api/ai-models/test-model", 
                            headers=admin_headers, 
                            json=update_data)
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Model updated successfully"
        assert data["model"]["display_name"] == "Updated GPT-4"
    
    @patch('ai_model_management.ai_model_service')
    def test_update_model_not_found(self, mock_service, client, admin_headers):
        """Test updating non-existent model"""
        mock_service.update_model_config = AsyncMock(side_effect=ValueError("Model not found"))
        
        update_data = {"display_name": "Updated Name"}
        
        response = client.put("/api/ai-models/nonexistent", 
                            headers=admin_headers, 
                            json=update_data)
        
        assert response.status_code == 404
    
    @patch('ai_model_management.ai_model_service')
    def test_delete_model_success(self, mock_service, client, admin_headers):
        """Test deleting a model successfully"""
        mock_service.delete_model = AsyncMock(return_value=True)
        
        response = client.delete("/api/ai-models/test-model", headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Model deleted successfully"
    
    @patch('ai_model_management.ai_model_service')
    def test_delete_model_protected(self, mock_service, client, admin_headers):
        """Test deleting a protected model"""
        mock_service.delete_model = AsyncMock(side_effect=ValueError("Cannot delete default model"))
        
        response = client.delete("/api/ai-models/protected-model", headers=admin_headers)
        
        assert response.status_code == 400
        data = response.json()
        assert "Cannot delete" in data["detail"]
    
    @patch('ai_model_management.ai_model_service')
    def test_get_model_details_success(self, mock_service, client, admin_headers):
        """Test getting model details successfully"""
        mock_model = AIModelConfig(
            model_id="test-model",
            provider=ModelProvider.OPENAI,
            model_name="gpt-4",
            display_name="Test GPT-4"
        )
        mock_service.get_model_config = AsyncMock(return_value=mock_model)
        
        response = client.get("/api/ai-models/test-model", headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["model_id"] == "test-model"
        assert data["display_name"] == "Test GPT-4"
    
    @patch('ai_model_management.ai_model_service')
    def test_test_model_connection_success(self, mock_service, client, admin_headers):
        """Test model connection testing successfully"""
        mock_result = {
            "model_id": "test-model",
            "is_healthy": True,
            "health_score": 0.95,
            "test_results": [
                {"name": "basic_connection", "success": True, "latency": 0.5},
                {"name": "korean_processing", "success": True, "latency": 0.7}
            ],
            "avg_response_time": 0.6,
            "successful_tests": 2,
            "total_tests": 2
        }
        mock_service.test_model_connection = AsyncMock(return_value=mock_result)
        
        response = client.post("/api/ai-models/test-model/test-connection", headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_healthy"] is True
        assert data["health_score"] == 0.95
        assert len(data["test_results"]) == 2
    
    @patch('ai_model_management.ai_model_service')
    def test_test_model_connection_failure(self, mock_service, client, admin_headers):
        """Test model connection testing with failures"""
        mock_result = {
            "model_id": "test-model",
            "is_healthy": False,
            "health_score": 0.2,
            "test_results": [
                {"name": "basic_connection", "success": False, "error": "Connection timeout"},
                {"name": "korean_processing", "success": True, "latency": 0.7}
            ],
            "avg_response_time": None,
            "successful_tests": 1,
            "total_tests": 2
        }
        mock_service.test_model_connection = AsyncMock(return_value=mock_result)
        
        response = client.post("/api/ai-models/test-model/test-connection", headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_healthy"] is False
        assert data["health_score"] == 0.2
        assert data["successful_tests"] == 1
    
    @patch('ai_model_management.DEFAULT_MODEL_TEMPLATES')
    def test_get_templates_list(self, mock_templates, client, admin_headers):
        """Test getting templates list"""
        mock_templates.items.return_value = [
            ("openai-gpt4", {
                "name": "openai-gpt4",
                "provider": "openai",
                "display_name": "GPT-4 Template",
                "description": "High-quality evaluation model",
                "capabilities": ["text-generation", "evaluation"]
            })
        ]
        
        response = client.get("/api/ai-models/templates/list", headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "templates" in data
    
    @patch('ai_model_management.ai_model_service')
    def test_create_from_template_success(self, mock_service, client, admin_headers):
        """Test creating model from template successfully"""
        mock_model = AIModelConfig(
            model_id="template-created",
            provider=ModelProvider.OPENAI,
            model_name="gpt-4",
            display_name="Template Created Model"
        )
        mock_service.create_model_from_template = AsyncMock(return_value=mock_model)
        
        response = client.post("/api/ai-models/templates/openai-gpt4/create", headers=admin_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "Model created from template successfully"
        assert data["model"]["model_id"] == "template-created"
    
    @patch('ai_model_management.smart_recommender')
    def test_recommend_model_success(self, mock_recommender, client, admin_headers):
        """Test model recommendation successfully"""
        from ai_model_management import ModelRecommendation
        
        mock_recommendation = ModelRecommendation(
            model_id="recommended-model",
            confidence=0.85,
            reasoning="Best balance of quality and cost for evaluation tasks",
            estimated_cost=0.05,
            estimated_quality=0.9
        )
        mock_recommender.recommend_model = Mock(return_value=mock_recommendation)
        
        request_data = {
            "budget": "medium",
            "quality_level": "high",
            "speed_requirement": "medium",
            "task_type": "evaluation",
            "estimated_tokens": 1000,
            "estimated_requests_per_month": 100
        }
        
        response = client.post("/api/ai-models/optimize/recommend", 
                             headers=admin_headers, 
                             json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["model_id"] == "recommended-model"
        assert data["confidence"] == 0.85
        assert "evaluation tasks" in data["reasoning"]
    
    @patch('ai_model_management.ai_model_service')
    def test_get_performance_metrics_success(self, mock_service, client, admin_headers):
        """Test getting performance metrics successfully"""
        mock_metrics = {
            "model_id": "test-model",
            "period_days": 7,
            "total_requests": 150,
            "total_tokens": 50000,
            "total_cost": 1.5,
            "avg_response_time": 1.2,
            "error_rate": 0.02,
            "quality_score": 0.92,
            "user_satisfaction": 0.88
        }
        mock_service.get_performance_metrics = AsyncMock(return_value=mock_metrics)
        
        response = client.get("/api/ai-models/test-model/metrics?period_days=7", headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_requests"] == 150
        assert data["avg_response_time"] == 1.2
        assert data["error_rate"] == 0.02
    
    def test_unauthorized_access(self, client):
        """Test unauthorized access to endpoints"""
        # No headers
        response = client.get("/api/ai-models/available")
        assert response.status_code == 401
        
        # Invalid token
        invalid_headers = {"Authorization": "Bearer invalid-token"}
        response = client.get("/api/ai-models/available", headers=invalid_headers)
        assert response.status_code == 401
    
    @patch('security.check_admin_or_secretary')
    def test_evaluator_access_denied(self, mock_check, client, evaluator_headers):
        """Test evaluator access is denied for management operations"""
        mock_check.side_effect = HTTPException(status_code=403, detail="Access denied")
        
        response = client.post("/api/ai-models/create", 
                             headers=evaluator_headers, 
                             json={"model_id": "test"})
        
        assert response.status_code == 403
    
    @patch('ai_model_management.ai_model_service')
    def test_clear_default_models_success(self, mock_service, client, admin_headers):
        """Test clearing all default models successfully"""
        mock_service.clear_default_models = AsyncMock()
        
        response = client.post("/api/ai-models/admin/clear-defaults", headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "All default model settings cleared"
        mock_service.clear_default_models.assert_called_once()
    
    @patch('ai_model_management.ai_model_service')
    def test_bulk_model_operations(self, mock_service, client, admin_headers):
        """Test bulk operations on models"""
        # Mock bulk update
        mock_service.bulk_update_models = AsyncMock(return_value=3)
        
        bulk_data = {
            "model_ids": ["model1", "model2", "model3"],
            "updates": {"status": "maintenance"}
        }
        
        response = client.put("/api/ai-models/bulk-update", 
                            headers=admin_headers, 
                            json=bulk_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["updated_count"] == 3
    
    @patch('ai_model_management.ai_model_service')
    def test_model_health_monitoring(self, mock_service, client, admin_headers):
        """Test model health monitoring endpoint"""
        mock_health_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_models": 5,
            "healthy_models": 4,
            "unhealthy_models": 1,
            "models_in_maintenance": 0,
            "overall_health_score": 0.82,
            "model_status": [
                {"model_id": "gpt-4", "status": "healthy", "health_score": 0.95},
                {"model_id": "claude-3", "status": "healthy", "health_score": 0.88},
                {"model_id": "failing-model", "status": "unhealthy", "health_score": 0.15}
            ]
        }
        mock_service.get_health_status = AsyncMock(return_value=mock_health_data)
        
        response = client.get("/api/ai-models/health/status", headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_models"] == 5
        assert data["healthy_models"] == 4
        assert data["overall_health_score"] == 0.82
        assert len(data["model_status"]) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])