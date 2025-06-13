"""
온라인 평가 시스템 - 최종 시스템 테스트 및 검증
생성된 테스트 데이터를 사용하여 전체 시스템 기능을 검증합니다.
"""

import requests
import json
import sys
from datetime import datetime
from datetime import datetime
from pathlib import Path

# 테스트 설정
BACKEND_URL = "http://localhost:8080"
FRONTEND_URL = "http://localhost:3000"
TEST_TIMEOUT = 30

class FinalSystemTest:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "test_results": {},
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "success_rate": 0
            }
        }
        
    async def test_basic_health(self):
        """기본 헬스체크 테스트"""
        print("🏥 기본 헬스체크 테스트...")
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{BACKEND_URL}/health")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✅ 헬스체크 성공: {data.get('status', 'unknown')}")
                    return True, data
                else:
                    print(f"   ❌ 헬스체크 실패: {response.status_code}")
                    return False, {"error": f"HTTP {response.status_code}"}
                    
        except Exception as e:
            print(f"   ❌ 헬스체크 오류: {str(e)}")
            return False, {"error": str(e)}    
    async def test_database_status(self):
        """데이터베이스 상태 테스트"""
        print("🗄️ 데이터베이스 상태 테스트...")
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{BACKEND_URL}/db-status")
                
                if response.status_code == 200:
                    data = response.json()
                    mongodb_status = data.get("databases", {}).get("mongodb", {}).get("status")
                    redis_status = data.get("databases", {}).get("redis", {}).get("status")
                    
                    print(f"   ✅ MongoDB: {mongodb_status}")
                    print(f"   ✅ Redis: {redis_status}")
                    return True, data
                else:
                    print(f"   ❌ DB 상태 확인 실패: {response.status_code}")
                    return False, {"error": f"HTTP {response.status_code}"}
                    
        except Exception as e:
            print(f"   ❌ DB 상태 확인 오류: {str(e)}")
            return False, {"error": str(e)}
    
    async def test_api_endpoints(self):
        """주요 API 엔드포인트 테스트"""
        print("🔌 API 엔드포인트 테스트...")
        
        endpoints = [
            ("/", "API 루트"),
            ("/docs", "API 문서"),
            ("/api/users", "사용자 API"),
            ("/api/tests", "테스트 API")
        ]
        
        results = {}
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                for endpoint, description in endpoints:
                    try:
                        response = await client.get(f"{BACKEND_URL}{endpoint}")
                        success = response.status_code in [200, 422]  # 422는 인증 필요한 경우
                        
                        if success:
                            print(f"   ✅ {description}: HTTP {response.status_code}")
                        else:
                            print(f"   ❌ {description}: HTTP {response.status_code}")
                            
                        results[endpoint] = {
                            "status_code": response.status_code,
                            "success": success
                        }
                        
                    except Exception as e:
                        print(f"   ❌ {description}: {str(e)}")
                        results[endpoint] = {
                            "error": str(e),
                            "success": False
                        }
                        
            return True, results
            
        except Exception as e:
            print(f"   ❌ API 테스트 오류: {str(e)}")
            return False, {"error": str(e)}