#!/usr/bin/env python3
"""비밀번호 해시 생성 도구"""

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

passwords = {
    "admin123": pwd_context.hash("admin123"),
    "secretary123": pwd_context.hash("secretary123"), 
    "evaluator123": pwd_context.hash("evaluator123")
}

for password, hash_value in passwords.items():
    print(f"{password}: {hash_value}")
