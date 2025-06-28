#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
사용자 계정 검증 스크립트
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext

# 비밀번호 해시 컨텍스트
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

async def verify_users():
    """사용자 계정 확인"""
    
    # 다양한 데이터베이스 연결 시도
    connection_attempts = [
        # Production 환경 연결들
        {
            'url': 'mongodb://admin:password123@mongodb-prod:27017/online_evaluation_prod?authSource=admin',
            'db_name': 'online_evaluation_prod'
        },
        {
            'url': 'mongodb://admin:password123@mongodb-prod:27017/online_evaluation?authSource=admin',
            'db_name': 'online_evaluation'
        },
        {
            'url': 'mongodb://admin:password123@mongodb-prod:27017/online_evaluation_db?authSource=admin', 
            'db_name': 'online_evaluation_db'
        }
    ]
    
    for attempt in connection_attempts:
        try:
            print(f"📡 연결 시도: {attempt['db_name']} 데이터베이스")
            
            client = AsyncIOMotorClient(attempt['url'], serverSelectionTimeoutMS=5000)
            await client.admin.command('ping')
            
            db = client[attempt['db_name']]
            
            # 사용자 수 확인
            user_count = await db.users.count_documents({})
            print(f"   📊 사용자 수: {user_count}명")
            
            if user_count > 0:
                # 모든 사용자 조회
                users = await db.users.find({}).to_list(100)
                print(f"   👥 사용자 목록:")
                
                for user in users:
                    login_id = user.get('login_id', 'unknown')
                    user_name = user.get('user_name', 'unknown') 
                    role = user.get('role', 'unknown')
                    is_active = user.get('is_active', False)
                    has_password = bool(user.get('password_hash'))
                    
                    status = "활성" if is_active else "비활성"
                    pwd_status = "✅" if has_password else "❌"
                    
                    print(f"      - {login_id} ({user_name}) - {role} - {status} - 비밀번호: {pwd_status}")
                
                # 테스트 계정 비밀번호 검증
                print(f"\n   🧪 비밀번호 검증:")
                test_accounts = [
                    ("admin", "admin123"),
                    ("secretary", "secretary123"), 
                    ("evaluator", "evaluator123"),
                    ("evaluator01", "evaluator123")
                ]
                
                for login_id, password in test_accounts:
                    user = await db.users.find_one({"login_id": login_id})
                    if user:
                        stored_hash = user.get('password_hash')
                        if stored_hash:
                            try:
                                is_valid = pwd_context.verify(password, stored_hash)
                                result = "✅ 성공" if is_valid else "❌ 실패"
                                print(f"      - {login_id}: {result}")
                            except Exception as e:
                                print(f"      - {login_id}: ❌ 검증 오류 - {e}")
                        else:
                            print(f"      - {login_id}: ❌ 비밀번호 해시 없음")
                    else:
                        print(f"      - {login_id}: ❌ 사용자 없음")
                
                print(f"✅ {attempt['db_name']} 데이터베이스 확인 완료\n")
            else:
                print(f"   ⚠️ {attempt['db_name']} 데이터베이스에 사용자가 없습니다.\n")
            
            client.close()
            
        except Exception as e:
            print(f"   ❌ 연결 실패: {e}\n")

async def main():
    print("🔍 사용자 계정 검증")
    print("=" * 60)
    await verify_users()

if __name__ == "__main__":
    asyncio.run(main())