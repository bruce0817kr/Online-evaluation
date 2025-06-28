"""
AI 공급자 관리 API 엔드포인트 (관리자 전용)
관리자가 AI 공급자 설정, 모델 설정, 사용량 모니터링 등을 관리할 수 있는 API
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import logging
import asyncio
import json
import base64
from cryptography.fernet import Fernet
import os
import traceback
from bson import ObjectId

from models import (
    User, AIProviderConfig, AIProviderConfigCreate, AIProviderConfigUpdate,
    AIModelConfig, AIServiceStatus, AIAnalysisJob, AIUsageStatistics,
    AIProviderTestRequest
)
from security import get_current_user

def check_admin_role(user):
    """관리자 권한 확인"""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다")
    return True

logger = logging.getLogger(__name__)

# AI 관리자 라우터 생성
ai_admin_router = APIRouter(prefix="/api/admin/ai", tags=["AI 관리자"])

# 암호화 키 설정 (환경변수에서 가져오거나 생성)
ENCRYPTION_KEY = os.getenv("AI_CONFIG_ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    ENCRYPTION_KEY = Fernet.generate_key()
    logger.warning("AI_CONFIG_ENCRYPTION_KEY가 설정되지 않았습니다. 임시 키를 생성했습니다.")

cipher_suite = Fernet(ENCRYPTION_KEY)

def encrypt_api_key(api_key: str) -> str:
    """API 키 암호화"""
    return base64.b64encode(cipher_suite.encrypt(api_key.encode())).decode()

def decrypt_api_key(encrypted_key: str) -> str:
    """API 키 복호화"""
    try:
        return cipher_suite.decrypt(base64.b64decode(encrypted_key.encode())).decode()
    except Exception as e:
        logger.error(f"API 키 복호화 실패: {e}")
        return ""

# 데이터베이스 연결 안정화
async def get_database():
    """안정적인 데이터베이스 연결 획득"""
    try:
        # server.py에서 db 가져오기 시도
        from server import db
        logger.info("Successfully imported database connection from server.py")
        return db
    except ImportError:
        # 직접 연결 생성
        logger.warning("Failed to import from server.py, creating direct connection")
        MONGODB_URL = os.getenv("MONGO_URL", "mongodb://admin:password123@mongodb:27017/evaluation_db?authSource=admin")
        logger.info(f"Using MongoDB URL: {MONGODB_URL}")
        client = AsyncIOMotorClient(MONGODB_URL)
        return client.evaluation_db

# 전역 데이터베이스 변수 초기화
db = None
ai_providers_collection = None
ai_models_collection = None
ai_jobs_collection = None

async def initialize_collections():
    """컬렉션 초기화"""
    global db, ai_providers_collection, ai_models_collection, ai_jobs_collection
    
    if db is None:
        db = await get_database()
        ai_providers_collection = db.ai_providers
        ai_models_collection = db.ai_models
        ai_jobs_collection = db.ai_analysis_jobs
        logger.info("Database collections initialized successfully")
    
    return db

@ai_admin_router.post("/providers", response_model=AIProviderConfig)
async def create_ai_provider(
    config: AIProviderConfigCreate,
    current_user: User = Depends(get_current_user)
):
    """AI 공급자 설정 생성"""
    # 관리자 권한 확인
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="관리자만 AI 공급자를 설정할 수 있습니다")
    
    try:
        # API 키 암호화
        encrypted_api_key = encrypt_api_key(config.api_key)
        
        # 공급자 설정 생성
        provider_data = {
            "provider_name": config.provider_name,
            "display_name": config.display_name,
            "api_key": encrypted_api_key,
            "api_endpoint": config.api_endpoint,
            "is_active": config.is_active,
            "priority": config.priority,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "created_by": current_user.id
        }
        
        # 데이터베이스 컬렉션 초기화
        await initialize_collections()
        
        # 기존 공급자 중복 확인
        existing = await ai_providers_collection.find_one({"provider_name": config.provider_name})
        if existing:
            raise HTTPException(status_code=400, detail="이미 설정된 AI 공급자입니다")
        
        # 데이터베이스에 저장
        result = await ai_providers_collection.insert_one(provider_data)
        provider_data["_id"] = result.inserted_id
        
        # 기본 모델들 자동 추가
        await _create_default_models(str(result.inserted_id), config.provider_name)
        
        logger.info(f"AI 공급자 생성: {config.provider_name}", extra={
            'user_id': current_user.id,
            'provider_name': config.provider_name
        })
        
        # 응답에서는 암호화된 키 제외
        provider_data["api_key"] = "***encrypted***"
        return AIProviderConfig.from_mongo(provider_data)
        
    except Exception as e:
        logger.error(f"AI 공급자 생성 오류: {e}")
        raise HTTPException(status_code=500, detail=f"공급자 생성 중 오류가 발생했습니다: {str(e)}")

@ai_admin_router.get("/test")
async def test_ai_admin(current_user: User = Depends(get_current_user)):
    """AI 관리자 테스트 엔드포인트"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="관리자만 접근 가능합니다")
    
    try:
        logger.info("Testing AI admin endpoint")
        
        # 데이터베이스 컬렉션 초기화 테스트
        await initialize_collections()
        logger.info("Collections initialized successfully")
        
        # AIProviderConfig 클래스 테스트
        test_data = {
            "_id": "test123",
            "provider_name": "test",
            "display_name": "Test Provider",
            "api_key": "***encrypted***",
            "is_active": True,
            "priority": 1,
            "temperature": 0.3,
            "created_by": "test_admin",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # from_mongo 메서드 테스트
        logger.info("Testing from_mongo method")
        test_obj = AIProviderConfig.from_mongo(test_data)
        logger.info(f"from_mongo test successful: {test_obj}")
        
        return {"status": "success", "test_result": "AI admin endpoint working"}
        
    except Exception as e:
        logger.error(f"AI 테스트 오류: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"테스트 중 오류: {str(e)}")

@ai_admin_router.get("/providers", response_model=List[AIProviderConfig])
async def get_ai_providers(current_user: User = Depends(get_current_user)):
    """AI 공급자 목록 조회"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="관리자만 AI 공급자 목록을 볼 수 있습니다")
    
    try:
        # 데이터베이스 컬렉션 초기화
        await initialize_collections()
        
        providers = await ai_providers_collection.find().to_list(length=None)
        logger.info(f"Found {len(providers)} providers from database")
        
        # API 키 마스킹
        result_providers = []
        for i, provider in enumerate(providers):
            try:
                logger.info(f"Processing provider {i}: {provider.get('provider_name', 'unknown')}")
                provider["api_key"] = "***encrypted***"
                
                # 필수 필드 기본값 설정 (기존 데이터 호환성)
                if "created_by" not in provider:
                    provider["created_by"] = "system"
                if "created_at" not in provider:
                    provider["created_at"] = datetime.utcnow()
                if "updated_at" not in provider:
                    provider["updated_at"] = datetime.utcnow()
                if "temperature" not in provider:
                    provider["temperature"] = 0.3
                
                # from_mongo 메서드 호출 시 상세 로깅
                provider_obj = AIProviderConfig.from_mongo(provider)
                if provider_obj:
                    result_providers.append(provider_obj)
                else:
                    logger.warning(f"from_mongo returned None for provider {i}")
                    
            except Exception as provider_error:
                logger.error(f"Error processing provider {i}: {str(provider_error)}")
                logger.error(f"Provider data: {provider}")
                # 개별 공급자 오류는 건너뛰고 계속 진행
                continue
        
        return result_providers
        
    except Exception as e:
        logger.error(f"AI 공급자 목록 조회 오류: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"공급자 목록 조회 중 오류가 발생했습니다: {str(e)}")

@ai_admin_router.put("/providers/{provider_id}", response_model=AIProviderConfig)
async def update_ai_provider(
    provider_id: str,
    config: AIProviderConfigUpdate,
    current_user: User = Depends(get_current_user)
):
    """AI 공급자 설정 업데이트"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="관리자만 AI 공급자를 수정할 수 있습니다")
    
    try:
        # 데이터베이스 컬렉션 초기화
        await initialize_collections()
        
        # 기존 설정 조회
        try:
            object_id = ObjectId(provider_id)
        except:
            raise HTTPException(status_code=400, detail="잘못된 공급자 ID 형식입니다")
        
        existing = await ai_providers_collection.find_one({"_id": object_id})
        if not existing:
            raise HTTPException(status_code=404, detail="AI 공급자를 찾을 수 없습니다")
        
        # 업데이트 데이터 준비
        update_data = {"updated_at": datetime.utcnow()}
        
        # 변경된 필드만 업데이트
        if config.display_name is not None:
            update_data["display_name"] = config.display_name
        if config.api_key is not None:
            update_data["api_key"] = encrypt_api_key(config.api_key)
        if config.api_endpoint is not None:
            update_data["api_endpoint"] = config.api_endpoint
        if config.is_active is not None:
            update_data["is_active"] = config.is_active
        if config.priority is not None:
            update_data["priority"] = config.priority
        if config.max_tokens is not None:
            update_data["max_tokens"] = config.max_tokens
        if config.temperature is not None:
            update_data["temperature"] = config.temperature
        
        # 데이터베이스 업데이트
        await ai_providers_collection.update_one(
            {"_id": object_id},
            {"$set": update_data}
        )
        
        # 업데이트된 설정 조회
        updated = await ai_providers_collection.find_one({"_id": object_id})
        updated["api_key"] = "***encrypted***"
        
        logger.info(f"AI 공급자 업데이트: {provider_id}", extra={
            'user_id': current_user.id,
            'provider_id': provider_id
        })
        
        return AIProviderConfig.from_mongo(updated)
        
    except Exception as e:
        logger.error(f"AI 공급자 업데이트 오류: {e}")
        raise HTTPException(status_code=500, detail=f"공급자 업데이트 중 오류가 발생했습니다: {str(e)}")

@ai_admin_router.delete("/providers/{provider_id}")
async def delete_ai_provider(
    provider_id: str,
    current_user: User = Depends(get_current_user)
):
    """AI 공급자 설정 삭제"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="관리자만 AI 공급자를 삭제할 수 있습니다")
    
    try:
        # 공급자 존재 확인
        try:
            object_id = ObjectId(provider_id)
        except:
            raise HTTPException(status_code=400, detail="잘못된 공급자 ID 형식입니다")
        
        existing = await ai_providers_collection.find_one({"_id": object_id})
        if not existing:
            raise HTTPException(status_code=404, detail="AI 공급자를 찾을 수 없습니다")
        
        # 관련 모델 설정도 함께 삭제
        await ai_models_collection.delete_many({"provider_id": str(object_id)})
        
        # 공급자 삭제
        await ai_providers_collection.delete_one({"_id": object_id})
        
        logger.info(f"AI 공급자 삭제: {provider_id}", extra={
            'user_id': current_user.id,
            'provider_id': provider_id
        })
        
        return {"message": "AI 공급자가 성공적으로 삭제되었습니다"}
        
    except Exception as e:
        logger.error(f"AI 공급자 삭제 오류: {e}")
        raise HTTPException(status_code=500, detail=f"공급자 삭제 중 오류가 발생했습니다: {str(e)}")

@ai_admin_router.post("/providers/{provider_id}/test")
async def test_ai_provider(
    provider_id: str,
    current_user: User = Depends(get_current_user)
):
    """AI 공급자 연결 테스트"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="관리자만 AI 공급자를 테스트할 수 있습니다")
    
    try:
        # 공급자 설정 조회
        try:
            object_id = ObjectId(provider_id)
        except:
            raise HTTPException(status_code=400, detail="잘못된 공급자 ID 형식입니다")
        
        provider = await ai_providers_collection.find_one({"_id": object_id})
        if not provider:
            raise HTTPException(status_code=404, detail="AI 공급자를 찾을 수 없습니다")
        
        # API 키 복호화
        api_key = decrypt_api_key(provider["api_key"])
        provider_name = provider["provider_name"]
        
        # 공급자별 테스트 수행
        test_result = await _test_provider_connection(provider_name, api_key, provider.get("api_endpoint"))
        
        logger.info(f"AI 공급자 테스트: {provider_id}", extra={
            'user_id': current_user.id,
            'provider_id': provider_id,
            'test_result': test_result["status"]
        })
        
        return test_result
        
    except Exception as e:
        logger.error(f"AI 공급자 테스트 오류: {e}")
        raise HTTPException(status_code=500, detail=f"공급자 테스트 중 오류가 발생했습니다: {str(e)}")

@ai_admin_router.get("/status", response_model=AIServiceStatus)
async def get_ai_service_status(current_user: User = Depends(get_current_user)):
    """AI 서비스 전체 상태 조회"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="관리자만 AI 서비스 상태를 볼 수 있습니다")
    
    try:
        # 모든 공급자 조회
        providers = await ai_providers_collection.find().to_list(length=None)
        
        provider_statuses = []
        active_count = 0
        default_provider = None
        
        for provider in providers:
            status_info = {
                "id": str(provider["_id"]),
                "provider_name": provider["provider_name"],
                "display_name": provider["display_name"],
                "is_active": provider["is_active"],
                "priority": provider["priority"],
                "last_tested": provider.get("last_tested"),
                "status": "unknown"
            }
            
            if provider["is_active"]:
                active_count += 1
                if not default_provider or provider["priority"] < providers[0]["priority"]:
                    default_provider = provider["provider_name"]
            
            provider_statuses.append(status_info)
        
        return AIServiceStatus(
            provider_statuses=provider_statuses,
            active_providers=active_count,
            total_providers=len(providers),
            default_provider=default_provider,
            last_updated=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"AI 서비스 상태 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="서비스 상태 조회 중 오류가 발생했습니다")

@ai_admin_router.get("/providers/{provider_name}/models")
async def get_available_models(
    provider_name: str,
    api_key: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """AI 공급자의 사용 가능한 모델 목록을 동적으로 가져오기"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="관리자만 모델 목록을 조회할 수 있습니다")
    
    try:
        # API 키가 제공되지 않은 경우 저장된 공급자에서 가져오기
        if not api_key:
            await initialize_collections()
            provider = await ai_providers_collection.find_one({"provider_name": provider_name})
            if provider:
                api_key = decrypt_api_key(provider["api_key"])
        
        if not api_key:
            # API 키가 없는 경우 기본 모델 목록 반환
            return await _get_default_models_for_provider(provider_name)
        
        # 공급자별로 실제 API에서 모델 목록 가져오기
        models = await _fetch_models_from_provider(provider_name, api_key)
        
        return {
            "provider_name": provider_name,
            "models": models,
            "source": "dynamic",
            "fetched_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"모델 목록 조회 오류 ({provider_name}): {e}")
        # 오류 발생 시 기본 모델 목록 반환
        fallback_models = await _get_default_models_for_provider(provider_name)
        return {
            "provider_name": provider_name,
            "models": fallback_models["models"],
            "source": "fallback",
            "error": str(e),
            "fetched_at": datetime.utcnow().isoformat()
        }

@ai_admin_router.get("/usage-statistics")
async def get_ai_usage_statistics(
    period: str = "daily",
    days: int = 30,
    current_user: User = Depends(get_current_user)
):
    """AI 사용 통계 조회"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="관리자만 사용 통계를 볼 수 있습니다")
    
    try:
        # TODO: 실제 사용 통계 집계 로직 구현
        # 현재는 샘플 데이터 반환
        
        sample_stats = []
        for i in range(days):
            date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            date = date.replace(day=date.day - i)
            
            stats = {
                "period": period,
                "date": date.isoformat(),
                "provider_usage": {
                    "openai": 10 + i,
                    "anthropic": 5 + i//2,
                    "google": 3 + i//3
                },
                "total_requests": 18 + i,
                "total_tokens": (18 + i) * 1500,
                "total_cost": (18 + i) * 0.002,
                "success_rate": 0.95 + (i % 5) * 0.01,
                "average_response_time": 1.2 + (i % 10) * 0.1
            }
            sample_stats.append(stats)
        
        return sample_stats
        
    except Exception as e:
        logger.error(f"AI 사용 통계 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="사용 통계 조회 중 오류가 발생했습니다")

async def _create_default_models(provider_id: str, provider_name: str):
    """공급자별 기본 모델 설정 생성"""
    default_models = {
        "openai": [
            {"model_name": "gpt-4o-mini", "display_name": "GPT-4o Mini", "is_default": True},
            {"model_name": "gpt-4o", "display_name": "GPT-4o", "is_default": False},
            {"model_name": "gpt-3.5-turbo", "display_name": "GPT-3.5 Turbo", "is_default": False}
        ],
        "anthropic": [
            {"model_name": "claude-3-haiku-20240307", "display_name": "Claude 3 Haiku", "is_default": True},
            {"model_name": "claude-3-sonnet-20240229", "display_name": "Claude 3 Sonnet", "is_default": False},
            {"model_name": "claude-3-opus-20240229", "display_name": "Claude 3 Opus", "is_default": False}
        ],
        "google": [
            {"model_name": "gemini-pro", "display_name": "Gemini Pro", "is_default": True},
            {"model_name": "gemini-pro-vision", "display_name": "Gemini Pro Vision", "is_default": False}
        ],
        "groq": [
            {"model_name": "llama3-70b-8192", "display_name": "Llama 3 70B", "is_default": True},
            {"model_name": "llama3-8b-8192", "display_name": "Llama 3 8B", "is_default": False},
            {"model_name": "mixtral-8x7b-32768", "display_name": "Mixtral 8x7B", "is_default": False}
        ]
    }
    
    models_to_create = default_models.get(provider_name, [])
    
    for model_config in models_to_create:
        model_data = {
            "provider_id": provider_id,
            "model_name": model_config["model_name"],
            "display_name": model_config["display_name"],
            "model_type": "chat",
            "is_default": model_config["is_default"],
            "is_active": True,
            "max_tokens": 4096,
            "capabilities": ["text_generation", "document_analysis"],
            "created_at": datetime.utcnow()
        }
        
        await ai_models_collection.insert_one(model_data)

async def _get_default_models_for_provider(provider_name: str):
    """공급자별 기본 모델 목록 반환"""
    default_models = {
        "openai": [
            {"value": "gpt-4", "label": "GPT-4", "description": "Most capable GPT-4 model"},
            {"value": "gpt-4-turbo", "label": "GPT-4 Turbo", "description": "Faster and more affordable GPT-4"},
            {"value": "gpt-3.5-turbo", "label": "GPT-3.5 Turbo", "description": "Fast and cost-effective model"}
        ],
        "anthropic": [
            {"value": "claude-3-opus-20240229", "label": "Claude 3 Opus", "description": "Most capable Claude model"},
            {"value": "claude-3-sonnet-20240229", "label": "Claude 3 Sonnet", "description": "Balanced performance and speed"},
            {"value": "claude-3-haiku-20240307", "label": "Claude 3 Haiku", "description": "Fastest Claude model"}
        ],
        "google": [
            {"value": "gemini-pro", "label": "Gemini Pro", "description": "Google's most capable model"},
            {"value": "gemini-pro-vision", "label": "Gemini Pro Vision", "description": "Multimodal model with vision capabilities"}
        ],
        "groq": [
            {"value": "llama3-70b-8192", "label": "Llama 3 70B", "description": "Meta's large language model"},
            {"value": "llama3-8b-8192", "label": "Llama 3 8B", "description": "Smaller, faster Llama model"},
            {"value": "mixtral-8x7b-32768", "label": "Mixtral 8x7B", "description": "Mistral's mixture of experts model"}
        ]
    }
    
    models = default_models.get(provider_name, [])
    return {
        "provider_name": provider_name,
        "models": models,
        "source": "default"
    }

async def _fetch_models_from_provider(provider_name: str, api_key: str):
    """실제 AI 공급자 API에서 사용 가능한 모델 목록 가져오기"""
    try:
        if provider_name == "openai":
            import openai
            client = openai.AsyncOpenAI(api_key=api_key)
            models_response = await client.models.list()
            models = []
            
            # 채팅 모델만 필터링
            chat_models = [
                "gpt-4", "gpt-4-turbo", "gpt-4-turbo-preview", "gpt-4-0125-preview",
                "gpt-3.5-turbo", "gpt-3.5-turbo-0125", "gpt-3.5-turbo-1106"
            ]
            
            for model in models_response.data:
                if any(chat_model in model.id for chat_model in chat_models):
                    models.append({
                        "value": model.id,
                        "label": model.id.replace("-", " ").title(),
                        "description": f"OpenAI model: {model.id}",
                        "created": model.created
                    })
            
            return sorted(models, key=lambda x: x.get("created", 0), reverse=True)
            
        elif provider_name == "anthropic":
            # Anthropic doesn't have a models API, return updated default list
            return [
                {"value": "claude-3-opus-20240229", "label": "Claude 3 Opus", "description": "Most capable Claude model"},
                {"value": "claude-3-sonnet-20240229", "label": "Claude 3 Sonnet", "description": "Balanced performance and speed"},
                {"value": "claude-3-haiku-20240307", "label": "Claude 3 Haiku", "description": "Fastest Claude model"},
                {"value": "claude-2.1", "label": "Claude 2.1", "description": "Previous generation Claude model"},
                {"value": "claude-2.0", "label": "Claude 2.0", "description": "Earlier Claude model"}
            ]
            
        elif provider_name == "google":
            # Google Gemini API doesn't have a public models endpoint yet
            return [
                {"value": "gemini-pro", "label": "Gemini Pro", "description": "Google's most capable model"},
                {"value": "gemini-pro-vision", "label": "Gemini Pro Vision", "description": "Multimodal model with vision capabilities"},
                {"value": "gemini-1.5-pro-latest", "label": "Gemini 1.5 Pro", "description": "Latest Gemini model with extended context"}
            ]
            
        elif provider_name == "groq":
            # Groq uses OpenAI-compatible API
            import openai
            client = openai.AsyncOpenAI(
                api_key=api_key,
                base_url="https://api.groq.com/openai/v1"
            )
            models_response = await client.models.list()
            models = []
            
            for model in models_response.data:
                models.append({
                    "value": model.id,
                    "label": model.id.replace("-", " ").title(),
                    "description": f"Groq model: {model.id}",
                    "created": getattr(model, 'created', 0)
                })
            
            return sorted(models, key=lambda x: x.get("created", 0), reverse=True)
            
        else:
            # 지원하지 않는 공급자의 경우 기본 목록 반환
            fallback = await _get_default_models_for_provider(provider_name)
            return fallback["models"]
            
    except Exception as e:
        logger.error(f"모델 목록 API 호출 실패 ({provider_name}): {e}")
        # API 호출 실패 시 기본 목록 반환
        fallback = await _get_default_models_for_provider(provider_name)
        return fallback["models"]

async def _test_provider_connection(provider_name: str, api_key: str, api_endpoint: Optional[str] = None):
    """AI 공급자 연결 테스트"""
    try:
        if provider_name == "openai":
            import openai
            client = openai.AsyncOpenAI(api_key=api_key)
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Test connection"}],
                max_tokens=10
            )
            return {"status": "success", "message": "OpenAI 연결 성공", "response": response.choices[0].message.content}
            
        elif provider_name == "anthropic":
            from anthropic import AsyncAnthropic
            client = AsyncAnthropic(api_key=api_key)
            response = await client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=10,
                messages=[{"role": "user", "content": "Test connection"}]
            )
            return {"status": "success", "message": "Anthropic 연결 성공", "response": response.content[0].text}
            
        elif provider_name == "google":
            # Google Gemini API 테스트
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content("Test connection")
            return {"status": "success", "message": "Google Gemini 연결 성공", "response": response.text}
            
        elif provider_name == "groq":
            # Groq API 테스트 (OpenAI 호환)
            import openai
            client = openai.AsyncOpenAI(
                api_key=api_key,
                base_url="https://api.groq.com/openai/v1"
            )
            response = await client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{"role": "user", "content": "Test connection"}],
                max_tokens=10
            )
            return {"status": "success", "message": "Groq 연결 성공", "response": response.choices[0].message.content}
            
        else:
            return {"status": "error", "message": f"지원하지 않는 공급자: {provider_name}"}
            
    except Exception as e:
        return {"status": "error", "message": f"연결 테스트 실패: {str(e)}"}