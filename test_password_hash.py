#!/usr/bin/env python3
"""
비밀번호 해시 테스트
"""

import bcrypt

# admin123 비밀번호를 해시화
password = "admin123"
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12))
print(f"Password: {password}")
print(f"Hash: {hashed.decode('utf-8')}")

# 검증 테스트
test_passwords = [
    "admin123",
    "Admin123", 
    "password"
]

for test_pwd in test_passwords:
    is_valid = bcrypt.checkpw(test_pwd.encode('utf-8'), hashed)
    print(f"Test '{test_pwd}': {'✅ Valid' if is_valid else '❌ Invalid'}")