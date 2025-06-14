#!/usr/bin/env python3
"""
데이터베이스 마이그레이션 스크립트
evaluation_db의 사용자를 online_evaluation으로 복사
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os

async def migrate_users():
    """사용자 데이터를 올바른 데이터베이스로 마이그레이션"""
    print("🚀 사용자 데이터 마이그레이션 시작")
    print("=" * 50)
    
    # MongoDB 연결
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://admin:password123@localhost:27017/evaluation_db?authSource=admin')
    client = AsyncIOMotorClient(mongo_url)
    
    try:
        # 소스 및 대상 데이터베이스
        source_db = client['evaluation_db']
        target_db = client['online_evaluation']
        
        print("📂 소스 데이터베이스: evaluation_db")
        print("📂 대상 데이터베이스: online_evaluation")
        
        # 1. 소스에서 모든 사용자 조회
        print("\n🔍 소스 데이터베이스에서 사용자 조회 중...")
        users = await source_db.users.find({}).to_list(length=None)
        
        if not users:
            print("❌ 소스 데이터베이스에 사용자가 없습니다!")
            return
        
        print(f"✅ {len(users)}명의 사용자를 발견했습니다.")
        
        # 2. 대상 데이터베이스의 기존 사용자 확인
        print("\n🔍 대상 데이터베이스 확인 중...")
        existing_users = await target_db.users.find({}).to_list(length=None)
        print(f"📊 기존 사용자 수: {len(existing_users)}명")
        
        # 3. 기존 사용자 삭제 (선택적)
        if existing_users:
            print("\n🗑️  기존 사용자 데이터 삭제 중...")
            result = await target_db.users.delete_many({})
            print(f"✅ {result.deleted_count}명의 기존 사용자 삭제 완료")
        
        # 4. 사용자 데이터 복사
        print("\n📋 사용자 데이터 복사 중...")
        copied_count = 0
        
        for user in users:
            try:
                # _id 제거 (새로 생성됨)
                if '_id' in user:
                    del user['_id']
                
                # 대상 데이터베이스에 삽입
                await target_db.users.insert_one(user)
                print(f"✅ 복사 완료: {user.get('login_id')} ({user.get('user_name')})")
                copied_count += 1
                
            except Exception as e:
                print(f"❌ 복사 실패: {user.get('login_id')} - {e}")
        
        # 5. 결과 확인
        print(f"\n📊 마이그레이션 결과:")
        print(f"   - 복사된 사용자: {copied_count}명")
        
        # 대상 데이터베이스에서 최종 확인
        final_users = await target_db.users.find({}).to_list(length=None)
        print(f"   - 최종 사용자 수: {len(final_users)}명")
        
        # 6. 각 사용자 확인
        print(f"\n👥 복사된 사용자 목록:")
        for i, user in enumerate(final_users, 1):
            print(f"   {i}. {user.get('login_id')} ({user.get('user_name')}) - {user.get('role')}")
        
        print(f"\n🎉 마이그레이션 완료!")
        return True
        
    except Exception as e:
        print(f"❌ 마이그레이션 오류: {e}")
        return False
        
    finally:
        client.close()

async def test_migrated_login():
    """마이그레이션 후 로그인 테스트"""
    print("\n🧪 마이그레이션 후 로그인 테스트")
    print("-" * 30)
    
    import requests
    
    try:
        # 로그인 시도
        login_data = "username=admin&password=admin123"
        
        response = requests.post(
            "http://localhost:8080/api/auth/login",
            data=login_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=10
        )
        
        print(f"응답 코드: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 로그인 성공!")
            print(f"사용자: {data.get('user', {}).get('user_name', 'N/A')}")
            print(f"역할: {data.get('user', {}).get('role', 'N/A')}")
            return True
        else:
            print(f"❌ 로그인 실패: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 로그인 테스트 오류: {e}")
        return False

async def main():
    """메인 마이그레이션 프로세스"""
    # 1. 마이그레이션 실행
    success = await migrate_users()
    
    if success:
        # 2. 로그인 테스트
        await asyncio.sleep(2)  # 잠시 대기
        login_success = await test_migrated_login()
        
        if login_success:
            print("\n🎉🎉🎉 마이그레이션 및 로그인 테스트 모두 성공! 🎉🎉🎉")
        else:
            print("\n⚠️ 마이그레이션은 성공했지만 로그인 테스트에 실패했습니다.")
    else:
        print("\n❌ 마이그레이션에 실패했습니다.")

if __name__ == "__main__":
    asyncio.run(main())
