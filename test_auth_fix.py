#!/usr/bin/env python3
import requests
import json

def test_auth_fix():
    base_url = "http://localhost:8080"
    
    print("🔍 Testing Authentication Fix...")
    print("=" * 50)
      # Test 1: Login to get token
    print("\n1. Testing Admin Login...")
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    response = requests.post(f"{base_url}/api/auth/login", data=login_data)
    print(f"Login Status: {response.status_code}")
    
    if response.status_code == 200:
        login_result = response.json()
        token = login_result.get('access_token')
        print(f"✅ Login successful, token received: {token[:20]}...")
        
        # Test 2: Use token to get current user
        print("\n2. Testing Get Current User...")
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(f"{base_url}/api/auth/me", headers=headers)
        print(f"Get User Status: {response.status_code}")
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ Authentication fix successful!")
            print(f"User data: {json.dumps(user_data, indent=2)}")
            return True
        else:
            print(f"❌ Authentication still failing!")
            print(f"Response: {response.text}")
            return False
    else:
        print(f"❌ Login failed!")
        print(f"Response: {response.text}")
        return False

if __name__ == "__main__":
    success = test_auth_fix()
    if success:
        print("\n🎉 Authentication fix verified successfully!")
    else:
        print("\n💥 Authentication fix still needs work!")
