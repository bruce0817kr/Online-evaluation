#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
간단한 사용자 생성 스크립트 - Docker 환경용
"""

import asyncio
import uuid
import os
from datetime import datetime
from passlib.context import CryptContext
from motor.motor_asyncio import AsyncIOMotorClient
import json

# 비밀번호 해시 컨텍스트
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

def get_password_hash(password):
    return pwd_context.hash(password)

async def create_users():
    """사용자 생성"""
    
    # MongoDB 연결 설정
    mongo_url = "mongodb://admin:password123@mongodb:27017/online_evaluation?authSource=admin"
    print(f"MongoDB 연결: {mongo_url}")
    
    client = AsyncIOMotorClient(mongo_url)
    db = client['online_evaluation']
    
    try:
        # 연결 테스트
        await client.admin.command('ping')
        print("✅ MongoDB 연결 성공")
        
        # 테스트 사용자 데이터
        users = [
            {
                "id": str(uuid.uuid4()),
                "login_id": "admin",
                "password_hash": get_password_hash("admin123"),
                "user_name": "시스템 관리자",
                "email": "admin@evaluation.com",
                "phone": "010-1234-5678",
                "role": "admin",
                "created_at": datetime.utcnow(),
                "is_active": True,
                "last_login": None
            },
            {
                "id": str(uuid.uuid4()),
                "login_id": "secretary01",
                "password_hash": get_password_hash("secretary123"),
                "user_name": "김비서",
                "email": "secretary1@evaluation.com",
                "phone": "010-2345-6789",
                "role": "secretary",
                "created_at": datetime.utcnow(),
                "is_active": True,
                "last_login": None
            },
            {
                "id": str(uuid.uuid4()),
                "login_id": "evaluator01",
                "password_hash": get_password_hash("evaluator123"),
                "user_name": "박평가",
                "email": "evaluator1@evaluation.com",
                "phone": "010-4567-8901",
                "role": "evaluator",
                "created_at": datetime.utcnow(),
                "is_active": True,
                "last_login": None
            }
        ]
        
        # 기존 사용자 삭제 (중복 방지)
        for user in users:
            await db.users.delete_many({"login_id": user["login_id"]})
            print(f"기존 사용자 삭제: {user['login_id']}")
        
        # 새 사용자 생성
        for user in users:
            result = await db.users.insert_one(user)
            if result.inserted_id:
                print(f"✅ 사용자 생성: {user['login_id']} ({user['role']})")
            else:
                print(f"❌ 사용자 생성 실패: {user['login_id']}")
        
        # 결과 확인
        total_users = await db.users.count_documents({})
        print(f"\n총 사용자 수: {total_users}")
        
        # 역할별 확인
        for role in ['admin', 'secretary', 'evaluator']:
            count = await db.users.count_documents({"role": role})
            print(f"{role}: {count}명")
        
        print("\n✅ 사용자 생성 완료!")
        
        # 테스트 계정 정보 저장
        test_accounts = [
            {"login_id": "admin", "password": "admin123", "role": "admin"},
            {"login_id": "secretary01", "password": "secretary123", "role": "secretary"},
            {"login_id": "evaluator01", "password": "evaluator123", "role": "evaluator"}
        ]
        
        with open('/app/test_accounts.json', 'w', encoding='utf-8') as f:
            json.dump(test_accounts, f, ensure_ascii=False, indent=2)
        
        print("💾 테스트 계정 정보 저장: /app/test_accounts.json")
        
    except Exception as e:
        print(f"❌ 오류: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(create_users())