#!/usr/bin/env python3
"""
로그인 디버깅 스크립트
실제 데이터베이스 데이터와 API 로그인을 비교 검증
"""

import asyncio
import requests
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
import os
from dotenv import load_dotenv

load_dotenv()

# 비밀번호 컨텍스트 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def check_database_user():
    """데이터베이스에서 직접 사용자 확인"""
    print("🔍 데이터베이스 직접 확인...")
    
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://admin:password123@localhost:27017/evaluation_db?authSource=admin')
    client = AsyncIOMotorClient(mongo_url)
    
    try:
        # 데이터베이스 선택 (여러 가능성 확인)
        possible_dbs = ['online_evaluation', 'evaluation_db']
        
        for db_name in possible_dbs:
            print(f"\n📂 데이터베이스 '{db_name}' 확인 중...")
            db = client[db_name]
            
            # admin 사용자 찾기
            admin_user = await db.users.find_one({"login_id": "admin"})
            
            if admin_user:
                print(f"✅ '{db_name}'에서 admin 사용자 발견!")
                print(f"   - 로그인 ID: {admin_user.get('login_id')}")
                print(f"   - 사용자 이름: {admin_user.get('user_name')}")
                print(f"   - 역할: {admin_user.get('role')}")
                print(f"   - 이메일: {admin_user.get('email')}")
                print(f"   - 활성: {admin_user.get('is_active', '정보 없음')}")
                print(f"   - 비밀번호 해시: {admin_user.get('password_hash', 'N/A')[:30]}...")
                
                # 비밀번호 검증
                stored_hash = admin_user.get('password_hash')
                if stored_hash:
                    # 여러 가능한 비밀번호 테스트
                    passwords_to_test = ['admin123', 'admin', 'password123', 'test123']
                    
                    for password in passwords_to_test:
                        try:
                            is_valid = pwd_context.verify(password, stored_hash)
                            print(f"   - 비밀번호 '{password}' 검증: {'✅ 성공' if is_valid else '❌ 실패'}")
                            if is_valid:
                                return db_name, admin_user, password
                        except Exception as e:
                            print(f"   - 비밀번호 '{password}' 검증 오류: {e}")
                
                return db_name, admin_user, None
            else:
                print(f"❌ '{db_name}'에서 admin 사용자를 찾을 수 없음")
        
        return None, None, None
        
    except Exception as e:
        print(f"❌ 데이터베이스 오류: {e}")
        return None, None, None
        
    finally:
        client.close()

def test_api_login(password):
    """API로 로그인 테스트"""
    print(f"\n🔑 API 로그인 테스트 (비밀번호: {password})...")
    
    try:
        # Form data로 로그인 시도
        login_data = f"username=admin&password={password}"
        
        response = requests.post(
            "http://localhost:8080/api/auth/login",
            data=login_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=10
        )
        
        print(f"   - 응답 코드: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("   ✅ 로그인 성공!")
            print(f"   - 토큰: {data.get('access_token', 'N/A')[:20]}...")
            print(f"   - 사용자 정보: {data.get('user', {})}")
            return True, data
        else:
            print(f"   ❌ 로그인 실패: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"   ❌ API 오류: {e}")
        return False, None

async def main():
    """메인 검증 프로세스"""
    print("🚀 로그인 문제 디버깅 시작")
    print("=" * 50)
    
    # 1. 데이터베이스 확인
    db_name, admin_user, correct_password = await check_database_user()
    
    if not admin_user:
        print("\n❌ 데이터베이스에서 admin 사용자를 찾을 수 없습니다!")
        return
    
    if not correct_password:
        print("\n⚠️ 올바른 비밀번호를 찾을 수 없습니다. 기본값으로 테스트합니다.")
        correct_password = "admin123"
    
    print(f"\n✅ 사용된 데이터베이스: {db_name}")
    print(f"✅ 확인된 비밀번호: {correct_password}")
    
    # 2. API 로그인 테스트
    success, login_data = test_api_login(correct_password)
    
    # 3. 결과 정리
    print("\n" + "=" * 50)
    print("🏁 디버깅 결과 요약")
    print("=" * 50)
    
    print(f"📂 데이터베이스: {db_name}")
    print(f"👤 Admin 사용자: {'존재' if admin_user else '없음'}")
    print(f"🔑 올바른 비밀번호: {correct_password}")
    print(f"🌐 API 로그인: {'성공' if success else '실패'}")
    
    if not success:
        print("\n💡 추가 조사 필요:")
        print("   - 백엔드 로그 확인")
        print("   - 비밀번호 해시 알고리즘 확인")
        print("   - API 엔드포인트 경로 확인")
    else:
        print("\n🎉 로그인 시스템이 정상 작동합니다!")

if __name__ == "__main__":
    asyncio.run(main())
