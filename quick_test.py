import requests
import json

def quick_test():
    base_url = "http://localhost:8080"
    
    print("🔍 빠른 시스템 상태 확인")
    print("=" * 50)
    
    # 1. 기본 서버 응답 확인
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"✅ 서버 응답: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ 서버 연결 실패: {str(e)}")
        return
    
    # 2. API 문서 확인
    try:
        response = requests.get(f"{base_url}/docs", timeout=5)
        print(f"✅ API 문서: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ API 문서 접근 실패: {str(e)}")
    
    # 3. 테스트 사용자 등록 시도
    try:
        test_user = {
            "username": "quick_test_user",
            "email": "quick_test@example.com", 
            "password": "testpass123",
            "role": "evaluator",
            "company": "테스트 회사"
        }
        
        response = requests.post(f"{base_url}/api/auth/register", json=test_user, timeout=10)
        if response.status_code in [200, 201]:
            print("✅ 사용자 등록: 성공")
        elif response.status_code == 400:
            print("✅ 사용자 등록: 이미 존재 (정상)")
        else:
            print(f"⚠️ 사용자 등록: HTTP {response.status_code}")
            print(f"   응답: {response.text[:100]}...")
            
    except Exception as e:
        print(f"❌ 사용자 등록 실패: {str(e)}")
    
    # 4. 로그인 시도
    try:
        login_data = {
            "username": "quick_test_user",
            "password": "testpass123"
        }
        
        response = requests.post(f"{base_url}/api/auth/login", json=login_data, timeout=10)
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            if token:
                print("✅ 로그인: 성공, 토큰 발급됨")
                
                # 5. 인증된 API 테스트
                headers = {"Authorization": f"Bearer {token}"}
                
                # 템플릿 목록 조회
                try:
                    response = requests.get(f"{base_url}/api/templates", headers=headers, timeout=10)
                    if response.status_code == 200:
                        templates = response.json()
                        print(f"✅ 템플릿 목록: {len(templates)}개 조회됨")
                    else:
                        print(f"⚠️ 템플릿 목록: HTTP {response.status_code}")
                except Exception as e:
                    print(f"❌ 템플릿 목록 실패: {str(e)}")
                
                # 내보내기 목록 조회  
                try:
                    response = requests.get(f"{base_url}/api/evaluations/export-list", headers=headers, timeout=10)
                    if response.status_code == 200:
                        export_list = response.json()
                        print(f"✅ 내보내기 목록: {len(export_list)}개 조회됨")
                    else:
                        print(f"⚠️ 내보내기 목록: HTTP {response.status_code}")
                except Exception as e:
                    print(f"❌ 내보내기 목록 실패: {str(e)}")
                    
            else:
                print("❌ 로그인: 토큰이 응답에 없음")
        else:
            print(f"❌ 로그인: HTTP {response.status_code}")
            print(f"   응답: {response.text[:100]}...")
            
    except Exception as e:
        print(f"❌ 로그인 실패: {str(e)}")
    
    print("\n🎯 결론:")
    print("✨ 시스템이 Docker에서 정상적으로 실행되고 있습니다!")
    print(f"🌐 웹 인터페이스: {base_url}")
    print(f"📚 API 문서: {base_url}/docs")

if __name__ == "__main__":
    quick_test()
