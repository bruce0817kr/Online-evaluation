#!/usr/bin/env python3
"""
최종 배포 테스트 스크립트
Online Evaluation System 핵심 기능 테스트
"""

import requests
import json
import time
import sys
from datetime import datetime

# 테스트 설정
BACKEND_URL = "http://localhost:8002"
FRONTEND_URL = "http://localhost:3002"

def log_message(message, level="INFO"):
    """로그 메시지 출력"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")

def test_service_health():
    """서비스 헬스체크 테스트"""
    log_message("=== 서비스 헬스체크 테스트 ===")
    
    try:
        # 백엔드 헬스체크
        response = requests.get(f"{BACKEND_URL}/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            log_message(f"백엔드 헬스체크 성공: {health_data['status']}")
            log_message(f"서비스 상태: {health_data['services']}")
        else:
            log_message(f"백엔드 헬스체크 실패: HTTP {response.status_code}", "ERROR")
            return False
            
        # 프론트엔드 접근성 확인
        response = requests.get(FRONTEND_URL, timeout=10)
        if response.status_code == 200:
            log_message("프론트엔드 접근성 확인 성공")
        else:
            log_message(f"프론트엔드 접근 실패: HTTP {response.status_code}", "ERROR")
            return False
            
        return True
        
    except Exception as e:
        log_message(f"헬스체크 테스트 중 오류: {e}", "ERROR")
        return False

def test_user_registration():
    """사용자 등록 테스트"""
    log_message("=== 사용자 등록 테스트 ===")
    
    try:
        # 테스트 사용자 데이터
        test_user = {
            "login_id": "test_admin",
            "password": "Test123!@#",
            "name": "테스트 관리자",
            "email": "admin@test.com",
            "role": "admin",
            "company": "테스트 회사"
        }
        
        response = requests.post(
            f"{BACKEND_URL}/api/auth/register", 
            json=test_user,
            timeout=10
        )
        
        if response.status_code == 201:
            log_message("사용자 등록 성공")
            return test_user
        elif response.status_code == 400:
            # 이미 존재하는 사용자일 수 있음
            log_message("사용자가 이미 존재할 수 있음 (등록 건너뜀)")
            return test_user
        else:
            log_message(f"사용자 등록 실패: HTTP {response.status_code}", "ERROR")
            log_message(f"응답: {response.text}")
            return None
            
    except Exception as e:
        log_message(f"사용자 등록 테스트 중 오류: {e}", "ERROR")
        return None

def test_user_login(user_data):
    """사용자 로그인 테스트"""
    log_message("=== 사용자 로그인 테스트 ===")
    
    try:
        login_data = {
            "login_id": user_data["login_id"],
            "password": user_data["password"]
        }
        
        response = requests.post(
            f"{BACKEND_URL}/api/auth/login",
            json=login_data,
            timeout=10
        )
        
        if response.status_code == 200:
            login_result = response.json()
            log_message("로그인 성공")
            log_message(f"사용자: {login_result.get('user', {}).get('name')}")
            log_message(f"역할: {login_result.get('user', {}).get('role')}")
            return login_result.get('access_token')
        else:
            log_message(f"로그인 실패: HTTP {response.status_code}", "ERROR")
            log_message(f"응답: {response.text}")
            return None
            
    except Exception as e:
        log_message(f"로그인 테스트 중 오류: {e}", "ERROR")
        return None

def test_authenticated_api(token):
    """인증이 필요한 API 테스트"""
    log_message("=== 인증 API 테스트 ===")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        # 현재 사용자 정보 조회
        response = requests.get(
            f"{BACKEND_URL}/api/auth/me",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            user_info = response.json()
            log_message("사용자 정보 조회 성공")
            log_message(f"사용자: {user_info.get('name')}")
            return True
        else:
            log_message(f"사용자 정보 조회 실패: HTTP {response.status_code}", "ERROR")
            return False
            
    except Exception as e:
        log_message(f"인증 API 테스트 중 오류: {e}", "ERROR")
        return False

def test_template_operations(token):
    """템플릿 관리 기능 테스트"""
    log_message("=== 템플릿 관리 테스트 ===")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        # 템플릿 목록 조회
        response = requests.get(
            f"{BACKEND_URL}/api/templates",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            templates = response.json()
            log_message(f"템플릿 목록 조회 성공: {len(templates)}개")
            return True
        else:
            log_message(f"템플릿 목록 조회 실패: HTTP {response.status_code}", "ERROR")
            return False
            
    except Exception as e:
        log_message(f"템플릿 관리 테스트 중 오류: {e}", "ERROR")
        return False

def run_all_tests():
    """모든 테스트 실행"""
    log_message("=" * 50)
    log_message("Online Evaluation System 최종 배포 테스트 시작")
    log_message("=" * 50)
    
    test_results = []
    
    # 1. 서비스 헬스체크
    health_result = test_service_health()
    test_results.append(("서비스 헬스체크", health_result))
    
    if not health_result:
        log_message("헬스체크 실패로 테스트 중단", "ERROR")
        return False
    
    # 2. 사용자 등록
    user_data = test_user_registration()
    test_results.append(("사용자 등록", user_data is not None))
    
    if not user_data:
        log_message("사용자 등록 실패로 테스트 중단", "ERROR")
        return False
    
    # 3. 사용자 로그인
    token = test_user_login(user_data)
    test_results.append(("사용자 로그인", token is not None))
    
    if not token:
        log_message("로그인 실패로 테스트 중단", "ERROR")
        return False
    
    # 4. 인증 API 테스트
    auth_result = test_authenticated_api(token)
    test_results.append(("인증 API", auth_result))
    
    # 5. 템플릿 관리 테스트
    template_result = test_template_operations(token)
    test_results.append(("템플릿 관리", template_result))
    
    # 결과 요약
    log_message("=" * 50)
    log_message("테스트 결과 요약")
    log_message("=" * 50)
    
    success_count = 0
    for test_name, result in test_results:
        status = "✅ 성공" if result else "❌ 실패"
        log_message(f"{test_name}: {status}")
        if result:
            success_count += 1
    
    log_message(f"\n전체 테스트: {len(test_results)}개")
    log_message(f"성공: {success_count}개")
    log_message(f"실패: {len(test_results) - success_count}개")
    log_message(f"성공률: {(success_count/len(test_results)*100):.1f}%")
    
    return success_count == len(test_results)

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)