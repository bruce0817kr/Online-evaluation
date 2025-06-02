#!/usr/bin/env python3
"""
최종 통합 테스트 스크립트
온라인 평가 시스템의 모든 새로운 기능들을 테스트합니다.
"""

import asyncio
import json
import time
import requests
import websockets
from concurrent.futures import ThreadPoolExecutor
import sys
import os

# 기본 설정
BACKEND_URL = "http://localhost:8080"
WS_URL = "ws://localhost:8080"

class FinalIntegrationTest:
    def __init__(self):
        self.results = {
            "basic_health": False,
            "detailed_health": False,
            "liveness_probe": False,
            "readiness_probe": False,
            "websocket_connection": False,
            "cache_performance": False,
            "notification_system": False,
            "overall_score": 0
        }
        
    def print_status(self, test_name, status, details=""):
        """테스트 결과 출력"""
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {test_name}")
        if details:
            print(f"   📋 {details}")
        print()
        
    def test_basic_health(self):
        """기본 헬스 체크"""
        try:
            response = requests.get(f"{BACKEND_URL}/health", timeout=5)
            success = response.status_code == 200
            self.results["basic_health"] = success
            
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                details += f", Message: {data.get('message', 'N/A')}"
                
            self.print_status("기본 헬스 체크", success, details)
            return success
        except Exception as e:
            self.print_status("기본 헬스 체크", False, f"Error: {str(e)}")
            return False
            
    def test_detailed_health(self):
        """향상된 헬스 체크"""
        try:
            response = requests.get(f"{BACKEND_URL}/api/health/detailed", timeout=10)
            success = response.status_code == 200
            self.results["detailed_health"] = success
            
            if success:
                data = response.json()
                cpu_usage = data.get('system_metrics', {}).get('cpu_usage', 0)
                memory_usage = data.get('system_metrics', {}).get('memory_usage', {}).get('percent', 0)
                details = f"CPU: {cpu_usage:.1f}%, Memory: {memory_usage:.1f}%"
            else:
                details = f"Status: {response.status_code}"
                
            self.print_status("향상된 헬스 체크", success, details)
            return success
        except Exception as e:
            self.print_status("향상된 헬스 체크", False, f"Error: {str(e)}")
            return False
            
    def test_liveness_probe(self):
        """Liveness 프로브 테스트"""
        try:
            response = requests.get(f"{BACKEND_URL}/api/health/liveness", timeout=5)
            success = response.status_code == 200
            self.results["liveness_probe"] = success
            
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                details += f", Status: {data.get('status', 'N/A')}"
                
            self.print_status("Liveness Probe", success, details)
            return success
        except Exception as e:
            self.print_status("Liveness Probe", False, f"Error: {str(e)}")
            return False
            
    def test_readiness_probe(self):
        """Readiness 프로브 테스트"""
        try:
            response = requests.get(f"{BACKEND_URL}/api/health/readiness", timeout=5)
            success = response.status_code == 200
            self.results["readiness_probe"] = success
            
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                details += f", Ready: {data.get('ready', False)}"
                
            self.print_status("Readiness Probe", success, details)
            return success
        except Exception as e:
            self.print_status("Readiness Probe", False, f"Error: {str(e)}")
            return False
            
    async def test_websocket_connection(self):
        """WebSocket 연결 테스트"""
        try:
            # 테스트용 사용자 ID
            test_user_id = "test_user_123"
            uri = f"{WS_URL}/ws/{test_user_id}"
            
            async with websockets.connect(uri) as websocket:
                # 연결 테스트
                self.results["websocket_connection"] = True
                
                # 테스트 메시지 전송 (실제로는 서버에서 전송)
                await asyncio.sleep(1)  # 연결 안정화 대기
                
                self.print_status("WebSocket 연결", True, f"Connected to {uri}")
                return True
                
        except Exception as e:
            self.print_status("WebSocket 연결", False, f"Error: {str(e)}")
            return False
            
    def test_cache_performance(self):
        """캐시 성능 테스트"""
        try:
            # 여러 번 요청하여 캐시 성능 측정
            times = []
            
            for i in range(3):
                start_time = time.time()
                response = requests.get(f"{BACKEND_URL}/api/health/detailed", timeout=10)
                end_time = time.time()
                
                if response.status_code == 200:
                    times.append(end_time - start_time)
                    
            if times:
                avg_time = sum(times) / len(times)
                success = avg_time < 2.0  # 2초 이내 응답
                self.results["cache_performance"] = success
                
                details = f"평균 응답시간: {avg_time:.3f}초"
                self.print_status("캐시 성능", success, details)
                return success
            else:
                self.print_status("캐시 성능", False, "No successful requests")
                return False
                
        except Exception as e:
            self.print_status("캐시 성능", False, f"Error: {str(e)}")
            return False

    def test_notification_system(self):
        """알림 시스템 테스트"""
        try:
            # Redis 기반 알림 시스템 테스트
            response = requests.get(f"{BACKEND_URL}/api/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                cache_status = data.get('cache', {}).get('status', 'disconnected')
                success = cache_status == 'connected'
                self.results["notification_system"] = success
                
                details = f"Cache status: {cache_status}"
                self.print_status("알림 시스템", success, details)
                return success
            else:
                self.print_status("알림 시스템", False, f"Status check failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.print_status("알림 시스템", False, f"Error: {str(e)}")
            return False
            
    def calculate_score(self):
        """전체 점수 계산"""
        total_tests = len([k for k in self.results.keys() if k != "overall_score"])
        passed_tests = sum([1 for k, v in self.results.items() if k != "overall_score" and v])
        
        score = (passed_tests / total_tests) * 100
        self.results["overall_score"] = score
        return score
        
    async def run_all_tests(self):
        """모든 테스트 실행"""
        print("🚀 온라인 평가 시스템 최종 통합 테스트 시작\n")
        print("=" * 60)
        
        # 기본 테스트들
        self.test_basic_health()
        self.test_detailed_health()
        self.test_liveness_probe()
        self.test_readiness_probe()
        
        # WebSocket 테스트 (비동기)
        await self.test_websocket_connection()
        
        # 성능 및 기능 테스트
        self.test_cache_performance()
        self.test_notification_system()
        
        # 최종 결과
        score = self.calculate_score()
        
        print("=" * 60)
        print("📊 최종 테스트 결과")
        print("=" * 60)
        
        for test_name, result in self.results.items():
            if test_name != "overall_score":
                status_icon = "✅" if result else "❌"
                print(f"{status_icon} {test_name}: {result}")
                
        print(f"\n🎯 전체 점수: {score:.1f}%")
        
        if score >= 90:
            print("🎉 탁월함! 시스템이 프로덕션 준비 완료상태입니다.")
        elif score >= 80:
            print("👍 우수함! 대부분의 기능이 정상 작동합니다.")
        elif score >= 70:
            print("⚠️  양호함! 일부 개선이 필요합니다.")
        else:
            print("🚨 주의! 여러 기능에 문제가 있습니다.")
            
        print("\n" + "=" * 60)
        
        return score

def main():
    """메인 함수"""
    test_runner = FinalIntegrationTest()
    
    try:
        # 비동기 테스트 실행
        score = asyncio.run(test_runner.run_all_tests())
        
        # 결과에 따른 종료 코드
        if score >= 90:
            sys.exit(0)  # 성공
        elif score >= 70:
            sys.exit(1)  # 경고
        else:
            sys.exit(2)  # 실패
            
    except KeyboardInterrupt:
        print("\n❌ 테스트가 사용자에 의해 중단되었습니다.")
        sys.exit(130)
    except Exception as e:
        print(f"\n🚨 테스트 실행 중 오류 발생: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
