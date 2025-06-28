#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
사용자 생성 API 문제 진단 및 수정 스크립트
"""

import asyncio
import sys
import traceback
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
import json

# 백엔드와 동일한 비밀번호 해시 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

def get_password_hash(password):
    """비밀번호를 해시화합니다."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호를 검증합니다."""
    return pwd_context.verify(plain_password, hashed_password)

async def diagnose_system():
    """시스템 현재 상태를 진단합니다."""
    print("🔍 시스템 진단 시작...")
    
    # MongoDB 연결 시도 (여러 포트 시도)
    mongo_urls = [
        'mongodb://localhost:27017/online_evaluation',
        'mongodb://admin:password123@localhost:27017/online_evaluation?authSource=admin',
        'mongodb://localhost:27018/online_evaluation',
        'mongodb://admin:password123@localhost:27018/online_evaluation?authSource=admin'
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
        print("❌ MongoDB에 연결할 수 없습니다. Docker가 실행되고 있는지 확인하세요.")
        return None, None
    
    try:
        # 현재 사용자 확인
        users = await db.users.find({}).to_list(100)
        print(f"\n📊 현재 데이터베이스 사용자 수: {len(users)}명")
        
        if users:
            print("\n👥 기존 사용자 목록:")
            for user in users:
                role = user.get('role', 'unknown')
                login_id = user.get('login_id', 'unknown')
                user_name = user.get('user_name', 'unknown')
                is_active = user.get('is_active', False)
                print(f"  - {login_id} ({user_name}) - {role} - {'활성' if is_active else '비활성'}")
        else:
            print("👥 사용자가 없습니다.")
        
        # 컬렉션 정보 확인
        collections = await db.list_collection_names()
        print(f"\n📋 데이터베이스 컬렉션: {collections}")
        
        return client, db
        
    except Exception as e:
        print(f"❌ 데이터베이스 조회 오류: {e}")
        traceback.print_exc()
        if client:
            client.close()
        return None, None

async def create_test_users(db):
    """테스트 사용자들을 생성합니다."""
    print("\n🔧 테스트 사용자 생성 시작...")
    
    # 필수 테스트 사용자들
    test_users = [
        {
            "login_id": "admin",
            "password": "admin123",
            "user_name": "시스템 관리자",
            "email": "admin@evaluation.com",
            "phone": "010-1234-5678",
            "role": "admin"
        },
        {
            "login_id": "secretary01",
            "password": "secretary123",
            "user_name": "김비서",
            "email": "secretary1@evaluation.com",
            "phone": "010-2345-6789",
            "role": "secretary"
        },
        {
            "login_id": "evaluator01",
            "password": "evaluator123",
            "user_name": "박평가",
            "email": "evaluator1@evaluation.com",
            "phone": "010-4567-8901",
            "role": "evaluator"
        }
    ]
    
    created_users = []
    
    for user_data in test_users:
        try:
            # 기존 사용자 확인
            existing_user = await db.users.find_one({"login_id": user_data["login_id"]})
            
            if existing_user:
                print(f"⚠️  사용자 '{user_data['login_id']}'는 이미 존재합니다.")
                
                # 비밀번호 검증 테스트
                stored_hash = existing_user.get('password_hash')
                if stored_hash and verify_password(user_data['password'], stored_hash):
                    print(f"✅ 사용자 '{user_data['login_id']}' 비밀번호 검증 성공")
                else:
                    print(f"❌ 사용자 '{user_data['login_id']}' 비밀번호 검증 실패 - 패스워드 재설정 필요")
                    
                    # 비밀번호 업데이트
                    new_hash = get_password_hash(user_data['password'])
                    await db.users.update_one(
                        {"login_id": user_data["login_id"]},
                        {"$set": {"password_hash": new_hash}}
                    )
                    print(f"🔄 사용자 '{user_data['login_id']}' 비밀번호 업데이트 완료")
                
                continue
            
            # 새 사용자 생성
            import uuid
            user_doc = {
                "id": str(uuid.uuid4()),
                "login_id": user_data["login_id"],
                "password_hash": get_password_hash(user_data["password"]),
                "user_name": user_data["user_name"],
                "email": user_data["email"],
                "phone": user_data["phone"],
                "role": user_data["role"],
                "created_at": datetime.utcnow(),
                "is_active": True,
                "last_login": None
            }
            
            result = await db.users.insert_one(user_doc)
            
            if result.inserted_id:
                created_users.append(user_data)
                print(f"✅ 사용자 생성: {user_data['login_id']} ({user_data['user_name']}) - {user_data['role']}")
            else:
                print(f"❌ 사용자 생성 실패: {user_data['login_id']}")
                
        except Exception as e:
            print(f"❌ 사용자 '{user_data['login_id']}' 생성 중 오류: {e}")
            traceback.print_exc()
    
    return created_users

async def test_login_credentials(db):
    """생성된 사용자들의 로그인 자격증명을 테스트합니다."""
    print("\n🧪 로그인 자격증명 테스트...")
    
    test_credentials = [
        {"login_id": "admin", "password": "admin123"},
        {"login_id": "secretary01", "password": "secretary123"},  
        {"login_id": "evaluator01", "password": "evaluator123"}
    ]
    
    for cred in test_credentials:
        try:
            user = await db.users.find_one({"login_id": cred["login_id"]})
            
            if not user:
                print(f"❌ 사용자 '{cred['login_id']}'를 찾을 수 없습니다.")
                continue
            
            stored_hash = user.get('password_hash')
            if not stored_hash:
                print(f"❌ 사용자 '{cred['login_id']}'의 비밀번호 해시가 없습니다.")
                continue
            
            if verify_password(cred['password'], stored_hash):
                print(f"✅ 로그인 테스트 성공: {cred['login_id']} ({user.get('role')})")
            else:
                print(f"❌ 로그인 테스트 실패: {cred['login_id']} - 비밀번호 불일치")
                
        except Exception as e:
            print(f"❌ 로그인 테스트 오류 ({cred['login_id']}): {e}")

async def test_api_endpoints():
    """API 엔드포인트 연결 테스트"""
    print("\n🌐 API 엔드포인트 테스트...")
    
    try:
        import aiohttp
        
        backend_urls = [
            "http://localhost:8000",
            "http://localhost:8002", 
            "http://localhost:8080"
        ]
        
        for url in backend_urls:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{url}/health", timeout=5) as response:
                        if response.status == 200:
                            print(f"✅ 백엔드 API 연결 성공: {url}")
                            return url
                        else:
                            print(f"⚠️  백엔드 API 응답 코드: {response.status} - {url}")
            except Exception as e:
                print(f"❌ 백엔드 API 연결 실패: {url} - {e}")
        
        print("❌ 모든 백엔드 API 엔드포인트 연결 실패")
        return None
                
    except ImportError:
        print("⚠️  aiohttp가 설치되지 않아 API 테스트를 건너뜁니다.")
        print("설치하려면: pip install aiohttp")
        return None

async def main():
    """메인 실행 함수"""
    print("🚀 사용자 생성 API 문제 진단 및 수정 시작")
    print("=" * 60)
    
    # 1. 시스템 진단
    client, db = await diagnose_system()
    
    if not client or not db:
        print("\n❌ MongoDB 연결 실패로 종료합니다.")
        print("💡 해결방법:")
        print("1. Docker Compose가 실행되고 있는지 확인: docker-compose ps")
        print("2. MongoDB 서비스 재시작: docker-compose restart mongodb")
        print("3. 포트 설정 확인: docker-compose logs mongodb")
        return
    
    try:
        # 2. 테스트 사용자 생성
        created_users = await create_test_users(db)
        
        # 3. 로그인 자격증명 테스트
        await test_login_credentials(db)
        
        # 4. API 엔드포인트 테스트
        api_url = await test_api_endpoints()
        
        # 5. 최종 결과 요약
        print("\n" + "=" * 60)
        print("📋 최종 진단 결과")
        print("=" * 60)
        
        final_users = await db.users.find({}).to_list(100)
        admin_count = len([u for u in final_users if u.get('role') == 'admin'])
        secretary_count = len([u for u in final_users if u.get('role') == 'secretary'])
        evaluator_count = len([u for u in final_users if u.get('role') == 'evaluator'])
        
        print(f"👥 총 사용자 수: {len(final_users)}명")
        print(f"  - 관리자: {admin_count}명")
        print(f"  - 비서: {secretary_count}명")  
        print(f"  - 평가자: {evaluator_count}명")
        
        if api_url:
            print(f"🌐 백엔드 API: {api_url} (정상)")
        else:
            print("🌐 백엔드 API: 연결 불가")
        
        # 테스트 자격증명 정보 저장
        test_creds = [
            {"login_id": "admin", "password": "admin123", "role": "admin"},
            {"login_id": "secretary01", "password": "secretary123", "role": "secretary"},
            {"login_id": "evaluator01", "password": "evaluator123", "role": "evaluator"}
        ]
        
        with open('test_login_credentials.json', 'w', encoding='utf-8') as f:
            json.dump(test_creds, f, ensure_ascii=False, indent=2)
        
        print("\n💾 테스트 로그인 정보가 'test_login_credentials.json'에 저장되었습니다.")
        
        print("\n✅ 사용자 생성 시스템 진단 및 수정 완료!")
        print("\n🧪 테스트 방법:")
        print("1. 프론트엔드에서 위 계정들로 로그인 테스트")
        print("2. 각 역할별 권한 확인")
        print("3. 새 사용자 생성 API 테스트")
        
    except Exception as e:
        print(f"\n❌ 실행 중 오류 발생: {e}")
        traceback.print_exc()
    
    finally:
        if client:
            client.close()
            print("\n🔒 MongoDB 연결 종료")

if __name__ == "__main__":
    asyncio.run(main())