"""
성능 벤치마크 테스트
시스템의 성능 지표를 측정하고 기준치와 비교
"""

import asyncio
import aiohttp
import time
import statistics
import psutil
import json
from datetime import datetime
from typing import Dict, List, Any
import concurrent.futures
import threading

# 성능 기준치
PERFORMANCE_BENCHMARKS = {
    "api_response_time_ms": 1000,  # 1초 이하
    "concurrent_users": 50,        # 동시 사용자 50명
    "throughput_rps": 100,         # 초당 100 요청
    "memory_usage_mb": 512,        # 512MB 이하
    "cpu_usage_percent": 80,       # CPU 80% 이하
    "database_query_time_ms": 500, # 데이터베이스 쿼리 0.5초 이하
}

class PerformanceBenchmarkTest:
    """성능 벤치마크 테스트 클래스"""
    
    def __init__(self):
        self.backend_url = "http://localhost:8080"
        self.frontend_url = "http://localhost:3000"
        self.admin_token = None
        self.results = {}
        
    async def setup(self):
        """테스트 환경 설정"""
        print("🔧 성능 테스트 환경 설정 중...")
        
        # 관리자 토큰 획득
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.backend_url}/api/auth/login",
                    data={"username": "admin", "password": "admin123"}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        self.admin_token = result.get("access_token")
                        print("✅ 관리자 인증 완료")
                    else:
                        print(f"❌ 관리자 인증 실패: {response.status}")
            except Exception as e:
                print(f"❌ 인증 오류: {e}")
    
    async def test_api_response_time(self):
        """API 응답 시간 테스트"""
        print("\n⚡ API 응답 시간 테스트")
        print("-" * 40)
        
        # 테스트할 API 엔드포인트
        endpoints = [
            {"url": "/api/health", "name": "헬스체크", "auth": False},
            {"url": "/api/auth/me", "name": "사용자 정보", "auth": True},
            {"url": "/api/users", "name": "사용자 목록", "auth": True},
            {"url": "/api/projects", "name": "프로젝트 목록", "auth": True},
            {"url": "/api/companies", "name": "기업 목록", "auth": True},
            {"url": "/api/evaluations", "name": "평가 목록", "auth": True},
            {"url": "/api/templates", "name": "템플릿 목록", "auth": True},
        ]
        
        response_times = []
        
        async with aiohttp.ClientSession() as session:
            for endpoint in endpoints:
                headers = {}
                if endpoint["auth"] and self.admin_token:
                    headers["Authorization"] = f"Bearer {self.admin_token}"
                
                # 5회 반복 측정
                times = []
                for i in range(5):
                    start_time = time.time()
                    try:
                        async with session.get(
                            f"{self.backend_url}{endpoint['url']}",
                            headers=headers
                        ) as response:
                            await response.read()
                            response_time = (time.time() - start_time) * 1000
                            times.append(response_time)
                    except Exception as e:
                        print(f"   ❌ {endpoint['name']} 오류: {e}")
                        continue
                
                if times:
                    avg_time = statistics.mean(times)
                    min_time = min(times)
                    max_time = max(times)
                    
                    response_times.extend(times)
                    
                    status = "✅" if avg_time < PERFORMANCE_BENCHMARKS["api_response_time_ms"] else "⚠️"
                    print(f"   {status} {endpoint['name']}: {avg_time:.2f}ms (min: {min_time:.2f}, max: {max_time:.2f})")
        
        if response_times:
            overall_avg = statistics.mean(response_times)
            benchmark = PERFORMANCE_BENCHMARKS["api_response_time_ms"]
            
            self.results["api_response_time"] = {
                "average_ms": overall_avg,
                "benchmark_ms": benchmark,
                "passed": overall_avg < benchmark
            }
            
            print(f"\n📊 전체 평균 응답시간: {overall_avg:.2f}ms")
            print(f"🎯 기준치: {benchmark}ms")
            print(f"{'✅ 통과' if overall_avg < benchmark else '❌ 기준치 초과'}")
    
    async def test_concurrent_users(self):
        """동시 사용자 처리 테스트"""
        print("\n👥 동시 사용자 처리 테스트")
        print("-" * 40)
        
        concurrent_users = PERFORMANCE_BENCHMARKS["concurrent_users"]
        test_duration = 30  # 30초 동안 테스트
        
        async def user_simulation(user_id: int, session: aiohttp.ClientSession):
            """개별 사용자 시뮬레이션"""
            requests_made = 0
            errors = 0
            start_time = time.time()
            
            headers = {}
            if self.admin_token:
                headers["Authorization"] = f"Bearer {self.admin_token}"
            
            while time.time() - start_time < test_duration:
                try:
                    async with session.get(
                        f"{self.backend_url}/api/health",
                        headers=headers
                    ) as response:
                        if response.status == 200:
                            requests_made += 1
                        else:
                            errors += 1
                except Exception:
                    errors += 1
                
                await asyncio.sleep(0.1)  # 100ms 간격
            
            return {"user_id": user_id, "requests": requests_made, "errors": errors}
        
        print(f"🚀 {concurrent_users}명의 동시 사용자로 {test_duration}초간 테스트 시작...")
        
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit=concurrent_users * 2)
        ) as session:
            start_time = time.time()
            
            # 동시 사용자 시뮬레이션
            tasks = [
                user_simulation(i, session) 
                for i in range(concurrent_users)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            test_time = time.time() - start_time
            
            # 결과 분석
            successful_users = [r for r in results if isinstance(r, dict)]
            total_requests = sum(r["requests"] for r in successful_users)
            total_errors = sum(r["errors"] for r in successful_users)
            
            throughput = total_requests / test_time
            error_rate = total_errors / (total_requests + total_errors) * 100 if (total_requests + total_errors) > 0 else 0
            
            self.results["concurrent_users"] = {
                "users_tested": len(successful_users),
                "total_requests": total_requests,
                "total_errors": total_errors,
                "throughput_rps": throughput,
                "error_rate_percent": error_rate,
                "test_duration_seconds": test_time,
                "passed": len(successful_users) >= concurrent_users * 0.9  # 90% 성공률
            }
            
            print(f"📊 테스트 결과:")
            print(f"   ✅ 성공한 사용자: {len(successful_users)}/{concurrent_users}")
            print(f"   📈 총 요청 수: {total_requests}")
            print(f"   ❌ 총 오류 수: {total_errors}")
            print(f"   ⚡ 처리량: {throughput:.2f} RPS")
            print(f"   📉 오류율: {error_rate:.2f}%")
    
    async def test_throughput(self):
        """처리량 테스트"""
        print("\n🔥 처리량 테스트")
        print("-" * 40)
        
        target_rps = PERFORMANCE_BENCHMARKS["throughput_rps"]
        test_duration = 10  # 10초 동안 테스트
        
        async def make_request(session: aiohttp.ClientSession, semaphore: asyncio.Semaphore):
            """단일 요청 수행"""
            async with semaphore:
                try:
                    start_time = time.time()
                    async with session.get(f"{self.backend_url}/api/health") as response:
                        response_time = (time.time() - start_time) * 1000
                        return {
                            "success": response.status == 200,
                            "response_time": response_time,
                            "status": response.status
                        }
                except Exception as e:
                    return {
                        "success": False,
                        "response_time": None,
                        "error": str(e)
                    }
        
        print(f"🎯 목표: {target_rps} RPS로 {test_duration}초간 테스트")
        
        # 동시 연결 수 제한
        max_concurrent = min(target_rps, 100)
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit=max_concurrent * 2)
        ) as session:
            start_time = time.time()
            tasks = []
            
            # 목표 RPS로 요청 생성
            request_interval = 1.0 / target_rps
            
            for i in range(target_rps * test_duration):
                task = asyncio.create_task(make_request(session, semaphore))
                tasks.append(task)
                
                # 요청 간격 유지
                if i < (target_rps * test_duration - 1):
                    await asyncio.sleep(request_interval)
            
            # 모든 요청 완료 대기
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            actual_duration = time.time() - start_time
            
            # 결과 분석
            successful_requests = [r for r in results if isinstance(r, dict) and r.get("success")]
            failed_requests = [r for r in results if isinstance(r, dict) and not r.get("success")]
            
            actual_rps = len(successful_requests) / actual_duration
            success_rate = len(successful_requests) / len(results) * 100
            
            response_times = [r["response_time"] for r in successful_requests if r.get("response_time")]
            avg_response_time = statistics.mean(response_times) if response_times else 0
            
            self.results["throughput"] = {
                "target_rps": target_rps,
                "actual_rps": actual_rps,
                "success_rate_percent": success_rate,
                "average_response_time_ms": avg_response_time,
                "total_requests": len(results),
                "successful_requests": len(successful_requests),
                "failed_requests": len(failed_requests),
                "passed": actual_rps >= target_rps * 0.8  # 80% 달성
            }
            
            print(f"📊 처리량 테스트 결과:")
            print(f"   🎯 목표 RPS: {target_rps}")
            print(f"   ⚡ 실제 RPS: {actual_rps:.2f}")
            print(f"   ✅ 성공율: {success_rate:.2f}%")
            print(f"   ⏱️ 평균 응답시간: {avg_response_time:.2f}ms")
            print(f"   {'✅ 목표 달성' if actual_rps >= target_rps * 0.8 else '❌ 목표 미달성'}")
    
    def test_resource_usage(self):
        """리소스 사용량 테스트"""
        print("\n💻 리소스 사용량 테스트")
        print("-" * 40)
        
        # 시스템 리소스 모니터링
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # 메모리 사용량 (MB)
        memory_used_mb = (memory.total - memory.available) / (1024 * 1024)
        memory_percent = memory.percent
        
        # 디스크 사용량
        disk_used_gb = disk.used / (1024 * 1024 * 1024)
        disk_percent = (disk.used / disk.total) * 100
        
        # 네트워크 상태
        network = psutil.net_io_counters()
        
        self.results["resource_usage"] = {
            "cpu_percent": cpu_percent,
            "memory_used_mb": memory_used_mb,
            "memory_percent": memory_percent,
            "disk_used_gb": disk_used_gb,
            "disk_percent": disk_percent,
            "network_bytes_sent": network.bytes_sent,
            "network_bytes_recv": network.bytes_recv,
            "cpu_passed": cpu_percent < PERFORMANCE_BENCHMARKS["cpu_usage_percent"],
            "memory_passed": memory_used_mb < PERFORMANCE_BENCHMARKS["memory_usage_mb"]
        }
        
        print(f"📊 리소스 사용량:")
        print(f"   🖥️ CPU 사용률: {cpu_percent:.1f}% ({'✅' if cpu_percent < PERFORMANCE_BENCHMARKS['cpu_usage_percent'] else '❌'})")
        print(f"   🧠 메모리 사용량: {memory_used_mb:.1f}MB ({memory_percent:.1f}%) ({'✅' if memory_used_mb < PERFORMANCE_BENCHMARKS['memory_usage_mb'] else '❌'})")
        print(f"   💽 디스크 사용량: {disk_used_gb:.1f}GB ({disk_percent:.1f}%)")
        print(f"   🌐 네트워크 송신: {network.bytes_sent / (1024*1024):.1f}MB")
        print(f"   🌐 네트워크 수신: {network.bytes_recv / (1024*1024):.1f}MB")
    
    async def test_database_performance(self):
        """데이터베이스 성능 테스트"""
        print("\n🗄️ 데이터베이스 성능 테스트")
        print("-" * 40)
        
        if not self.admin_token:
            print("❌ 관리자 토큰 없음")
            return
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # 데이터베이스 관련 API 엔드포인트 테스트
        db_endpoints = [
            {"url": "/api/users", "name": "사용자 조회"},
            {"url": "/api/projects", "name": "프로젝트 조회"},
            {"url": "/api/companies", "name": "기업 조회"},
            {"url": "/api/evaluations", "name": "평가 조회"},
            {"url": "/api/templates", "name": "템플릿 조회"},
        ]
        
        db_response_times = []
        
        async with aiohttp.ClientSession() as session:
            for endpoint in db_endpoints:
                times = []
                
                # 각 엔드포인트를 3회 테스트
                for i in range(3):
                    start_time = time.time()
                    try:
                        async with session.get(
                            f"{self.backend_url}{endpoint['url']}",
                            headers=headers
                        ) as response:
                            await response.read()
                            response_time = (time.time() - start_time) * 1000
                            times.append(response_time)
                    except Exception as e:
                        print(f"   ❌ {endpoint['name']} 오류: {e}")
                        continue
                
                if times:
                    avg_time = statistics.mean(times)
                    db_response_times.extend(times)
                    
                    benchmark = PERFORMANCE_BENCHMARKS["database_query_time_ms"]
                    status = "✅" if avg_time < benchmark else "⚠️"
                    print(f"   {status} {endpoint['name']}: {avg_time:.2f}ms")
        
        if db_response_times:
            avg_db_time = statistics.mean(db_response_times)
            benchmark = PERFORMANCE_BENCHMARKS["database_query_time_ms"]
            
            self.results["database_performance"] = {
                "average_query_time_ms": avg_db_time,
                "benchmark_ms": benchmark,
                "passed": avg_db_time < benchmark
            }
            
            print(f"\n📊 데이터베이스 평균 응답시간: {avg_db_time:.2f}ms")
            print(f"🎯 기준치: {benchmark}ms")
            print(f"{'✅ 통과' if avg_db_time < benchmark else '❌ 기준치 초과'}")
    
    async def test_memory_leaks(self):
        """메모리 누수 테스트"""
        print("\n🔍 메모리 누수 테스트")
        print("-" * 40)
        
        # 초기 메모리 사용량
        initial_memory = psutil.virtual_memory().percent
        print(f"초기 메모리 사용량: {initial_memory:.2f}%")
        
        # 반복적인 API 호출로 메모리 누수 테스트
        iterations = 100
        
        async with aiohttp.ClientSession() as session:
            for i in range(iterations):
                try:
                    async with session.get(f"{self.backend_url}/api/health") as response:
                        await response.read()
                except:
                    pass
                
                if i % 20 == 0:
                    current_memory = psutil.virtual_memory().percent
                    print(f"   반복 {i}: 메모리 사용량 {current_memory:.2f}%")
        
        # 최종 메모리 사용량
        final_memory = psutil.virtual_memory().percent
        memory_increase = final_memory - initial_memory
        
        self.results["memory_leak_test"] = {
            "initial_memory_percent": initial_memory,
            "final_memory_percent": final_memory,
            "memory_increase_percent": memory_increase,
            "iterations": iterations,
            "passed": memory_increase < 5.0  # 5% 이하 증가만 허용
        }
        
        print(f"최종 메모리 사용량: {final_memory:.2f}%")
        print(f"메모리 증가량: {memory_increase:.2f}%")
        print(f"{'✅ 메모리 누수 없음' if memory_increase < 5.0 else '⚠️ 메모리 증가 감지'}")
    
    def generate_performance_report(self):
        """성능 테스트 보고서 생성"""
        print("\n📊 성능 테스트 종합 보고서")
        print("=" * 60)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results.values() if result.get("passed", False))
        
        print(f"📈 테스트 통과율: {passed_tests}/{total_tests} ({passed_tests/total_tests*100:.1f}%)")
        print("\n🎯 성능 지표 상세:")
        
        for test_name, result in self.results.items():
            status = "✅ 통과" if result.get("passed", False) else "❌ 실패"
            print(f"   {test_name}: {status}")
            
            # 주요 메트릭 표시
            if "average_ms" in result:
                print(f"      평균 시간: {result['average_ms']:.2f}ms")
            if "actual_rps" in result:
                print(f"      처리량: {result['actual_rps']:.2f} RPS")
            if "success_rate_percent" in result:
                print(f"      성공률: {result['success_rate_percent']:.2f}%")
        
        # JSON 보고서 저장
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "pass_rate": passed_tests / total_tests * 100
            },
            "benchmarks": PERFORMANCE_BENCHMARKS,
            "results": self.results
        }
        
        with open("performance_report.json", "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 상세 보고서가 performance_report.json에 저장되었습니다")
        
        return passed_tests == total_tests
    
    async def run_all_performance_tests(self):
        """모든 성능 테스트 실행"""
        print("🚀 온라인 평가 시스템 성능 벤치마크 테스트 시작")
        print("=" * 60)
        
        start_time = time.time()
        
        try:
            await self.setup()
            
            # 성능 테스트 실행
            await self.test_api_response_time()
            await self.test_concurrent_users()
            await self.test_throughput()
            self.test_resource_usage()
            await self.test_database_performance()
            await self.test_memory_leaks()
            
        except Exception as e:
            print(f"\n❌ 성능 테스트 중 오류 발생: {e}")
        
        total_time = time.time() - start_time
        
        print(f"\n⏱️ 총 테스트 시간: {total_time:.2f}초")
        
        # 성능 보고서 생성
        return self.generate_performance_report()

async def main():
    """메인 성능 테스트 함수"""
    test_runner = PerformanceBenchmarkTest()
    success = await test_runner.run_all_performance_tests()
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)