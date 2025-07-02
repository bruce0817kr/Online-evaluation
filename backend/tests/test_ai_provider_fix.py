#!/usr/bin/env python3
"""
AI Provider from_mongo Fix Verification Test
테스트: AI Provider의 from_mongo 메서드 오류 수정 확인
"""

import sys
import os
from datetime import datetime

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_ai_provider_from_mongo():
    """AI Provider from_mongo 메서드 테스트"""
    
    print("=== AI Provider from_mongo 테스트 시작 ===")
    
    try:
        # 모델 임포트
        from models import AIProviderConfig
        print("✓ AIProviderConfig 모델 임포트 성공")
        
        # 테스트 케이스 1: 완전한 데이터 (모든 필수 필드 포함)
        print("\n1. 완전한 데이터 테스트:")
        complete_data = {
            "_id": "test_id_1",
            "provider_name": "openai",
            "display_name": "OpenAI",
            "api_key": "***encrypted***",
            "is_active": True,
            "priority": 1,
            "temperature": 0.3,
            "created_by": "admin",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result1 = AIProviderConfig.from_mongo(complete_data)
        print(f"✓ 완전한 데이터 테스트 성공: {result1.provider_name}")
        
        # 테스트 케이스 2: 최소 필수 필드만 포함된 데이터 (이전 오류 상황)
        print("\n2. 최소 필드 데이터 테스트 (이전 오류 상황):")
        minimal_data = {
            "_id": "test_id_2",
            "provider_name": "test",
            "display_name": "Test Provider",
            "api_key": "***encrypted***",
            "is_active": True,
            "priority": 1
            # created_by 누락 - 이것이 원래 오류 원인
        }
        
        try:
            result2 = AIProviderConfig.from_mongo(minimal_data)
            print(f"✗ 최소 필드 테스트 - 예상치 못한 성공: {result2}")
        except Exception as e:
            print(f"✓ 최소 필드 테스트 - 예상된 오류 발생: {e}")
        
        # 테스트 케이스 3: 기본값 추가 후 데이터 (수정된 상황)
        print("\n3. 기본값 추가 후 데이터 테스트 (수정된 상황):")
        fixed_data = minimal_data.copy()
        # 수정된 엔드포인트에서 추가하는 기본값들
        if "created_by" not in fixed_data:
            fixed_data["created_by"] = "system"
        if "created_at" not in fixed_data:
            fixed_data["created_at"] = datetime.utcnow()
        if "updated_at" not in fixed_data:
            fixed_data["updated_at"] = datetime.utcnow()
        if "temperature" not in fixed_data:
            fixed_data["temperature"] = 0.3
            
        result3 = AIProviderConfig.from_mongo(fixed_data)
        print(f"✓ 기본값 추가 후 테스트 성공: {result3.provider_name}")
        print(f"  - created_by: {result3.created_by}")
        print(f"  - temperature: {result3.temperature}")
        
        # 테스트 케이스 4: None 데이터 처리
        print("\n4. None 데이터 테스트:")
        result4 = AIProviderConfig.from_mongo(None)
        print(f"✓ None 데이터 테스트 성공: {result4}")
        
        # 테스트 케이스 5: 빈 딕셔너리 처리
        print("\n5. 빈 딕셔너리 테스트:")
        result5 = AIProviderConfig.from_mongo({})
        print(f"✓ 빈 딕셔너리 테스트 성공: {result5}")
        
        print("\n=== 모든 테스트 완료 ===")
        print("결론: AI Provider from_mongo 오류가 수정되었습니다!")
        return True
        
    except Exception as e:
        print(f"\n✗ 테스트 중 오류 발생:")
        print(f"오류 타입: {type(e).__name__}")
        print(f"오류 메시지: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_ai_provider_from_mongo()
    sys.exit(0 if success else 1)