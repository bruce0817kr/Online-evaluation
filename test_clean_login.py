#!/usr/bin/env python3

import requests
import json

def test_clean_login():
    """Clean login endpoint 테스트"""
    
    base_url = "http://localhost:8080"
    login_url = f"{base_url}/api/auth/clean-login"
    
    # OAuth2PasswordRequestForm 형식으로 데이터 준비
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    try:
        print("🔍 Clean login 엔드포인트 테스트 시작...")
        print(f"📡 URL: {login_url}")
        print(f"📄 Data: {login_data}")
        
        response = requests.post(login_url, data=login_data, headers=headers, timeout=10)
        
        print(f"📊 상태 코드: {response.status_code}")
        print(f"📝 응답 헤더: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Clean login 성공!")
            print(f"🎫 토큰: {result.get('access_token', 'N/A')[:50]}...")
            print(f"👤 사용자: {result.get('user', {}).get('user_name', 'N/A')}")
            print(f"🔧 역할: {result.get('user', {}).get('role', 'N/A')}")
        else:
            print("❌ Clean login 실패:")
            print(f"📄 응답 내용: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 연결 실패: 서버가 실행 중인지 확인하세요")
    except requests.exceptions.Timeout:
        print("❌ 타임아웃: 서버 응답이 느립니다")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    test_clean_login()