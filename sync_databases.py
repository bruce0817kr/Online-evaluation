#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
데이터베이스 동기화 스크립트
online_evaluation에서 online_evaluation_prod로 사용자 복사
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def sync_users():
    """사용자를 online_evaluation에서 online_evaluation_prod로 동기화"""
    
    print("🔄 데이터베이스 동기화 시작")
    print("📂 Source: online_evaluation")
    print("📂 Target: online_evaluation_prod")
    print("=" * 60)
    
    try:
        # 소스 데이터베이스 연결 (online_evaluation)
        source_url = 'mongodb://admin:password123@mongodb-prod:27017/online_evaluation?authSource=admin'
        source_client = AsyncIOMotorClient(source_url, serverSelectionTimeoutMS=5000)
        await source_client.admin.command('ping')
        source_db = source_client['online_evaluation']
        print("✅ Source DB 연결 성공")
        
        # 타겟 데이터베이스 연결 (online_evaluation_prod) 
        target_url = 'mongodb://admin:password123@mongodb-prod:27017/online_evaluation_prod?authSource=admin'
        target_client = AsyncIOMotorClient(target_url, serverSelectionTimeoutMS=5000)
        await target_client.admin.command('ping')
        target_db = target_client['online_evaluation_prod']
        print("✅ Target DB 연결 성공")
        
        # 소스에서 필요한 사용자들 조회
        required_users = ["admin", "secretary", "evaluator", "evaluator01"]
        
        print(f"\n📋 필요한 사용자: {', '.join(required_users)}")
        
        copied_count = 0
        updated_count = 0
        
        for login_id in required_users:
            try:
                # 소스에서 사용자 조회
                source_user = await source_db.users.find_one({"login_id": login_id})
                
                if not source_user:
                    print(f"❌ {login_id}: 소스 DB에 없음")
                    continue
                
                # 타겟에서 기존 사용자 확인
                existing_user = await target_db.users.find_one({"login_id": login_id})
                
                if existing_user:
                    # 기존 사용자 업데이트
                    await target_db.users.replace_one(
                        {"login_id": login_id},
                        source_user
                    )
                    updated_count += 1
                    print(f"🔄 {login_id}: 업데이트 완료")
                else:
                    # 새 사용자 삽입
                    await target_db.users.insert_one(source_user)
                    copied_count += 1
                    print(f"✅ {login_id}: 복사 완료")
                    
            except Exception as e:
                print(f"❌ {login_id}: 오류 - {e}")
        
        print(f"\n📊 동기화 결과:")
        print(f"   🆕 신규 복사: {copied_count}명")
        print(f"   🔄 업데이트: {updated_count}명")
        
        # 최종 검증
        print(f"\n🧪 최종 검증:")
        for login_id in required_users:
            user = await target_db.users.find_one({"login_id": login_id})
            if user and user.get('is_active', False):
                print(f"   ✅ {login_id}: 활성 상태")
            else:
                print(f"   ❌ {login_id}: 없음 또는 비활성")
        
        # 연결 종료
        source_client.close()
        target_client.close()
        
        print(f"\n🎉 데이터베이스 동기화 완료!")
        return True
        
    except Exception as e:
        print(f"❌ 동기화 오류: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("🔄 MongoDB 데이터베이스 사용자 동기화")
    print("🎯 online_evaluation → online_evaluation_prod")
    print("=" * 60)
    
    success = await sync_users()
    
    if success:
        print("\n✨ 동기화가 성공적으로 완료되었습니다!")
        print("🧪 이제 모든 테스트 계정이 production DB에서 작동할 것입니다.")
    else:
        print("\n⚠️ 동기화 중 문제가 발생했습니다.")

if __name__ == "__main__":
    asyncio.run(main())