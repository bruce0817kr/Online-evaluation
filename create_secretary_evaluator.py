#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
비서 및 평가자 계정 생성 스크립트
"""

import requests
import json
import time

def get_admin_token():
    """관리자 토큰 가져오기"""
    backend_urls = ["http://localhost:8019", "http://localhost:8002"]
    
    for backend_url in backend_urls:
        try:
            print(f"🔍 백엔드 연결 시도: {backend_url}")
            response = requests.get(f"{backend_url}/health", timeout=5)
            if response.status_code == 200:
                print(f"✅ 백엔드 발견: {backend_url}")
                break
        except:
            continue
    else:
        print("❌ 사용 가능한 백엔드를 찾을 수 없습니다.")
        return None, None
    
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        response = requests.post(
            f"{backend_url}/api/auth/login",
            data=login_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            token = result.get("access_token")
            print(f"✅ 관리자 로그인 성공")
            return backend_url, token
        else:
            print(f"❌ 관리자 로그인 실패: {response.status_code}")
            return None, None
            
    except Exception as e:
        print(f"❌ 관리자 로그인 오류: {e}")
        return None, None

def create_secretary_user(backend_url, admin_token):
    """비서 사용자 생성"""
    print("\n👩‍💼 비서 사용자 생성...")
    
    secretary_data = {
        "login_id": "secretary01",
        "password": "secretary123",
        "user_name": "김비서",
        "email": "secretary1@evaluation.com",
        "phone": "010-2345-6789",
        "role": "secretary"
    }
    
    headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{backend_url}/api/users",
            json=secretary_data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 비서 생성 성공: {result.get('login_id')} ({result.get('role')})")
            return True
        else:
            print(f"❌ 비서 생성 실패: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"   오류 내용: {error_detail}")
            except:
                print(f"   응답 내용: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ 비서 생성 오류: {e}")
        return False

def create_evaluator_user(backend_url, admin_token):
    """평가자 사용자 생성"""
    print("\n📋 평가자 사용자 생성...")
    
    evaluator_data = {
        "user_name": "박평가",
        "email": "evaluator1@evaluation.com",
        "phone": "010-4567-8901"
    }
    
    headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{backend_url}/api/evaluators",
            json=evaluator_data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            login_id = result.get("generated_login_id")
            password = result.get("generated_password")
            
            print(f"✅ 평가자 생성 성공:")
            print(f"   로그인 ID: {login_id}")
            print(f"   비밀번호: {password}")
            
            return True, login_id, password
        else:
            print(f"❌ 평가자 생성 실패: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"   오류 내용: {error_detail}")
            except:
                print(f"   응답 내용: {response.text[:200]}")
            return False, None, None
            
    except Exception as e:
        print(f"❌ 평가자 생성 오류: {e}")
        return False, None, None

def test_created_accounts(backend_url, secretary_created, evaluator_login_id, evaluator_password):
    """생성된 계정 로그인 테스트"""
    print("\n🧪 생성된 계정 로그인 테스트...")
    
    test_accounts = []
    
    # 비서 계정 테스트
    if secretary_created:
        test_accounts.append({
            "username": "secretary01",
            "password": "secretary123",
            "role": "secretary"
        })
    
    # 평가자 계정 테스트
    if evaluator_login_id and evaluator_password:
        test_accounts.append({
            "username": evaluator_login_id,
            "password": evaluator_password,
            "role": "evaluator"
        })
    
    working_accounts = []
    
    for account in test_accounts:
        try:
            login_data = {
                "username": account["username"],
                "password": account["password"]
            }
            
            print(f"🔐 로그인 테스트: {account['username']}")
            response = requests.post(
                f"{backend_url}/api/auth/login",
                data=login_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                user_info = result.get("user", {})
                working_accounts.append({
                    "username": account["username"],
                    "password": account["password"],
                    "role": user_info.get("role", "unknown")
                })
                print(f"✅ 로그인 성공: {account['username']} ({user_info.get('role')})")
            else:
                print(f"❌ 로그인 실패: {account['username']} - 상태코드: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 로그인 테스트 오류: {account['username']} - {e}")
    
    return working_accounts

def main():
    """메인 실행 함수"""
    print("🚀 비서 및 평가자 계정 생성 시작")
    print("=" * 60)
    
    # 1. 관리자 토큰 가져오기
    backend_url, admin_token = get_admin_token()
    
    if not admin_token:
        print("❌ 관리자 토큰을 가져올 수 없습니다.")
        return
    
    # 2. 비서 계정 생성
    secretary_created = create_secretary_user(backend_url, admin_token)
    
    # 3. 평가자 계정 생성
    evaluator_created, evaluator_login_id, evaluator_password = create_evaluator_user(backend_url, admin_token)
    
    # 4. 생성된 계정 로그인 테스트
    working_accounts = test_created_accounts(backend_url, secretary_created, evaluator_login_id, evaluator_password)
    
    # 5. 최종 결과
    print("\n" + "=" * 60)
    print("📋 최종 결과")
    print("=" * 60)
    
    print(f"👩‍💼 비서 계정 생성: {'✅ 성공' if secretary_created else '❌ 실패'}")
    print(f"📋 평가자 계정 생성: {'✅ 성공' if evaluator_created else '❌ 실패'}")
    print(f"🔐 로그인 테스트 성공: {len(working_accounts)}개 계정")
    
    # 모든 테스트 계정 정보 저장
    all_accounts = [
        {"login_id": "admin", "password": "admin123", "role": "admin"},
    ]
    
    if secretary_created:
        all_accounts.append({"login_id": "secretary01", "password": "secretary123", "role": "secretary"})
    
    if evaluator_created and evaluator_login_id:
        all_accounts.append({"login_id": evaluator_login_id, "password": evaluator_password, "role": "evaluator"})
    
    with open('complete_test_accounts.json', 'w', encoding='utf-8') as f:
        json.dump(all_accounts, f, ensure_ascii=False, indent=2)
    
    print("\n💾 완전한 테스트 계정 정보가 'complete_test_accounts.json'에 저장되었습니다.")
    
    if secretary_created and evaluator_created and len(working_accounts) >= 2:
        print("\n🎉 모든 사용자 계정이 성공적으로 생성되고 테스트되었습니다!")
        print("\n🧪 사용 가능한 테스트 계정:")
        for account in all_accounts:
            print(f"  - {account['login_id']} / {account['password']} ({account['role']})")
    else:
        print("\n⚠️  일부 계정 생성에 문제가 있습니다.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류 발생: {e}")
        import traceback
        traceback.print_exc()