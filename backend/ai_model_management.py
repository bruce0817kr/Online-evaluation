"""
AI Model Management Service
AI 모델 관리, 설정, 성능 모니터링 및 스마트 추천 시스템
"""

from fastapi import HTTPException
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from enum import Enum
import logging
import asyncio
import json
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)

# Enums and Models
class ModelProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    COHERE = "cohere"
    NOVITA = "novita"
    LOCAL = "local"

class ModelStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    ERROR = "error"

class TaskType(str, Enum):
    EVALUATION = "evaluation"
    SUMMARY = "summary"
    ANALYSIS = "analysis"
    TRANSLATION = "translation"
    RECOMMENDATION = "recommendation"

@dataclass
class ModelRecommendation:
    model_id: str
    confidence: float
    reasoning: str
    estimated_cost: float
    estimated_quality: float

class AIModelConfig(BaseModel):
    model_id: str = Field(..., description="고유 모델 ID")
    provider: ModelProvider = Field(..., description="AI 모델 제공업체")
    model_name: str = Field(..., description="모델명")
    display_name: str = Field(..., description="표시용 이름")
    api_endpoint: Optional[str] = Field(None, description="API 엔드포인트")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="모델 매개변수")
    cost_per_token: float = Field(0.0, description="토큰당 비용")
    max_tokens: int = Field(4096, description="최대 토큰 수")
    context_window: int = Field(4096, description="컨텍스트 윈도우 크기")
    supports_streaming: bool = Field(True, description="스트리밍 지원 여부")
    capabilities: List[str] = Field(default_factory=list, description="모델 기능 목록")
    status: ModelStatus = Field(ModelStatus.ACTIVE, description="모델 상태")
    is_default: bool = Field(False, description="기본 모델 여부")
    quality_score: float = Field(0.0, description="품질 점수 (0-1)")
    speed_score: float = Field(0.0, description="속도 점수 (0-1)")
    cost_score: float = Field(0.0, description="비용 효율성 점수 (0-1)")
    reliability_score: float = Field(0.0, description="안정성 점수 (0-1)")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ModelUsageStats(BaseModel):
    model_id: str
    date: datetime
    total_requests: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    avg_response_time: float = 0.0
    error_rate: float = 0.0
    quality_score: float = 0.0
    user_satisfaction: float = 0.0

class ModelPerformanceMetric(BaseModel):
    model_id: str
    metric_type: str  # quality, speed, cost, reliability
    value: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    context: Dict[str, Any] = Field(default_factory=dict)

class ModelComparisonRequest(BaseModel):
    model_ids: List[str] = Field(..., description="비교할 모델 ID 목록")
    test_prompt: str = Field(..., description="테스트 프롬프트")
    task_type: TaskType = Field(TaskType.EVALUATION, description="작업 유형")
    max_tokens: Optional[int] = Field(None, description="최대 토큰 수")

class AIModelManagementService:
    """AI 모델 관리 핵심 서비스"""
    
    def __init__(self, db=None):
        self.db = db
        self.model_registry: Dict[str, AIModelConfig] = {}
        self.performance_cache: Dict[str, Dict] = {}
        self.usage_stats: Dict[str, List[ModelUsageStats]] = {}
        self.health_status: Dict[str, bool] = {}
        
        # Initialize with default models
        self._initialize_default_models()
        
    def _initialize_default_models(self):
        """기본 AI 모델들을 초기화"""
        default_models = [
            AIModelConfig(
                model_id="gpt-4",
                provider=ModelProvider.OPENAI,
                model_name="gpt-4",
                display_name="GPT-4 (OpenAI)",
                cost_per_token=0.00003,
                max_tokens=8192,
                context_window=8192,
                capabilities=["text-generation", "analysis", "code", "reasoning"],
                quality_score=0.95,
                speed_score=0.75,
                cost_score=0.60,
                reliability_score=0.90,
                is_default=True
            ),
            AIModelConfig(
                model_id="gpt-3.5-turbo",
                provider=ModelProvider.OPENAI,
                model_name="gpt-3.5-turbo",
                display_name="GPT-3.5 Turbo (OpenAI)",
                cost_per_token=0.000002,
                max_tokens=4096,
                context_window=4096,
                capabilities=["text-generation", "analysis", "code"],
                quality_score=0.85,
                speed_score=0.90,
                cost_score=0.95,
                reliability_score=0.95
            ),
            AIModelConfig(
                model_id="claude-3-opus",
                provider=ModelProvider.ANTHROPIC,
                model_name="claude-3-opus-20240229",
                display_name="Claude 3 Opus (Anthropic)",
                cost_per_token=0.000015,
                max_tokens=4096,
                context_window=200000,
                capabilities=["text-generation", "analysis", "reasoning", "safety"],
                quality_score=0.98,
                speed_score=0.70,
                cost_score=0.70,
                reliability_score=0.92
            ),
            AIModelConfig(
                model_id="gemini-pro",
                provider=ModelProvider.GOOGLE,
                model_name="gemini-pro",
                display_name="Gemini Pro (Google)",
                cost_per_token=0.0000005,
                max_tokens=2048,
                context_window=30720,
                capabilities=["text-generation", "analysis", "multimodal"],
                quality_score=0.88,
                speed_score=0.85,
                cost_score=0.98,
                reliability_score=0.88
            ),
            # Novita AI Models
            AIModelConfig(
                model_id="deepseek-r1",
                provider=ModelProvider.NOVITA,
                model_name="deepseek/deepseek-r1",
                display_name="DeepSeek R1 (Novita AI)",
                api_endpoint="https://api.novita.ai/v3/openai",
                cost_per_token=0.000001,
                max_tokens=4096,
                context_window=8192,
                capabilities=["text-generation", "reasoning", "analysis", "coding"],
                quality_score=0.92,
                speed_score=0.88,
                cost_score=0.95,
                reliability_score=0.90
            ),
            AIModelConfig(
                model_id="deepseek-chat",
                provider=ModelProvider.NOVITA,
                model_name="deepseek/deepseek-chat",
                display_name="DeepSeek Chat (Novita AI)",
                api_endpoint="https://api.novita.ai/v3/openai",
                cost_per_token=0.0000008,
                max_tokens=4096,
                context_window=8192,
                capabilities=["text-generation", "conversation", "analysis"],
                quality_score=0.87,
                speed_score=0.90,
                cost_score=0.97,
                reliability_score=0.88
            ),
            AIModelConfig(
                model_id="qwen2-72b",
                provider=ModelProvider.NOVITA,
                model_name="qwen/qwen2-72b-instruct",
                display_name="Qwen2 72B (Novita AI)",
                api_endpoint="https://api.novita.ai/v3/openai",
                cost_per_token=0.000002,
                max_tokens=4096,
                context_window=8192,
                capabilities=["text-generation", "analysis", "multilingual"],
                quality_score=0.89,
                speed_score=0.85,
                cost_score=0.92,
                reliability_score=0.87
            ),
            AIModelConfig(
                model_id="llama3-8b",
                provider=ModelProvider.NOVITA,
                model_name="meta-llama/llama-3-8b-instruct",
                display_name="Llama 3 8B (Novita AI)",
                api_endpoint="https://api.novita.ai/v3/openai",
                cost_per_token=0.0000005,
                max_tokens=4096,
                context_window=8192,
                capabilities=["text-generation", "analysis", "coding"],
                quality_score=0.84,
                speed_score=0.92,
                cost_score=0.98,
                reliability_score=0.89
            ),
            # 최신 Novita AI Models
            AIModelConfig(
                model_id="llama3-70b",
                provider=ModelProvider.NOVITA,
                model_name="meta-llama/llama-3-70b-instruct",
                display_name="Llama 3 70B (Novita AI)",
                api_endpoint="https://api.novita.ai/v3/openai",
                cost_per_token=0.000004,
                max_tokens=8192,
                context_window=8192,
                capabilities=["text-generation", "reasoning", "analysis", "coding", "complex-tasks"],
                quality_score=0.93,
                speed_score=0.82,
                cost_score=0.85,
                reliability_score=0.91
            ),
            AIModelConfig(
                model_id="claude3-haiku",
                provider=ModelProvider.NOVITA,
                model_name="anthropic/claude-3-haiku",
                display_name="Claude 3 Haiku (Novita AI)",
                api_endpoint="https://api.novita.ai/v3/openai",
                cost_per_token=0.000001,
                max_tokens=4096,
                context_window=200000,
                capabilities=["text-generation", "analysis", "speed-optimized", "safety"],
                quality_score=0.88,
                speed_score=0.95,
                cost_score=0.96,
                reliability_score=0.93
            ),
            AIModelConfig(
                model_id="claude3-sonnet",
                provider=ModelProvider.NOVITA,
                model_name="anthropic/claude-3-sonnet",
                display_name="Claude 3 Sonnet (Novita AI)",
                api_endpoint="https://api.novita.ai/v3/openai",
                cost_per_token=0.000008,
                max_tokens=4096,
                context_window=200000,
                capabilities=["text-generation", "analysis", "reasoning", "balanced-performance"],
                quality_score=0.94,
                speed_score=0.88,
                cost_score=0.78,
                reliability_score=0.94
            ),
            AIModelConfig(
                model_id="gemma2-9b",
                provider=ModelProvider.NOVITA,
                model_name="google/gemma-2-9b-it",
                display_name="Gemma 2 9B (Novita AI)",
                api_endpoint="https://api.novita.ai/v3/openai",
                cost_per_token=0.0000008,
                max_tokens=8192,
                context_window=8192,
                capabilities=["text-generation", "analysis", "efficient", "google-tech"],
                quality_score=0.86,
                speed_score=0.90,
                cost_score=0.97,
                reliability_score=0.87
            ),
            AIModelConfig(
                model_id="gemma2-27b",
                provider=ModelProvider.NOVITA,
                model_name="google/gemma-2-27b-it",
                display_name="Gemma 2 27B (Novita AI)",
                api_endpoint="https://api.novita.ai/v3/openai",
                cost_per_token=0.000003,
                max_tokens=8192,
                context_window=8192,
                capabilities=["text-generation", "analysis", "reasoning", "google-tech"],
                quality_score=0.91,
                speed_score=0.85,
                cost_score=0.88,
                reliability_score=0.89
            ),
            AIModelConfig(
                model_id="mixtral-8x7b",
                provider=ModelProvider.NOVITA,
                model_name="mistralai/mixtral-8x7b-instruct",
                display_name="Mixtral 8x7B (Novita AI)",
                api_endpoint="https://api.novita.ai/v3/openai",
                cost_per_token=0.000002,
                max_tokens=32768,
                context_window=32768,
                capabilities=["text-generation", "analysis", "coding", "multilingual", "moe-architecture"],
                quality_score=0.89,
                speed_score=0.87,
                cost_score=0.91,
                reliability_score=0.88
            ),
            AIModelConfig(
                model_id="codestral-22b",
                provider=ModelProvider.NOVITA,
                model_name="mistralai/codestral-22b",
                display_name="Codestral 22B (Novita AI)",
                api_endpoint="https://api.novita.ai/v3/openai",
                cost_per_token=0.000003,
                max_tokens=32768,
                context_window=32768,
                capabilities=["code-generation", "code-completion", "programming", "technical-analysis"],
                quality_score=0.92,
                speed_score=0.86,
                cost_score=0.87,
                reliability_score=0.90
            ),
            AIModelConfig(
                model_id="yi-large",
                provider=ModelProvider.NOVITA,
                model_name="01-ai/yi-large",
                display_name="Yi Large (Novita AI)",
                api_endpoint="https://api.novita.ai/v3/openai",
                cost_per_token=0.000005,
                max_tokens=32768,
                context_window=32768,
                capabilities=["text-generation", "reasoning", "analysis", "chinese-optimized"],
                quality_score=0.93,
                speed_score=0.83,
                cost_score=0.82,
                reliability_score=0.91
            ),
            AIModelConfig(
                model_id="qwen2-57b",
                provider=ModelProvider.NOVITA,
                model_name="qwen/qwen2-57b-a14b-instruct",
                display_name="Qwen2 57B (Novita AI)",
                api_endpoint="https://api.novita.ai/v3/openai",
                cost_per_token=0.000004,
                max_tokens=32768,
                context_window=32768,
                capabilities=["text-generation", "analysis", "multilingual", "chinese-optimized"],
                quality_score=0.90,
                speed_score=0.84,
                cost_score=0.86,
                reliability_score=0.88
            ),
            AIModelConfig(
                model_id="phi3-medium",
                provider=ModelProvider.NOVITA,
                model_name="microsoft/phi-3-medium-128k-instruct",
                display_name="Phi-3 Medium (Novita AI)",
                api_endpoint="https://api.novita.ai/v3/openai",
                cost_per_token=0.000002,
                max_tokens=4096,
                context_window=128000,
                capabilities=["text-generation", "analysis", "efficient", "microsoft-tech"],
                quality_score=0.87,
                speed_score=0.89,
                cost_score=0.92,
                reliability_score=0.86
            )
        ]
        
        for model in default_models:
            self.model_registry[model.model_id] = model
            self.health_status[model.model_id] = True
    
    async def get_available_models(self, include_inactive: bool = False) -> List[AIModelConfig]:
        """사용 가능한 모델 목록 조회"""
        try:
            models = []
            for model in self.model_registry.values():
                if include_inactive or model.status == ModelStatus.ACTIVE:
                    models.append(model)
            
            # Sort by quality score and cost efficiency
            models.sort(key=lambda x: (x.quality_score + x.cost_score) / 2, reverse=True)
            return models
            
        except Exception as e:
            logger.error(f"모델 목록 조회 오류: {e}")
            raise HTTPException(status_code=500, detail="모델 목록 조회에 실패했습니다")
    
    async def get_model_by_id(self, model_id: str) -> Optional[AIModelConfig]:
        """특정 모델 정보 조회"""
        return self.model_registry.get(model_id)
    
    async def register_model(self, model_config: AIModelConfig) -> AIModelConfig:
        """새로운 AI 모델 등록"""
        try:
            # Validate model configuration
            if model_config.model_id in self.model_registry:
                raise HTTPException(
                    status_code=400, 
                    detail=f"모델 {model_config.model_id}는 이미 등록되어 있습니다"
                )
            
            # Test model availability
            is_healthy = await self._test_model_health(model_config)
            if not is_healthy:
                logger.warning(f"모델 {model_config.model_id}의 상태가 불안정합니다")
            
            # Register model
            model_config.updated_at = datetime.utcnow()
            self.model_registry[model_config.model_id] = model_config
            self.health_status[model_config.model_id] = is_healthy
            
            # Save to database if available
            if self.db:
                await self._save_model_to_db(model_config)
            
            logger.info(f"모델 등록 완료: {model_config.model_id}")
            return model_config
            
        except Exception as e:
            logger.error(f"모델 등록 오류: {e}")
            raise HTTPException(status_code=500, detail="모델 등록에 실패했습니다")
    
    async def clear_default_models(self):
        """모든 모델의 기본 설정 해제"""
        try:
            for model_id, model in self.model_registry.items():
                if model.is_default:
                    model.is_default = False
                    model.updated_at = datetime.utcnow()
                    
                    # Save to database if available
                    if self.db:
                        await self._save_model_to_db(model)
            
            logger.info("모든 기본 모델 설정 해제 완료")
            
        except Exception as e:
            logger.error(f"기본 모델 설정 해제 오류: {e}")
            raise HTTPException(status_code=500, detail="기본 모델 설정 해제에 실패했습니다")
    
    async def update_model(self, model_id: str, updates: Dict[str, Any]) -> AIModelConfig:
        """모델 업데이트 (update_model_config의 별칭)"""
        return await self.update_model_config(model_id, updates)
    
    async def update_model_config(self, model_id: str, updates: Dict[str, Any]) -> AIModelConfig:
        """모델 설정 업데이트"""
        try:
            if model_id not in self.model_registry:
                raise HTTPException(status_code=404, detail="모델을 찾을 수 없습니다")
            
            model = self.model_registry[model_id]
            
            # Update allowed fields
            allowed_fields = {
                'parameters', 'status', 'is_default', 'display_name',
                'cost_per_token', 'max_tokens', 'capabilities'
            }
            
            for field, value in updates.items():
                if field in allowed_fields:
                    setattr(model, field, value)
            
            model.updated_at = datetime.utcnow()
            
            # Save to database
            if self.db:
                await self._save_model_to_db(model)
            
            logger.info(f"모델 설정 업데이트 완료: {model_id}")
            return model
            
        except Exception as e:
            logger.error(f"모델 설정 업데이트 오류: {e}")
            raise HTTPException(status_code=500, detail="모델 설정 업데이트에 실패했습니다")
    
    async def delete_model(self, model_id: str) -> bool:
        """모델 삭제"""
        try:
            if model_id not in self.model_registry:
                raise HTTPException(status_code=404, detail="모델을 찾을 수 없습니다")
            
            model = self.model_registry[model_id]
            
            # 기본 모델은 삭제 방지
            if model.is_default:
                raise HTTPException(
                    status_code=400, 
                    detail="기본 모델은 삭제할 수 없습니다. 먼저 기본 설정을 해제하세요."
                )
            
            # 레지스트리에서 제거
            del self.model_registry[model_id]
            
            # 성능 캐시 정리
            if model_id in self.performance_cache:
                del self.performance_cache[model_id]
            
            # 사용량 통계 정리
            if model_id in self.usage_stats:
                del self.usage_stats[model_id]
            
            # 건강 상태 정리
            if model_id in self.health_status:
                del self.health_status[model_id]
            
            # 데이터베이스에서 삭제
            if self.db:
                await self.db.ai_model_configs.delete_one({"model_id": model_id})
            
            logger.info(f"모델 삭제 완료: {model_id}")
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"모델 삭제 오류: {e}")
            raise HTTPException(status_code=500, detail="모델 삭제에 실패했습니다")
    
    async def get_model_performance(self, model_id: str, timeframe: str = "7d") -> Dict[str, Any]:
        """모델 성능 메트릭 조회"""
        try:
            if model_id not in self.model_registry:
                raise HTTPException(status_code=404, detail="모델을 찾을 수 없습니다")
            
            # Calculate timeframe
            now = datetime.utcnow()
            if timeframe == "1d":
                start_date = now - timedelta(days=1)
            elif timeframe == "7d":
                start_date = now - timedelta(days=7)
            elif timeframe == "30d":
                start_date = now - timedelta(days=30)
            else:
                start_date = now - timedelta(days=7)
            
            # Get cached performance data or calculate
            if model_id in self.performance_cache:
                cache_data = self.performance_cache[model_id]
                if cache_data.get('last_updated', datetime.min) > now - timedelta(hours=1):
                    return cache_data['data']
            
            # Calculate performance metrics
            model = self.model_registry[model_id]
            stats = self.usage_stats.get(model_id, [])
            
            # Filter stats by timeframe
            filtered_stats = [
                stat for stat in stats 
                if stat.date >= start_date
            ]
            
            if not filtered_stats:
                # Return default metrics based on model scores
                performance = {
                    'model_id': model_id,
                    'timeframe': timeframe,
                    'total_requests': 0,
                    'total_tokens': 0,
                    'total_cost': 0.0,
                    'avg_response_time': 0.0,
                    'error_rate': 0.0,
                    'quality_score': model.quality_score,
                    'speed_score': model.speed_score,
                    'cost_score': model.cost_score,
                    'reliability_score': model.reliability_score,
                    'health_status': self.health_status.get(model_id, True),
                    'recommendations': []
                }
            else:
                # Aggregate stats
                total_requests = sum(stat.total_requests for stat in filtered_stats)
                total_tokens = sum(stat.total_tokens for stat in filtered_stats)
                total_cost = sum(stat.total_cost for stat in filtered_stats)
                avg_response_time = sum(stat.avg_response_time for stat in filtered_stats) / len(filtered_stats)
                error_rate = sum(stat.error_rate for stat in filtered_stats) / len(filtered_stats)
                quality_score = sum(stat.quality_score for stat in filtered_stats) / len(filtered_stats)
                
                performance = {
                    'model_id': model_id,
                    'timeframe': timeframe,
                    'total_requests': total_requests,
                    'total_tokens': total_tokens,
                    'total_cost': total_cost,
                    'avg_response_time': avg_response_time,
                    'error_rate': error_rate,
                    'quality_score': quality_score,
                    'speed_score': model.speed_score,
                    'cost_score': model.cost_score,
                    'reliability_score': model.reliability_score,
                    'health_status': self.health_status.get(model_id, True),
                    'cost_per_request': total_cost / total_requests if total_requests > 0 else 0,
                    'tokens_per_request': total_tokens / total_requests if total_requests > 0 else 0,
                    'recommendations': await self._generate_performance_recommendations(model_id, filtered_stats)
                }
            
            # Cache the result
            self.performance_cache[model_id] = {
                'data': performance,
                'last_updated': now
            }
            
            return performance
            
        except Exception as e:
            logger.error(f"모델 성능 조회 오류: {e}")
            raise HTTPException(status_code=500, detail="모델 성능 조회에 실패했습니다")
    
    async def _test_model_health(self, model_config: AIModelConfig) -> bool:
        """모델 상태 테스트"""
        try:
            # Simple health check - in real implementation, this would make actual API calls
            # For now, return True for default models including Novita AI models
            healthy_models = [
                "gpt-4", "gpt-3.5-turbo", "claude-3-opus", "gemini-pro",
                "deepseek-r1", "deepseek-chat", "qwen2-72b", "llama3-8b",
                "llama3-70b", "claude3-haiku", "claude3-sonnet", "gemma2-9b", 
                "gemma2-27b", "mixtral-8x7b", "codestral-22b", "yi-large", 
                "qwen2-57b", "phi3-medium"
            ]
            return model_config.model_id in healthy_models
        except Exception:
            return False
    
    async def _save_model_to_db(self, model_config: AIModelConfig):
        """모델 설정을 데이터베이스에 저장"""
        if not self.db:
            return
        
        try:
            await self.db.ai_model_configs.update_one(
                {"model_id": model_config.model_id},
                {"$set": model_config.dict()},
                upsert=True
            )
        except Exception as e:
            logger.error(f"모델 DB 저장 오류: {e}")
    
    async def _generate_performance_recommendations(self, model_id: str, stats: List[ModelUsageStats]) -> List[str]:
        """성능 기반 추천사항 생성"""
        recommendations = []
        
        if not stats:
            return recommendations
        
        avg_error_rate = sum(stat.error_rate for stat in stats) / len(stats)
        avg_cost = sum(stat.total_cost for stat in stats) / len(stats)
        avg_quality = sum(stat.quality_score for stat in stats) / len(stats)
        
        if avg_error_rate > 0.05:
            recommendations.append("오류율이 높습니다. 대체 모델 사용을 고려하세요.")
        
        if avg_cost > 10.0:  # $10 threshold
            recommendations.append("비용이 높습니다. 더 경제적인 모델로 전환을 고려하세요.")
        
        if avg_quality < 0.7:
            recommendations.append("품질 점수가 낮습니다. 더 고품질 모델로 업그레이드를 고려하세요.")
        
        return recommendations


class SmartModelRecommender:
    """스마트 모델 추천 시스템"""
    
    def __init__(self, model_service: AIModelManagementService):
        self.model_service = model_service
        self.recommendation_weights = {
            'quality': 0.4,
            'cost': 0.3,
            'speed': 0.2,
            'reliability': 0.1
        }
    
    async def recommend_model(self, context: Dict[str, Any]) -> ModelRecommendation:
        """컨텍스트 기반 최적 모델 추천"""
        try:
            available_models = await self.model_service.get_available_models()
            
            if not available_models:
                raise HTTPException(status_code=404, detail="사용 가능한 모델이 없습니다")
            
            # Extract context factors
            budget = context.get('budget', 'medium')  # low, medium, high
            quality_requirement = context.get('quality_level', 'medium')  # low, medium, high
            speed_requirement = context.get('speed_requirement', 'medium')  # low, medium, high
            task_type = context.get('task_type', TaskType.EVALUATION)
            
            # Calculate scores for each model
            model_scores = []
            for model in available_models:
                score = await self._calculate_model_score(
                    model, budget, quality_requirement, speed_requirement, task_type
                )
                model_scores.append((model, score))
            
            # Sort by score and get the best model
            model_scores.sort(key=lambda x: x[1], reverse=True)
            best_model, best_score = model_scores[0]
            
            # Generate reasoning
            reasoning = self._generate_recommendation_reasoning(
                best_model, budget, quality_requirement, speed_requirement
            )
            
            # Estimate cost and quality
            estimated_cost = await self._estimate_cost(best_model, context)
            estimated_quality = best_model.quality_score
            
            return ModelRecommendation(
                model_id=best_model.model_id,
                confidence=best_score,
                reasoning=reasoning,
                estimated_cost=estimated_cost,
                estimated_quality=estimated_quality
            )
            
        except Exception as e:
            logger.error(f"모델 추천 오류: {e}")
            raise HTTPException(status_code=500, detail="모델 추천에 실패했습니다")
    
    async def _calculate_model_score(
        self, 
        model: AIModelConfig, 
        budget: str, 
        quality_requirement: str, 
        speed_requirement: str, 
        task_type: TaskType
    ) -> float:
        """모델 점수 계산"""
        
        # Base scores from model
        quality_score = model.quality_score
        cost_score = model.cost_score
        speed_score = model.speed_score
        reliability_score = model.reliability_score
        
        # Adjust weights based on requirements
        weights = dict(self.recommendation_weights)
        
        if quality_requirement == 'high':
            weights['quality'] = 0.6
            weights['cost'] = 0.2
        elif budget == 'low':
            weights['cost'] = 0.5
            weights['quality'] = 0.3
        
        if speed_requirement == 'high':
            weights['speed'] = 0.4
            weights['quality'] = 0.3
        
        # Task-specific adjustments
        if task_type == TaskType.ANALYSIS and 'analysis' in model.capabilities:
            quality_score *= 1.1
        elif task_type == TaskType.SUMMARY and 'text-generation' in model.capabilities:
            speed_score *= 1.1
        
        # Calculate weighted score
        total_score = (
            quality_score * weights['quality'] +
            cost_score * weights['cost'] +
            speed_score * weights['speed'] +
            reliability_score * weights['reliability']
        )
        
        return min(total_score, 1.0)  # Cap at 1.0
    
    def _generate_recommendation_reasoning(
        self, 
        model: AIModelConfig, 
        budget: str, 
        quality_requirement: str, 
        speed_requirement: str
    ) -> str:
        """추천 이유 생성"""
        reasons = []
        
        if model.quality_score > 0.9:
            reasons.append("뛰어난 품질")
        elif model.quality_score > 0.8:
            reasons.append("우수한 품질")
        
        if model.cost_score > 0.9:
            reasons.append("경제적인 비용")
        elif model.cost_score > 0.8:
            reasons.append("합리적인 비용")
        
        if model.speed_score > 0.9:
            reasons.append("빠른 응답 속도")
        elif model.speed_score > 0.8:
            reasons.append("우수한 응답 속도")
        
        if model.reliability_score > 0.9:
            reasons.append("높은 안정성")
        
        reasoning = f"{model.display_name}을(를) 추천합니다. "
        if reasons:
            reasoning += "주요 장점: " + ", ".join(reasons) + "."
        
        return reasoning
    
    async def _estimate_cost(self, model: AIModelConfig, context: Dict[str, Any]) -> float:
        """예상 비용 계산"""
        estimated_tokens = context.get('estimated_tokens', 1000)
        estimated_requests = context.get('estimated_requests_per_month', 100)
        
        monthly_cost = model.cost_per_token * estimated_tokens * estimated_requests
        return round(monthly_cost, 4)


class ModelLoadBalancer:
    """AI 모델 로드 밸런서 및 장애 복구 시스템"""
    
    def __init__(self, model_service: AIModelManagementService):
        self.model_service = model_service
        self.fallback_chain = ["gpt-4", "gpt-3.5-turbo", "claude-3-opus", "gemini-pro"]
        self.circuit_breaker_threshold = 5  # 연속 실패 임계값
        self.failure_counts: Dict[str, int] = {}
        self.last_failure_times: Dict[str, datetime] = {}
    
    async def get_healthy_models(self) -> List[str]:
        """건강한 모델 목록 반환"""
        healthy_models = []
        
        for model_id in self.fallback_chain:
            if await self._is_model_healthy(model_id):
                healthy_models.append(model_id)
        
        return healthy_models
    
    async def _is_model_healthy(self, model_id: str) -> bool:
        """모델 상태 확인"""
        # Circuit breaker pattern
        failure_count = self.failure_counts.get(model_id, 0)
        last_failure = self.last_failure_times.get(model_id)
        
        # If model has failed too many times recently, mark as unhealthy
        if failure_count >= self.circuit_breaker_threshold:
            if last_failure and datetime.utcnow() - last_failure < timedelta(minutes=5):
                return False
            else:
                # Reset failure count after cooldown period
                self.failure_counts[model_id] = 0
        
        return self.model_service.health_status.get(model_id, True)
    
    def mark_model_failure(self, model_id: str):
        """모델 실패 기록"""
        self.failure_counts[model_id] = self.failure_counts.get(model_id, 0) + 1
        self.last_failure_times[model_id] = datetime.utcnow()
        self.model_service.health_status[model_id] = False
        
        logger.warning(f"모델 {model_id} 실패 기록. 실패 횟수: {self.failure_counts[model_id]}")
    
    def mark_model_success(self, model_id: str):
        """모델 성공 기록"""
        if model_id in self.failure_counts:
            self.failure_counts[model_id] = max(0, self.failure_counts[model_id] - 1)
        
        self.model_service.health_status[model_id] = True


# Initialize global services
ai_model_service = AIModelManagementService()
smart_recommender = SmartModelRecommender(ai_model_service)
load_balancer = ModelLoadBalancer(ai_model_service)