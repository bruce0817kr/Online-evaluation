"""AI Provider MongoDB 오류 테스트"""

import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import logging

# 로깅 설정
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_ai_provider_creation():
    """AI Provider 생성 시 발생하는 오류 테스트"""
    
    # MongoDB 연결
    mongo_url = os.getenv("MONGO_URL", "mongodb://admin:password123@localhost:27017/evaluation_db?authSource=admin")
    logger.info(f"MongoDB URL: {mongo_url}")
    
    try:
        client = AsyncIOMotorClient(mongo_url)
        db = client.evaluation_db
        ai_providers_collection = db.ai_providers
        
        # 연결 테스트
        await client.admin.command('ping')
        logger.info("MongoDB 연결 성공")
        
        # AI Provider 데이터 생성 시도
        provider_data = {
            "provider_name": "openai",
            "display_name": "OpenAI",
            "api_key": "encrypted_test_key",
            "api_endpoint": "https://api.openai.com/v1",
            "is_active": True,
            "priority": 1,
            "max_tokens": 4096,
            "temperature": 0.7,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "created_by": "test_admin"
        }
        
        logger.info("AI Provider 데이터 삽입 시도...")
        result = await ai_providers_collection.insert_one(provider_data)
        logger.info(f"삽입 성공! ID: {result.inserted_id}")
        
        # 데이터 조회
        inserted = await ai_providers_collection.find_one({"_id": result.inserted_id})
        logger.info(f"조회된 데이터: {inserted}")
        
        # 모델 임포트 시도
        try:
            from models import AIProviderConfig
            logger.info("AIProviderConfig 모델 임포트 성공")
        except ImportError as e:
            logger.error(f"AIProviderConfig 모델 임포트 실패: {e}")
            
        # ai_admin_endpoints 임포트 시도
        try:
            from ai_admin_endpoints import encrypt_api_key, get_database
            logger.info("ai_admin_endpoints 함수 임포트 성공")
            
            # 암호화 테스트
            encrypted = encrypt_api_key("test_key")
            logger.info(f"API 키 암호화 성공: {encrypted[:20]}...")
            
        except ImportError as e:
            logger.error(f"ai_admin_endpoints 임포트 실패: {e}")
            
    except Exception as e:
        logger.error(f"테스트 중 오류 발생: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    asyncio.run(test_ai_provider_creation())