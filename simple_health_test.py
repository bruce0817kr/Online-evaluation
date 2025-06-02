#!/usr/bin/env python3
"""
간단한 헬스 체크 테스트
"""

import requests
import json

# 기본 설정
BACKEND_URL = "http://localhost:8080"

def test_endpoints():
    """엔드포인트 테스트"""
    endpoints = [
        ("기본 헬스", "/health"),
        ("API 헬스", "/api/health"),
        ("상세 헬스", "/api/health/detailed"), 
        ("Liveness", "/api/health/liveness"),
        ("Readiness", "/api/health/readiness"),
        ("API 상태", "/api/status")
    ]
    
    results = {}
    print("🚀 헬스체크 테스트 시작\n")
    
    for name, endpoint in endpoints:
        try:
            url = f"{BACKEND_URL}{endpoint}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ {name}: OK (200)")
                results[name] = True
            else:
                print(f"❌ {name}: {response.status_code}")
                results[name] = False
                
        except Exception as e:
            print(f"❌ {name}: Error - {str(e)}")
            results[name] = False
    
    # 결과 요약
    total = len(results)
    passed = sum(results.values())
    score = (passed / total) * 100
    
    print(f"\n📊 결과: {passed}/{total} 테스트 통과 ({score:.1f}%)")
    
    return score

if __name__ == "__main__":
    score = test_endpoints()
    print(f"\n🎯 최종 점수: {score:.1f}%")
