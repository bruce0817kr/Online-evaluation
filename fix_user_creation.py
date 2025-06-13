#!/usr/bin/env python3
"""
온라인 평가 시스템 - 사용자 데이터 수정 스크립트 (password_hash 필드 맞춤)
"""

import asyncio
import os
import uuid
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from datetime import datetime

# 비밀번호 해싱 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def fix_users():
    """사용자 데이터 수정 - password_hash 필드로 통일"""
      # MongoDB 연결
    mongo_url = "mongodb://app_user:app_password123@localhost:27017/online_evaluation?authSource=online_evaluation"
    client = AsyncIOMotorClient(mongo_url)
    db = client.online_evaluation
    
    try:
        # 기존 사용자 삭제
        await db.users.delete_many({})
        print("🗑️ 기존 사용자 데이터 삭제 완료")
        
        # 테스트 사용자들 (백엔드 스키마에 맞춤)
        test_users = [
            {
                "id": str(uuid.uuid4()),
                "login_id": "admin",
                "user_name": "관리자",
                "password": "admin123",
                "role": "admin",
                "email": "admin@example.com",
                "phone": "010-1111-2222",
                "created_at": datetime.utcnow(),
                "is_active": True
            },
            {
                "id": str(uuid.uuid4()),
                "login_id": "secretary01",
                "user_name": "간사01",
                "password": "secretary123",
                "role": "secretary",
                "email": "secretary01@example.com",
                "phone": "010-2222-3333",
                "created_at": datetime.utcnow(),
                "is_active": True
            },
            {
                "id": str(uuid.uuid4()),
                "login_id": "evaluator01",
                "user_name": "평가위원01",
                "password": "evaluator123",
                "role": "evaluator",
                "email": "evaluator01@example.com",
                "phone": "010-3333-4444",
                "created_at": datetime.utcnow(),
                "is_active": True
            }
        ]
        
        # 사용자 생성
        for user_data in test_users:
            # 비밀번호 해시화 (올바른 필드명으로)
            password_hash = pwd_context.hash(user_data["password"])
            user_data["password_hash"] = password_hash
            del user_data["password"]  # 평문 비밀번호 제거
              # 데이터베이스에 삽입
            await db.users.insert_one(user_data)
            print(f"✅ 사용자 생성 완료: {user_data['login_id']} ({user_data['user_name']}) - {user_data['role']}")
        
        # 생성된 사용자 확인
        total_users = await db.users.count_documents({})
        print(f"\n📊 총 사용자 수: {total_users}")
        
        # 데이터 검증
        print("\n🔍 데이터 검증:")
        users = await db.users.find({}).to_list(None)
        for user in users:
            print(f"- {user['login_id']}: password_hash 존재 = {'password_hash' in user}")
        
        print("\n🎉 사용자 데이터 수정 완료!")
        print("\n📋 로그인 정보:")
        print("- 관리자: admin / admin123")
        print("- 간사: secretary01 / secretary123") 
        print("- 평가위원: evaluator01 / evaluator123")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(fix_users())
