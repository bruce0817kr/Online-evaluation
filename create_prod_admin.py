#!/usr/bin/env python3
"""
프로덕션 환경 관리자 계정 생성 스크립트
"""

import asyncio
import bcrypt
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

async def create_admin_user():
    """프로덕션 데이터베이스에 관리자 계정 생성"""
    
    # 프로덕션 MongoDB 연결 (컨테이너 내부에서는 서비스명 사용)
    client = AsyncIOMotorClient("mongodb://admin:password123@mongodb-prod:27017/online_evaluation_prod?authSource=admin")
    db = client.online_evaluation_prod
    
    try:
        # 기존 admin 사용자 확인
        existing_admin = await db.users.find_one({"login_id": "admin"})
        if existing_admin:
            print("✅ 관리자 계정이 이미 존재합니다.")
            return
        
        # 비밀번호 해시 생성
        password = "admin123"
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
        
        # 관리자 계정 데이터
        admin_user = {
            "login_id": "admin",
            "password_hash": password_hash,
            "name": "시스템 관리자",
            "email": "admin@system.com",
            "role": "admin",
            "company_id": "system",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # 관리자 계정 생성
        result = await db.users.insert_one(admin_user)
        print(f"✅ 관리자 계정 생성 완료: {result.inserted_id}")
        print(f"로그인 정보: admin / admin123")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(create_admin_user())