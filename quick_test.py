import requests
import json

BACKEND_URL = "http://localhost:8080"

def create_admin_user():
    try:
        print("시스템 초기화 시도 중...")
        response = requests.post(
            f"{BACKEND_URL}/api/init",
            headers={'Content-Type': 'application/json'},
            json={},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 시스템 초기화 성공! {data.get('message', '')}")
            return True
        else:
            print(f"❌ 시스템 초기화 실패 - Status: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   응답: {error_data}")
            except:
                pass
            return False
            
    except Exception as e:
        print(f"❌ API 호출 실패: {str(e)}")
        return False

def test_login():
    try:
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        print("로그인 테스트 중...")
        response = requests.post(
            f"{BACKEND_URL}/api/auth/login",
            data=login_data,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            user = data.get('user', {})
            print(f"✅ 로그인 성공! 사용자: {user.get('user_name', 'N/A')}")
            return True
        else:
            print(f"❌ 로그인 실패 - Status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 로그인 테스트 실패: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 사용자 생성 및 로그인 테스트")
    print("=" * 40)
    
    user_created = create_admin_user()
    
    if user_created:
        login_success = test_login()
        if login_success:
            print("\n🎉 모든 테스트 성공!")
        else:
            print("\n⚠️ 로그인 실패")
    else:
        print("\n❌ 사용자 생성 실패")
