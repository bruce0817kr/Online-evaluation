#!/usr/bin/env python3
import requests
import json

def test_auth_me():
    base_url = "http://localhost:8080"
    
    print("🔍 Testing /auth/me endpoint...")
    print("=" * 50)
    
    # Step 1: Login to get token
    print("\n1. Getting fresh token...")
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    response = requests.post(f"{base_url}/api/auth/login", data=login_data)
    print(f"Login Status: {response.status_code}")
    
    if response.status_code == 200:
        login_result = response.json()
        token = login_result.get('access_token')
        print(f"✅ Token received: {token[:30]}...")
        
        # Step 2: Test /auth/me endpoint
        print("\n2. Testing /auth/me...")
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(f"{base_url}/api/auth/me", headers=headers)
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ /auth/me endpoint working perfectly!")
            print(f"User data: {json.dumps(user_data, indent=2, ensure_ascii=False)}")
            
            # Verify response structure
            expected_fields = ['id', 'login_id', 'user_name', 'email', 'role', 'created_at', 'is_active']
            missing_fields = [field for field in expected_fields if field not in user_data]
            
            if missing_fields:
                print(f"⚠️ Missing fields: {missing_fields}")
            else:
                print("✅ All expected fields present in response")
                
            return True
        else:
            print(f"❌ /auth/me endpoint failed!")
            print(f"Response: {response.text}")
            return False
    else:
        print(f"❌ Login failed!")
        print(f"Response: {response.text}")
        return False

if __name__ == "__main__":
    success = test_auth_me()
    if success:
        print("\n🎉 SUCCESS: /auth/me endpoint is working correctly!")
    else:
        print("\n❌ FAILED: /auth/me endpoint has issues")
