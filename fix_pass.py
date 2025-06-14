import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import bcrypt
from datetime import datetime
import os

async def fix_passwords():
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = client[os.environ['DB_NAME']]
    
    # 기본 사용자들의 패스워드 업데이트
    test_users = [
        ('admin', 'admin123'),
        ('secretary', 'secretary123'), 
        ('evaluator', 'evaluator123')
    ]
    
    for login_id, password in test_users:
        # bcrypt로 해시 생성
        salt = bcrypt.gensalt(rounds=12)
        new_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
        
        result = await db.users.update_one(
            {'login_id': login_id},
            {'$set': {'password_hash': new_hash}}
        )
        print(f'{login_id}: {result.modified_count} 업데이트됨')
    
    client.close()

asyncio.run(fix_passwords())
print('패스워드 해시 업데이트 완료')
