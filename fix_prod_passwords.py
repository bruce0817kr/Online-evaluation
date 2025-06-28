#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Production 데이터베이스 비밀번호 수정 스크립트
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext

# 비밀번호 해시 컨텍스트 (백엔드와 정확히 동일)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

async def fix_production_passwords():
    """Production 데이터베이스의 비밀번호를 올바르게 수정"""
    
    print("🔧 Production 데이터베이스 비밀번호 수정")
    print("=" * 60)
    
    try:
        # Production 데이터베이스 연결
        prod_url = 'mongodb://admin:password123@mongodb-prod:27017/online_evaluation_prod?authSource=admin'
        client = AsyncIOMotorClient(prod_url, serverSelectionTimeoutMS=5000)
        await client.admin.command('ping')
        db = client['online_evaluation_prod']
        print("✅ Production DB 연결 성공")
        
        # 수정할 계정들 (테스트에서 기대하는 정확한 계정 정보)
        accounts_to_fix = [
            {"login_id": "admin", "password": "admin123", "user_name": "시스템 관리자", "role": "admin"},
            {"login_id": "secretary", "password": "secretary123", "user_name": "간사", "role": "secretary"},
            {"login_id": "evaluator", "password": "evaluator123", "user_name": "평가위원", "role": "evaluator"},
            {"login_id": "evaluator01", "password": "evaluator123", "user_name": "평가위원01", "role": "evaluator"}
        ]
        
        fixed_count = 0
        
        for account in accounts_to_fix:
            try:
                login_id = account["login_id"]
                password = account["password"]
                
                # 기존 사용자 확인
                existing_user = await db.users.find_one({"login_id": login_id})
                
                if existing_user:
                    # 새 비밀번호 해시 생성
                    new_password_hash = pwd_context.hash(password)
                    
                    # 사용자 정보 업데이트 (비밀번호 해시 + 기본 정보)
                    update_data = {
                        "password_hash": new_password_hash,
                        "is_active": True,
                        "user_name": account["user_name"],
                        "role": account["role"]
                    }
                    
                    # 이메일 설정 (없으면 기본값)
                    if not existing_user.get("email"):
                        update_data["email"] = f"{login_id}@evaluation.com"
                    
                    await db.users.update_one(
                        {"login_id": login_id},
                        {"$set": update_data}
                    )
                    
                    # 비밀번호 검증
                    verification_user = await db.users.find_one({"login_id": login_id})
                    stored_hash = verification_user.get('password_hash')
                    
                    if stored_hash and pwd_context.verify(password, stored_hash):
                        print(f"✅ {login_id}: 비밀번호 해시 수정 및 검증 성공")
                        fixed_count += 1
                    else:
                        print(f"❌ {login_id}: 비밀번호 검증 실패")
                        
                else:
                    print(f"❌ {login_id}: 사용자 없음")
                    
            except Exception as e:
                print(f"❌ {account['login_id']}: 수정 오류 - {e}")
        
        print(f"\n📊 수정 결과: {fixed_count}/{len(accounts_to_fix)}개 계정 수정 완료")
        
        # 최종 전체 검증
        print(f"\n🧪 최종 비밀번호 검증:")
        all_verified = True
        
        for account in accounts_to_fix:
            login_id = account["login_id"]
            password = account["password"]
            
            user = await db.users.find_one({"login_id": login_id})
            if user and user.get('is_active', False):
                stored_hash = user.get('password_hash')
                if stored_hash:
                    try:
                        is_valid = pwd_context.verify(password, stored_hash)
                        if is_valid:
                            print(f"   ✅ {login_id}: 로그인 가능")
                        else:
                            print(f"   ❌ {login_id}: 비밀번호 불일치")
                            all_verified = False
                    except Exception as e:
                        print(f"   ❌ {login_id}: 검증 오류 - {e}")
                        all_verified = False
                else:
                    print(f"   ❌ {login_id}: 비밀번호 해시 없음")
                    all_verified = False
            else:
                print(f"   ❌ {login_id}: 없음 또는 비활성")
                all_verified = False
        
        client.close()
        
        if all_verified:
            print(f"\n🎉 모든 계정 검증 완료! 이제 로그인이 가능합니다.")
            print(f"\n📝 테스트 가능한 계정:")
            for account in accounts_to_fix:
                print(f"   - {account['login_id']} / {account['password']} ({account['user_name']})")
        else:
            print(f"\n⚠️ 일부 계정에 여전히 문제가 있습니다.")
        
        return all_verified
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("🔧 Production 환경 비밀번호 수정")
    print("🎯 목표: 모든 테스트 계정의 비밀번호를 올바르게 설정")
    print("=" * 60)
    
    success = await fix_production_passwords()
    
    if success:
        print("\n✨ 비밀번호 수정이 성공적으로 완료되었습니다!")
        print("🧪 이제 모든 테스트 계정으로 로그인할 수 있습니다.")
    else:
        print("\n⚠️ 비밀번호 수정 중 문제가 발생했습니다.")

if __name__ == "__main__":
    asyncio.run(main())