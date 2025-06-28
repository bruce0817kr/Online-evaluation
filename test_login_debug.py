#!/usr/bin/env python3

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext

# MongoDB 설정
MONGODB_URL = "mongodb://admin:password123@mongodb:27017/online_evaluation_db?authSource=admin"
DATABASE_NAME = "online_evaluation_db"

# Password context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def test_login():
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    
    # 로그인 시도 시뮬레이션
    username = "admin"
    password = "admin123"
    
    print(f"로그인 시도: username='{username}', password='{password}'")
    
    # 서버에서 하는 것과 동일한 쿼리
    user_data = await db.users.find_one({"login_id": username})
    print(f"login_id로 찾기 결과: {user_data}")
    
    if not user_data:
        print("사용자를 찾을 수 없습니다. 다른 필드로 시도...")
        user_data = await db.users.find_one({"username": username})
        print(f"username으로 찾기 결과: {user_data}")
    
    if user_data:
        print(f"사용자 발견:")
        print(f"  - _id: {user_data.get('_id')}")
        print(f"  - username: {user_data.get('username')}")
        print(f"  - login_id: {user_data.get('login_id')}")
        print(f"  - password_hash: {user_data.get('password_hash')}")
        print(f"  - hashed_password: {user_data.get('hashed_password')}")
        
        # 비밀번호 검증
        password_hash = user_data.get("password_hash") or user_data.get("hashed_password")
        if password_hash:
            is_valid = pwd_context.verify(password, password_hash)
            print(f"비밀번호 검증 결과: {is_valid}")
        else:
            print("비밀번호 해시가 없습니다!")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(test_login())