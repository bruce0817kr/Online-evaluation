#!/usr/bin/env python3
"""
간단한 로그인 API 테스트
"""

import requests

# Test the login API with correct format
data = {
    "username": "admin",
    "password": "admin123"
}

# Try form data format (OAuth2PasswordRequestForm)
response = requests.post(
    "http://localhost:8080/api/auth/login",
    data=data,  # Use data instead of json for form data
    headers={"Content-Type": "application/x-www-form-urlencoded"}
)

print(f"Status: {response.status_code}")
print(f"Response: {response.text}")

if response.status_code == 200:
    print("✅ Login successful with form data format!")
else:
    print("❌ Login failed with form data format")
    
    # Try JSON format as backup
    response2 = requests.post(
        "http://localhost:8080/api/auth/login",
        json={"user_name": "admin", "password": "admin123"}
    )
    print(f"\nJSON format Status: {response2.status_code}")
    print(f"JSON format Response: {response2.text}")
