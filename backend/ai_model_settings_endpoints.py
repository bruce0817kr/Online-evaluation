"""
AI Model Settings API Endpoints
AI 모델 설정, 관리, 비교 및 모니터링 API
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import logging
import json
import asyncio
from io import BytesIO
import time
import os

# AI Provider clients
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI library not available")

from models import User
from security import get_current_user, check_admin_or_secretary
from ai_model_management import (
    AIModelConfig, ModelUsageStats, ModelPerformanceMetric, ModelComparisonRequest,
    TaskType, ModelProvider, ModelStatus, ModelRecommendation,
    ai_model_service, smart_recommender, load_balancer
)

logger = logging.getLogger(__name__)

# AI Model Settings Router
ai_model_settings_router = APIRouter(
    prefix="/api/ai-models", 
    tags=["AI Model Settings"]
)

# Request/Response Models
class ModelConfigurationRequest(BaseModel):
    parameters: Dict[str, Any] = Field(default_factory=dict, description="모델 매개변수")
    status: Optional[ModelStatus] = Field(None, description="모델 상태")
    is_default: Optional[bool] = Field(None, description="기본 모델 설정")
    cost_per_token: Optional[float] = Field(None, description="토큰당 비용")
    max_tokens: Optional[int] = Field(None, description="최대 토큰 수")

class ModelRecommendationRequest(BaseModel):
    budget: str = Field("medium", description="예산 수준: low, medium, high")
    quality_level: str = Field("medium", description="품질 요구사항: low, medium, high")
    speed_requirement: str = Field("medium", description="속도 요구사항: low, medium, high")
    task_type: TaskType = Field(TaskType.EVALUATION, description="작업 유형")
    estimated_tokens: Optional[int] = Field(1000, description="예상 토큰 수")
    estimated_requests_per_month: Optional[int] = Field(100, description="월간 예상 요청 수")

class ModelTestRequest(BaseModel):
    model_id: str = Field(..., description="테스트할 모델 ID")
    test_prompt: str = Field(..., description="테스트 프롬프트")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="테스트 매개변수")

class ModelComparisonResult(BaseModel):
    model_id: str
    response: str
    response_time: float
    token_count: int
    cost: float
    quality_score: float
    error: Optional[str] = None

class UsageLimitConfig(BaseModel):
    daily_limit: Optional[int] = Field(None, description="일일 요청 한도")
    monthly_limit: Optional[int] = Field(None, description="월간 요청 한도")
    cost_limit: Optional[float] = Field(None, description="비용 한도")
    alert_threshold: float = Field(0.8, description="알림 임계값 (한도의 비율)")

class CreateModelRequest(BaseModel):
    model_id: str = Field(..., description="고유 모델 ID", pattern="^[a-z0-9-]+$")
    provider: ModelProvider = Field(..., description="AI 모델 제공업체")
    model_name: str = Field(..., description="실제 모델명 (API 호출시 사용)")
    display_name: str = Field(..., description="사용자에게 표시될 이름")
    api_endpoint: Optional[str] = Field(None, description="커스텀 API 엔드포인트")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="기본 매개변수")
    cost_per_token: float = Field(0.0, ge=0, description="토큰당 비용")
    max_tokens: int = Field(4096, gt=0, description="최대 토큰 수")
    context_window: int = Field(4096, gt=0, description="컨텍스트 윈도우 크기")
    capabilities: List[str] = Field(default_factory=list, description="모델 기능 목록")
    quality_score: float = Field(0.5, ge=0, le=1, description="품질 점수 (0-1)")
    speed_score: float = Field(0.5, ge=0, le=1, description="속도 점수 (0-1)")
    cost_score: float = Field(0.5, ge=0, le=1, description="비용 효율성 점수 (0-1)")
    reliability_score: float = Field(0.5, ge=0, le=1, description="안정성 점수 (0-1)")
    is_default: bool = Field(False, description="기본 모델 여부")

class UpdateModelRequest(BaseModel):
    display_name: Optional[str] = Field(None, description="사용자에게 표시될 이름")
    api_endpoint: Optional[str] = Field(None, description="커스텀 API 엔드포인트")
    parameters: Optional[Dict[str, Any]] = Field(None, description="기본 매개변수")
    cost_per_token: Optional[float] = Field(None, ge=0, description="토큰당 비용")
    max_tokens: Optional[int] = Field(None, gt=0, description="최대 토큰 수")
    context_window: Optional[int] = Field(None, gt=0, description="컨텍스트 윈도우 크기")
    capabilities: Optional[List[str]] = Field(None, description="모델 기능 목록")
    quality_score: Optional[float] = Field(None, ge=0, le=1, description="품질 점수 (0-1)")
    speed_score: Optional[float] = Field(None, ge=0, le=1, description="속도 점수 (0-1)")
    cost_score: Optional[float] = Field(None, ge=0, le=1, description="비용 효율성 점수 (0-1)")
    reliability_score: Optional[float] = Field(None, ge=0, le=1, description="안정성 점수 (0-1)")
    status: Optional[ModelStatus] = Field(None, description="모델 상태")
    is_default: Optional[bool] = Field(None, description="기본 모델 여부")

class ModelTemplate(BaseModel):
    name: str = Field(..., description="템플릿 이름")
    provider: ModelProvider = Field(..., description="제공업체")
    description: str = Field(..., description="템플릿 설명")
    default_config: CreateModelRequest = Field(..., description="기본 설정")

# AI Model Client Functions

def create_novita_client(api_key: str = None) -> OpenAI:
    """Novita AI 클라이언트 생성"""
    if not OPENAI_AVAILABLE:
        raise HTTPException(status_code=500, detail="OpenAI library not available")
    
    api_key = api_key or os.getenv('NOVITA_API_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="Novita API key not configured")
    
    return OpenAI(
        base_url="https://api.novita.ai/v3/openai",
        api_key=api_key
    )

async def call_novita_model(model_config: AIModelConfig, prompt: str, **kwargs) -> Dict[str, Any]:
    """Novita AI 모델 호출"""
    try:
        client = create_novita_client()
        
        start_time = time.time()
        
        # 기본 매개변수 설정
        params = {
            "model": model_config.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a professional AI assistant."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "max_tokens": kwargs.get('max_tokens', model_config.max_tokens),
            "temperature": kwargs.get('temperature', 0.7),
            "stream": kwargs.get('stream', False)
        }
        
        # 모델별 특별 설정
        if 'deepseek' in model_config.model_name:
            params["temperature"] = min(params["temperature"], 1.0)  # DeepSeek 온도 제한
        elif 'claude' in model_config.model_name:
            params["temperature"] = min(params["temperature"], 1.0)  # Claude 온도 제한
        elif 'codestral' in model_config.model_name:
            # 코딩 특화 모델은 낮은 온도로 설정
            params["temperature"] = min(params["temperature"], 0.3)
        elif 'phi-3' in model_config.model_name:
            # Phi-3은 Microsoft의 효율적인 모델
            params["temperature"] = min(params["temperature"], 0.8)
        
        response = client.chat.completions.create(**params)
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # 응답 처리
        if kwargs.get('stream', False):
            # 스트리밍 응답 처리
            content = ""
            for chunk in response:
                if chunk.choices[0].delta.content:
                    content += chunk.choices[0].delta.content
        else:
            content = response.choices[0].message.content
        
        # 토큰 수 추정 (실제로는 response.usage.total_tokens 사용 가능)
        token_count = len(content.split()) * 1.3  # 간단한 토큰 수 추정
        
        # 비용 계산
        cost = token_count * model_config.cost_per_token
        
        return {
            "response": content,
            "response_time": response_time,
            "token_count": int(token_count),
            "cost": cost,
            "quality_score": model_config.quality_score,
            "error": None
        }
        
    except Exception as e:
        logger.error(f"Novita AI 모델 호출 오류: {e}")
        return {
            "response": "",
            "response_time": 0.0,
            "token_count": 0,
            "cost": 0.0,
            "quality_score": 0.0,
            "error": str(e)
        }

async def call_ai_model(model_config: AIModelConfig, prompt: str, **kwargs) -> Dict[str, Any]:
    """통합 AI 모델 호출 함수"""
    try:
        if model_config.provider == ModelProvider.NOVITA:
            return await call_novita_model(model_config, prompt, **kwargs)
        elif model_config.provider == ModelProvider.OPENAI:
            # OpenAI 모델 호출 로직 (기존)
            return {
                "response": f"[Mock] OpenAI {model_config.model_name} response to: {prompt[:50]}...",
                "response_time": 1.2,
                "token_count": 100,
                "cost": 0.002,
                "quality_score": model_config.quality_score,
                "error": None
            }
        else:
            # 다른 제공업체 모델 (Mock 응답)
            return {
                "response": f"[Mock] {model_config.provider.upper()} {model_config.model_name} response to: {prompt[:50]}...",
                "response_time": 1.5,
                "token_count": 120,
                "cost": 0.001,
                "quality_score": model_config.quality_score,
                "error": None
            }
            
    except Exception as e:
        logger.error(f"AI 모델 호출 오류: {e}")
        return {
            "response": "",
            "response_time": 0.0,
            "token_count": 0,
            "cost": 0.0,
            "quality_score": 0.0,
            "error": str(e)
        }

# 모델 템플릿 정의

DEFAULT_MODEL_TEMPLATES = {
    "openai-gpt4-evaluation": ModelTemplate(
        name="openai-gpt4-evaluation",
        provider=ModelProvider.OPENAI,
        description="OpenAI GPT-4 모델 - 고품질 평가 작업에 최적화",
        default_config=CreateModelRequest(
            model_id="gpt-4-evaluation",
            provider=ModelProvider.OPENAI,
            model_name="gpt-4",
            display_name="GPT-4 평가 특화 (OpenAI)",
            parameters={"temperature": 0.3, "max_tokens": 2000, "top_p": 0.9},
            cost_per_token=0.00003,
            max_tokens=8192,
            context_window=8192,
            capabilities=["evaluation", "analysis", "reasoning", "korean"],
            quality_score=0.95,
            speed_score=0.75,
            cost_score=0.60,
            reliability_score=0.90,
            is_default=False
        )
    ),
    "novita-deepseek-r1": ModelTemplate(
        name="novita-deepseek-r1",
        provider=ModelProvider.NOVITA,
        description="Novita AI의 DeepSeek R1 모델 - 추론 능력이 뛰어난 모델",
        default_config=CreateModelRequest(
            model_id="deepseek-r1-reasoning",
            provider=ModelProvider.NOVITA,
            model_name="deepseek/deepseek-r1",
            display_name="DeepSeek R1 추론 (Novita AI)",
            api_endpoint="https://api.novita.ai/v3/openai",
            parameters={"temperature": 0.2, "max_tokens": 4000, "top_p": 0.85},
            cost_per_token=0.000001,
            max_tokens=8192,
            context_window=8192,
            capabilities=["reasoning", "analysis", "evaluation", "complex-thinking"],
            quality_score=0.92,
            speed_score=0.88,
            cost_score=0.95,
            reliability_score=0.90,
            is_default=False
        )
    ),
    "novita-claude3-sonnet": ModelTemplate(
        name="novita-claude3-sonnet",
        provider=ModelProvider.NOVITA,
        description="Novita AI의 Claude 3 Sonnet - 균형 잡힌 성능",
        default_config=CreateModelRequest(
            model_id="claude3-sonnet-balanced",
            provider=ModelProvider.NOVITA,
            model_name="anthropic/claude-3-sonnet",
            display_name="Claude 3 Sonnet 균형형 (Novita AI)",
            api_endpoint="https://api.novita.ai/v3/openai",
            parameters={"temperature": 0.4, "max_tokens": 3000, "top_p": 0.9},
            cost_per_token=0.000008,
            max_tokens=4096,
            context_window=200000,
            capabilities=["evaluation", "analysis", "safety", "korean", "long-context"],
            quality_score=0.94,
            speed_score=0.88,
            cost_score=0.78,
            reliability_score=0.94,
            is_default=False
        )
    ),
    "novita-llama3-70b": ModelTemplate(
        name="novita-llama3-70b",
        provider=ModelProvider.NOVITA,
        description="Novita AI의 Llama 3 70B - 복잡한 작업에 특화",
        default_config=CreateModelRequest(
            model_id="llama3-70b-complex",
            provider=ModelProvider.NOVITA,
            model_name="meta-llama/llama-3-70b-instruct",
            display_name="Llama 3 70B 복합 작업 (Novita AI)",
            api_endpoint="https://api.novita.ai/v3/openai",
            parameters={"temperature": 0.3, "max_tokens": 4000, "top_p": 0.8},
            cost_per_token=0.000004,
            max_tokens=8192,
            context_window=8192,
            capabilities=["complex-tasks", "reasoning", "analysis", "evaluation", "multilingual"],
            quality_score=0.93,
            speed_score=0.82,
            cost_score=0.85,
            reliability_score=0.91,
            is_default=False
        )
    ),
    "novita-codestral-22b": ModelTemplate(
        name="novita-codestral-22b",
        provider=ModelProvider.NOVITA,
        description="Novita AI의 Codestral 22B - 코드 및 기술 분석 특화",
        default_config=CreateModelRequest(
            model_id="codestral-22b-tech",
            provider=ModelProvider.NOVITA,
            model_name="mistralai/codestral-22b",
            display_name="Codestral 22B 기술 분석 (Novita AI)",
            api_endpoint="https://api.novita.ai/v3/openai",
            parameters={"temperature": 0.1, "max_tokens": 6000, "top_p": 0.75},
            cost_per_token=0.000003,
            max_tokens=32768,
            context_window=32768,
            capabilities=["code-analysis", "technical-evaluation", "programming", "documentation"],
            quality_score=0.92,
            speed_score=0.86,
            cost_score=0.87,
            reliability_score=0.90,
            is_default=False
        )
    ),
    "anthropic-claude3-opus": ModelTemplate(
        name="anthropic-claude3-opus",
        provider=ModelProvider.ANTHROPIC,
        description="Anthropic Claude 3 Opus - 최고 품질 평가",
        default_config=CreateModelRequest(
            model_id="claude3-opus-premium",
            provider=ModelProvider.ANTHROPIC,
            model_name="claude-3-opus-20240229",
            display_name="Claude 3 Opus 프리미엄 (Anthropic)",
            parameters={"temperature": 0.2, "max_tokens": 3000, "top_p": 0.95},
            cost_per_token=0.000015,
            max_tokens=4096,
            context_window=200000,
            capabilities=["premium-evaluation", "complex-reasoning", "safety", "ethics"],
            quality_score=0.98,
            speed_score=0.70,
            cost_score=0.70,
            reliability_score=0.92,
            is_default=False
        )
    ),
    "google-gemini-pro": ModelTemplate(
        name="google-gemini-pro",
        provider=ModelProvider.GOOGLE,
        description="Google Gemini Pro - 멀티모달 분석 가능",
        default_config=CreateModelRequest(
            model_id="gemini-pro-multimodal",
            provider=ModelProvider.GOOGLE,
            model_name="gemini-pro",
            display_name="Gemini Pro 멀티모달 (Google)",
            parameters={"temperature": 0.4, "max_tokens": 2000, "top_p": 0.8},
            cost_per_token=0.0000005,
            max_tokens=2048,
            context_window=30720,
            capabilities=["multimodal", "image-analysis", "text-evaluation", "efficiency"],
            quality_score=0.88,
            speed_score=0.85,
            cost_score=0.98,
            reliability_score=0.88,
            is_default=False
        )
    ),
    "budget-efficient": ModelTemplate(
        name="budget-efficient",
        provider=ModelProvider.NOVITA,
        description="비용 효율적인 모델 - 대량 평가용",
        default_config=CreateModelRequest(
            model_id="llama3-8b-budget",
            provider=ModelProvider.NOVITA,
            model_name="meta-llama/llama-3-8b-instruct",
            display_name="Llama 3 8B 경제형 (Novita AI)",
            api_endpoint="https://api.novita.ai/v3/openai",
            parameters={"temperature": 0.5, "max_tokens": 1500, "top_p": 0.9},
            cost_per_token=0.0000005,
            max_tokens=4096,
            context_window=8192,
            capabilities=["cost-effective", "batch-processing", "basic-evaluation"],
            quality_score=0.84,
            speed_score=0.92,
            cost_score=0.98,
            reliability_score=0.89,
            is_default=False
        )
    ),
    "speed-optimized": ModelTemplate(
        name="speed-optimized",
        provider=ModelProvider.NOVITA,
        description="속도 최적화 모델 - 실시간 처리용",
        default_config=CreateModelRequest(
            model_id="claude3-haiku-speed",
            provider=ModelProvider.NOVITA,
            model_name="anthropic/claude-3-haiku",
            display_name="Claude 3 Haiku 고속 (Novita AI)",
            api_endpoint="https://api.novita.ai/v3/openai",
            parameters={"temperature": 0.3, "max_tokens": 1000, "top_p": 0.85},
            cost_per_token=0.000001,
            max_tokens=4096,
            context_window=200000,
            capabilities=["speed-optimized", "real-time", "quick-evaluation"],
            quality_score=0.88,
            speed_score=0.95,
            cost_score=0.96,
            reliability_score=0.93,
            is_default=False
        )
    )
}

# API Endpoints

@ai_model_settings_router.get("/available", response_model=List[AIModelConfig])
async def get_available_models(
    include_inactive: bool = Query(False, description="비활성 모델 포함 여부"),
    current_user: User = Depends(get_current_user)
):
    """사용 가능한 AI 모델 목록 조회"""
    try:
        if current_user.role not in ["admin", "secretary"]:
            raise HTTPException(
                status_code=403, 
                detail="AI 모델 설정 권한이 없습니다"
            )
        
        models = await ai_model_service.get_available_models(include_inactive)
        
        logger.info(f"AI 모델 목록 조회: {len(models)}개 모델", extra={
            'user_id': current_user.id,
            'model_count': len(models)
        })
        
        return models
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"모델 목록 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="모델 목록 조회에 실패했습니다")

@ai_model_settings_router.get("/{model_id}", response_model=AIModelConfig)
async def get_model_details(
    model_id: str,
    current_user: User = Depends(get_current_user)
):
    """특정 AI 모델 상세 정보 조회"""
    try:
        if current_user.role not in ["admin", "secretary"]:
            raise HTTPException(
                status_code=403, 
                detail="AI 모델 정보 조회 권한이 없습니다"
            )
        
        model = await ai_model_service.get_model_by_id(model_id)
        if not model:
            raise HTTPException(status_code=404, detail="모델을 찾을 수 없습니다")
        
        return model
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"모델 상세 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="모델 정보 조회에 실패했습니다")

@ai_model_settings_router.post("/{model_id}/configure", response_model=AIModelConfig)
async def configure_model(
    model_id: str,
    config: ModelConfigurationRequest,
    current_user: User = Depends(get_current_user)
):
    """AI 모델 설정 구성"""
    try:
        if current_user.role not in ["admin", "secretary"]:
            raise HTTPException(
                status_code=403, 
                detail="AI 모델 설정 권한이 없습니다"
            )
        
        # Prepare updates dictionary
        updates = {}
        for field, value in config.dict(exclude_unset=True).items():
            if value is not None:
                updates[field] = value
        
        updated_model = await ai_model_service.update_model_config(model_id, updates)
        
        logger.info(f"모델 설정 업데이트: {model_id}", extra={
            'user_id': current_user.id,
            'model_id': model_id,
            'updates': list(updates.keys())
        })
        
        return updated_model
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"모델 설정 오류: {e}")
        raise HTTPException(status_code=500, detail="모델 설정에 실패했습니다")

@ai_model_settings_router.post("/register", response_model=AIModelConfig)
async def register_new_model(
    model_config: AIModelConfig,
    current_user: User = Depends(get_current_user)
):
    """새로운 AI 모델 등록"""
    try:
        if current_user.role != "admin":
            raise HTTPException(
                status_code=403, 
                detail="관리자만 새 모델을 등록할 수 있습니다"
            )
        
        registered_model = await ai_model_service.register_model(model_config)
        
        logger.info(f"새 모델 등록: {model_config.model_id}", extra={
            'user_id': current_user.id,
            'model_id': model_config.model_id,
            'provider': model_config.provider
        })
        
        return registered_model
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"모델 등록 오류: {e}")
        raise HTTPException(status_code=500, detail="모델 등록에 실패했습니다")

@ai_model_settings_router.get("/{model_id}/performance")
async def get_model_performance(
    model_id: str,
    timeframe: str = Query("7d", description="조회 기간: 1d, 7d, 30d"),
    current_user: User = Depends(get_current_user)
):
    """모델 성능 메트릭 조회"""
    try:
        if current_user.role not in ["admin", "secretary"]:
            raise HTTPException(
                status_code=403, 
                detail="모델 성능 조회 권한이 없습니다"
            )
        
        performance = await ai_model_service.get_model_performance(model_id, timeframe)
        
        return {
            "success": True,
            "performance": performance
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"모델 성능 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="모델 성능 조회에 실패했습니다")

@ai_model_settings_router.post("/recommend", response_model=ModelRecommendation)
async def get_model_recommendation(
    request: ModelRecommendationRequest,
    current_user: User = Depends(get_current_user)
):
    """스마트 모델 추천"""
    try:
        if current_user.role not in ["admin", "secretary"]:
            raise HTTPException(
                status_code=403, 
                detail="모델 추천 기능 권한이 없습니다"
            )
        
        context = request.dict()
        recommendation = await smart_recommender.recommend_model(context)
        
        logger.info(f"모델 추천 요청 처리: {recommendation.model_id}", extra={
            'user_id': current_user.id,
            'recommended_model': recommendation.model_id,
            'confidence': recommendation.confidence
        })
        
        return recommendation
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"모델 추천 오류: {e}")
        raise HTTPException(status_code=500, detail="모델 추천에 실패했습니다")

@ai_model_settings_router.post("/test", response_model=Dict[str, Any])
async def test_model(
    request: ModelTestRequest,
    current_user: User = Depends(get_current_user)
):
    """AI 모델 테스트"""
    try:
        if current_user.role not in ["admin", "secretary"]:
            raise HTTPException(
                status_code=403, 
                detail="모델 테스트 권한이 없습니다"
            )
        
        model = await ai_model_service.get_model_by_id(request.model_id)
        if not model:
            raise HTTPException(status_code=404, detail="모델을 찾을 수 없습니다")
        
        # Simulate model test (in real implementation, this would call the actual model)
        start_time = datetime.utcnow()
        
        # Mock response for demonstration
        test_response = {
            "model_id": request.model_id,
            "test_prompt": request.test_prompt,
            "response": f"[테스트 응답] {request.model_id}로부터의 응답입니다. 프롬프트: {request.test_prompt[:50]}...",
            "response_time": 1.2,  # seconds
            "token_count": len(request.test_prompt.split()) * 1.3,  # rough estimate
            "cost": model.cost_per_token * len(request.test_prompt.split()) * 1.3,
            "quality_score": model.quality_score,
            "parameters_used": request.parameters,
            "timestamp": start_time.isoformat()
        }
        
        logger.info(f"모델 테스트 완료: {request.model_id}", extra={
            'user_id': current_user.id,
            'model_id': request.model_id,
            'response_time': test_response["response_time"]
        })
        
        return {
            "success": True,
            "test_result": test_response
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"모델 테스트 오류: {e}")
        raise HTTPException(status_code=500, detail="모델 테스트에 실패했습니다")

@ai_model_settings_router.post("/compare", response_model=List[ModelComparisonResult])
async def compare_models(
    request: ModelComparisonRequest,
    current_user: User = Depends(get_current_user)
):
    """여러 AI 모델 성능 비교"""
    try:
        if current_user.role not in ["admin", "secretary"]:
            raise HTTPException(
                status_code=403, 
                detail="모델 비교 권한이 없습니다"
            )
        
        if len(request.model_ids) < 2:
            raise HTTPException(
                status_code=400, 
                detail="비교를 위해서는 최소 2개의 모델이 필요합니다"
            )
        
        comparison_results = []
        
        for model_id in request.model_ids:
            model = await ai_model_service.get_model_by_id(model_id)
            if not model:
                comparison_results.append(ModelComparisonResult(
                    model_id=model_id,
                    response="",
                    response_time=0.0,
                    token_count=0,
                    cost=0.0,
                    quality_score=0.0,
                    error=f"모델 {model_id}를 찾을 수 없습니다"
                ))
                continue
            
            try:
                # 실제 AI 모델 호출
                call_result = await call_ai_model(
                    model_config=model,
                    prompt=request.test_prompt,
                    max_tokens=request.max_tokens or model.max_tokens,
                    temperature=0.7
                )
                
                if call_result["error"]:
                    comparison_results.append(ModelComparisonResult(
                        model_id=model_id,
                        response="",
                        response_time=0.0,
                        token_count=0,
                        cost=0.0,
                        quality_score=0.0,
                        error=call_result["error"]
                    ))
                else:
                    comparison_results.append(ModelComparisonResult(
                        model_id=model_id,
                        response=call_result["response"],
                        response_time=call_result["response_time"],
                        token_count=call_result["token_count"],
                        cost=call_result["cost"],
                        quality_score=call_result["quality_score"]
                    ))
                
            except Exception as model_error:
                comparison_results.append(ModelComparisonResult(
                    model_id=model_id,
                    response="",
                    response_time=0.0,
                    token_count=0,
                    cost=0.0,
                    quality_score=0.0,
                    error=str(model_error)
                ))
        
        logger.info(f"모델 비교 완료: {len(comparison_results)}개 모델", extra={
            'user_id': current_user.id,
            'model_ids': request.model_ids,
            'task_type': request.task_type
        })
        
        return comparison_results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"모델 비교 오류: {e}")
        raise HTTPException(status_code=500, detail="모델 비교에 실패했습니다")

@ai_model_settings_router.get("/usage-stats/summary")
async def get_usage_summary(
    timeframe: str = Query("30d", description="조회 기간: 1d, 7d, 30d"),
    current_user: User = Depends(get_current_user)
):
    """전체 모델 사용량 요약"""
    try:
        if current_user.role not in ["admin", "secretary"]:
            raise HTTPException(
                status_code=403, 
                detail="사용량 통계 조회 권한이 없습니다"
            )
        
        models = await ai_model_service.get_available_models()
        
        summary = {
            "timeframe": timeframe,
            "total_models": len(models),
            "active_models": len([m for m in models if m.status == ModelStatus.ACTIVE]),
            "total_requests": 0,
            "total_cost": 0.0,
            "model_breakdown": []
        }
        
        for model in models:
            performance = await ai_model_service.get_model_performance(model.model_id, timeframe)
            
            model_summary = {
                "model_id": model.model_id,
                "display_name": model.display_name,
                "provider": model.provider,
                "total_requests": performance.get("total_requests", 0),
                "total_cost": performance.get("total_cost", 0.0),
                "avg_response_time": performance.get("avg_response_time", 0.0),
                "error_rate": performance.get("error_rate", 0.0),
                "quality_score": performance.get("quality_score", model.quality_score),
                "health_status": performance.get("health_status", True)
            }
            
            summary["model_breakdown"].append(model_summary)
            summary["total_requests"] += model_summary["total_requests"]
            summary["total_cost"] += model_summary["total_cost"]
        
        # Sort by usage
        summary["model_breakdown"].sort(key=lambda x: x["total_requests"], reverse=True)
        
        return {
            "success": True,
            "summary": summary
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"사용량 요약 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="사용량 요약 조회에 실패했습니다")

@ai_model_settings_router.post("/{model_id}/usage-limits")
async def set_usage_limits(
    model_id: str,
    limits: UsageLimitConfig,
    current_user: User = Depends(get_current_user)
):
    """모델 사용량 제한 설정"""
    try:
        if current_user.role != "admin":
            raise HTTPException(
                status_code=403, 
                detail="관리자만 사용량 제한을 설정할 수 있습니다"
            )
        
        model = await ai_model_service.get_model_by_id(model_id)
        if not model:
            raise HTTPException(status_code=404, detail="모델을 찾을 수 없습니다")
        
        # Store usage limits (in real implementation, this would be saved to database)
        usage_limits = {
            "model_id": model_id,
            "daily_limit": limits.daily_limit,
            "monthly_limit": limits.monthly_limit,
            "cost_limit": limits.cost_limit,
            "alert_threshold": limits.alert_threshold,
            "set_by": current_user.id,
            "set_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"사용량 제한 설정: {model_id}", extra={
            'user_id': current_user.id,
            'model_id': model_id,
            'limits': limits.dict(exclude_unset=True)
        })
        
        return {
            "success": True,
            "message": "사용량 제한이 설정되었습니다",
            "limits": usage_limits
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"사용량 제한 설정 오류: {e}")
        raise HTTPException(status_code=500, detail="사용량 제한 설정에 실패했습니다")

@ai_model_settings_router.get("/health/status")
async def get_health_status(
    current_user: User = Depends(get_current_user)
):
    """모든 모델의 건강 상태 조회"""
    try:
        if current_user.role not in ["admin", "secretary"]:
            raise HTTPException(
                status_code=403, 
                detail="모델 상태 조회 권한이 없습니다"
            )
        
        healthy_models = await load_balancer.get_healthy_models()
        all_models = await ai_model_service.get_available_models()
        
        health_status = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_models": len(all_models),
            "healthy_models": len(healthy_models),
            "unhealthy_models": len(all_models) - len(healthy_models),
            "models": []
        }
        
        for model in all_models:
            is_healthy = model.model_id in healthy_models
            failure_count = load_balancer.failure_counts.get(model.model_id, 0)
            last_failure = load_balancer.last_failure_times.get(model.model_id)
            
            model_health = {
                "model_id": model.model_id,
                "display_name": model.display_name,
                "provider": model.provider,
                "status": model.status,
                "is_healthy": is_healthy,
                "failure_count": failure_count,
                "last_failure": last_failure.isoformat() if last_failure else None,
                "quality_score": model.quality_score,
                "reliability_score": model.reliability_score
            }
            
            health_status["models"].append(model_health)
        
        return {
            "success": True,
            "health_status": health_status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"모델 상태 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="모델 상태 조회에 실패했습니다")

@ai_model_settings_router.post("/optimize/auto-select")
async def auto_select_optimal_model(
    request: ModelRecommendationRequest,
    current_user: User = Depends(get_current_user)
):
    """컨텍스트 기반 자동 최적 모델 선택"""
    try:
        if current_user.role not in ["admin", "secretary"]:
            raise HTTPException(
                status_code=403, 
                detail="자동 모델 선택 권한이 없습니다"
            )
        
        context = request.dict()
        recommendation = await smart_recommender.recommend_model(context)
        
        # Auto-apply the recommendation (set as default for the context)
        optimal_model = await ai_model_service.get_model_by_id(recommendation.model_id)
        
        result = {
            "success": True,
            "selected_model": {
                "model_id": recommendation.model_id,
                "display_name": optimal_model.display_name,
                "provider": optimal_model.provider,
                "confidence": recommendation.confidence,
                "reasoning": recommendation.reasoning,
                "estimated_cost": recommendation.estimated_cost,
                "estimated_quality": recommendation.estimated_quality
            },
            "context": context,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"자동 모델 선택 완료: {recommendation.model_id}", extra={
            'user_id': current_user.id,
            'selected_model': recommendation.model_id,
            'confidence': recommendation.confidence,
            'context': context
        })
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"자동 모델 선택 오류: {e}")
        raise HTTPException(status_code=500, detail="자동 모델 선택에 실패했습니다")

# === 모델 관리 CRUD 엔드포인트 ===

@ai_model_settings_router.post("/create", response_model=AIModelConfig)
async def create_new_model(
    request: CreateModelRequest,
    current_user: User = Depends(get_current_user)
):
    """새로운 AI 모델 추가"""
    try:
        if current_user.role != "admin":
            raise HTTPException(
                status_code=403, 
                detail="모델 생성 권한은 관리자만 가능합니다"
            )
        
        # 중복 ID 확인
        existing_model = await ai_model_service.get_model_by_id(request.model_id)
        if existing_model:
            raise HTTPException(
                status_code=400, 
                detail=f"모델 ID '{request.model_id}'가 이미 존재합니다"
            )
        
        # 새 모델 설정 생성
        new_model = AIModelConfig(
            model_id=request.model_id,
            provider=request.provider,
            model_name=request.model_name,
            display_name=request.display_name,
            api_endpoint=request.api_endpoint,
            parameters=request.parameters,
            cost_per_token=request.cost_per_token,
            max_tokens=request.max_tokens,
            context_window=request.context_window,
            capabilities=request.capabilities,
            quality_score=request.quality_score,
            speed_score=request.speed_score,
            cost_score=request.cost_score,
            reliability_score=request.reliability_score,
            status=ModelStatus.ACTIVE,
            is_default=request.is_default,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # 기본 모델 설정시 기존 기본 모델 해제
        if request.is_default:
            await ai_model_service.clear_default_models()
        
        # 모델 등록
        registered_model = await ai_model_service.register_model(new_model)
        
        logger.info(f"새 모델 생성: {request.model_id}", extra={
            'user_id': current_user.id,
            'model_id': request.model_id,
            'provider': request.provider
        })
        
        return registered_model
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"모델 생성 오류: {e}")
        raise HTTPException(status_code=500, detail="모델 생성에 실패했습니다")

@ai_model_settings_router.put("/{model_id}", response_model=AIModelConfig)
async def update_model(
    model_id: str,
    request: UpdateModelRequest,
    current_user: User = Depends(get_current_user)
):
    """기존 AI 모델 수정"""
    try:
        if current_user.role != "admin":
            raise HTTPException(
                status_code=403, 
                detail="모델 수정 권한은 관리자만 가능합니다"
            )
        
        # 기존 모델 확인
        existing_model = await ai_model_service.get_model_by_id(model_id)
        if not existing_model:
            raise HTTPException(
                status_code=404, 
                detail=f"모델 ID '{model_id}'를 찾을 수 없습니다"
            )
        
        # 업데이트할 필드만 수정
        update_data = request.dict(exclude_unset=True)
        
        # 기본 모델 설정시 기존 기본 모델 해제
        if update_data.get('is_default'):
            await ai_model_service.clear_default_models()
        
        # 모델 업데이트
        updated_model = await ai_model_service.update_model(model_id, update_data)
        
        logger.info(f"모델 수정: {model_id}", extra={
            'user_id': current_user.id,
            'model_id': model_id,
            'updated_fields': list(update_data.keys())
        })
        
        return updated_model
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"모델 수정 오류: {e}")
        raise HTTPException(status_code=500, detail="모델 수정에 실패했습니다")

@ai_model_settings_router.delete("/{model_id}")
async def delete_model(
    model_id: str,
    current_user: User = Depends(get_current_user)
):
    """AI 모델 삭제"""
    try:
        if current_user.role != "admin":
            raise HTTPException(
                status_code=403, 
                detail="모델 삭제 권한은 관리자만 가능합니다"
            )
        
        # 기존 모델 확인
        existing_model = await ai_model_service.get_model_by_id(model_id)
        if not existing_model:
            raise HTTPException(
                status_code=404, 
                detail=f"모델 ID '{model_id}'를 찾을 수 없습니다"
            )
        
        # 기본 시스템 모델은 삭제 방지
        protected_models = ["gpt-4", "gpt-3.5-turbo", "claude-3-opus", "gemini-pro"]
        if model_id in protected_models:
            raise HTTPException(
                status_code=400, 
                detail="기본 시스템 모델은 삭제할 수 없습니다"
            )
        
        # 모델 삭제
        await ai_model_service.delete_model(model_id)
        
        logger.info(f"모델 삭제: {model_id}", extra={
            'user_id': current_user.id,
            'model_id': model_id
        })
        
        return {
            "success": True,
            "message": f"모델 '{model_id}'가 성공적으로 삭제되었습니다",
            "deleted_model_id": model_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"모델 삭제 오류: {e}")
        raise HTTPException(status_code=500, detail="모델 삭제에 실패했습니다")

@ai_model_settings_router.get("/templates/list")
async def get_model_templates(
    current_user: User = Depends(get_current_user)
):
    """사용 가능한 모델 템플릿 목록 조회"""
    try:
        if current_user.role not in ["admin", "secretary"]:
            raise HTTPException(
                status_code=403, 
                detail="템플릿 조회 권한이 없습니다"
            )
        
        # DEFAULT_MODEL_TEMPLATES 사용하여 동적 템플릿 목록 생성
        templates = []
        for template_name, template in DEFAULT_MODEL_TEMPLATES.items():
            template_dict = {
                "name": template.name,
                "provider": template.provider.value,
                "description": template.description,
                "capabilities": template.default_config.capabilities,
                "default_config": {
                    "provider": template.default_config.provider.value,
                    "model_name": template.default_config.model_name,
                    "display_name": template.default_config.display_name,
                    "api_endpoint": template.default_config.api_endpoint,
                    "parameters": template.default_config.parameters,
                    "cost_per_token": template.default_config.cost_per_token,
                    "max_tokens": template.default_config.max_tokens,
                    "context_window": template.default_config.context_window,
                    "capabilities": template.default_config.capabilities,
                    "quality_score": template.default_config.quality_score,
                    "speed_score": template.default_config.speed_score,
                    "cost_score": template.default_config.cost_score,
                    "reliability_score": template.default_config.reliability_score
                }
            }
            templates.append(template_dict)
        
        return {
            "success": True,
            "templates": templates
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"템플릿 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="템플릿 조회에 실패했습니다")

@ai_model_settings_router.post("/templates/{template_name}/create")
async def create_model_from_template(
    template_name: str,
    current_user: User = Depends(get_current_user)
):
    """템플릿을 기반으로 새 모델 생성"""
    try:
        if current_user.role != "admin":
            raise HTTPException(
                status_code=403, 
                detail="템플릿 기반 모델 생성 권한은 관리자만 가능합니다"
            )
        
        # DEFAULT_MODEL_TEMPLATES에서 직접 찾기
        if template_name not in DEFAULT_MODEL_TEMPLATES:
            raise HTTPException(
                status_code=404, 
                detail=f"템플릿 '{template_name}'을 찾을 수 없습니다"
            )
        
        template = DEFAULT_MODEL_TEMPLATES[template_name]
        
        # 중복 ID 확인
        existing_model = await ai_model_service.get_model_by_id(template.default_config.model_id)
        if existing_model:
            # 기존 모델 ID에 타임스탬프 추가
            timestamp = int(datetime.utcnow().timestamp())
            new_model_id = f"{template.default_config.model_id}-{timestamp}"
        else:
            new_model_id = template.default_config.model_id
        
        # 템플릿 기반으로 모델 생성
        create_request = CreateModelRequest(
            model_id=new_model_id,
            provider=template.default_config.provider,
            model_name=template.default_config.model_name,
            display_name=template.default_config.display_name,
            api_endpoint=template.default_config.api_endpoint,
            parameters=template.default_config.parameters,
            cost_per_token=template.default_config.cost_per_token,
            max_tokens=template.default_config.max_tokens,
            context_window=template.default_config.context_window,
            capabilities=template.default_config.capabilities,
            quality_score=template.default_config.quality_score,
            speed_score=template.default_config.speed_score,
            cost_score=template.default_config.cost_score,
            reliability_score=template.default_config.reliability_score,
            is_default=template.default_config.is_default
        )
        
        # 모델 생성
        new_model = await create_new_model(create_request, current_user)
        
        logger.info(f"템플릿 기반 모델 생성: {new_model_id} (템플릿: {template_name})", extra={
            'user_id': current_user.id,
            'model_id': new_model_id,
            'template': template_name
        })
        
        return new_model
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"템플릿 기반 모델 생성 오류: {e}")
        raise HTTPException(status_code=500, detail="템플릿 기반 모델 생성에 실패했습니다")

@ai_model_settings_router.post("/{model_id}/test-connection")
async def test_model_connection(
    model_id: str,
    current_user: User = Depends(get_current_user)
):
    """모델 연결 테스트"""
    try:
        if current_user.role not in ["admin", "secretary"]:
            raise HTTPException(
                status_code=403, 
                detail="모델 테스트 권한이 없습니다"
            )
        
        # 모델 정보 조회
        model = await ai_model_service.get_model_by_id(model_id)
        if not model:
            raise HTTPException(
                status_code=404, 
                detail=f"모델 ID '{model_id}'를 찾을 수 없습니다"
            )
        
        # 다중 테스트 실행
        test_results = []
        
        # 기본 연결 테스트
        basic_test = await call_ai_model(
            model_config=model,
            prompt="안녕하세요. 연결 테스트입니다. '연결 성공'이라고 간단히 응답해주세요.",
            max_tokens=20,
            temperature=0.1
        )
        test_results.append({
            "test_name": "기본 연결",
            "result": basic_test
        })
        
        # 한국어 처리 테스트 (korean capability가 있는 경우)
        if "korean" in model.capabilities or "multilingual" in model.capabilities:
            korean_test = await call_ai_model(
                model_config=model,
                prompt="다음 문장을 요약해주세요: '인공지능 기술이 빠르게 발전하면서 다양한 분야에서 활용되고 있습니다.' 한 문장으로 요약해주세요.",
                max_tokens=50,
                temperature=0.3
            )
            test_results.append({
                "test_name": "한국어 처리",
                "result": korean_test
            })
        
        # 평가 능력 테스트 (evaluation capability가 있는 경우)
        if "evaluation" in model.capabilities:
            eval_test = await call_ai_model(
                model_config=model,
                prompt="1에서 10점까지 중에서 '좋은 날씨'를 평가해주세요. 점수만 답해주세요.",
                max_tokens=10,
                temperature=0.1
            )
            test_results.append({
                "test_name": "평가 능력",
                "result": eval_test
            })
        
        # 분석 능력 테스트 (analysis capability가 있는 경우)
        if "analysis" in model.capabilities:
            analysis_test = await call_ai_model(
                model_config=model,
                prompt="다음 데이터를 분석해주세요: [1, 3, 5, 7, 9]. 패턴을 한 문장으로 설명해주세요.",
                max_tokens=30,
                temperature=0.2
            )
            test_results.append({
                "test_name": "분석 능력",
                "result": analysis_test
            })
        
        # 전체 건강도 판단
        healthy_tests = sum(1 for test in test_results if test["result"]["error"] is None)
        total_tests = len(test_results)
        health_score = healthy_tests / total_tests if total_tests > 0 else 0
        is_healthy = health_score >= 0.8  # 80% 이상 성공시 건강
        
        # 평균 응답 시간 계산
        avg_response_time = sum(test["result"]["response_time"] for test in test_results) / total_tests
        
        # 결과 반환
        result = {
            "success": True,
            "model_id": model_id,
            "is_healthy": is_healthy,
            "health_score": health_score,
            "avg_response_time": avg_response_time,
            "total_tests": total_tests,
            "successful_tests": healthy_tests,
            "test_details": test_results,
            "model_info": {
                "display_name": model.display_name,
                "provider": model.provider.value,
                "capabilities": model.capabilities,
                "quality_score": model.quality_score,
                "speed_score": model.speed_score
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"모델 연결 테스트: {model_id} - {'성공' if is_healthy else '실패'}", extra={
            'user_id': current_user.id,
            'model_id': model_id,
            'is_healthy': is_healthy,
            'response_time': test_result["response_time"]
        })
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"모델 연결 테스트 오류: {e}")
        raise HTTPException(status_code=500, detail="모델 연결 테스트에 실패했습니다")