#!/usr/bin/env python3
"""
사용자 목록 확인 스크립트
데이터베이스에 있는 실제 사용자들을 확인합니다.
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def check_users():
    """데이터베이스에 있는 사용자들 확인"""
    # MongoDB 연결
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://admin:password123@localhost:27017/evaluation_db?authSource=admin')
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ.get('DB_NAME', 'evaluation_db')]
    
    try:
        print("🔍 데이터베이스 사용자 확인...")
        print("=" * 50)
        
        # 모든 사용자 조회
        users = await db.users.find({}).to_list(length=None)
        
        if not users:
            print("❌ 데이터베이스에 사용자가 없습니다!")
            return
        
        print(f"📊 총 사용자 수: {len(users)}")
        print("\n👥 사용자 목록:")
        print("-" * 70)
        
        for i, user in enumerate(users, 1):
            print(f"{i}. 로그인 ID: {user.get('login_id', 'N/A')}")
            print(f"   이름: {user.get('user_name', 'N/A')}")
            print(f"   역할: {user.get('role', 'N/A')}")
            print(f"   이메일: {user.get('email', 'N/A')}")
            print(f"   활성: {user.get('is_active', 'N/A')}")
            print(f"   비밀번호 해시: {user.get('password_hash', 'N/A')[:20]}...")
            print("-" * 70)
        
        print("\n✅ 사용자 확인 완료!")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(check_users())
