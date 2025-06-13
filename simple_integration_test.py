#!/usr/bin/env python3
"""
간단한 통합 테스트 스크립트
"""

import requests
import json
from datetime import datetime

# 기본 설정
BACKEND_URL = "http://localhost:8080"
FRONTEND_URL = "http://localhost:3001"

def test_backend_health():
    """백엔드 헬스 체크"""
    try:
        print("🔍 백엔드 헬스 체크 중...")
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 백엔드 정상 - {data.get('message', 'OK')}")
            return True
        else:
            print(f"❌ 백엔드 오류 - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 백엔드 연결 실패 - {str(e)}")
        return False

def test_frontend_access():
    """프론트엔드 접근 테스트"""
    try:
        print("🔍 프론트엔드 접근 확인 중...")
        response = requests.get(FRONTEND_URL, timeout=10)
        if response.status_code == 200:
            print("✅ 프론트엔드 접근 가능")
            return True
        else:
            print(f"❌ 프론트엔드 접근 실패 - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 프론트엔드 연결 실패 - {str(e)}")
        return False

def test_authentication():
    """인증 시스템 테스트"""
    try:
        print("🔍 인증 시스템 테스트 중...")
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = requests.post(
            f"{BACKEND_URL}/api/auth/login", 
            data=login_data,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            user = data.get('user', {})
            print(f"✅ 로그인 성공 - 사용자: {user.get('user_name', 'N/A')}")
            return True, data
        else:
            print(f"❌ 로그인 실패 - Status: {response.status_code}")
            return False, None
    except Exception as e:
        print(f"❌ 인증 테스트 실패 - {str(e)}")
        return False, None

def main():
    print("🚀 온라인 평가 시스템 간단 통합 테스트")
    print(f"⏰ 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 3
    
    # 1. 백엔드 헬스 체크
    if test_backend_health():
        tests_passed += 1
    
    # 2. 프론트엔드 접근
    if test_frontend_access():
        tests_passed += 1
    
    # 3. 인증 시스템
    auth_success, auth_data = test_authentication()
    if auth_success:
        tests_passed += 1
    
    # 결과 요약
    print("\n" + "=" * 50)
    print("📊 테스트 결과 요약")
    print("=" * 50)
    
    score = int((tests_passed / total_tests) * 100)
    print(f"✅ 통과한 테스트: {tests_passed}/{total_tests}")
    print(f"🏆 전체 점수: {score}%")
    
    if score >= 90:
        print("🎉 시스템이 완벽하게 작동하고 있습니다!")
    elif score >= 70:
        print("👍 시스템이 대체로 잘 작동하고 있습니다.")
    else:
        print("⚠️ 일부 개선이 필요합니다.")
    
    print("=" * 50)
    
    # 결과 저장
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    result_file = f"simple_test_results_{timestamp}.json"
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "tests_passed": tests_passed,
        "total_tests": total_tests,
        "score": score,
        "backend_healthy": tests_passed >= 1,
        "frontend_accessible": tests_passed >= 2,
        "authentication_working": tests_passed >= 3
    }
    
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 결과가 {result_file}에 저장되었습니다.")

if __name__ == "__main__":
    main()
