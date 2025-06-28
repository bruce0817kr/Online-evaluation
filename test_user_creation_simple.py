#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
사용자 생성 API 간단한 테스트 스크립트
Docker 환경에서 실행 가능한 간단한 버전
"""

import json
import requests
import time

def test_backend_connection():
    """백엔드 API 연결 테스트"""
    backends = [
        "http://localhost:8002",  # Development backend
        "http://localhost:8019",  # Production backend
    ]
    
    for backend_url in backends:
        try:
            print(f"🔍 백엔드 테스트: {backend_url}")
            response = requests.get(f"{backend_url}/health", timeout=5)
            if response.status_code == 200:
                print(f"✅ 백엔드 연결 성공: {backend_url}")
                return backend_url
            else:
                print(f"⚠️  백엔드 응답 코드: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ 백엔드 연결 실패: {e}")
    
    return None

def test_login_with_existing_accounts(backend_url):
    """기존 계정으로 로그인 테스트"""
    print("\n🔐 로그인 테스트...")
    
    test_accounts = [
        {"username": "admin", "password": "admin123"},
        {"username": "secretary01", "password": "secretary123"},
        {"username": "evaluator01", "password": "evaluator123"},
    ]
    
    working_accounts = []
    failed_accounts = []
    
    for account in test_accounts:
        try:
            login_data = {
                "username": account["username"],
                "password": account["password"]
            }
            
            print(f"🧪 로그인 시도: {account['username']}")
            response = requests.post(
                f"{backend_url}/api/auth/login",
                data=login_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                token = result.get("access_token")
                user_info = result.get("user", {})
                
                working_accounts.append({
                    "username": account["username"],
                    "password": account["password"],
                    "role": user_info.get("role", "unknown"),
                    "token": token[:20] + "..." if token else "none"
                })
                print(f"✅ 로그인 성공: {account['username']} ({user_info.get('role', 'unknown')})")
            else:
                failed_accounts.append(account["username"])
                print(f"❌ 로그인 실패: {account['username']} - 상태코드: {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   오류 내용: {error_detail}")
                except:
                    print(f"   응답 내용: {response.text[:200]}")
                    
        except requests.exceptions.RequestException as e:
            failed_accounts.append(account["username"])
            print(f"❌ 로그인 요청 실패: {account['username']} - {e}")
    
    return working_accounts, failed_accounts

def test_create_user_api(backend_url, admin_token):
    """사용자 생성 API 테스트"""
    print("\n👥 사용자 생성 API 테스트...")
    
    if not admin_token:
        print("❌ 관리자 토큰이 없어서 사용자 생성 테스트를 건너뜁니다.")
        return
    
    test_user = {
        "login_id": "test_secretary_" + str(int(time.time())),
        "password": "testpass123",
        "user_name": "테스트 비서",
        "email": f"test_secretary_{int(time.time())}@evaluation.com",
        "phone": "010-9999-8888",
        "role": "secretary"
    }
    
    headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }
    
    try:
        print(f"🧪 새 사용자 생성 시도: {test_user['login_id']}")
        response = requests.post(
            f"{backend_url}/api/users",
            json=test_user,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 사용자 생성 성공: {result.get('login_id')} ({result.get('role')})")
            
            # 생성된 사용자로 로그인 테스트
            print("🔐 생성된 사용자 로그인 테스트...")
            login_response = requests.post(
                f"{backend_url}/api/auth/login",
                data={
                    "username": test_user["login_id"],
                    "password": test_user["password"]
                },
                timeout=10
            )
            
            if login_response.status_code == 200:
                print("✅ 생성된 사용자 로그인 성공!")
                return True
            else:
                print(f"❌ 생성된 사용자 로그인 실패: {login_response.status_code}")
                return False
                
        else:
            print(f"❌ 사용자 생성 실패: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"   오류 내용: {error_detail}")
            except:
                print(f"   응답 내용: {response.text[:200]}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 사용자 생성 요청 실패: {e}")
        return False

def test_evaluator_creation_api(backend_url, admin_token):
    """평가자 생성 API 테스트"""
    print("\n📋 평가자 생성 API 테스트...")
    
    if not admin_token:
        print("❌ 관리자 토큰이 없어서 평가자 생성 테스트를 건너뜁니다.")
        return
    
    test_evaluator = {
        "user_name": f"테스트평가자_{int(time.time())}",
        "email": f"test_evaluator_{int(time.time())}@evaluation.com",
        "phone": "010-8888-9999"
    }
    
    headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }
    
    try:
        print(f"🧪 새 평가자 생성 시도: {test_evaluator['user_name']}")
        response = requests.post(
            f"{backend_url}/api/evaluators",
            json=test_evaluator,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            generated_login_id = result.get("generated_login_id")
            generated_password = result.get("generated_password")
            
            print(f"✅ 평가자 생성 성공:")
            print(f"   로그인 ID: {generated_login_id}")
            print(f"   비밀번호: {generated_password}")
            
            # 생성된 평가자로 로그인 테스트
            if generated_login_id and generated_password:
                print("🔐 생성된 평가자 로그인 테스트...")
                login_response = requests.post(
                    f"{backend_url}/api/auth/login",
                    data={
                        "username": generated_login_id,
                        "password": generated_password
                    },
                    timeout=10
                )
                
                if login_response.status_code == 200:
                    print("✅ 생성된 평가자 로그인 성공!")
                    return True
                else:
                    print(f"❌ 생성된 평가자 로그인 실패: {login_response.status_code}")
                    return False
            else:
                print("⚠️  생성된 계정 정보가 불완전합니다.")
                return False
                
        else:
            print(f"❌ 평가자 생성 실패: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"   오류 내용: {error_detail}")
            except:
                print(f"   응답 내용: {response.text[:200]}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 평가자 생성 요청 실패: {e}")
        return False

def main():
    """메인 실행 함수"""
    print("🚀 사용자 생성 API 테스트 시작")
    print("=" * 60)
    
    # 1. 백엔드 연결 테스트
    backend_url = test_backend_connection()
    if not backend_url:
        print("\n❌ 백엔드에 연결할 수 없습니다.")
        print("💡 해결방법:")
        print("1. Docker 컨테이너가 실행되고 있는지 확인: docker ps")
        print("2. 백엔드 서비스 재시작: docker-compose restart backend")
        return
    
    # 2. 기존 계정 로그인 테스트
    working_accounts, failed_accounts = test_login_with_existing_accounts(backend_url)
    
    # 관리자 토큰 가져오기
    admin_token = None
    for account in working_accounts:
        if account.get("role") == "admin":
            # 관리자 토큰 다시 가져오기
            try:
                response = requests.post(
                    f"{backend_url}/api/auth/login",
                    data={
                        "username": account["username"],
                        "password": account["password"]
                    },
                    timeout=10
                )
                if response.status_code == 200:
                    admin_token = response.json().get("access_token")
                    break
            except:
                pass
    
    # 3. 사용자 생성 API 테스트
    user_creation_success = test_create_user_api(backend_url, admin_token)
    
    # 4. 평가자 생성 API 테스트
    evaluator_creation_success = test_evaluator_creation_api(backend_url, admin_token)
    
    # 5. 최종 결과 요약
    print("\n" + "=" * 60)
    print("📋 최종 테스트 결과")
    print("=" * 60)
    
    print(f"🌐 백엔드 URL: {backend_url}")
    print(f"✅ 작동하는 계정: {len(working_accounts)}개")
    for account in working_accounts:
        print(f"   - {account['username']} ({account['role']})")
    
    if failed_accounts:
        print(f"❌ 실패한 계정: {len(failed_accounts)}개")
        for username in failed_accounts:
            print(f"   - {username}")
    
    print(f"👥 사용자 생성 API: {'✅ 성공' if user_creation_success else '❌ 실패'}")
    print(f"📋 평가자 생성 API: {'✅ 성공' if evaluator_creation_success else '❌ 실패'}")
    
    # 테스트 결과 저장
    test_results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "backend_url": backend_url,
        "working_accounts": working_accounts,
        "failed_accounts": failed_accounts,
        "user_creation_api_working": user_creation_success,
        "evaluator_creation_api_working": evaluator_creation_success
    }
    
    with open('user_creation_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(test_results, f, ensure_ascii=False, indent=2)
    
    print("\n💾 테스트 결과가 'user_creation_test_results.json'에 저장되었습니다.")
    
    if working_accounts and user_creation_success and evaluator_creation_success:
        print("\n🎉 모든 사용자 생성 API가 정상 작동합니다!")
    else:
        print("\n⚠️  일부 기능에 문제가 있습니다. 상세 로그를 확인하세요.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류 발생: {e}")
        import traceback
        traceback.print_exc()