#!/usr/bin/env python3
"""
데이터베이스 연결 테스트 스크립트
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def test_connection():
    """데이터베이스 연결 테스트"""
    
    mongo_url = os.getenv("MONGO_URL", "mongodb://admin:password123@mongodb-prod:27017/online_evaluation_prod?authSource=admin")
    print(f"MongoDB URL: {mongo_url}")
    
    try:
        client = AsyncIOMotorClient(mongo_url)
        
        # 데이터베이스 선택
        if "online_evaluation_prod" in mongo_url:
            db_name = "online_evaluation_prod"
        else:
            db_name = "online_evaluation"
            
        db = client[db_name]
        print(f"사용 중인 데이터베이스: {db_name}")
        
        # 연결 테스트
        await client.admin.command('ping')
        print("✅ MongoDB 연결 성공")
        
        # 사용자 컬렉션 조회
        users_count = await db.users.count_documents({})
        print(f"사용자 수: {users_count}")
        
        # admin 사용자 조회
        admin_user = await db.users.find_one({"login_id": "admin"})
        if admin_user:
            print("✅ admin 사용자 존재함")
            print(f"  - ID: {admin_user['_id']}")
            print(f"  - 이름: {admin_user['name']}")
            print(f"  - 역할: {admin_user['role']}")
            print(f"  - 활성화: {admin_user['is_active']}")
        else:
            print("❌ admin 사용자 없음")
            
        # 모든 데이터베이스 목록
        db_list = await client.list_database_names()
        print(f"사용 가능한 데이터베이스: {db_list}")
            
    except Exception as e:
        print(f"❌ 연결 오류: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(test_connection())