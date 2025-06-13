#!/usr/bin/env python3
"""
온라인 평가 시스템 빠른 테스트
Quick test for Online Evaluation System
"""

import asyncio
import httpx
import sys
from datetime import datetime

async def quick_test():
    """빠른 시스템 테스트"""
    print("🚀 온라인 평가 시스템 빠른 테스트 시작")
    print("=" * 50)
    
    backend_url = "http://localhost:8080"
    passed = 0
    total = 0
    
    # 1. 헬스체크
    print("1️⃣ 헬스체크...")
    total += 1
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(f"{backend_url}/health")
            if response.status_code == 200:
                print("   ✅ 헬스체크 성공")
                passed += 1
            else:
                print(f"   ❌ 헬스체크 실패: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 헬스체크 오류: {str(e)}")
    
    # 2. API 루트
    print("2️⃣ API 루트...")
    total += 1
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(f"{backend_url}/")
            if response.status_code == 200:
                print("   ✅ API 루트 성공")
                passed += 1
            else:
                print(f"   ❌ API 루트 실패: {response.status_code}")
    except Exception as e:
        print(f"   ❌ API 루트 오류: {str(e)}")
    
    # 3. API 문서
    print("3️⃣ API 문서...")
    total += 1
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(f"{backend_url}/docs")
            if response.status_code == 200:
                print("   ✅ API 문서 성공")
                passed += 1
            else:
                print(f"   ❌ API 문서 실패: {response.status_code}")
    except Exception as e:
        print(f"   ❌ API 문서 오류: {str(e)}")
    
    # 결과 출력
    print("=" * 50)
    print(f"📊 테스트 결과: {passed}/{total} 성공")
    success_rate = (passed / total * 100) if total > 0 else 0
    print(f"📈 성공률: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("🎉 시스템이 정상 작동하고 있습니다!")
    else:
        print("⚠️ 시스템에 문제가 있을 수 있습니다.")

if __name__ == "__main__":
    print("서버를 먼저 실행해주세요...")
    print("Python 서버 실행: python backend/server.py")
    print("또는 uvicorn backend.server:app --host 0.0.0.0 --port 8080")
    print("-" * 50)
    
    try:
        asyncio.run(quick_test())
    except KeyboardInterrupt:
        print("\n❌ 테스트가 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 테스트 오류: {str(e)}")