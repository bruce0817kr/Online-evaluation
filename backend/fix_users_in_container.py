import asyncio
import os
import uuid
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from datetime import datetime

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

async def fix_users():
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client.online_evaluation
    
    try:
        await db.users.delete_many({})
        print('기존 사용자 삭제 완료')
        
        users = [
            {
                'id': str(uuid.uuid4()), 
                'login_id': 'admin', 
                'user_name': '관리자', 
                'password': 'admin123', 
                'role': 'admin', 
                'email': 'admin@example.com', 
                'phone': '010-1111-2222', 
                'created_at': datetime.utcnow(), 
                'is_active': True
            },
            {
                'id': str(uuid.uuid4()), 
                'login_id': 'secretary01', 
                'user_name': '간사01', 
                'password': 'secretary123', 
                'role': 'secretary', 
                'email': 'secretary01@example.com', 
                'phone': '010-2222-3333', 
                'created_at': datetime.utcnow(), 
                'is_active': True
            },
            {
                'id': str(uuid.uuid4()), 
                'login_id': 'evaluator01', 
                'user_name': '평가위원01', 
                'password': 'evaluator123', 
                'role': 'evaluator', 
                'email': 'evaluator01@example.com', 
                'phone': '010-3333-4444', 
                'created_at': datetime.utcnow(), 
                'is_active': True
            }
        ]
        
        for user in users:
            user['password_hash'] = pwd_context.hash(user['password'])
            del user['password']
            await db.users.insert_one(user)
            print(f"사용자 생성: {user['login_id']} - {user['user_name']}")
        
        print(f"총 사용자 수: {await db.users.count_documents({})}")
        
        # 검증
        users_check = await db.users.find({}).to_list(None)
        for user in users_check:
            has_hash = 'password_hash' in user
            print(f"- {user['login_id']}: password_hash 존재 = {has_hash}")
        
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(fix_users())
