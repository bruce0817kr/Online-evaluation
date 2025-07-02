"""AI Provider 최소 테스트 - 실제 오류 재현"""

import asyncio
import os
import sys
from datetime import datetime

# 환경 설정
os.environ['MONGO_URL'] = 'mongodb://localhost:27017/online_evaluation'
os.environ['DB_NAME'] = 'online_evaluation'
os.environ['AI_CONFIG_ENCRYPTION_KEY'] = 'pRmNGW_K1H1TGTgC_-VNyAQXDJtHgqq4lA8cXYz1FCE='

async def test_ai_provider_error():
    """AI Provider 생성 시 실제 오류 재현"""
    
    print("테스트 시작...")
    
    try:
        # MongoDB 연결
        from motor.motor_asyncio import AsyncIOMotorClient
        client = AsyncIOMotorClient(os.environ['MONGO_URL'])
        db = client[os.environ['DB_NAME']]
        
        # Ping 테스트
        result = await client.admin.command('ping')
        print(f"MongoDB 연결 성공: {result}")
        
        # AI Provider 모델 임포트
        from models import AIProviderConfig, AIProviderConfigCreate
        print("모델 임포트 성공")
        
        # from_mongo 메서드 테스트
        test_data = {
            "_id": "test_id",
            "provider_name": "openai",
            "display_name": "OpenAI",
            "api_key": "encrypted",
            "is_active": True,
            "priority": 1,
            "temperature": 0.7,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "created_by": "admin"
        }
        
        result = AIProviderConfig.from_mongo(test_data)
        print(f"from_mongo 테스트 성공: {result.provider_name}")
        
        # AI admin endpoints 테스트
        from ai_admin_endpoints import initialize_collections, encrypt_api_key
        
        await initialize_collections()
        print("컬렉션 초기화 성공")
        
        # 암호화 테스트
        encrypted = encrypt_api_key("test_key")
        print(f"암호화 성공: {encrypted[:20]}...")
        
        # 실제 삽입 테스트
        ai_providers_collection = db.ai_providers
        
        provider_data = {
            "provider_name": "openai",
            "display_name": "OpenAI Test",
            "api_key": encrypted,
            "is_active": True,
            "priority": 1,
            "temperature": 0.7,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "created_by": "test_admin"
        }
        
        result = await ai_providers_collection.insert_one(provider_data)
        print(f"삽입 성공! ID: {result.inserted_id}")
        
        # 조회 테스트
        found = await ai_providers_collection.find_one({"_id": result.inserted_id})
        print(f"조회 성공: {found}")
        
        # from_mongo 테스트
        provider_obj = AIProviderConfig.from_mongo(found)
        print(f"객체 변환 성공: {provider_obj.id}")
        
        # 삭제
        await ai_providers_collection.delete_one({"_id": result.inserted_id})
        print("테스트 데이터 삭제 완료")
        
    except Exception as e:
        print(f"\n오류 발생!")
        print(f"오류 타입: {type(e).__name__}")
        print(f"오류 메시지: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    asyncio.run(test_ai_provider_error())