#!/usr/bin/env python3

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
import sys
import os

# Add the backend directory to the path
sys.path.append('/app')

# MongoDB 설정
MONGODB_URL = "mongodb://admin:password123@mongodb:27017/online_evaluation_db?authSource=admin"
DATABASE_NAME = "online_evaluation_db"

async def test_server_login():
    try:
        # Import server's functions
        from security import verify_password
        print("✅ security.verify_password imported successfully")
        
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client[DATABASE_NAME]
        
        # 로그인 시뮬레이션 (서버와 동일한 로직)
        username = "admin"
        password = "admin123"
        
        print(f"🔍 서버 로그인 로직 테스트: username='{username}', password='{password}'")
        
        # 서버와 정확히 동일한 쿼리
        user_data = await db.users.find_one({"login_id": username})
        print(f"📄 사용자 데이터: {user_data is not None}")
        
        if user_data:
            print(f"   - login_id: {user_data.get('login_id')}")
            print(f"   - role: {user_data.get('role')}")
            print(f"   - is_active: {user_data.get('is_active')}")
            print(f"   - password_hash exists: {bool(user_data.get('password_hash'))}")
            
            # 서버와 동일한 검증
            password_hash = user_data.get("password_hash")
            if password_hash:
                print(f"🔐 비밀번호 해시: {password_hash[:30]}...")
                is_valid = verify_password(password, password_hash)
                print(f"✅ verify_password 결과: {is_valid}")
            else:
                print("❌ password_hash 필드가 없습니다!")
        else:
            print("❌ 사용자를 찾을 수 없습니다")
        
        client.close()
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_server_login())