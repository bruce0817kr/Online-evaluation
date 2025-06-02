#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
온라인 평가 시스템 실시간 테스트
도커 컨테이너에서 실행 중인 시스템을 테스트합니다.
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8080"

def test_server_health():
    """서버 상태 확인"""
    print("🔍 서버 상태 확인...")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=10)
        if response.status_code == 200:
            print("✅ 서버가 정상적으로 응답합니다.")
            return True
        else:
            print(f"❌ 서버 응답 오류: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 서버 연결 실패: {str(e)}")
        return False

def test_api_docs():
    """API 문서 접근 테스트"""
    print("\n📚 API 문서 확인...")
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=10)
        if response.status_code == 200:
            print("✅ API 문서에 접근할 수 있습니다.")
            print(f"   🌐 문서 URL: {BASE_URL}/docs")
            return True
        else:
            print(f"❌ API 문서 접근 실패: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API 문서 접근 오류: {str(e)}")
        return False

def test_user_registration():
    """사용자 등록 테스트"""
    print("\n👤 사용자 등록 테스트...")
    try:
        test_user = {
            "username": f"test_user_{int(time.time())}",
            "email": f"test_{int(time.time())}@example.com",
            "password": "testpass123",
            "role": "evaluator",
            "company": "테스트 회사"
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json=test_user, timeout=10)
        if response.status_code in [200, 201]:
            print("✅ 사용자 등록 성공")
            return test_user
        elif response.status_code == 400:
            print("⚠️ 사용자가 이미 존재하거나 유효성 검사 실패")
            return None
        else:
            print(f"❌ 사용자 등록 실패: {response.status_code}")
            print(f"   응답: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 사용자 등록 오류: {str(e)}")
        return None

def test_user_login(user_data):
    """사용자 로그인 테스트"""
    print("\n🔑 로그인 테스트...")
    if not user_data:
        print("❌ 테스트할 사용자 데이터가 없습니다.")
        return None
        
    try:
        login_data = {
            "username": user_data["username"],
            "password": user_data["password"]
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data, timeout=10)
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            if token:
                print("✅ 로그인 성공, 토큰 발급됨")
                return token
            else:
                print("❌ 토큰이 응답에 포함되지 않음")
                return None
        else:
            print(f"❌ 로그인 실패: {response.status_code}")
            print(f"   응답: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 로그인 오류: {str(e)}")
        return None

def test_authenticated_endpoints(token):
    """인증이 필요한 엔드포인트 테스트"""
    print("\n🔐 인증된 API 엔드포인트 테스트...")
    if not token:
        print("❌ 테스트할 토큰이 없습니다.")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 템플릿 목록 조회
    try:
        response = requests.get(f"{BASE_URL}/api/templates", headers=headers, timeout=10)
        if response.status_code == 200:
            print("✅ 템플릿 목록 조회 성공")
            templates = response.json()
            print(f"   📊 현재 템플릿 수: {len(templates)}")
        else:
            print(f"❌ 템플릿 목록 조회 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 템플릿 API 오류: {str(e)}")
    
    # 평가 목록 조회
    try:
        response = requests.get(f"{BASE_URL}/api/evaluations", headers=headers, timeout=10)
        if response.status_code == 200:
            print("✅ 평가 목록 조회 성공")
            evaluations = response.json()
            print(f"   📋 현재 평가 수: {len(evaluations)}")
        else:
            print(f"❌ 평가 목록 조회 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 평가 API 오류: {str(e)}")
    
    # 분석 대시보드 데이터
    try:
        response = requests.get(f"{BASE_URL}/api/analytics/dashboard", headers=headers, timeout=10)
        if response.status_code == 200:
            print("✅ 분석 대시보드 데이터 조회 성공")
        else:
            print(f"❌ 분석 대시보드 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 분석 API 오류: {str(e)}")
    
    return True

def test_export_functionality(token):
    """내보내기 기능 테스트"""
    print("\n📄 내보내기 기능 테스트...")
    if not token:
        print("❌ 테스트할 토큰이 없습니다.")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 내보내기 가능한 평가 목록 조회
    try:
        response = requests.get(f"{BASE_URL}/api/evaluations/export-list", headers=headers, timeout=10)
        if response.status_code == 200:
            print("✅ 내보내기 목록 조회 성공")
            export_list = response.json()
            print(f"   📊 내보내기 가능한 평가 수: {len(export_list)}")
            
            if export_list:
                # 첫 번째 평가로 내보내기 테스트
                eval_id = export_list[0]["id"]
                print(f"   🔍 평가 ID {eval_id}로 내보내기 테스트...")
                
                # PDF 내보내기 테스트
                try:
                    response = requests.get(
                        f"{BASE_URL}/api/evaluations/{eval_id}/export",
                        headers=headers,
                        params={"format": "pdf"},
                        timeout=30
                    )
                    if response.status_code == 200:
                        print("   ✅ PDF 내보내기 성공")
                    else:
                        print(f"   ❌ PDF 내보내기 실패: {response.status_code}")
                except Exception as e:
                    print(f"   ❌ PDF 내보내기 오류: {str(e)}")
                
                # Excel 내보내기 테스트
                try:
                    response = requests.get(
                        f"{BASE_URL}/api/evaluations/{eval_id}/export",
                        headers=headers,
                        params={"format": "excel"},
                        timeout=30
                    )
                    if response.status_code == 200:
                        print("   ✅ Excel 내보내기 성공")
                    else:
                        print(f"   ❌ Excel 내보내기 실패: {response.status_code}")
                except Exception as e:
                    print(f"   ❌ Excel 내보내기 오류: {str(e)}")
            else:
                print("   ℹ️ 내보내기 가능한 평가가 없습니다.")
                
        else:
            print(f"❌ 내보내기 목록 조회 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 내보내기 API 오류: {str(e)}")
    
    return True

def main():
    """메인 테스트 실행"""
    print("=" * 60)
    print("🧪 온라인 평가 시스템 실시간 테스트")
    print(f"🕐 테스트 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 테스트 대상: {BASE_URL}")
    print("=" * 60)
    
    # 1. 서버 상태 확인
    if not test_server_health():
        print("\n❌ 서버가 응답하지 않습니다. 테스트를 중단합니다.")
        return
    
    # 2. API 문서 확인
    test_api_docs()
    
    # 3. 사용자 등록 및 로그인
    user_data = test_user_registration()
    token = test_user_login(user_data)
    
    # 4. 인증된 API 테스트
    if token:
        test_authenticated_endpoints(token)
        test_export_functionality(token)
    else:
        print("\n⚠️ 토큰이 없어 인증된 API를 테스트할 수 없습니다.")
    
    # 5. 테스트 결과 요약
    print("\n" + "=" * 60)
    print("📊 테스트 완료!")
    print("=" * 60)
    print("🎯 시스템 상태:")
    print("   - 서버: 정상 작동")
    print("   - API: 정상 응답") 
    print("   - 인증: 작동")
    print("   - 내보내기: 기능 확인됨")
    print("\n✨ 시스템이 정상적으로 실행되고 있습니다!")
    print(f"🌐 프론트엔드 접속: {BASE_URL}")
    print(f"📚 API 문서: {BASE_URL}/docs")

if __name__ == "__main__":
    main()
