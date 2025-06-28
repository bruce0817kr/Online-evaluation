#!/usr/bin/env python3
"""
AI 모델 관리 시스템 - AI API 성능 테스트
외부 AI 서비스 성능 및 안정성 테스트
"""

import asyncio
import aiohttp
import time
import statistics
from typing import Dict, List, Optional
import logging
from datetime import datetime
from dataclasses import dataclass, asdict
import json
import os
from dotenv import load_dotenv
import random

load_dotenv('.env.performance')

@dataclass
class AIAPITestResult:
    """AI API 테스트 결과"""
    provider: str
    model: str
    test_type: str
    response_times: List[float]
    token_counts: List[int]
    costs: List[float]
    success_count: int
    error_count: int
    errors: List[str]
    avg_response_time: float
    avg_tokens: float
    avg_cost: float
    success_rate: float

class AIAPIPerformanceTest:
    """AI API 성능 테스트 클래스"""
    
    def __init__(self):
        self.api_keys = {
            'openai': os.getenv('OPENAI_TEST_API_KEY'),
            'anthropic': os.getenv('ANTHROPIC_TEST_API_KEY'),
            'google': os.getenv('GOOGLE_TEST_API_KEY'),
            'novita': os.getenv('NOVITA_TEST_API_KEY')
        }
        
        self.session = None
        self.results: List[AIAPITestResult] = []
        
        # 로깅 설정
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # 테스트 프롬프트들
        self.test_prompts = {
            'simple': "안녕하세요. 오늘 날씨가 어떤가요?",
            'evaluation': """다음 텍스트의 품질을 1-10점으로 평가해주세요:
            "인공지능 기술의 발전으로 우리 삶이 많이 편해졌습니다. 특히 자동번역과 음성인식 기술이 발달하면서 언어 장벽이 많이 해소되었습니다."
            
            평가 기준:
            1. 문법 정확성
            2. 내용의 논리성
            3. 표현의 명확성
            
            점수와 함께 간단한 이유를 설명해주세요.""",
            'korean_analysis': """다음 한국어 문장을 분석해주세요:
            "머신러닝과 딥러닝 기술이 발전하면서 AI가 인간의 창작 활동에도 영향을 미치고 있다."
            
            분석 요소:
            - 주요 키워드 추출
            - 문장 구조 분석
            - 의미 해석""",
            'long_context': """긴 텍스트 처리 테스트입니다. """ + "이것은 긴 텍스트 처리 능력을 테스트하기 위한 문장입니다. " * 50 + """
            위 텍스트를 요약해주세요."""
        }
        
    async def setup_session(self):
        """HTTP 세션 설정"""
        connector = aiohttp.TCPConnector(
            limit=50,
            limit_per_host=10,
            keepalive_timeout=30
        )
        
        timeout = aiohttp.ClientTimeout(total=60, connect=10)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout
        )
        
    async def cleanup_session(self):
        """세션 정리"""
        if self.session:
            await self.session.close()
            
    async def test_openai_api(self, iterations: int = 20) -> List[AIAPITestResult]:
        """OpenAI API 성능 테스트"""
        if not self.api_keys['openai']:
            self.logger.warning("OpenAI API 키가 설정되지 않음")
            return []
            
        models = ['gpt-3.5-turbo', 'gpt-4']
        results = []
        
        for model in models:
            for test_type, prompt in self.test_prompts.items():
                result = await self._test_openai_model(model, test_type, prompt, iterations)
                results.append(result)
                
        return results
        
    async def _test_openai_model(self, model: str, test_type: str, prompt: str, iterations: int) -> AIAPITestResult:
        """개별 OpenAI 모델 테스트"""
        self.logger.info(f"OpenAI {model} 테스트 중: {test_type}")
        
        response_times = []
        token_counts = []
        costs = []
        errors = []
        success_count = 0
        
        headers = {
            'Authorization': f'Bearer {self.api_keys["openai"]}',
            'Content-Type': 'application/json'
        }
        
        for i in range(iterations):
            try:
                start_time = time.time()
                
                data = {
                    'model': model,
                    'messages': [
                        {'role': 'user', 'content': prompt}
                    ],
                    'max_tokens': 500,
                    'temperature': 0.7
                }
                
                async with self.session.post(
                    'https://api.openai.com/v1/chat/completions',
                    headers=headers,
                    json=data
                ) as response:
                    end_time = time.time()
                    response_time = (end_time - start_time) * 1000  # ms
                    
                    if response.status == 200:
                        result = await response.json()
                        
                        # 토큰 수 및 비용 계산
                        usage = result.get('usage', {})
                        total_tokens = usage.get('total_tokens', 0)
                        
                        # 모델별 비용 계산 (예시 가격)
                        cost_per_1k_tokens = 0.002 if model == 'gpt-3.5-turbo' else 0.03
                        cost = (total_tokens / 1000) * cost_per_1k_tokens
                        
                        response_times.append(response_time)
                        token_counts.append(total_tokens)
                        costs.append(cost)
                        success_count += 1
                        
                    else:
                        error_text = await response.text()
                        errors.append(f"HTTP {response.status}: {error_text}")
                        
            except asyncio.TimeoutError:
                errors.append("Request timeout")
            except Exception as e:
                errors.append(f"Exception: {str(e)}")
                
            # API 율제한 고려 (요청 간 간격)
            await asyncio.sleep(0.1)
            
        # 통계 계산
        avg_response_time = statistics.mean(response_times) if response_times else 0
        avg_tokens = statistics.mean(token_counts) if token_counts else 0
        avg_cost = statistics.mean(costs) if costs else 0
        success_rate = (success_count / iterations) * 100
        
        return AIAPITestResult(
            provider='openai',
            model=model,
            test_type=test_type,
            response_times=response_times,
            token_counts=token_counts,
            costs=costs,
            success_count=success_count,
            error_count=len(errors),
            errors=errors,
            avg_response_time=avg_response_time,
            avg_tokens=avg_tokens,
            avg_cost=avg_cost,
            success_rate=success_rate
        )
        
    async def test_anthropic_api(self, iterations: int = 20) -> List[AIAPITestResult]:
        """Anthropic API 성능 테스트"""
        if not self.api_keys['anthropic']:
            self.logger.warning("Anthropic API 키가 설정되지 않음")
            return []
            
        models = ['claude-3-haiku-20240307', 'claude-3-sonnet-20240229']
        results = []
        
        for model in models:
            for test_type, prompt in self.test_prompts.items():
                result = await self._test_anthropic_model(model, test_type, prompt, iterations)
                results.append(result)
                
        return results
        
    async def _test_anthropic_model(self, model: str, test_type: str, prompt: str, iterations: int) -> AIAPITestResult:
        """개별 Anthropic 모델 테스트"""
        self.logger.info(f"Anthropic {model} 테스트 중: {test_type}")
        
        response_times = []
        token_counts = []
        costs = []
        errors = []
        success_count = 0
        
        headers = {
            'x-api-key': self.api_keys['anthropic'],
            'Content-Type': 'application/json',
            'anthropic-version': '2023-06-01'
        }
        
        for i in range(iterations):
            try:
                start_time = time.time()
                
                data = {
                    'model': model,
                    'max_tokens': 500,
                    'messages': [
                        {'role': 'user', 'content': prompt}
                    ]
                }
                
                async with self.session.post(
                    'https://api.anthropic.com/v1/messages',
                    headers=headers,
                    json=data
                ) as response:
                    end_time = time.time()
                    response_time = (end_time - start_time) * 1000
                    
                    if response.status == 200:
                        result = await response.json()
                        
                        # 토큰 수 추정 (Anthropic은 상세 사용량 정보 제한적)
                        content = result.get('content', [])
                        if content and isinstance(content, list):
                            text = content[0].get('text', '')
                            estimated_tokens = len(text.split()) * 1.3  # 대략적 추정
                        else:
                            estimated_tokens = 100  # 기본값
                            
                        # 모델별 비용 계산
                        cost_per_1k_tokens = 0.00025 if 'haiku' in model else 0.003
                        cost = (estimated_tokens / 1000) * cost_per_1k_tokens
                        
                        response_times.append(response_time)
                        token_counts.append(int(estimated_tokens))
                        costs.append(cost)
                        success_count += 1
                        
                    else:
                        error_text = await response.text()
                        errors.append(f"HTTP {response.status}: {error_text}")
                        
            except asyncio.TimeoutError:
                errors.append("Request timeout")
            except Exception as e:
                errors.append(f"Exception: {str(e)}")
                
            await asyncio.sleep(0.1)
            
        # 통계 계산
        avg_response_time = statistics.mean(response_times) if response_times else 0
        avg_tokens = statistics.mean(token_counts) if token_counts else 0
        avg_cost = statistics.mean(costs) if costs else 0
        success_rate = (success_count / iterations) * 100
        
        return AIAPITestResult(
            provider='anthropic',
            model=model,
            test_type=test_type,
            response_times=response_times,
            token_counts=token_counts,
            costs=costs,
            success_count=success_count,
            error_count=len(errors),
            errors=errors,
            avg_response_time=avg_response_time,
            avg_tokens=avg_tokens,
            avg_cost=avg_cost,
            success_rate=success_rate
        )
        
    async def test_stress_scenarios(self, concurrent_requests: int = 10) -> List[AIAPITestResult]:
        """스트레스 테스트 시나리오"""
        self.logger.info(f"스트레스 테스트: {concurrent_requests}개 동시 요청")
        
        # OpenAI API 스트레스 테스트 (API 키가 있는 경우)
        if self.api_keys['openai']:
            stress_result = await self._concurrent_api_test(
                'openai', 'gpt-3.5-turbo', concurrent_requests
            )
            return [stress_result]
        else:
            self.logger.warning("스트레스 테스트를 위한 API 키가 없음")
            return []
            
    async def _concurrent_api_test(self, provider: str, model: str, concurrent_requests: int) -> AIAPITestResult:
        """동시 API 요청 테스트"""
        async def single_request():
            """단일 API 요청"""
            start_time = time.time()
            
            try:
                if provider == 'openai':
                    headers = {
                        'Authorization': f'Bearer {self.api_keys["openai"]}',
                        'Content-Type': 'application/json'
                    }
                    
                    data = {
                        'model': model,
                        'messages': [
                            {'role': 'user', 'content': self.test_prompts['simple']}
                        ],
                        'max_tokens': 100
                    }
                    
                    async with self.session.post(
                        'https://api.openai.com/v1/chat/completions',
                        headers=headers,
                        json=data
                    ) as response:
                        end_time = time.time()
                        response_time = (end_time - start_time) * 1000
                        
                        if response.status == 200:
                            result = await response.json()
                            usage = result.get('usage', {})
                            tokens = usage.get('total_tokens', 0)
                            return {
                                'success': True,
                                'response_time': response_time,
                                'tokens': tokens,
                                'error': None
                            }
                        else:
                            error_text = await response.text()
                            return {
                                'success': False,
                                'response_time': response_time,
                                'tokens': 0,
                                'error': f"HTTP {response.status}: {error_text}"
                            }
                            
            except Exception as e:
                end_time = time.time()
                return {
                    'success': False,
                    'response_time': (end_time - start_time) * 1000,
                    'tokens': 0,
                    'error': str(e)
                }
                
        # 동시 요청 실행
        tasks = [single_request() for _ in range(concurrent_requests)]
        results = await asyncio.gather(*tasks)
        
        # 결과 분석
        response_times = []
        token_counts = []
        costs = []
        errors = []
        success_count = 0
        
        for result in results:
            response_times.append(result['response_time'])
            token_counts.append(result['tokens'])
            
            if result['success']:
                success_count += 1
                # 비용 계산
                cost = (result['tokens'] / 1000) * 0.002  # gpt-3.5-turbo 기준
                costs.append(cost)
            else:
                errors.append(result['error'])
                costs.append(0)
                
        avg_response_time = statistics.mean(response_times) if response_times else 0
        avg_tokens = statistics.mean(token_counts) if token_counts else 0
        avg_cost = statistics.mean(costs) if costs else 0
        success_rate = (success_count / concurrent_requests) * 100
        
        return AIAPITestResult(
            provider=provider,
            model=model,
            test_type='concurrent_stress',
            response_times=response_times,
            token_counts=token_counts,
            costs=costs,
            success_count=success_count,
            error_count=len(errors),
            errors=errors,
            avg_response_time=avg_response_time,
            avg_tokens=avg_tokens,
            avg_cost=avg_cost,
            success_rate=success_rate
        )
        
    async def test_reliability_scenarios(self) -> List[AIAPITestResult]:
        """신뢰성 테스트 시나리오"""
        reliability_results = []
        
        # 1. 연속 요청 안정성 테스트
        if self.api_keys['openai']:
            self.logger.info("연속 요청 안정성 테스트")
            result = await self._continuous_requests_test('openai', 'gpt-3.5-turbo', 50)
            reliability_results.append(result)
            
        # 2. 타임아웃 처리 테스트
        if self.api_keys['openai']:
            self.logger.info("타임아웃 처리 테스트")
            result = await self._timeout_handling_test('openai', 'gpt-3.5-turbo')
            reliability_results.append(result)
            
        return reliability_results
        
    async def _continuous_requests_test(self, provider: str, model: str, request_count: int) -> AIAPITestResult:
        """연속 요청 안정성 테스트"""
        response_times = []
        token_counts = []
        costs = []
        errors = []
        success_count = 0
        
        headers = {
            'Authorization': f'Bearer {self.api_keys[provider]}',
            'Content-Type': 'application/json'
        }
        
        for i in range(request_count):
            try:
                start_time = time.time()
                
                data = {
                    'model': model,
                    'messages': [
                        {'role': 'user', 'content': f"테스트 요청 #{i+1}: {self.test_prompts['simple']}"}
                    ],
                    'max_tokens': 100
                }
                
                async with self.session.post(
                    'https://api.openai.com/v1/chat/completions',
                    headers=headers,
                    json=data
                ) as response:
                    end_time = time.time()
                    response_time = (end_time - start_time) * 1000
                    
                    if response.status == 200:
                        result = await response.json()
                        usage = result.get('usage', {})
                        tokens = usage.get('total_tokens', 0)
                        cost = (tokens / 1000) * 0.002
                        
                        response_times.append(response_time)
                        token_counts.append(tokens)
                        costs.append(cost)
                        success_count += 1
                    else:
                        error_text = await response.text()
                        errors.append(f"Request {i+1}: HTTP {response.status}: {error_text}")
                        
            except Exception as e:
                errors.append(f"Request {i+1}: {str(e)}")
                
            # 안정성 측정을 위한 간격
            await asyncio.sleep(0.5)
            
        avg_response_time = statistics.mean(response_times) if response_times else 0
        avg_tokens = statistics.mean(token_counts) if token_counts else 0
        avg_cost = statistics.mean(costs) if costs else 0
        success_rate = (success_count / request_count) * 100
        
        return AIAPITestResult(
            provider=provider,
            model=model,
            test_type='continuous_reliability',
            response_times=response_times,
            token_counts=token_counts,
            costs=costs,
            success_count=success_count,
            error_count=len(errors),
            errors=errors,
            avg_response_time=avg_response_time,
            avg_tokens=avg_tokens,
            avg_cost=avg_cost,
            success_rate=success_rate
        )
        
    async def _timeout_handling_test(self, provider: str, model: str) -> AIAPITestResult:
        """타임아웃 처리 테스트"""
        # 매우 긴 프롬프트로 타임아웃 유발 시도
        long_prompt = "다음 텍스트를 매우 상세히 분석해주세요. " + "이는 긴 텍스트입니다. " * 200
        
        response_times = []
        errors = []
        success_count = 0
        
        headers = {
            'Authorization': f'Bearer {self.api_keys[provider]}',
            'Content-Type': 'application/json'
        }
        
        # 짧은 타임아웃으로 설정
        short_timeout = aiohttp.ClientTimeout(total=5, connect=2)
        
        for i in range(10):
            try:
                start_time = time.time()
                
                data = {
                    'model': model,
                    'messages': [
                        {'role': 'user', 'content': long_prompt}
                    ],
                    'max_tokens': 1000
                }
                
                async with self.session.post(
                    'https://api.openai.com/v1/chat/completions',
                    headers=headers,
                    json=data,
                    timeout=short_timeout
                ) as response:
                    end_time = time.time()
                    response_time = (end_time - start_time) * 1000
                    
                    if response.status == 200:
                        response_times.append(response_time)
                        success_count += 1
                    else:
                        error_text = await response.text()
                        errors.append(f"HTTP {response.status}: {error_text}")
                        
            except asyncio.TimeoutError:
                end_time = time.time()
                response_times.append((end_time - start_time) * 1000)
                errors.append("Timeout as expected")
            except Exception as e:
                errors.append(f"Exception: {str(e)}")
                
            await asyncio.sleep(1)
            
        avg_response_time = statistics.mean(response_times) if response_times else 0
        success_rate = (success_count / 10) * 100
        
        return AIAPITestResult(
            provider=provider,
            model=model,
            test_type='timeout_handling',
            response_times=response_times,
            token_counts=[],
            costs=[],
            success_count=success_count,
            error_count=len(errors),
            errors=errors,
            avg_response_time=avg_response_time,
            avg_tokens=0,
            avg_cost=0,
            success_rate=success_rate
        )
        
    def analyze_results(self, results: List[AIAPITestResult]) -> Dict:
        """AI API 테스트 결과 분석"""
        if not results:
            return {}
            
        analysis = {
            'summary': {
                'total_tests': len(results),
                'total_requests': sum(r.success_count + r.error_count for r in results),
                'overall_success_rate': 0,
                'avg_response_time': 0,
                'total_cost': 0,
                'fastest_provider': '',
                'most_reliable_provider': ''
            },
            'by_provider': {},
            'by_model': {},
            'by_test_type': {},
            'recommendations': []
        }
        
        # 제공업체별 분석
        provider_stats = {}
        for result in results:
            provider = result.provider
            if provider not in provider_stats:
                provider_stats[provider] = {
                    'total_requests': 0,
                    'successful_requests': 0,
                    'total_response_time': 0,
                    'total_cost': 0,
                    'response_times': []
                }
                
            stats = provider_stats[provider]
            stats['total_requests'] += result.success_count + result.error_count
            stats['successful_requests'] += result.success_count
            stats['total_response_time'] += sum(result.response_times)
            stats['total_cost'] += sum(result.costs)
            stats['response_times'].extend(result.response_times)
            
        # 제공업체별 요약
        for provider, stats in provider_stats.items():
            if stats['total_requests'] > 0:
                success_rate = (stats['successful_requests'] / stats['total_requests']) * 100
                avg_response_time = statistics.mean(stats['response_times']) if stats['response_times'] else 0
                
                analysis['by_provider'][provider] = {
                    'success_rate': success_rate,
                    'avg_response_time': avg_response_time,
                    'total_cost': stats['total_cost'],
                    'total_requests': stats['total_requests']
                }
                
        # 전체 요약 계산
        all_response_times = []
        total_successful = 0
        total_requests = 0
        total_cost = 0
        
        for result in results:
            all_response_times.extend(result.response_times)
            total_successful += result.success_count
            total_requests += result.success_count + result.error_count
            total_cost += sum(result.costs)
            
        if total_requests > 0:
            analysis['summary']['overall_success_rate'] = (total_successful / total_requests) * 100
            
        if all_response_times:
            analysis['summary']['avg_response_time'] = statistics.mean(all_response_times)
            
        analysis['summary']['total_cost'] = total_cost
        
        # 가장 빠른 제공업체 찾기
        if analysis['by_provider']:
            fastest = min(analysis['by_provider'].items(), key=lambda x: x[1]['avg_response_time'])
            analysis['summary']['fastest_provider'] = f"{fastest[0]} ({fastest[1]['avg_response_time']:.2f}ms)"
            
            # 가장 신뢰할 수 있는 제공업체
            most_reliable = max(analysis['by_provider'].items(), key=lambda x: x[1]['success_rate'])
            analysis['summary']['most_reliable_provider'] = f"{most_reliable[0]} ({most_reliable[1]['success_rate']:.1f}%)"
            
        # 권장사항 생성
        recommendations = []
        
        for provider, stats in analysis['by_provider'].items():
            if stats['success_rate'] < 95:
                recommendations.append(f"{provider}: 성공률 {stats['success_rate']:.1f}% - 안정성 개선 필요")
                
            if stats['avg_response_time'] > 5000:  # 5초 초과
                recommendations.append(f"{provider}: 평균 응답시간 {stats['avg_response_time']:.2f}ms - 성능 최적화 필요")
                
        analysis['recommendations'] = recommendations
        
        return analysis
        
    def generate_report(self, analysis: Dict) -> str:
        """AI API 성능 테스트 리포트 생성"""
        report = []
        report.append("=" * 60)
        report.append("AI 모델 관리 시스템 - AI API 성능 테스트 리포트")
        report.append("=" * 60)
        report.append(f"테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # 전체 요약
        summary = analysis['summary']
        report.append("📊 전체 요약")
        report.append("-" * 30)
        report.append(f"총 테스트 수: {summary['total_tests']}")
        report.append(f"총 요청 수: {summary['total_requests']:,}")
        report.append(f"전체 성공률: {summary['overall_success_rate']:.1f}%")
        report.append(f"평균 응답시간: {summary['avg_response_time']:.2f}ms")
        report.append(f"총 비용: ${summary['total_cost']:.4f}")
        report.append(f"가장 빠른 제공업체: {summary['fastest_provider']}")
        report.append(f"가장 안정적인 제공업체: {summary['most_reliable_provider']}")
        report.append("")
        
        # 제공업체별 분석
        if analysis['by_provider']:
            report.append("🏢 제공업체별 성능 분석")
            report.append("-" * 30)
            
            for provider, stats in analysis['by_provider'].items():
                report.append(f"📋 {provider.upper()}")
                report.append(f"  성공률: {stats['success_rate']:.1f}%")
                report.append(f"  평균 응답시간: {stats['avg_response_time']:.2f}ms")
                report.append(f"  총 비용: ${stats['total_cost']:.4f}")
                report.append(f"  총 요청: {stats['total_requests']:,}회")
                
                # 성능 등급
                if stats['success_rate'] >= 98 and stats['avg_response_time'] <= 3000:
                    grade = "🥇 우수"
                elif stats['success_rate'] >= 95 and stats['avg_response_time'] <= 5000:
                    grade = "🥈 양호"
                elif stats['success_rate'] >= 90:
                    grade = "🥉 보통"
                else:
                    grade = "❌ 개선필요"
                    
                report.append(f"  성능 등급: {grade}")
                report.append("")
                
        # 성능 기준 평가
        report.append("🎯 성능 기준 평가")
        report.append("-" * 30)
        
        criteria = {
            'success_rate': (95, '%'),
            'avg_response_time': (3000, 'ms')
        }
        
        for metric, (target, unit) in criteria.items():
            actual = summary.get(metric.replace('_', '_'), 0)
            if metric == 'success_rate':
                status = "✅ 통과" if actual >= target else "❌ 미달"
                report.append(f"  성공률: {actual:.1f}% (기준: ≥{target}%) {status}")
            else:
                status = "✅ 통과" if actual <= target else "❌ 미달"
                report.append(f"  응답시간: {actual:.2f}ms (기준: ≤{target}ms) {status}")
                
        report.append("")
        
        # 개선 권장사항
        if analysis['recommendations']:
            report.append("💡 개선 권장사항")
            report.append("-" * 30)
            for i, recommendation in enumerate(analysis['recommendations'], 1):
                report.append(f"  {i}. {recommendation}")
            report.append("")
            
        return "\n".join(report)

async def main():
    """메인 함수"""
    api_test = AIAPIPerformanceTest()
    
    try:
        await api_test.setup_session()
        
        # 기본 API 테스트
        print("🧪 OpenAI API 성능 테스트 실행 중...")
        openai_results = await api_test.test_openai_api(10)
        
        print("🧪 Anthropic API 성능 테스트 실행 중...")
        anthropic_results = await api_test.test_anthropic_api(10)
        
        # 스트레스 테스트
        print("🔥 스트레스 테스트 실행 중...")
        stress_results = await api_test.test_stress_scenarios(5)
        
        # 신뢰성 테스트
        print("🛡️ 신뢰성 테스트 실행 중...")
        reliability_results = await api_test.test_reliability_scenarios()
        
        # 전체 결과 분석
        all_results = openai_results + anthropic_results + stress_results + reliability_results
        analysis = api_test.analyze_results(all_results)
        
        # 리포트 생성 및 출력
        report = api_test.generate_report(analysis)
        print(report)
        
        # 결과 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 텍스트 리포트
        report_file = f"ai_api_performance_report_{timestamp}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
            
        # JSON 결과
        json_file = f"ai_api_performance_results_{timestamp}.json"
        json_data = {
            'analysis': analysis,
            'raw_results': [asdict(result) for result in all_results]
        }
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
            
        print(f"\n📄 리포트 저장: {report_file}")
        print(f"📊 JSON 결과 저장: {json_file}")
        
    finally:
        await api_test.cleanup_session()

if __name__ == "__main__":
    asyncio.run(main())