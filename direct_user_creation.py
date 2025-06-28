#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MongoDB에 직접 사용자 생성 - 최종 해결책
"""

import asyncio
import uuid
from datetime import datetime
from passlib.context import CryptContext
from motor.motor_asyncio import AsyncIOMotorClient
import json

# 비밀번호 해시 컨텍스트
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

def get_password_hash(password):
    return pwd_context.hash(password)

async def create_users_directly():
    """MongoDB에 직접 사용자 생성"""
    
    # MongoDB 연결 - 다양한 주소 시도
    mongo_urls = [
        "mongodb://localhost:27017/online_evaluation",
        "mongodb://admin:password123@localhost:27017/online_evaluation?authSource=admin",
        "mongodb://host.docker.internal:27017/online_evaluation",
        "mongodb://online-evaluation-mongodb:27017/online_evaluation",
        "mongodb://admin:password123@online-evaluation-mongodb:27017/online_evaluation?authSource=admin"
    ]
    
    client = None
    db = None
    
    for mongo_url in mongo_urls:
        try:
            print(f"📡 MongoDB 연결 시도: {mongo_url}")
            client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=5000)
            await client.admin.command('ping')
            db = client['online_evaluation']
            print(f"✅ MongoDB 연결 성공: {mongo_url}")
            break
        except Exception as e:
            print(f"❌ 연결 실패: {e}")
            if client:
                client.close()
            client = None
    
    if not client or not db:
        print("❌ MongoDB에 연결할 수 없습니다.")
        return False
    
    try:
        
        # 테스트 사용자 데이터 (기존 삭제 후 재생성)
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
        
        print("\n🗑️  기존 사용자 데이터 정리...")
        # 기존 사용자 모두 삭제 (깨끗한 상태로 시작)
        deleted = await db.users.delete_many({})
        print(f"삭제된 기존 사용자: {deleted.deleted_count}개")
        
        print("\n👥 새 사용자 생성...")
        created_count = 0
        
        # 새 사용자 생성
        for user in users:
            try:
                result = await db.users.insert_one(user)
                if result.inserted_id:
                    created_count += 1
                    print(f"✅ 사용자 생성: {user['login_id']} ({user['role']})")
                else:
                    print(f"❌ 사용자 생성 실패: {user['login_id']}")
            except Exception as e:
                print(f"❌ 사용자 생성 오류 {user['login_id']}: {e}")
        
        # 결과 확인
        print(f"\n📊 생성 결과:")
        print(f"  - 생성된 사용자 수: {created_count}개")
        
        # 데이터베이스 상태 확인
        total_users = await db.users.count_documents({})
        print(f"  - 총 사용자 수: {total_users}개")
        
        # 역할별 확인
        for role in ['admin', 'secretary', 'evaluator']:
            count = await db.users.count_documents({"role": role})
            print(f"  - {role}: {count}명")
        
        # 모든 사용자 목록 출력
        print("\n👥 생성된 사용자 목록:")
        all_users = await db.users.find({}).to_list(100)
        for user in all_users:
            login_id = user.get('login_id')
            role = user.get('role')
            user_name = user.get('user_name')
            is_active = user.get('is_active', False)
            print(f"  - {login_id} ({user_name}) - {role} - {'활성' if is_active else '비활성'}")
        
        print("\n✅ 사용자 생성 완료!")
        
        # 테스트 계정 정보 저장
        test_accounts = [
            {"login_id": "admin", "password": "admin123", "role": "admin"},
            {"login_id": "secretary01", "password": "secretary123", "role": "secretary"},
            {"login_id": "evaluator01", "password": "evaluator123", "role": "evaluator"}
        ]
        
        with open('/tmp/final_test_accounts.json', 'w', encoding='utf-8') as f:
            json.dump(test_accounts, f, ensure_ascii=False, indent=2)
        
        print("💾 최종 테스트 계정 정보 저장: /tmp/final_test_accounts.json")
        return True
        
    except Exception as e:
        print(f"❌ 오류: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        client.close()

if __name__ == "__main__":
    print("🚀 MongoDB 직접 사용자 생성 시작")
    print("=" * 60)
    success = asyncio.run(create_users_directly())
    
    if success:
        print("\n🎉 사용자 생성 완료! 이제 API 테스트를 진행하세요.")
        print("\n🧪 테스트 계정:")
        print("  - admin / admin123 (관리자)")
        print("  - secretary01 / secretary123 (비서)")
        print("  - evaluator01 / evaluator123 (평가자)")
    else:
        print("\n❌ 사용자 생성에 실패했습니다.")