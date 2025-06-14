#!/usr/bin/env python3
"""
패스워드 해시 재생성 스크립트
기존 사용자들의 패스워드를 새로운 bcrypt 해시로 변환합니다.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
import logging

# 패스워드 컨텍스트 직접 정의
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

def get_password_hash(password: str) -> str:
    """패스워드 해시 생성"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """패스워드 검증"""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.debug(f"Failed to verify with passlib: {e}")
        try:
            import bcrypt
            if isinstance(plain_password, str):
                plain_password = plain_password.encode('utf-8')
            if isinstance(hashed_password, str):
                hashed_password = hashed_password.encode('utf-8')
            return bcrypt.checkpw(plain_password, hashed_password)
        except Exception as e2:
            logger.error(f"Password verification failed: {e2}")
            return False
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB 연결 설정
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "evaluation_system")

async def rehash_user_passwords():
    """모든 사용자의 패스워드를 새로운 해시로 변환"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    try:
        # 기본 사용자 패스워드 정의
        default_passwords = {
            "admin": "admin123",
            "secretary": "secretary123", 
            "evaluator": "evaluator123"
        }
        
        users_collection = db.users
        users = await users_collection.find({}).to_list(None)
        
        logger.info(f"총 {len(users)}명의 사용자를 찾았습니다.")
        
        updated_count = 0
        for user in users:
            login_id = user.get("login_id", "")
            
            # 사용자 역할에 따른 기본 패스워드 할당
            if login_id in default_passwords:
                new_password = default_passwords[login_id]
            elif user.get("role") == "admin":
                new_password = "admin123"
            elif user.get("role") == "secretary":
                new_password = "secretary123"
            elif user.get("role") == "evaluator":
                new_password = "evaluator123"
            else:
                # 기본 패스워드
                new_password = "password123"
            
            # 새로운 해시 생성
            new_hash = get_password_hash(new_password)
            
            # 데이터베이스 업데이트
            result = await users_collection.update_one(
                {"_id": user["_id"]},
                {"$set": {"password_hash": new_hash}}
            )
            
            if result.modified_count > 0:
                updated_count += 1
                logger.info(f"사용자 {login_id} 패스워드 해시 업데이트 완료 (패스워드: {new_password})")
            else:
                logger.warning(f"사용자 {login_id} 패스워드 해시 업데이트 실패")
        
        logger.info(f"총 {updated_count}명의 사용자 패스워드 해시가 업데이트되었습니다.")
        
        # 테스트용 사용자 생성 (없는 경우)
        await create_test_users_if_needed(users_collection)
        
    except Exception as e:
        logger.error(f"패스워드 재해시 중 오류 발생: {e}")
        raise
    finally:
        client.close()

async def create_test_users_if_needed(users_collection):
    """필요한 테스트 사용자가 없는 경우 생성"""
    from datetime import datetime
    
    test_users = [
        {
            "login_id": "admin",
            "password": "admin123",
            "email": "admin@example.com",
            "user_name": "관리자",
            "role": "admin",
            "phone": "010-1234-5678",
            "is_active": True
        },
        {
            "login_id": "secretary",
            "password": "secretary123", 
            "email": "secretary@example.com",
            "user_name": "간사",
            "role": "secretary",
            "phone": "010-1234-5679",
            "is_active": True
        },
        {
            "login_id": "evaluator",
            "password": "evaluator123",
            "email": "evaluator@example.com", 
            "user_name": "평가자",
            "role": "evaluator",
            "phone": "010-1234-5680",
            "is_active": True
        }
    ]
    
    for user_data in test_users:
        existing_user = await users_collection.find_one({"login_id": user_data["login_id"]})
        
        if not existing_user:
            # 패스워드 해시 생성
            password_hash = get_password_hash(user_data.pop("password"))
            
            user_doc = {
                **user_data,
                "password_hash": password_hash,
                "created_at": datetime.utcnow(),
                "last_login": None
            }
            
            result = await users_collection.insert_one(user_doc)
            if result.inserted_id:
                logger.info(f"테스트 사용자 {user_data['login_id']} 생성 완료")
            else:
                logger.error(f"테스트 사용자 {user_data['login_id']} 생성 실패")

async def verify_passwords():
    """패스워드 해시가 올바르게 작동하는지 확인"""
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    try:
        users_collection = db.users
        test_cases = [
            ("admin", "admin123"),
            ("secretary", "secretary123"),
            ("evaluator", "evaluator123")
        ]
        
        logger.info("패스워드 검증 테스트 시작...")
        
        for login_id, password in test_cases:
            user = await users_collection.find_one({"login_id": login_id})
            if user:
                is_valid = verify_password(password, user["password_hash"])
                status = "✓ 성공" if is_valid else "✗ 실패"
                logger.info(f"{login_id} / {password}: {status}")
            else:
                logger.warning(f"사용자 {login_id}를 찾을 수 없습니다.")
                
    except Exception as e:
        logger.error(f"패스워드 검증 중 오류 발생: {e}")
        raise
    finally:
        client.close()

async def main():
    """메인 실행 함수"""
    if len(sys.argv) > 1 and sys.argv[1] == "verify":
        await verify_passwords()
    else:
        await rehash_user_passwords()
        print("\n패스워드 재해시 완료. 검증을 위해 다음 명령어를 실행하세요:")
        print("python scripts/fix_password_hashes.py verify")

if __name__ == "__main__":
    asyncio.run(main())
