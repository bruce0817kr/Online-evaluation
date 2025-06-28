#!/usr/bin/env python3
"""
로그인 시스템 핫픽스 스크립트
기존 로그인 함수를 간단하고 안정적인 버전으로 교체
"""

import os
import asyncio
import bcrypt
from motor.motor_asyncio import AsyncIOMotorClient

async def create_working_admin():
    """완전히 새로운 관리자 계정 생성"""
    
    print("🔧 로그인 시스템 핫픽스 시작")
    
    # MongoDB 연결
    client = AsyncIOMotorClient('mongodb://admin:password123@mongodb:27017/online_evaluation?authSource=admin')
    db = client.online_evaluation
    
    # 1. 기존 admin 사용자 삭제
    result = await db.users.delete_many({"login_id": "admin"})
    print(f"기존 admin 사용자 삭제: {result.deleted_count}개")
    
    # 2. 새로운 bcrypt 해시 생성
    password = "admin123!"
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    print(f"새 비밀번호 해시 생성: {password_hash[:20]}...")
    
    # 3. 완전히 새로운 관리자 계정 생성
    from datetime import datetime
    from bson import ObjectId
    
    admin_user = {
        "_id": ObjectId(),
        "id": "admin_001",
        "login_id": "admin",
        "password_hash": password_hash,
        "user_name": "시스템 관리자",
        "email": "admin@system.local",
        "phone": "010-0000-0000",
        "role": "admin",
        "created_at": datetime.utcnow(),
        "is_active": True,
        "last_login": datetime.utcnow()
    }
    
    result = await db.users.insert_one(admin_user)
    print(f"새 관리자 계정 생성: {result.inserted_id}")
    
    # 4. 직접 검증
    stored_user = await db.users.find_one({"login_id": "admin"})
    if stored_user:
        # bcrypt 검증
        test_result = bcrypt.checkpw(password.encode('utf-8'), stored_user["password_hash"].encode('utf-8'))
        print(f"비밀번호 검증 테스트: {test_result}")
        
        print("✅ 로그인 핫픽스 완료!")
        print(f"로그인 정보: username=admin, password={password}")
    else:
        print("❌ 사용자 생성 실패")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(create_working_admin())