#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
인증 수정사항 테스트 스크립트
"""

import asyncio
import aiohttp
import json
import time

BACKEND_URL = "http://localhost:8019"

# 테스트 계정들
TEST_ACCOUNTS = [
    {"username": "admin", "password": "admin123", "role": "관리자"},
    {"username": "secretary", "password": "secretary123", "role": "간사"},
    {"username": "evaluator", "password": "evaluator123", "role": "평가위원"},
    {"username": "evaluator01", "password": "evaluator123", "role": "평가위원01"}
]

async def test_login(session, account):
    """로그인 테스트"""
    login_url = f"{BACKEND_URL}/api/auth/login"
    
    login_data = {
        "login_id": account["username"],
        "password": account["password"]
    }
    
    try:
        print(f"🔐 로그인 시도: {account['username']} ({account['role']})")
        
        async with session.post(login_url, json=login_data) as response:
            if response.status == 200:
                result = await response.json()
                token = result.get("access_token")
                user_info = result.get("user", {})
                
                print(f"✅ 로그인 성공: {account['username']}")
                print(f"   - 사용자: {user_info.get('user_name', 'Unknown')}")
                print(f"   - 역할: {user_info.get('role', 'Unknown')}")
                print(f"   - 토큰 길이: {len(token) if token else 0}")
                
                return True, token
            else:
                error_text = await response.text()
                print(f"❌ 로그인 실패: {account['username']} - {response.status}")
                print(f"   오류: {error_text}")
                return False, None
                
    except Exception as e:
        print(f"❌ 로그인 예외: {account['username']} - {e}")
        return False, None

async def test_api_access(session, token, account):
    """인증이 필요한 API 엔드포인트 테스트"""
    if not token:
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 테스트할 엔드포인트들
    endpoints = [
        ("/api/auth/me", "프로필 조회"),
        ("/api/projects", "프로젝트 목록"),
        ("/api/users", "사용자 목록")
    ]
    
    print(f"🧪 API 접근 테스트: {account['username']}")
    
    success_count = 0
    for endpoint, description in endpoints:
        try:
            async with session.get(f"{BACKEND_URL}{endpoint}", headers=headers) as response:
                if response.status == 200:
                    print(f"   ✅ {description}: 성공")
                    success_count += 1
                elif response.status == 403:
                    print(f"   ⚠️ {description}: 권한 없음 (정상)")
                    success_count += 1  # 권한 없음도 인증은 성공한 것
                else:
                    error_text = await response.text()
                    print(f"   ❌ {description}: {response.status} - {error_text}")
        except Exception as e:
            print(f"   ❌ {description}: 예외 - {e}")
    
    return success_count == len(endpoints)

async def test_rate_limiting():
    """Rate limiting 테스트 - 빠른 연속 요청"""
    print("\n🚀 Rate Limiting 테스트 (연속 로그인 시도)")
    
    async with aiohttp.ClientSession() as session:
        login_url = f"{BACKEND_URL}/api/auth/login"
        login_data = {"login_id": "admin", "password": "admin123"}
        
        success_count = 0
        rate_limited_count = 0
        
        # 10번 연속 빠른 요청
        for i in range(10):
            try:
                async with session.post(login_url, json=login_data) as response:
                    if response.status == 200:
                        success_count += 1
                        print(f"   시도 {i+1}: ✅ 성공")
                    elif response.status == 429:
                        rate_limited_count += 1
                        print(f"   시도 {i+1}: ⚠️ Rate Limited (429)")
                    else:
                        print(f"   시도 {i+1}: ❌ 오류 ({response.status})")
                        
                # 짧은 지연
                await asyncio.sleep(0.1)
            except Exception as e:
                print(f"   시도 {i+1}: ❌ 예외 - {e}")
        
        print(f"   결과: 성공 {success_count}회, Rate Limited {rate_limited_count}회")
        
        if success_count >= 5:  # 최소 5번은 성공해야 함 (rate limiting 완화됨)
            print("   ✅ Rate Limiting이 완화되어 연속 요청이 가능합니다")
            return True
        else:
            print("   ❌ Rate Limiting이 여전히 너무 엄격합니다")
            return False

async def main():
    """메인 테스트 함수"""
    print("🧪 인증 시스템 수정사항 테스트")
    print("=" * 60)
    
    # 백엔드 서버 대기
    print("⏳ 백엔드 서버 재시작 대기...")
    await asyncio.sleep(10)  # 재시작 완료 대기
    
    async with aiohttp.ClientSession() as session:
        total_tests = len(TEST_ACCOUNTS)
        successful_logins = 0
        successful_api_access = 0
        
        print(f"\n🔐 로그인 테스트 ({total_tests}개 계정)")
        print("-" * 40)
        
        # 각 계정 로그인 테스트
        for account in TEST_ACCOUNTS:
            success, token = await test_login(session, account)
            
            if success:
                successful_logins += 1
                
                # API 접근 테스트
                api_success = await test_api_access(session, token, account)
                if api_success:
                    successful_api_access += 1
            
            print()  # 줄바꿈
            await asyncio.sleep(1)  # 각 테스트 간 지연
        
        # Rate limiting 테스트
        rate_limit_success = await test_rate_limiting()
    
    # 최종 결과
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60)
    print(f"로그인 성공률: {successful_logins}/{total_tests} ({successful_logins/total_tests*100:.1f}%)")
    print(f"API 접근 성공률: {successful_api_access}/{successful_logins} ({successful_api_access/successful_logins*100:.1f}% of successful logins)")
    print(f"Rate Limiting 완화: {'✅ 성공' if rate_limit_success else '❌ 실패'}")
    
    overall_success = (successful_logins == total_tests and 
                      successful_api_access == successful_logins and 
                      rate_limit_success)
    
    if overall_success:
        print("\n🎉 모든 테스트 통과! 인증 시스템이 정상적으로 수정되었습니다.")
        print("\n✅ 해결된 문제:")
        print("   - Rate limiting이 테스트 환경에서 완화됨")
        print("   - 모든 테스트 계정이 정상 로그인")
        print("   - API 엔드포인트 접근 가능")
        print("\n🚀 이제 모든 기능이 정상적으로 작동할 것입니다!")
    else:
        print("\n⚠️ 일부 테스트 실패. 추가 수정이 필요할 수 있습니다.")

if __name__ == "__main__":
    asyncio.run(main())