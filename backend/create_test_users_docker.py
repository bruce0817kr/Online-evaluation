#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Docker 환경용 테스트 사용자 생성 스크립트
"""

import asyncio
import uuid
import os
from datetime import datetime
from passlib.context import CryptContext
from motor.motor_asyncio import AsyncIOMotorClient
import json

# 비밀번호 해시 컨텍스트 (백엔드와 동일한 설정)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

def get_password_hash(password):
    """비밀번호를 해시화합니다."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호를 검증합니다."""
    return pwd_context.verify(plain_password, hashed_password)

def generate_user_id():
    """UUID 기반 사용자 ID 생성"""
    return str(uuid.uuid4())

# 테스트 사용자 데이터 정의
TEST_USERS = [
    # 관리자 계정
    {
        "id": generate_user_id(),
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
    # 비서 계정들
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
    }
]

async def get_mongo_connection():
    """MongoDB 연결을 설정합니다."""
    mongo_url = os.getenv('MONGO_URL')
    if not mongo_url:
        print("❌ MONGO_URL 환경 변수가 설정되지 않았습니다.")
        return None, None

    try:
        print(f"📡 MongoDB 연결 시도: {mongo_url}")
        client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=5000)
        await client.admin.command('ping')
        # The database name is part of the MONGO_URL, but we can also specify it here
        db = client.get_default_database()
        if db is None:
            # Fallback to parsing from URL if not default
            from urllib.parse import urlparse
            db_name = urlparse(mongo_url).path.lstrip('/')
            db = client[db_name]
        print(f"✅ MongoDB 연결 성공: {mongo_url}")
        return client, db
    except Exception as e:
        print(f"❌ 연결 실패: {e}")
        return None, None

async def create_test_users():
    """테스트 사용자들을 MongoDB에 생성합니다."""
    
    print("🔧 테스트 사용자 생성 시작...")
    
    client, db = await get_mongo_connection()
    
    if client is None or db is None:
        print("❌ MongoDB에 연결할 수 없습니다.")
        return False
    
    try:
        # 기존 사용자 수 확인
        existing_count = await db.users.count_documents({})
        print(f"📊 기존 사용자 수: {existing_count}명")
        
        # 기존 사용자 확인
        if existing_count > 0:
            existing_users = await db.users.find({}).to_list(100)
            print("\n👥 기존 사용자 목록:")
            for user in existing_users:
                login_id = user.get('login_id', 'unknown')
                user_name = user.get('user_name', 'unknown')
                role = user.get('role', 'unknown')
                is_active = user.get('is_active', False)
                print(f"   - {login_id} ({user_name}) - {role} - {'활성' if is_active else '비활성'}")
        
        created_users = []
        updated_users = []
        
        for user_data in TEST_USERS:
            try:
                # 중복 검사 (login_id 기준)
                existing_user = await db.users.find_one({"login_id": user_data["login_id"]})
                
                if existing_user:
                    print(f"⚠️  사용자 '{user_data['login_id']}'는 이미 존재합니다.")
                    
                    # 비밀번호 검증
                    stored_hash = existing_user.get('password_hash')
                    if stored_hash and verify_password(user_data['password'], stored_hash):
                        print(f"✅ 사용자 '{user_data['login_id']}' 비밀번호 검증 성공")
                    else:
                        # 비밀번호 업데이트
                        new_hash = get_password_hash(user_data['password'])
                        await db.users.update_one(
                            {"login_id": user_data["login_id"]},
                            {
                                "$set": {
                                    "password_hash": new_hash,
                                    "is_active": True
                                }
                            }
                        )
                        updated_users.append(user_data["login_id"])
                        print(f"🔄 사용자 '{user_data['login_id']}' 비밀번호 및 상태 업데이트 완료")
                    
                    continue
                
                # 비밀번호 해시화
                password_hash = get_password_hash(user_data["password"])
                
                # 사용자 문서 생성 (password 제거, password_hash 추가)
                user_doc = user_data.copy()
                del user_doc["password"]
                user_doc["password_hash"] = password_hash
                # 'id' 필드를 'user_id'로 변경
                if 'id' in user_doc:
                    user_doc['user_id'] = user_doc.pop('id')
                
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
                    
            except Exception as e:
                print(f"❌ 사용자 '{user_data['login_id']}' 처리 중 오류: {e}")
                import traceback
                traceback.print_exc()
        
        # 최종 사용자 수 확인
        final_count = await db.users.count_documents({})
        print(f"\n📊 최종 사용자 수: {final_count}명")
        print(f"🆕 생성된 사용자 수: {len(created_users)}명")
        print(f"🔄 업데이트된 사용자 수: {len(updated_users)}명")
        
        # 역할별 사용자 수 확인
        print("\n📋 역할별 사용자 현황:")
        roles = ['admin', 'secretary', 'evaluator']
        for role in roles:
            count = await db.users.count_documents({"role": role, "is_active": True})
            print(f"  - {role}: {count}명")
        
        # 생성된 사용자 정보를 JSON 파일로 저장 (테스트용)
        if created_users or updated_users:
            all_test_users = []
            for user_data in TEST_USERS:
                all_test_users.append({
                    "login_id": user_data["login_id"],
                    "password": user_data["password"],
                    "user_name": user_data["user_name"],
                    "role": user_data["role"]
                })
            
            with open('/app/test_users_credentials.json', 'w', encoding='utf-8') as f:
                json.dump(all_test_users, f, ensure_ascii=False, indent=2)
            print("💾 테스트 사용자 정보가 '/app/test_users_credentials.json'에 저장되었습니다.")
        
        return True
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # 연결 종료
        client.close()
        print("\n🔒 MongoDB 연결 종료")

async def test_user_passwords():
    """생성된 사용자들의 비밀번호를 테스트합니다."""
    print("\n🧪 사용자 비밀번호 검증...")
    
    client, db = await get_mongo_connection()
    
    if client is None or db is None:
        print("❌ MongoDB에 연결할 수 없습니다.")
        return False
    
    try:
        test_credentials = [
            {"login_id": "admin", "password": "admin123"},
            {"login_id": "secretary01", "password": "secretary123"},
            {"login_id": "evaluator01", "password": "evaluator123"}
        ]
        
        all_passed = True
        
        for cred in test_credentials:
            try:
                user = await db.users.find_one({"login_id": cred["login_id"]})
                
                if not user:
                    print(f"❌ 사용자 '{cred['login_id']}'를 찾을 수 없습니다.")
                    all_passed = False
                    continue
                
                stored_hash = user.get('password_hash')
                if not stored_hash:
                    print(f"❌ 사용자 '{cred['login_id']}'의 비밀번호 해시가 없습니다.")
                    all_passed = False
                    continue
                
                if verify_password(cred['password'], stored_hash):
                    print(f"✅ 비밀번호 검증 성공: {cred['login_id']} ({user.get('role')})")
                else:
                    print(f"❌ 비밀번호 검증 실패: {cred['login_id']}")
                    all_passed = False
                    
            except Exception as e:
                print(f"❌ 비밀번호 검증 오류 ({cred['login_id']}): {e}")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ 비밀번호 테스트 오류: {e}")
        return False
    
    finally:
        client.close()

async def main():
    """메인 실행 함수"""
    print("🚀 Docker 환경용 테스트 사용자 생성 시작")
    print("=" * 60)
    
    # 환경 정보 출력
    mongo_url = os.getenv('MONGO_URL', 'not set')
    print(f"🔧 MONGO_URL 환경변수: {mongo_url}")
    
    # 1. 테스트 사용자 생성
    success = await create_test_users()
    
    if success:
        # 2. 비밀번호 검증 테스트
        password_test_success = await test_user_passwords()
        
        print("\n" + "=" * 60)
        print("📋 최종 결과")
        print("=" * 60)
        
        if password_test_success:
            print("🎉 모든 테스트 사용자가 성공적으로 생성되고 검증되었습니다!")
            print("\n🧪 테스트 계정:")
            print("  - admin / admin123 (관리자)")
            print("  - secretary01 / secretary123 (비서)")
            print("  - evaluator01 / evaluator123 (평가자)")
        else:
            print("⚠️  사용자는 생성되었지만 비밀번호 검증에 문제가 있습니다.")
    else:
        print("\n❌ 사용자 생성에 실패했습니다.")

if __name__ == "__main__":
    asyncio.run(main())