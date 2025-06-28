#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
테스트 사용자 계정 동기화 스크립트
테스트에서 기대하는 정확한 계정을 생성합니다.
"""

import asyncio
import uuid
import os
from datetime import datetime
from passlib.context import CryptContext
from motor.motor_asyncio import AsyncIOMotorClient

# 비밀번호 해시 컨텍스트 (백엔드와 동일한 설정)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

def get_password_hash(password):
    """비밀번호를 해시화합니다."""
    return pwd_context.hash(password)

# 테스트에서 기대하는 정확한 사용자 계정들
EXPECTED_TEST_USERS = [
    {
        "id": str(uuid.uuid4()),
        "login_id": "admin",
        "password": "admin123",
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
        "login_id": "secretary",  # 테스트에서 기대하는 정확한 계정명
        "password": "secretary123",
        "user_name": "간사",
        "email": "secretary@evaluation.com", 
        "phone": "010-2345-6789",
        "role": "secretary",
        "created_at": datetime.utcnow(),
        "is_active": True,
        "last_login": None
    },
    {
        "id": str(uuid.uuid4()),
        "login_id": "evaluator",  # 일부 테스트에서 기대하는 계정명
        "password": "evaluator123",
        "user_name": "평가위원",
        "email": "evaluator@evaluation.com",
        "phone": "010-4567-8901",
        "role": "evaluator", 
        "created_at": datetime.utcnow(),
        "is_active": True,
        "last_login": None
    },
    {
        "id": str(uuid.uuid4()),
        "login_id": "evaluator01",  # 다른 테스트에서 기대하는 계정명
        "password": "evaluator123", 
        "user_name": "평가위원01",
        "email": "evaluator01@evaluation.com",
        "phone": "010-5678-9012",
        "role": "evaluator",
        "created_at": datetime.utcnow(),
        "is_active": True,
        "last_login": None
    }
]

async def get_mongo_connection():
    """MongoDB 연결을 설정합니다."""
    # Production 환경 연결 시도 (현재 실행 중인 컨테이너)
    mongo_urls = [
        # Production 환경 (포트 27036)
        'mongodb://admin:password123@localhost:27036/online_evaluation_db?authSource=admin',
        # Development 환경 (포트 27018)
        'mongodb://admin:password123@localhost:27018/online_evaluation_db?authSource=admin',
        # 기본 포트
        'mongodb://admin:password123@localhost:27017/online_evaluation_db?authSource=admin',
        # 환경변수
        os.getenv('MONGO_URL', 'mongodb://localhost:27017/online_evaluation_db')
    ]
    
    for mongo_url in mongo_urls:
        try:
            print(f"📡 MongoDB 연결 시도: {mongo_url}")
            client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=5000)
            await client.admin.command('ping')
            
            # 데이터베이스 확인
            db_name = 'online_evaluation_db'
            if 'online_evaluation' in mongo_url and 'online_evaluation_db' not in mongo_url:
                db_name = 'online_evaluation'
            
            db = client[db_name]
            print(f"✅ MongoDB 연결 성공: {mongo_url} (DB: {db_name})")
            return client, db
        except Exception as e:
            print(f"❌ 연결 실패: {e}")
            if 'client' in locals():
                client.close()
    
    return None, None

async def fix_test_users():
    """테스트에서 기대하는 사용자 계정을 생성/수정합니다."""
    
    print("🔧 테스트 사용자 계정 동기화 시작...")
    print("=" * 60)
    
    client, db = await get_mongo_connection()
    
    if client is None or db is None:
        print("❌ MongoDB에 연결할 수 없습니다.")
        return False
    
    try:
        # 기존 사용자 현황 파악
        print("📊 현재 사용자 현황:")
        existing_count = await db.users.count_documents({})
        print(f"   총 사용자 수: {existing_count}명")
        
        if existing_count > 0:
            existing_users = await db.users.find({}, {"login_id": 1, "user_name": 1, "role": 1, "is_active": 1}).to_list(100)
            for user in existing_users:
                status = "활성" if user.get('is_active', False) else "비활성"
                print(f"   - {user.get('login_id', 'unknown')} ({user.get('user_name', 'unknown')}) - {user.get('role', 'unknown')} - {status}")
        
        print("\n🔄 테스트 계정 동기화 중...")
        
        created_count = 0
        updated_count = 0
        
        for user_data in EXPECTED_TEST_USERS:
            try:
                login_id = user_data["login_id"]
                
                # 기존 사용자 확인
                existing_user = await db.users.find_one({"login_id": login_id})
                
                if existing_user:
                    # 기존 사용자가 있으면 비밀번호와 활성 상태만 업데이트
                    password_hash = get_password_hash(user_data["password"])
                    
                    await db.users.update_one(
                        {"login_id": login_id},
                        {
                            "$set": {
                                "password_hash": password_hash,
                                "is_active": True,
                                "user_name": user_data["user_name"],
                                "email": user_data["email"],
                                "phone": user_data["phone"],
                                "role": user_data["role"]
                            }
                        }
                    )
                    updated_count += 1
                    print(f"🔄 업데이트: {login_id} ({user_data['user_name']}) - {user_data['role']}")
                    
                else:
                    # 새 사용자 생성
                    password_hash = get_password_hash(user_data["password"])
                    
                    user_doc = user_data.copy()
                    del user_doc["password"]
                    user_doc["password_hash"] = password_hash
                    
                    result = await db.users.insert_one(user_doc)
                    
                    if result.inserted_id:
                        created_count += 1
                        print(f"✅ 생성: {login_id} ({user_data['user_name']}) - {user_data['role']}")
                    else:
                        print(f"❌ 생성 실패: {login_id}")
                        
            except Exception as e:
                print(f"❌ 계정 '{user_data['login_id']}' 처리 중 오류: {e}")
        
        # 최종 결과 출력
        print("\n" + "=" * 60)
        print("📋 동기화 완료 결과")
        print("=" * 60)
        print(f"🆕 생성된 계정: {created_count}개")
        print(f"🔄 업데이트된 계정: {updated_count}개")
        
        # 최종 확인
        print("\n🧪 테스트 계정 검증:")
        test_credentials = [
            {"login_id": "admin", "password": "admin123"},
            {"login_id": "secretary", "password": "secretary123"},
            {"login_id": "evaluator", "password": "evaluator123"},
            {"login_id": "evaluator01", "password": "evaluator123"}
        ]
        
        all_verified = True
        for cred in test_credentials:
            user = await db.users.find_one({"login_id": cred["login_id"]})
            if user and user.get("is_active", False):
                print(f"✅ {cred['login_id']} - 활성 상태")
            else:
                print(f"❌ {cred['login_id']} - 없음 또는 비활성")
                all_verified = False
        
        if all_verified:
            print("\n🎉 모든 테스트 계정이 준비되었습니다!")
            print("\n📝 테스트 가능한 계정:")
            print("   - admin / admin123 (관리자)")
            print("   - secretary / secretary123 (간사)")
            print("   - evaluator / evaluator123 (평가위원)")
            print("   - evaluator01 / evaluator123 (평가위원01)")
        
        return all_verified
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        client.close()
        print("\n🔒 MongoDB 연결 종료")

async def main():
    """메인 실행 함수"""
    print("🚀 테스트 사용자 계정 동기화")
    print("🎯 목표: 테스트에서 기대하는 정확한 계정 생성")
    print("=" * 60)
    
    success = await fix_test_users()
    
    if success:
        print("\n✨ 테스트 계정 동기화가 성공적으로 완료되었습니다!")
        print("🧪 이제 모든 E2E 테스트가 정상적으로 실행될 것입니다.")
    else:
        print("\n⚠️ 일부 계정에 문제가 있을 수 있습니다.")

if __name__ == "__main__":
    asyncio.run(main())