"""MongoDB 연결 및 AI Provider 생성 테스트"""

import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from cryptography.fernet import Fernet
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_mongodb_connection():
    """MongoDB 연결 및 AI Provider 생성 문제 테스트"""
    
    # 환경 변수 설정
    os.environ['MONGO_URL'] = os.getenv('MONGO_URL', 'mongodb://localhost:27017/online_evaluation')
    os.environ['DB_NAME'] = 'online_evaluation'  # 누락된 DB_NAME 설정
    
    # AI 암호화 키 설정
    if not os.getenv('AI_CONFIG_ENCRYPTION_KEY'):
        os.environ['AI_CONFIG_ENCRYPTION_KEY'] = Fernet.generate_key().decode()
        logger.info("AI_CONFIG_ENCRYPTION_KEY 생성됨")
    
    mongo_url = os.environ['MONGO_URL']
    db_name = os.environ['DB_NAME']
    
    logger.info(f"MongoDB URL: {mongo_url}")
    logger.info(f"Database Name: {db_name}")
    
    try:
        # MongoDB 연결
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        
        # 연결 테스트
        result = await client.admin.command('ping')
        logger.info(f"MongoDB 연결 성공: {result}")
        
        # 컬렉션 초기화
        ai_providers_collection = db.ai_providers
        
        # 기존 데이터 확인
        count = await ai_providers_collection.count_documents({})
        logger.info(f"기존 AI Provider 수: {count}")
        
        # 암호화 테스트
        from cryptography.fernet import Fernet
        cipher_suite = Fernet(os.environ['AI_CONFIG_ENCRYPTION_KEY'].encode())
        
        # API 키 암호화
        test_api_key = "test-api-key-12345"
        encrypted_key = cipher_suite.encrypt(test_api_key.encode()).decode()
        logger.info(f"API 키 암호화 성공: {encrypted_key[:30]}...")
        
        # AI Provider 데이터 생성
        provider_data = {
            "provider_name": "openai",
            "display_name": "OpenAI",
            "api_key": encrypted_key,
            "api_endpoint": "https://api.openai.com/v1",
            "is_active": True,
            "priority": 1,
            "max_tokens": 4096,
            "temperature": 0.7,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "created_by": "test_admin"
        }
        
        # 데이터 삽입
        result = await ai_providers_collection.insert_one(provider_data)
        logger.info(f"AI Provider 삽입 성공! ID: {result.inserted_id}")
        
        # 삽입된 데이터 확인
        inserted = await ai_providers_collection.find_one({"_id": result.inserted_id})
        logger.info(f"삽입된 데이터 확인: {inserted}")
        
        # 모델 테스트
        try:
            from models import AIProviderConfig
            
            # from_mongo 메서드 테스트
            provider_obj = AIProviderConfig.from_mongo(inserted)
            logger.info(f"AIProviderConfig 객체 생성 성공: {provider_obj.provider_name}")
            
        except Exception as e:
            logger.error(f"모델 관련 오류: {e}")
            import traceback
            traceback.print_exc()
        
        # 테스트 데이터 삭제
        await ai_providers_collection.delete_one({"_id": result.inserted_id})
        logger.info("테스트 데이터 삭제 완료")
        
    except Exception as e:
        logger.error(f"MongoDB 테스트 중 오류: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    asyncio.run(test_mongodb_connection())