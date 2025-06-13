#!/usr/bin/env python3
"""
온라인 평가 시스템 - 테스트 사용자 생성 스크립트
"""

import asyncio
import os
import argparse  # Add argparse
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from datetime import datetime

# 비밀번호 해싱 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def create_test_users(mongo_uri: str):  # Add mongo_uri argument
    """테스트 사용자 계정 생성"""

    # MongoDB 연결
    # mongo_url = "mongodb://admin:password123@mongodb:27017/evaluation_db?authSource=admin" # Replaced by argument
    client = AsyncIOMotorClient(mongo_uri)  # Use argument
    # Extract DB name from URI or use a default if not easily parsable
    # For simplicity, assuming the db name is part of the URI path and is 'evaluation_db'
    # A more robust solution would parse the URI properly.
    try:
        db_name = mongo_uri.split("/")[-1].split("?")[0]
        if not db_name:  # Handle cases where db_name might be empty if URI ends with /
            db_name = "evaluation_db"
    except:
        db_name = "evaluation_db"  # Fallback

    db = client[db_name]  # Use extracted or fallback db_name

    try:
        # 기존 사용자 삭제
        await db.users.delete_many({})
        print("🗑️ 기존 사용자 데이터 삭제 완료")

        # 테스트 사용자들
        test_users = [
            {
                "login_id": "admin",  # 변경: user_id -> login_id
                "user_name": "관리자",
                "password": "admin123",
                "role": "admin",
                "email": "admin@example.com",
                "phone": "010-1111-2222",
                "created_at": datetime.now(),
            },
            {
                "login_id": "secretary01",  # 변경: user_id -> login_id
                "user_name": "간사01",
                "password": "secretary123",
                "role": "secretary",
                "email": "secretary01@example.com",
                "phone": "010-2222-3333",
                "created_at": datetime.now(),
            },
            {
                "login_id": "evaluator01",  # 변경: user_id -> login_id
                "user_name": "평가위원01",
                "password": "evaluator123",
                "role": "evaluator",
                "email": "evaluator01@example.com",
                "phone": "010-3333-4444",
                "created_at": datetime.now(),
            },
        ]

        # 사용자 생성
        for user_data in test_users:
            # 비밀번호 해시화
            hashed_password = pwd_context.hash(user_data["password"])
            user_data["password_hash"] = hashed_password  # 변경: "hashed_password" -> "password_hash"
            del user_data["password"]  # 평문 비밀번호 제거

            # 데이터베이스에 삽입
            result = await db.users.insert_one(user_data)
            print(
                f"✅ 사용자 생성 완료: {user_data['login_id']} ({user_data['user_name']}) - {user_data['role']}" # 변경: user_id -> login_id
            )

        # 생성된 사용자 확인
        total_users = await db.users.count_documents({})
        print(f"\n📊 총 사용자 수: {total_users}")

        print("\n🎉 테스트 사용자 생성 완료!")
        print("\n📋 로그인 정보:")
        print("- 관리자: admin / admin123")
        print("- 간사: secretary01 / secretary123")
        print("- 평가위원: evaluator01 / evaluator123")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")

    finally:
        client.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create test users for the Online Evaluation System."
    )
    parser.add_argument(
        "mongo_uri",
        type=str,
        help="MongoDB connection URI (e.g., 'mongodb://admin:password123@localhost:27017/evaluation_db?authSource=admin')",
    )
    args = parser.parse_args()

    asyncio.run(create_test_users(args.mongo_uri))
