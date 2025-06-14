#!/usr/bin/env python3
"""
로그인 테스트 스크립트
현재 로그인 문제를 확인하고 수정된 코드를 테스트합니다.
"""

import requests
import json
import sys

def test_login():
    """로그인 테스트"""
    url = "http://localhost:8080/api/auth/login"
      # 테스트할 사용자 계정들
    test_accounts = [
        {"username": "admin", "password": "admin123"},
        {"username": "secretary01", "password": "secretary123"},
        {"username": "evaluator01", "password": "evaluator123"}
    ]
    
    print("🔐 로그인 테스트 시작...")
    print("=" * 50)
    
    for account in test_accounts:
        print(f"\n📝 테스트 중: {account['username']}")
        
        # OAuth2 형식으로 데이터 준비
        form_data = {
            "username": account["username"],
            "password": account["password"]
        }
        
        try:
            response = requests.post(
                url,
                data=form_data,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                timeout=10
            )
            
            print(f"   📊 상태 코드: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ 로그인 성공!")
                print(f"   👤 사용자: {data.get('user', {}).get('user_name', 'N/A')}")
                print(f"   🏷️  역할: {data.get('user', {}).get('role', 'N/A')}")
                print(f"   🔑 토큰: {data.get('access_token', 'N/A')[:20]}...")
            else:
                print(f"   ❌ 로그인 실패!")
                try:
                    error_data = response.json()
                    print(f"   📋 오류: {error_data.get('detail', '알 수 없는 오류')}")
                except:
                    print(f"   📋 응답: {response.text[:100]}")
        
        except requests.exceptions.ConnectionError:
            print(f"   🔌 연결 오류: 백엔드 서버에 연결할 수 없습니다 (http://localhost:8080)")
            return False
        except requests.exceptions.Timeout:
            print(f"   ⏰ 타임아웃: 서버 응답이 느립니다")
        except Exception as e:
            print(f"   ⚠️  예상치 못한 오류: {e}")
    
    return True

def test_backend_health():
    """백엔드 헬스 체크"""
    health_urls = [
        "http://localhost:8080/docs",
        "http://localhost:8080/health",
        "http://localhost:8080/api"
    ]
    
    print("\n🏥 백엔드 헬스 체크...")
    print("=" * 30)
    
    for url in health_urls:
        try:
            response = requests.get(url, timeout=5)
            status = "✅ 정상" if response.status_code == 200 else f"⚠️ {response.status_code}"
            print(f"   {url}: {status}")
        except requests.exceptions.ConnectionError:
            print(f"   {url}: ❌ 연결 실패")
        except Exception as e:
            print(f"   {url}: ⚠️ 오류 - {e}")

def main():
    """메인 실행 함수"""
    print("🚀 온라인 평가 시스템 로그인 테스트")
    print("=" * 60)
    
    # 백엔드 헬스 체크
    test_backend_health()
    
    # 로그인 테스트
    success = test_login()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 테스트 완료! 결과를 확인해주세요.")
        print("\n💡 문제가 발생한 경우:")
        print("   1. Docker 컨테이너가 실행 중인지 확인: docker-compose ps")
        print("   2. 백엔드 로그 확인: docker-compose logs backend")
        print("   3. MongoDB 연결 상태 확인: docker-compose logs mongodb")
    else:
        print("❌ 테스트 중 연결 문제가 발생했습니다.")
        print("   Docker 컨테이너를 확인해주세요: docker-compose ps")

if __name__ == "__main__":
    main()
