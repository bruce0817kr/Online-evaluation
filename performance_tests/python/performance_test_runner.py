#!/usr/bin/env python3
"""
AI 모델 관리 시스템 - 성능 테스트 러너
종합적인 성능 테스트 실행 및 결과 분석
"""

import asyncio
import aiohttp
import time
import json
import statistics
from typing import Dict, List, Tuple
import argparse
from datetime import datetime
import logging
from dataclasses import dataclass
import psutil
import threading
from concurrent.futures import ThreadPoolExecutor
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv('.env.performance')

@dataclass
class TestConfig:
    """테스트 설정 클래스"""
    backend_url: str
    concurrent_users: int
    test_duration: int  # 초
    ramp_up_time: int   # 초
    scenarios: List[str]
    
@dataclass
class TestResult:
    """테스트 결과 클래스"""
    scenario: str
    response_times: List[float]
    status_codes: List[int]
    errors: List[str]
    start_time: datetime
    end_time: datetime
    
class PerformanceTestRunner:
    """성능 테스트 실행기"""
    
    def __init__(self, config: TestConfig):
        self.config = config
        self.results: List[TestResult] = []
        self.session = None
        self.auth_tokens = {}
        
        # 로깅 설정
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'performance_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    async def setup_session(self):
        """HTTP 세션 설정"""
        connector = aiohttp.TCPConnector(
            limit=200,  # 최대 연결 수
            limit_per_host=50,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'Content-Type': 'application/json'}
        )
        
    async def cleanup_session(self):
        """세션 정리"""
        if self.session:
            await self.session.close()
            
    async def authenticate_user(self, email: str, password: str) -> str:
        """사용자 인증 및 토큰 획득"""
        if email in self.auth_tokens:
            return self.auth_tokens[email]
            
        login_data = {
            "email": email,
            "password": password
        }
        
        try:
            async with self.session.post(
                f"{self.config.backend_url}/api/auth/login",
                json=login_data
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    token = data.get('access_token')
                    self.auth_tokens[email] = token
                    return token
                else:
                    self.logger.error(f"Authentication failed for {email}: {response.status}")
                    return None
        except Exception as e:
            self.logger.error(f"Authentication error for {email}: {str(e)}")
            return None
            
    async def execute_scenario(self, scenario_name: str, user_id: int) -> TestResult:
        """개별 시나리오 실행"""
        result = TestResult(
            scenario=scenario_name,
            response_times=[],
            status_codes=[],
            errors=[],
            start_time=datetime.now(),
            end_time=None
        )
        
        # 사용자별 인증 (라운드 로빈)
        users = [
            ("admin@test.com", "testpass123"),
            ("secretary@test.com", "testpass123"),
            ("admin2@test.com", "testpass123"),
            ("secretary2@test.com", "testpass123")
        ]
        email, password = users[user_id % len(users)]
        
        auth_token = await self.authenticate_user(email, password)
        if not auth_token:
            result.errors.append(f"Authentication failed for user {user_id}")
            result.end_time = datetime.now()
            return result
            
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        # 시나리오별 테스트 실행
        if scenario_name == "get_models":
            await self._test_get_models(result, headers)
        elif scenario_name == "connection_test":
            await self._test_connection(result, headers)
        elif scenario_name == "performance_metrics":
            await self._test_performance_metrics(result, headers)
        elif scenario_name == "model_crud":
            await self._test_model_crud(result, headers)
        elif scenario_name == "mixed_workload":
            await self._test_mixed_workload(result, headers)
            
        result.end_time = datetime.now()
        return result
        
    async def _test_get_models(self, result: TestResult, headers: Dict):
        """모델 목록 조회 테스트"""
        try:
            start_time = time.time()
            async with self.session.get(
                f"{self.config.backend_url}/api/ai-models/available",
                headers=headers
            ) as response:
                end_time = time.time()
                
                result.response_times.append((end_time - start_time) * 1000)  # ms
                result.status_codes.append(response.status)
                
                if response.status != 200:
                    error_text = await response.text()
                    result.errors.append(f"GET models failed: {response.status} - {error_text}")
                    
        except asyncio.TimeoutError:
            result.errors.append("GET models timeout")
            result.response_times.append(30000)  # 타임아웃을 30초로 기록
        except Exception as e:
            result.errors.append(f"GET models error: {str(e)}")
            
    async def _test_connection(self, result: TestResult, headers: Dict):
        """연결 테스트"""
        models_to_test = [
            "openai-gpt35-turbo",
            "openai-gpt4", 
            "anthropic-claude3-haiku",
            "google-gemini-pro"
        ]
        
        for model_id in models_to_test:
            try:
                start_time = time.time()
                test_data = {"model_id": model_id}
                
                async with self.session.post(
                    f"{self.config.backend_url}/api/ai-models/test-connection",
                    json=test_data,
                    headers=headers
                ) as response:
                    end_time = time.time()
                    
                    result.response_times.append((end_time - start_time) * 1000)
                    result.status_codes.append(response.status)
                    
                    if response.status != 200:
                        error_text = await response.text()
                        result.errors.append(f"Connection test failed for {model_id}: {response.status} - {error_text}")
                        
                # 연결 테스트 간 간격
                await asyncio.sleep(1)
                
            except asyncio.TimeoutError:
                result.errors.append(f"Connection test timeout for {model_id}")
                result.response_times.append(30000)
            except Exception as e:
                result.errors.append(f"Connection test error for {model_id}: {str(e)}")
                
    async def _test_performance_metrics(self, result: TestResult, headers: Dict):
        """성능 메트릭 조회 테스트"""
        endpoints = [
            "/api/ai-models/performance-metrics",
            "/api/ai-models/health/status"
        ]
        
        for endpoint in endpoints:
            try:
                start_time = time.time()
                async with self.session.get(
                    f"{self.config.backend_url}{endpoint}",
                    headers=headers
                ) as response:
                    end_time = time.time()
                    
                    result.response_times.append((end_time - start_time) * 1000)
                    result.status_codes.append(response.status)
                    
                    if response.status != 200:
                        error_text = await response.text()
                        result.errors.append(f"Metrics request failed for {endpoint}: {response.status} - {error_text}")
                        
            except asyncio.TimeoutError:
                result.errors.append(f"Metrics request timeout for {endpoint}")
                result.response_times.append(30000)
            except Exception as e:
                result.errors.append(f"Metrics request error for {endpoint}: {str(e)}")
                
    async def _test_model_crud(self, result: TestResult, headers: Dict):
        """모델 CRUD 테스트 (관리자만)"""
        if "admin" not in headers.get('Authorization', ''):
            # 관리자가 아닌 경우 스킵
            return
            
        model_id = f"test-model-{int(time.time())}-{asyncio.current_task().get_name()}"
        
        # 1. 모델 생성
        try:
            start_time = time.time()
            create_data = {
                "model_id": model_id,
                "provider": "openai",
                "model_name": "gpt-3.5-turbo",
                "display_name": f"Performance Test Model {model_id}",
                "quality_score": 0.8,
                "speed_score": 0.9,
                "cost_efficiency": 0.85,
                "reliability_score": 0.9
            }
            
            async with self.session.post(
                f"{self.config.backend_url}/api/ai-models/create",
                json=create_data,
                headers=headers
            ) as response:
                end_time = time.time()
                
                result.response_times.append((end_time - start_time) * 1000)
                result.status_codes.append(response.status)
                
                if response.status != 201:
                    error_text = await response.text()
                    result.errors.append(f"Model creation failed: {response.status} - {error_text}")
                    return
                    
        except Exception as e:
            result.errors.append(f"Model creation error: {str(e)}")
            return
            
        # 2. 모델 조회
        try:
            start_time = time.time()
            async with self.session.get(
                f"{self.config.backend_url}/api/ai-models/{model_id}",
                headers=headers
            ) as response:
                end_time = time.time()
                
                result.response_times.append((end_time - start_time) * 1000)
                result.status_codes.append(response.status)
                
        except Exception as e:
            result.errors.append(f"Model retrieval error: {str(e)}")
            
        # 3. 모델 수정
        try:
            start_time = time.time()
            update_data = {
                "display_name": f"Updated {model_id}",
                "quality_score": 0.85
            }
            
            async with self.session.put(
                f"{self.config.backend_url}/api/ai-models/{model_id}",
                json=update_data,
                headers=headers
            ) as response:
                end_time = time.time()
                
                result.response_times.append((end_time - start_time) * 1000)
                result.status_codes.append(response.status)
                
        except Exception as e:
            result.errors.append(f"Model update error: {str(e)}")
            
        # 4. 모델 삭제 (정리)
        try:
            start_time = time.time()
            async with self.session.delete(
                f"{self.config.backend_url}/api/ai-models/{model_id}",
                headers=headers
            ) as response:
                end_time = time.time()
                
                result.response_times.append((end_time - start_time) * 1000)
                result.status_codes.append(response.status)
                
        except Exception as e:
            result.errors.append(f"Model deletion error: {str(e)}")
            
    async def _test_mixed_workload(self, result: TestResult, headers: Dict):
        """혼합 워크로드 테스트"""
        # 실제 사용 패턴을 시뮬레이션
        workload = [
            ("get_models", 0.4),      # 40% - 모델 목록 조회
            ("performance_metrics", 0.3),  # 30% - 성능 메트릭
            ("connection_test", 0.2),      # 20% - 연결 테스트
            ("model_crud", 0.1)            # 10% - 모델 관리
        ]
        
        import random
        
        for _ in range(5):  # 5번 반복
            # 가중치에 따른 랜덤 선택
            rand = random.random()
            cumulative = 0
            selected_test = "get_models"  # 기본값
            
            for test_name, weight in workload:
                cumulative += weight
                if rand <= cumulative:
                    selected_test = test_name
                    break
                    
            # 선택된 테스트 실행
            if selected_test == "get_models":
                await self._test_get_models(result, headers)
            elif selected_test == "performance_metrics":
                await self._test_performance_metrics(result, headers)
            elif selected_test == "connection_test":
                await self._test_connection(result, headers)
            elif selected_test == "model_crud":
                await self._test_model_crud(result, headers)
                
            # 사용자 사고시간 시뮬레이션
            await asyncio.sleep(random.uniform(1, 3))
            
    async def run_load_test(self) -> List[TestResult]:
        """부하 테스트 실행"""
        self.logger.info(f"Starting load test with {self.config.concurrent_users} concurrent users")
        self.logger.info(f"Test duration: {self.config.test_duration} seconds")
        self.logger.info(f"Scenarios: {self.config.scenarios}")
        
        await self.setup_session()
        
        try:
            # 사용자별 태스크 생성
            tasks = []
            start_time = time.time()
            
            for user_id in range(self.config.concurrent_users):
                for scenario in self.config.scenarios:
                    # 램프업 시간에 따른 지연 시작
                    delay = (user_id * self.config.ramp_up_time) / self.config.concurrent_users
                    
                    task = asyncio.create_task(
                        self._run_user_scenario(scenario, user_id, delay)
                    )
                    tasks.append(task)
                    
            # 모든 태스크 완료 대기
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 예외 처리 및 결과 수집
            valid_results = []
            for result in results:
                if isinstance(result, Exception):
                    self.logger.error(f"Task failed with exception: {result}")
                else:
                    valid_results.append(result)
                    
            self.results = valid_results
            
            end_time = time.time()
            self.logger.info(f"Load test completed in {end_time - start_time:.2f} seconds")
            
            return self.results
            
        finally:
            await self.cleanup_session()
            
    async def _run_user_scenario(self, scenario: str, user_id: int, delay: float) -> TestResult:
        """개별 사용자 시나리오 실행"""
        # 램프업 지연
        if delay > 0:
            await asyncio.sleep(delay)
            
        return await self.execute_scenario(scenario, user_id)
        
    def analyze_results(self) -> Dict:
        """테스트 결과 분석"""
        if not self.results:
            return {}
            
        analysis = {
            'summary': {
                'total_requests': 0,
                'total_errors': 0,
                'error_rate': 0,
                'avg_response_time': 0,
                'median_response_time': 0,
                'p95_response_time': 0,
                'p99_response_time': 0,
                'min_response_time': 0,
                'max_response_time': 0
            },
            'by_scenario': {},
            'status_codes': {},
            'errors': []
        }
        
        all_response_times = []
        all_status_codes = []
        all_errors = []
        
        for result in self.results:
            scenario = result.scenario
            
            # 시나리오별 분석
            if scenario not in analysis['by_scenario']:
                analysis['by_scenario'][scenario] = {
                    'requests': 0,
                    'errors': 0,
                    'avg_response_time': 0,
                    'response_times': []
                }
                
            scenario_data = analysis['by_scenario'][scenario]
            scenario_data['requests'] += len(result.response_times)
            scenario_data['errors'] += len(result.errors)
            scenario_data['response_times'].extend(result.response_times)
            
            # 전체 데이터 수집
            all_response_times.extend(result.response_times)
            all_status_codes.extend(result.status_codes)
            all_errors.extend(result.errors)
            
        # 전체 요약 통계
        if all_response_times:
            analysis['summary']['total_requests'] = len(all_response_times)
            analysis['summary']['total_errors'] = len(all_errors)
            analysis['summary']['error_rate'] = (len(all_errors) / len(all_response_times)) * 100
            analysis['summary']['avg_response_time'] = statistics.mean(all_response_times)
            analysis['summary']['median_response_time'] = statistics.median(all_response_times)
            
            sorted_times = sorted(all_response_times)
            analysis['summary']['p95_response_time'] = sorted_times[int(0.95 * len(sorted_times))]
            analysis['summary']['p99_response_time'] = sorted_times[int(0.99 * len(sorted_times))]
            analysis['summary']['min_response_time'] = min(all_response_times)
            analysis['summary']['max_response_time'] = max(all_response_times)
            
        # 시나리오별 평균 계산
        for scenario, data in analysis['by_scenario'].items():
            if data['response_times']:
                data['avg_response_time'] = statistics.mean(data['response_times'])
                
        # 상태 코드 분포
        for code in all_status_codes:
            analysis['status_codes'][code] = analysis['status_codes'].get(code, 0) + 1
            
        # 에러 목록
        analysis['errors'] = all_errors
        
        return analysis
        
    def generate_report(self, analysis: Dict) -> str:
        """성능 테스트 리포트 생성"""
        report = []
        report.append("=" * 60)
        report.append("AI 모델 관리 시스템 - 성능 테스트 리포트")
        report.append("=" * 60)
        report.append(f"테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"동시 사용자: {self.config.concurrent_users}")
        report.append(f"테스트 시간: {self.config.test_duration}초")
        report.append("")
        
        # 전체 요약
        summary = analysis['summary']
        report.append("📊 전체 요약")
        report.append("-" * 30)
        report.append(f"총 요청 수: {summary['total_requests']:,}")
        report.append(f"총 에러 수: {summary['total_errors']:,}")
        report.append(f"에러율: {summary['error_rate']:.2f}%")
        report.append(f"평균 응답시간: {summary['avg_response_time']:.2f}ms")
        report.append(f"중간값 응답시간: {summary['median_response_time']:.2f}ms")
        report.append(f"95% 응답시간: {summary['p95_response_time']:.2f}ms")
        report.append(f"99% 응답시간: {summary['p99_response_time']:.2f}ms")
        report.append(f"최소 응답시간: {summary['min_response_time']:.2f}ms")
        report.append(f"최대 응답시간: {summary['max_response_time']:.2f}ms")
        report.append("")
        
        # 시나리오별 분석
        report.append("🎭 시나리오별 분석")
        report.append("-" * 30)
        for scenario, data in analysis['by_scenario'].items():
            report.append(f"📋 {scenario}")
            report.append(f"  요청 수: {data['requests']:,}")
            report.append(f"  에러 수: {data['errors']:,}")
            if data['requests'] > 0:
                error_rate = (data['errors'] / data['requests']) * 100
                report.append(f"  에러율: {error_rate:.2f}%")
            report.append(f"  평균 응답시간: {data['avg_response_time']:.2f}ms")
            report.append("")
            
        # 상태 코드 분포
        report.append("📈 HTTP 상태 코드 분포")
        report.append("-" * 30)
        for code, count in sorted(analysis['status_codes'].items()):
            percentage = (count / summary['total_requests']) * 100
            report.append(f"  {code}: {count:,} ({percentage:.2f}%)")
        report.append("")
        
        # 성능 평가
        report.append("🎯 성능 평가")
        report.append("-" * 30)
        
        # 목표 대비 평가
        goals = {
            'avg_response_time': 2000,  # 2초
            'p95_response_time': 5000,  # 5초
            'error_rate': 1.0           # 1%
        }
        
        for metric, target in goals.items():
            actual = summary[metric]
            if metric == 'error_rate':
                status = "✅ 통과" if actual <= target else "❌ 실패"
                report.append(f"  {metric}: {actual:.2f}% (목표: ≤{target}%) {status}")
            else:
                status = "✅ 통과" if actual <= target else "❌ 실패"
                report.append(f"  {metric}: {actual:.2f}ms (목표: ≤{target}ms) {status}")
                
        report.append("")
        
        # 에러 상세 (최대 10개)
        if analysis['errors']:
            report.append("❌ 주요 에러 목록 (최대 10개)")
            report.append("-" * 30)
            for error in analysis['errors'][:10]:
                report.append(f"  • {error}")
            if len(analysis['errors']) > 10:
                report.append(f"  ... 및 {len(analysis['errors']) - 10}개 더")
            report.append("")
            
        return "\n".join(report)

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='AI Model Management Performance Test')
    parser.add_argument('--users', type=int, default=50, help='Number of concurrent users')
    parser.add_argument('--duration', type=int, default=300, help='Test duration in seconds')
    parser.add_argument('--rampup', type=int, default=60, help='Ramp-up time in seconds')
    parser.add_argument('--scenarios', nargs='+', 
                       default=['get_models', 'connection_test', 'performance_metrics'],
                       help='Test scenarios to run')
    parser.add_argument('--backend-url', default=os.getenv('BACKEND_URL', 'http://localhost:8000'),
                       help='Backend URL')
    
    args = parser.parse_args()
    
    # 테스트 설정
    config = TestConfig(
        backend_url=args.backend_url,
        concurrent_users=args.users,
        test_duration=args.duration,
        ramp_up_time=args.rampup,
        scenarios=args.scenarios
    )
    
    # 테스트 실행
    runner = PerformanceTestRunner(config)
    
    async def run_test():
        results = await runner.run_load_test()
        analysis = runner.analyze_results()
        report = runner.generate_report(analysis)
        
        # 결과 출력 및 저장
        print(report)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"performance_report_{timestamp}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
            
        # JSON 결과도 저장
        json_file = f"performance_results_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
            
        print(f"\n리포트가 저장되었습니다: {report_file}")
        print(f"JSON 결과가 저장되었습니다: {json_file}")
        
    # 비동기 실행
    asyncio.run(run_test())

if __name__ == "__main__":
    main()