#!/usr/bin/env python3
"""
패스워드 해시 수정 스크립트
올바른 bcrypt 해시로 사용자 비밀번호를 업데이트합니다.
"""

from passlib.context import CryptContext
import pymongo
import os
from datetime import datetime

# 패스워드 컨텍스트 설정 (서버와 동일하게)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def generate_correct_hash(password):
    """올바른 bcrypt 해시 생성"""
    return pwd_context.hash(password)

def verify_hash(password, hash_str):
    """해시 검증"""
    return pwd_context.verify(password, hash_str)

# 테스트 사용자 정보
users_to_fix = [
    {"login_id": "admin", "password": "admin123"},
    {"login_id": "secretary01", "password": "secretary123"},
    {"login_id": "secretary02", "password": "secretary123"},
    {"login_id": "evaluator01", "password": "evaluator123"},
    {"login_id": "evaluator02", "password": "evaluator123"},
    {"login_id": "evaluator03", "password": "evaluator123"},
    {"login_id": "evaluator04", "password": "evaluator123"},
    {"login_id": "evaluator05", "password": "evaluator123"},
]

print("🔧 올바른 패스워드 해시 생성 중...")

# 각 사용자에 대해 올바른 해시 생성
for user in users_to_fix:
    correct_hash = generate_correct_hash(user["password"])
    print(f"사용자: {user['login_id']}")
    print(f"비밀번호: {user['password']}")
    print(f"해시 길이: {len(correct_hash)}")
    print(f"해시: {correct_hash}")
    print(f"검증 결과: {verify_hash(user['password'], correct_hash)}")
    print("-" * 50)

# MongoDB 연결 및 업데이트
try:
    # MongoDB 연결
    client = pymongo.MongoClient("mongodb://admin:password123@localhost:27017/online_evaluation?authSource=admin")
    db = client.online_evaluation
    
    print("\n🔄 MongoDB에서 패스워드 해시 업데이트 중...")
    
    updated_count = 0
    for user in users_to_fix:
        correct_hash = generate_correct_hash(user["password"])
        
        result = db.users.update_one(
            {"login_id": user["login_id"]},
            {
                "$set": {
                    "password_hash": correct_hash,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count > 0:
            print(f"✅ {user['login_id']} 패스워드 해시 업데이트 완료")
            updated_count += 1
        else:
            print(f"❌ {user['login_id']} 업데이트 실패 (사용자를 찾을 수 없음)")
    
    print(f"\n✅ 총 {updated_count}명의 사용자 패스워드 해시가 업데이트되었습니다.")
    
    # 업데이트 검증
    print("\n🔍 업데이트 검증 중...")
    for user in users_to_fix:
        user_data = db.users.find_one({"login_id": user["login_id"]})
        if user_data:
            verify_result = verify_hash(user["password"], user_data["password_hash"])
            print(f"{user['login_id']}: {verify_result}")
    
    client.close()
    
except Exception as e:
    print(f"❌ 오류 발생: {e}")
