#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
온라인 평가 시스템 테스트 사용자 생성 스크립트
admin, secretary, evaluator 역할의 사용자들을 생성합니다.
"""

import asyncio
import uuid
from datetime import datetime
from passlib.context import CryptContext
from motor.motor_asyncio import AsyncIOMotorClient
import json

# 비밀번호 해시 컨텍스트 (백엔드와 동일한 설정)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    """비밀번호를 해시화합니다."""
    return pwd_context.hash(password)

def generate_user_id():
    """UUID 기반 사용자 ID 생성"""
    return str(uuid.uuid4())

# 테스트 사용자 데이터 정의
TEST_USERS = [
    # 관리자 계정
    {
        "id": generate_user_id(),
        "login_id": "admin",
        "password": "admin123",  # 실제 저장 시 해시화됨
        "user_name": "시스템 관리자",
        "email": "admin@evaluation.com",
        "phone": "010-1234-5678",
        "role": "admin",
        "created_at": datetime.utcnow(),
        "is_active": True,
        "last_login": None
    },
    # 비서 계정 1
    {
        "id": generate_user_id(),
        "login_id": "secretary01",
        "password": "secretary123",
        "user_name": "김비서",
        "email": "secretary1@evaluation.com", 
        "phone": "010-2345-6789",
        "role": "secretary",
        "created_at": datetime.utcnow(),
        "is_active": True,
        "last_login": None
    },
    # 비서 계정 2
    {
        "id": generate_user_id(),
        "login_id": "secretary02", 
        "password": "secretary123",
        "user_name": "이비서",
        "email": "secretary2@evaluation.com",
        "phone": "010-3456-7890",
        "role": "secretary",
        "created_at": datetime.utcnow(),
        "is_active": True,
        "last_login": None
    },
    # 평가자 계정들
    {
        "id": generate_user_id(),
        "login_id": "evaluator01",
        "password": "evaluator123",
        "user_name": "박평가",
        "email": "evaluator1@evaluation.com",
        "phone": "010-4567-8901",
        "role": "evaluator", 
        "created_at": datetime.utcnow(),
        "is_active": True,
        "last_login": None
    },
    {
        "id": generate_user_id(),
        "login_id": "evaluator02",
        "password": "evaluator123", 
        "user_name": "최평가",
        "email": "evaluator2@evaluation.com",
        "phone": "010-5678-9012",
        "role": "evaluator",
        "created_at": datetime.utcnow(),
        "is_active": True,
        "last_login": None
    },
    {
        "id": generate_user_id(),
        "login_id": "evaluator03",
        "password": "evaluator123",
        "user_name": "정평가", 
        "email": "evaluator3@evaluation.com",
        "phone": "010-6789-0123",
        "role": "evaluator",
        "created_at": datetime.utcnow(),
        "is_active": True,
        "last_login": None
    },
    {
        "id": generate_user_id(),
        "login_id": "evaluator04",
        "password": "evaluator123",
        "user_name": "강평가",
        "email": "evaluator4@evaluation.com", 
        "phone": "010-7890-1234",
        "role": "evaluator",
        "created_at": datetime.utcnow(),
        "is_active": True,
        "last_login": None
    },
    {
        "id": generate_user_id(),
        "login_id": "evaluator05",
        "password": "evaluator123",
        "user_name": "신평가",
        "email": "evaluator5@evaluation.com",
        "phone": "010-8901-2345",
        "role": "evaluator",
        "created_at": datetime.utcnow(),
        "is_active": True,
        "last_login": None
    }
]

async def create_test_users():
    """테스트 사용자들을 MongoDB에 생성합니다."""
    
    print("🔧 테스트 사용자 생성 시작...")
      # MongoDB 연결 (Docker compose에서 설정한 인증 정보 사용)
    mongo_url = 'mongodb://admin:password123@localhost:27017/online_evaluation?authSource=admin'
    client = AsyncIOMotorClient(mongo_url)
    db = client['online_evaluation']
    
    try:
        # 데이터베이스 연결 확인
        await client.admin.command('ping')
        print("✅ MongoDB 연결 성공")
        
        # 기존 사용자 수 확인
        existing_count = await db.users.count_documents({})
        print(f"📊 기존 사용자 수: {existing_count}명")
        
        created_users = []
        
        for user_data in TEST_USERS:
            # 중복 검사 (login_id 기준)
            existing_user = await db.users.find_one({"login_id": user_data["login_id"]})
            
            if existing_user:
                print(f"⚠️  사용자 '{user_data['login_id']}'는 이미 존재합니다. 건너뛰기...")
                continue
            
            # 비밀번호 해시화
            password_hash = get_password_hash(user_data["password"])
            
            # 사용자 문서 생성 (password 제거, password_hash 추가)
            user_doc = user_data.copy()
            del user_doc["password"]
            user_doc["password_hash"] = password_hash
            
            # MongoDB에 삽입
            result = await db.users.insert_one(user_doc)
            
            if result.inserted_id:
                created_users.append({
                    "login_id": user_data["login_id"],
                    "user_name": user_data["user_name"],
                    "role": user_data["role"],
                    "password": user_data["password"]  # 로그인 테스트용
                })
                print(f"✅ 사용자 생성: {user_data['login_id']} ({user_data['user_name']}) - {user_data['role']}")
            else:
                print(f"❌ 사용자 생성 실패: {user_data['login_id']}")
        
        # 최종 사용자 수 확인
        final_count = await db.users.count_documents({})
        print(f"\n📊 최종 사용자 수: {final_count}명")
        print(f"🆕 생성된 사용자 수: {len(created_users)}명")
        
        # 생성된 사용자 정보를 JSON 파일로 저장 (테스트용)
        if created_users:
            with open('test_users_credentials.json', 'w', encoding='utf-8') as f:
                json.dump(created_users, f, ensure_ascii=False, indent=2)
            print("💾 테스트 사용자 정보가 'test_users_credentials.json'에 저장되었습니다.")
        
        # 역할별 사용자 수 확인
        print("\n📋 역할별 사용자 현황:")
        roles = ['admin', 'secretary', 'evaluator']
        for role in roles:
            count = await db.users.count_documents({"role": role})
            print(f"  - {role}: {count}명")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 연결 종료
        client.close()
        print("\n🔒 MongoDB 연결 종료")

if __name__ == "__main__":
    asyncio.run(create_test_users())
