#!/usr/bin/env python3
"""
간단한 웹페이지 접근 및 API 테스트
로그인 기능 문제 진단을 위한 기본 테스트
"""

import requests
import time
from datetime import datetime

def test_frontend_backend_integration():
    """프론트엔드-백엔드 통합 테스트"""
    print("🔄 프론트엔드-백엔드 통합 테스트 시작...")
    print("=" * 50)
    
    frontend_url = "http://localhost:3000"
    backend_url = "http://localhost:8000"
    api_url = f"{backend_url}/api"
    
    # 1. 프론트엔드 접근 테스트
    print("1️⃣ 프론트엔드 접근 테스트...")
    try:
        response = requests.get(frontend_url, timeout=5)
        if response.status_code == 200:
            print("✅ 프론트엔드 접근 성공")
            print(f"   응답 크기: {len(response.content)} bytes")
            
            # HTML에서 중요한 요소들 확인
            html = response.text
            if "온라인 평가 시스템" in html:
                print("✅ 페이지 제목 확인됨")
            if "로그인" in html:
                print("✅ 로그인 요소 확인됨")
            if "REACT_APP_BACKEND_URL" in html:
                print("⚠️ 환경변수가 HTML에 노출됨 (개발 모드)")
        else:
            print(f"❌ 프론트엔드 접근 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 프론트엔드 연결 오류: {e}")
    
    # 2. 백엔드 접근 테스트
    print("\n2️⃣ 백엔드 접근 테스트...")
    try:
        response = requests.get(f"{backend_url}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print("✅ 백엔드 접근 성공")
            print(f"   상태: {health_data.get('status')}")
            services = health_data.get('services', {})
            for service, status in services.items():
                print(f"   - {service}: {status}")
        else:
            print(f"❌ 백엔드 접근 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 백엔드 연결 오류: {e}")
    
    # 3. CORS 테스트 (프론트엔드에서 백엔드로의 요청 시뮬레이션)
    print("\n3️⃣ CORS 설정 테스트...")
    try:
        headers = {
            'Origin': 'http://localhost:3000',
            'Content-Type': 'application/json'
        }
        response = requests.options(f"{api_url}/auth/login", headers=headers, timeout=5)
        print(f"   OPTIONS 요청 응답: {response.status_code}")
        
        # CORS 헤더 확인
        cors_headers = {
            'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
        }
        
        print("   CORS 헤더:")
        for header, value in cors_headers.items():
            if value:
                print(f"   - {header}: {value}")
            else:
                print(f"   - {header}: ❌ 없음")
                
        if cors_headers['Access-Control-Allow-Origin'] == 'http://localhost:3000':
            print("✅ CORS 설정 올바름")
        else:
            print("⚠️ CORS 설정 확인 필요")
            
    except Exception as e:
        print(f"❌ CORS 테스트 오류: {e}")
    
    # 4. API 로그인 테스트 (백엔드 직접 호출)
    print("\n4️⃣ API 로그인 테스트...")
    test_accounts = [
        {"username": "admin", "password": "admin123"},
        {"username": "secretary01", "password": "secretary123"},
        {"username": "evaluator01", "password": "evaluator123"}
    ]
    
    for account in test_accounts:
        try:
            login_data = {
                'username': account['username'],
                'password': account['password']
            }
            
            response = requests.post(f"{api_url}/auth/login", data=login_data, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {account['username']} 로그인 성공")
                print(f"   토큰 타입: {data.get('token_type')}")
                print(f"   사용자 역할: {data.get('user', {}).get('role')}")
            else:
                print(f"❌ {account['username']} 로그인 실패: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   오류: {error_data.get('detail')}")
                except:
                    print(f"   응답: {response.text[:100]}")
                    
        except Exception as e:
            print(f"❌ {account['username']} 로그인 오류: {e}")
    
    # 5. 프론트엔드와 같은 방식으로 로그인 테스트 (FormData 사용)
    print("\n5️⃣ FormData 로그인 테스트 (프론트엔드 방식)...")
    try:
        # 프론트엔드와 동일한 CORS 헤더로 요청
        headers = {
            'Origin': 'http://localhost:3000',
        }
        
        # FormData와 유사한 방식
        login_data = {
            'username': 'admin',
            'password': 'admin123'
        }
        
        response = requests.post(f"{api_url}/auth/login", 
                               data=login_data, 
                               headers=headers, 
                               timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ FormData 로그인 성공")
            print(f"   응답 시간: {response.elapsed.total_seconds():.3f}초")
        else:
            print(f"❌ FormData 로그인 실패: {response.status_code}")
            print(f"   응답: {response.text}")
            
    except Exception as e:
        print(f"❌ FormData 로그인 오류: {e}")
    
    print("\n🏁 통합 테스트 완료!")

if __name__ == "__main__":
    test_frontend_backend_integration()
