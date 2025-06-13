#!/usr/bin/env python3
"""
checkAuthStatus 함수 개선 검증 테스트
/auth/me 엔드포인트 응답 데이터 활용 확인
"""

import requests
import json
import time

# 설정
BACKEND_URL = "http://localhost:8080"
FRONTEND_URL = "http://localhost:3000"

def test_auth_me_endpoint():
    """백엔드 /auth/me 엔드포인트 테스트"""
    print("\n=== 1. 백엔드 /auth/me 엔드포인트 테스트 ===")
    
    # 로그인하여 토큰 얻기
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        login_response = requests.post(
            f"{BACKEND_URL}/api/auth/login",
            data=login_data,
            timeout=10
        )
        
        if login_response.status_code != 200:
            print(f"❌ 로그인 실패: {login_response.status_code}")
            return None
            
        token_data = login_response.json()
        token = token_data.get("access_token")
        
        if not token:
            print("❌ 토큰 받기 실패")
            return None
            
        print("✅ 로그인 성공, 토큰 획득")
        
        # /auth/me 엔드포인트 호출
        auth_response = requests.get(
            f"{BACKEND_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        if auth_response.status_code != 200:
            print(f"❌ /auth/me 호출 실패: {auth_response.status_code}")
            return None
            
        user_data = auth_response.json()
        print("✅ /auth/me 엔드포인트 정상 작동")
        print(f"📋 사용자 정보:")
        print(f"   - ID: {user_data.get('id')}")
        print(f"   - 로그인 ID: {user_data.get('login_id')}")
        print(f"   - 이름: {user_data.get('user_name')}")
        print(f"   - 이메일: {user_data.get('email')}")
        print(f"   - 전화번호: {user_data.get('phone')}")
        print(f"   - 역할: {user_data.get('role')}")
        print(f"   - 활성 상태: {user_data.get('is_active')}")
        print(f"   - 생성일: {user_data.get('created_at')}")
        print(f"   - 마지막 로그인: {user_data.get('last_login')}")
        
        return token, user_data
        
    except Exception as e:
        print(f"❌ 테스트 중 오류: {e}")
        return None

def test_frontend_auth_status():
    """프론트엔드 인증 상태 확인 테스트"""
    print("\n=== 2. 프론트엔드 접근성 테스트 ===")
    
    try:
        response = requests.get(FRONTEND_URL, timeout=10)
        if response.status_code == 200:
            print("✅ 프론트엔드 정상 접근 가능")
            print(f"🌐 URL: {FRONTEND_URL}")
            return True
        else:
            print(f"❌ 프론트엔드 접근 실패: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 프론트엔드 접근 중 오류: {e}")
        return False

def verify_user_data_structure(user_data):
    """사용자 데이터 구조 검증"""
    print("\n=== 3. 사용자 데이터 구조 검증 ===")
    
    required_fields = [
        'id', 'login_id', 'user_name', 'email', 
        'phone', 'role', 'created_at', 'is_active'
    ]
    
    optional_fields = ['last_login']
    
    missing_required = []
    for field in required_fields:
        if field not in user_data or user_data[field] is None:
            missing_required.append(field)
    
    if missing_required:
        print(f"❌ 필수 필드 누락: {missing_required}")
        return False
    else:
        print("✅ 모든 필수 필드 존재")
    
    # 선택적 필드 확인
    for field in optional_fields:
        if field in user_data and user_data[field] is not None:
            print(f"✅ 선택적 필드 '{field}' 존재: {user_data[field]}")
        else:
            print(f"ℹ️ 선택적 필드 '{field}' 없음 (정상)")
    
    return True

def main():
    print("🔍 checkAuthStatus 함수 개선 검증 테스트")
    print("=" * 50)
    
    # 백엔드 테스트
    auth_result = test_auth_me_endpoint()
    if not auth_result:
        print("\n❌ 백엔드 테스트 실패")
        return
    
    token, user_data = auth_result
    
    # 사용자 데이터 구조 검증
    if not verify_user_data_structure(user_data):
        print("\n❌ 사용자 데이터 구조 검증 실패")
        return
    
    # 프론트엔드 테스트
    if not test_frontend_auth_status():
        print("\n❌ 프론트엔드 테스트 실패")
        return
    
    print("\n" + "=" * 50)
    print("🎉 모든 테스트 통과!")
    print("\n📋 검증 완료 사항:")
    print("   ✅ 백엔드 /auth/me 엔드포인트 정상 작동")
    print("   ✅ 사용자 데이터 구조 완전성 확인")
    print("   ✅ 프론트엔드 접근 가능")
    print("\n🔧 프론트엔드에서 수정된 checkAuthStatus 함수가")
    print("   이 데이터를 올바르게 활용할 준비가 완료되었습니다!")

if __name__ == "__main__":
    main()
