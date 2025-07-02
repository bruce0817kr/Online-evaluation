"""
Test Suite for AI Model Management System
Unit tests for the AI model management service
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import json

from ai_model_management import (
    AIModelManagementService, AIModelConfig, ModelProvider, ModelStatus,
    TaskType, ModelRecommendation, SmartModelRecommender, LoadBalancer,
    ModelUsageStats, ModelPerformanceMetric
)
from ai_model_settings_endpoints import (
    CreateModelRequest, UpdateModelRequest, ModelRecommendationRequest,
    ModelTestRequest, DEFAULT_MODEL_TEMPLATES
)

class TestAIModelManagementService:
    """Unit tests for AIModelManagementService"""
    
    @pytest.fixture
    def service(self):
        """Create a test service instance"""
        mock_db = Mock()
        service = AIModelManagementService(db=mock_db)
        return service
    
    @pytest.fixture
    def sample_model_config(self):
        """Sample model configuration for testing"""
        return AIModelConfig(
            model_id="test-gpt4",
            provider=ModelProvider.OPENAI,
            model_name="gpt-4",
            display_name="Test GPT-4",
            api_endpoint="https://api.openai.com/v1",
            parameters={"temperature": 0.7},
            cost_per_token=0.00003,
            max_tokens=8192,
            context_window=8192,
            capabilities=["text-generation", "analysis"],
            quality_score=0.95,
            speed_score=0.7,
            cost_score=0.3,
            reliability_score=0.9
        )
    
    @pytest.mark.asyncio
    async def test_create_model_config(self, service, sample_model_config):
        """Test creating a new model configuration"""
        # Mock database operations
        service.db.ai_model_configs.find_one = AsyncMock(return_value=None)
        service.db.ai_model_configs.insert_one = AsyncMock()
        
        # Create model
        result = await service.create_model_config(sample_model_config)
        
        # Assertions
        assert result.model_id == "test-gpt4"
        assert result.provider == ModelProvider.OPENAI
        assert service.model_registry["test-gpt4"] == sample_model_config
        service.db.ai_model_configs.insert_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_duplicate_model(self, service, sample_model_config):
        """Test creating a duplicate model should fail"""
        # Add model to registry
        service.model_registry[sample_model_config.model_id] = sample_model_config
        
        # Attempt to create duplicate
        with pytest.raises(ValueError, match="already exists"):
            await service.create_model_config(sample_model_config)
    
    @pytest.mark.asyncio
    async def test_update_model_config(self, service, sample_model_config):
        """Test updating an existing model configuration"""
        # Add model to registry
        service.model_registry[sample_model_config.model_id] = sample_model_config
        service.db.ai_model_configs.update_one = AsyncMock()
        
        # Update configuration
        updates = {
            "display_name": "Updated GPT-4",
            "cost_per_token": 0.00004,
            "quality_score": 0.98
        }
        
        result = await service.update_model_config(sample_model_config.model_id, updates)
        
        # Assertions
        assert result.display_name == "Updated GPT-4"
        assert result.cost_per_token == 0.00004
        assert result.quality_score == 0.98
        service.db.ai_model_configs.update_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_model(self, service, sample_model_config):
        """Test deleting a model"""
        # Add model to registry
        service.model_registry[sample_model_config.model_id] = sample_model_config
        service.db.ai_model_configs.delete_one = AsyncMock()
        
        # Delete model
        result = await service.delete_model(sample_model_config.model_id)
        
        # Assertions
        assert result is True
        assert sample_model_config.model_id not in service.model_registry
        service.db.ai_model_configs.delete_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_default_model_protection(self, service, sample_model_config):
        """Test that default models cannot be deleted"""
        # Set as default model
        sample_model_config.is_default = True
        service.model_registry[sample_model_config.model_id] = sample_model_config
        
        # Attempt to delete
        with pytest.raises(ValueError, match="Cannot delete default model"):
            await service.delete_model(sample_model_config.model_id)
    
    @pytest.mark.asyncio
    async def test_get_available_models(self, service, sample_model_config):
        """Test getting available models"""
        # Add multiple models
        service.model_registry["model1"] = sample_model_config
        inactive_model = sample_model_config.copy()
        inactive_model.model_id = "model2"
        inactive_model.status = ModelStatus.INACTIVE
        service.model_registry["model2"] = inactive_model
        
        # Get only active models
        active_models = await service.get_available_models(include_inactive=False)
        assert len(active_models) == 1
        assert active_models[0].model_id == "model1"
        
        # Get all models
        all_models = await service.get_available_models(include_inactive=True)
        assert len(all_models) == 2
    
    @pytest.mark.asyncio
    async def test_test_model_connection(self, service, sample_model_config):
        """Test model connection testing"""
        # Add model to registry
        service.model_registry[sample_model_config.model_id] = sample_model_config
        
        # Mock the actual API call
        with patch('ai_model_management.AIModelManagementService._call_model_api') as mock_call:
            mock_call.return_value = {
                "success": True,
                "response": "Test successful",
                "latency": 0.5
            }
            
            result = await service.test_model_connection(sample_model_config.model_id)
            
            # Assertions
            assert result["is_healthy"] is True
            assert result["model_id"] == sample_model_config.model_id
            assert "test_results" in result
            assert result["health_score"] > 0
    
    @pytest.mark.asyncio
    async def test_track_usage(self, service, sample_model_config):
        """Test usage tracking"""
        # Add model to registry
        service.model_registry[sample_model_config.model_id] = sample_model_config
        
        # Track usage
        await service.track_usage(
            model_id=sample_model_config.model_id,
            tokens_used=100,
            response_time=1.5,
            success=True
        )
        
        # Check metrics
        assert sample_model_config.model_id in service.usage_metrics
        metrics = service.usage_metrics[sample_model_config.model_id]
        assert metrics.total_requests == 1
        assert metrics.total_tokens == 100
        assert metrics.total_cost == 100 * sample_model_config.cost_per_token
    
    @pytest.mark.asyncio
    async def test_get_performance_metrics(self, service, sample_model_config):
        """Test getting performance metrics"""
        # Add model and track some usage
        service.model_registry[sample_model_config.model_id] = sample_model_config
        
        # Track multiple requests
        for i in range(5):
            await service.track_usage(
                model_id=sample_model_config.model_id,
                tokens_used=100 + i * 10,
                response_time=1.0 + i * 0.1,
                success=True
            )
        
        # Get metrics
        metrics = await service.get_performance_metrics(
            model_id=sample_model_config.model_id,
            period_days=1
        )
        
        # Assertions
        assert metrics["total_requests"] == 5
        assert metrics["avg_response_time"] == pytest.approx(1.2, 0.01)
        assert metrics["total_tokens"] == 550
    
    @pytest.mark.asyncio
    async def test_clear_default_models(self, service):
        """Test clearing all default model settings"""
        # Add models with one as default
        model1 = AIModelConfig(model_id="model1", provider=ModelProvider.OPENAI, 
                              model_name="gpt-3.5", display_name="GPT-3.5", is_default=True)
        model2 = AIModelConfig(model_id="model2", provider=ModelProvider.ANTHROPIC,
                              model_name="claude-2", display_name="Claude 2", is_default=True)
        
        service.model_registry = {"model1": model1, "model2": model2}
        service.db.ai_model_configs.update_many = AsyncMock()
        
        # Clear defaults
        await service.clear_default_models()
        
        # Assertions
        assert not model1.is_default
        assert not model2.is_default
        service.db.ai_model_configs.update_many.assert_called_once()


class TestSmartModelRecommender:
    """Unit tests for SmartModelRecommender"""
    
    @pytest.fixture
    def recommender(self):
        """Create a test recommender instance"""
        return SmartModelRecommender()
    
    @pytest.fixture
    def model_configs(self):
        """Sample model configurations for testing"""
        return [
            AIModelConfig(
                model_id="budget-model",
                provider=ModelProvider.OPENAI,
                model_name="gpt-3.5-turbo",
                display_name="Budget Model",
                cost_per_token=0.000002,
                quality_score=0.7,
                speed_score=0.9,
                cost_score=0.95,
                reliability_score=0.85,
                capabilities=["text-generation", "evaluation"]
            ),
            AIModelConfig(
                model_id="quality-model",
                provider=ModelProvider.OPENAI,
                model_name="gpt-4",
                display_name="Quality Model",
                cost_per_token=0.00003,
                quality_score=0.95,
                speed_score=0.7,
                cost_score=0.3,
                reliability_score=0.9,
                capabilities=["text-generation", "analysis", "evaluation"]
            ),
            AIModelConfig(
                model_id="speed-model",
                provider=ModelProvider.ANTHROPIC,
                model_name="claude-instant",
                display_name="Speed Model",
                cost_per_token=0.000001,
                quality_score=0.6,
                speed_score=0.95,
                cost_score=0.98,
                reliability_score=0.8,
                capabilities=["text-generation", "summary"]
            )
        ]
    
    def test_recommend_budget_conscious(self, recommender, model_configs):
        """Test recommendation for budget-conscious users"""
        recommendation = recommender.recommend_model(
            models=model_configs,
            budget="low",
            quality_level="medium",
            speed_requirement="medium",
            task_type=TaskType.EVALUATION
        )
        
        # Should recommend the budget model
        assert recommendation.model_id == "budget-model"
        assert recommendation.confidence > 0.7
        assert "budget" in recommendation.reasoning.lower()
    
    def test_recommend_quality_focused(self, recommender, model_configs):
        """Test recommendation for quality-focused users"""
        recommendation = recommender.recommend_model(
            models=model_configs,
            budget="high",
            quality_level="high",
            speed_requirement="low",
            task_type=TaskType.ANALYSIS
        )
        
        # Should recommend the quality model
        assert recommendation.model_id == "quality-model"
        assert recommendation.confidence > 0.8
        assert "quality" in recommendation.reasoning.lower()
    
    def test_recommend_speed_critical(self, recommender, model_configs):
        """Test recommendation for speed-critical tasks"""
        recommendation = recommender.recommend_model(
            models=model_configs,
            budget="medium",
            quality_level="low",
            speed_requirement="high",
            task_type=TaskType.SUMMARY
        )
        
        # Should recommend the speed model
        assert recommendation.model_id == "speed-model"
        assert recommendation.confidence > 0.7
        assert "speed" in recommendation.reasoning.lower()
    
    def test_recommend_with_task_capability_filter(self, recommender, model_configs):
        """Test that recommendations respect task capabilities"""
        # Only budget and quality models have "evaluation" capability
        recommendation = recommender.recommend_model(
            models=model_configs,
            budget="low",
            quality_level="low",
            speed_requirement="high",
            task_type=TaskType.EVALUATION
        )
        
        # Should not recommend speed model even though it matches other criteria
        assert recommendation.model_id in ["budget-model", "quality-model"]
    
    def test_calculate_weighted_score(self, recommender):
        """Test weighted score calculation"""
        model = AIModelConfig(
            model_id="test",
            provider=ModelProvider.OPENAI,
            model_name="test",
            display_name="Test",
            quality_score=0.8,
            speed_score=0.6,
            cost_score=0.9,
            reliability_score=0.7
        )
        
        # Equal weights
        score = recommender._calculate_weighted_score(
            model, 
            quality_weight=0.25,
            speed_weight=0.25,
            cost_weight=0.25,
            reliability_weight=0.25
        )
        assert score == pytest.approx(0.75, 0.01)
        
        # Quality-focused weights
        score = recommender._calculate_weighted_score(
            model,
            quality_weight=0.7,
            speed_weight=0.1,
            cost_weight=0.1,
            reliability_weight=0.1
        )
        assert score > 0.75  # Should be higher due to high quality score


class TestLoadBalancer:
    """Unit tests for LoadBalancer"""
    
    @pytest.fixture
    def load_balancer(self):
        """Create a test load balancer instance"""
        return LoadBalancer()
    
    @pytest.fixture
    def model_configs(self):
        """Sample model configurations for load balancing"""
        return [
            AIModelConfig(
                model_id="model1",
                provider=ModelProvider.OPENAI,
                model_name="gpt-3.5",
                display_name="Model 1",
                status=ModelStatus.ACTIVE,
                reliability_score=0.9
            ),
            AIModelConfig(
                model_id="model2",
                provider=ModelProvider.ANTHROPIC,
                model_name="claude-2",
                display_name="Model 2",
                status=ModelStatus.ACTIVE,
                reliability_score=0.8
            ),
            AIModelConfig(
                model_id="model3",
                provider=ModelProvider.GOOGLE,
                model_name="palm-2",
                display_name="Model 3",
                status=ModelStatus.MAINTENANCE,
                reliability_score=0.85
            )
        ]
    
    def test_select_model_round_robin(self, load_balancer, model_configs):
        """Test round-robin model selection"""
        # Only active models
        active_models = [m for m in model_configs if m.status == ModelStatus.ACTIVE]
        
        # Select models multiple times
        selections = []
        for _ in range(4):
            selected = load_balancer.select_model(active_models)
            selections.append(selected.model_id)
        
        # Should alternate between model1 and model2
        assert selections[0] != selections[1]
        assert selections[2] != selections[3]
        assert set(selections) == {"model1", "model2"}
    
    def test_select_model_weighted(self, load_balancer, model_configs):
        """Test weighted model selection"""
        active_models = [m for m in model_configs if m.status == ModelStatus.ACTIVE]
        
        # Track selections over many iterations
        selection_counts = {"model1": 0, "model2": 0}
        for _ in range(100):
            selected = load_balancer.select_model(active_models, strategy="weighted")
            selection_counts[selected.model_id] += 1
        
        # Model1 with higher reliability should be selected more often
        assert selection_counts["model1"] > selection_counts["model2"]
    
    def test_circuit_breaker_activation(self, load_balancer):
        """Test circuit breaker activation on failures"""
        model_id = "test-model"
        
        # Record multiple failures
        for _ in range(5):
            load_balancer.record_failure(model_id)
        
        # Check if circuit is open
        assert load_balancer.is_circuit_open(model_id) is True
    
    def test_circuit_breaker_recovery(self, load_balancer):
        """Test circuit breaker recovery after timeout"""
        model_id = "test-model"
        
        # Open circuit
        for _ in range(5):
            load_balancer.record_failure(model_id)
        
        assert load_balancer.is_circuit_open(model_id) is True
        
        # Simulate time passing
        breaker = load_balancer.circuit_breakers[model_id]
        breaker.last_failure_time = datetime.utcnow() - timedelta(minutes=6)
        
        # Circuit should be closed now
        assert load_balancer.is_circuit_open(model_id) is False


class TestModelTemplates:
    """Test model template functionality"""
    
    def test_all_templates_valid(self):
        """Test that all default templates are valid"""
        for name, template in DEFAULT_MODEL_TEMPLATES.items():
            # Check required fields
            assert template.name == name
            assert template.provider in ModelProvider
            assert isinstance(template.display_name, str)
            assert isinstance(template.description, str)
            assert isinstance(template.capabilities, list)
            assert len(template.capabilities) > 0
            
            # Check score ranges
            assert 0 <= template.quality_score <= 1
            assert 0 <= template.speed_score <= 1
            assert 0 <= template.cost_score <= 1
            assert 0 <= template.reliability_score <= 1
            
            # Check numeric fields
            assert template.cost_per_token >= 0
            assert template.max_tokens > 0
            assert template.context_window > 0
    
    def test_template_categories(self):
        """Test that templates cover different use cases"""
        providers = set()
        has_budget = False
        has_quality = False
        has_speed = False
        
        for template in DEFAULT_MODEL_TEMPLATES.values():
            providers.add(template.provider)
            
            if template.cost_score > 0.8:
                has_budget = True
            if template.quality_score > 0.8:
                has_quality = True
            if template.speed_score > 0.8:
                has_speed = True
        
        # Should have diverse providers
        assert len(providers) >= 3
        
        # Should have options for different priorities
        assert has_budget, "Should have budget-friendly options"
        assert has_quality, "Should have high-quality options"
        assert has_speed, "Should have high-speed options"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])