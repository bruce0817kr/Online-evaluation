#!/usr/bin/env python3
"""
온라인 평가 시스템 - 완전한 로그인 테스트
"""

import requests
import json
from datetime import datetime

def test_complete_login():
    """완전한 로그인 테스트"""
    base_url = "http://localhost:8080"
    
    print("🔐 온라인 평가 시스템 - 로그인 테스트")
    print("=" * 60)
    print(f"⏰ 테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 테스트할 사용자들
    test_users = [
        {"login_id": "admin", "password": "admin123", "name": "관리자"}, # 변경: user_id -> login_id
        {"login_id": "secretary01", "password": "secretary123", "name": "간사01"}, # 변경: user_id -> login_id
        {"login_id": "evaluator01", "password": "evaluator123", "name": "평가위원01"} # 변경: user_id -> login_id
    ]
    
    success_count = 0
    
    for i, user in enumerate(test_users, 1):
        print(f"\n{i}. {user['name']} 로그인 테스트")
        print("-" * 30)
        
        try:
            # 로그인 요청
            login_data = {
                "username": user["login_id"], # 변경: user_id -> login_id
                "password": user["password"]
            }
            
            response = requests.post(
                f"{base_url}/api/auth/login",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                token = result.get("access_token")
                user_info = result.get("user", {})
                
                print(f"✅ 로그인 성공!")
                # 백엔드 응답에 따라 'login_id' 또는 'user_id' 사용 (우선 'user_id'로 가정)
                print(f"   - 사용자 ID: {user_info.get('login_id', user_info.get('user_id'))}") # 변경: user_id -> login_id 우선
                print(f"   - 이름: {user_info.get('user_name')}")
                print(f"   - 역할: {user_info.get('role')}")
                print(f"   - 이메일: {user_info.get('email')}")
                print(f"   - 토큰: {token[:20]}...")
                
                # 토큰으로 사용자 정보 조회 테스트
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
                
                me_response = requests.get(f"{base_url}/api/auth/me", headers=headers)
                if me_response.status_code == 200:
                    print(f"✅ 인증 토큰 검증 성공!")
                    success_count += 1
                else:
                    print(f"❌ 토큰 검증 실패: {me_response.status_code}")
                
            else:
                print(f"❌ 로그인 실패: {response.status_code}")
                print(f"   응답: {response.text}")
                
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 테스트 결과: {success_count}/{len(test_users)} 성공")
    
    if success_count == len(test_users):
        print("🎉 모든 로그인 테스트 통과!")
        return True
    else:
        print("⚠️ 일부 테스트 실패")
        return False

def test_frontend_access():
    """프론트엔드 접근 테스트"""
    print("\n🌐 프론트엔드 접근 테스트")
    print("-" * 30)
    
    try:
        response = requests.get("http://localhost:3000", timeout=10)
        if response.status_code == 200:
            print("✅ 프론트엔드 정상 접근 가능")
            return True
        else:
            print(f"❌ 프론트엔드 접근 실패: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 프론트엔드 접근 오류: {e}")
        return False

def test_api_endpoints():
    """주요 API 엔드포인트 테스트"""
    print("\n🔌 API 엔드포인트 테스트")
    print("-" * 30)
    
    endpoints = [
        {"url": "http://localhost:8080/", "name": "API 루트"},
        {"url": "http://localhost:8080/health", "name": "헬스체크"},
        {"url": "http://localhost:8080/docs", "name": "API 문서"},
    ]
    
    success_count = 0
    
    for endpoint in endpoints:
        try:
            response = requests.get(endpoint["url"], timeout=5)
            if response.status_code == 200:
                print(f"✅ {endpoint['name']}: 정상")
                success_count += 1
            else:
                print(f"❌ {endpoint['name']}: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint['name']}: 오류 - {e}")
    
    print(f"\n📊 API 테스트 결과: {success_count}/{len(endpoints)} 성공")
    return success_count == len(endpoints)

if __name__ == "__main__":
    print("🚀 온라인 평가 시스템 - 종합 테스트 시작\n")
    
    # 각 테스트 실행
    login_test = test_complete_login()
    frontend_test = test_frontend_access()
    api_test = test_api_endpoints()
    
    print("\n" + "=" * 60)
    print("🏁 종합 테스트 결과")
    print("=" * 60)
    print(f"🔐 로그인 테스트: {'✅ 성공' if login_test else '❌ 실패'}")
    print(f"🌐 프론트엔드 테스트: {'✅ 성공' if frontend_test else '❌ 실패'}")
    print(f"🔌 API 테스트: {'✅ 성공' if api_test else '❌ 실패'}")
    
    if all([login_test, frontend_test, api_test]):
        print("\n🎉🎉🎉 모든 테스트 통과! 시스템이 정상 작동합니다! 🎉🎉🎉")
    else:
        print("\n⚠️ 일부 테스트 실패 - 추가 점검이 필요합니다.")
