#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
비밀번호 해시 생성 스크립트
"""

from passlib.context import CryptContext

# 비밀번호 해시 컨텍스트
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    """비밀번호를 해시화합니다."""
    return pwd_context.hash(password)

# 테스트 비밀번호들
passwords = {
    "admin123": get_password_hash("admin123"),
    "secretary123": get_password_hash("secretary123"),
    "evaluator123": get_password_hash("evaluator123")
}

print("=== 비밀번호 해시 결과 ===")
for password, hash_value in passwords.items():
    print(f"{password}: {hash_value}")
