#!/usr/bin/env python3
"""
🔧 AI 모델 관리 시스템 - 종합 통합 테스트 오케스트레이터
모든 테스트를 통합 실행하고 결과를 분석하는 마스터 컨트롤러
"""

import asyncio
import json
import os
import sys
import time
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
import yaml
import psutil
import aiohttp
from concurrent.futures import ThreadPoolExecutor, as_completed

# 프로젝트 루트 경로 설정
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

@dataclass
class TestResult:
    """테스트 결과 데이터 클래스"""
    suite_name: str
    status: str  # success, failure, error, skipped
    execution_time: float
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    error_details: List[str]
    performance_metrics: Dict[str, Any]
    coverage_data: Dict[str, float]
    
@dataclass
class SystemMetrics:
    """시스템 메트릭 데이터 클래스"""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    memory_total: float
    disk_usage: float
    network_io: Dict[str, int]
    active_connections: int

class ComprehensiveTestOrchestrator:
    """종합 테스트 오케스트레이터"""
    
    def __init__(self, config_file: str = "integration_tests/config/test_config.yml"):
        self.config = self._load_config(config_file)
        self.results: List[TestResult] = []
        self.system_metrics: List[SystemMetrics] = []
        self.start_time = None
        self.end_time = None
        
        # 로깅 설정
        self._setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # 테스트 환경 변수
        self.test_env = {
            'PYTHONPATH': str(PROJECT_ROOT),
            'TEST_MODE': 'integration',
            'LOG_LEVEL': 'INFO'
        }
        
    def _setup_logging(self):
        """로깅 설정"""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler(f'integration_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
    def _load_config(self, config_file: str) -> Dict:
        """설정 파일 로드"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            self.logger.warning(f"설정 파일을 찾을 수 없음: {config_file}")
            return self._get_default_config()
            
    def _get_default_config(self) -> Dict:
        """기본 설정 반환"""
        return {
            'test_suites': {
                'environment_setup': {'enabled': True, 'timeout': 300},
                'functional_tests': {'enabled': True, 'timeout': 1800},
                'performance_tests': {'enabled': True, 'timeout': 900},
                'security_tests': {'enabled': True, 'timeout': 600},
                'ui_e2e_tests': {'enabled': True, 'timeout': 1200}
            },
            'system_monitoring': {
                'enabled': True,
                'interval': 10,  # 초
                'metrics': ['cpu', 'memory', 'disk', 'network']
            },
            'reporting': {
                'formats': ['json', 'html', 'junit'],
                'include_logs': True,
                'include_screenshots': True
            }
        }
        
    async def run_comprehensive_tests(self) -> Dict[str, Any]:
        """종합 테스트 실행"""
        self.logger.info("🚀 AI 모델 관리 시스템 종합 통합 테스트 시작")
        self.start_time = datetime.now()
        
        try:
            # 시스템 모니터링 시작
            monitoring_task = None
            if self.config.get('system_monitoring', {}).get('enabled', True):
                monitoring_task = asyncio.create_task(self._monitor_system_metrics())
                
            # 1. 환경 설정 및 준비
            await self._setup_test_environment()
            
            # 2. 병렬 테스트 실행
            await self._run_parallel_test_suites()
            
            # 3. 결과 수집 및 분석
            analysis_results = await self._analyze_test_results()
            
            # 4. 종합 리포트 생성
            await self._generate_comprehensive_reports(analysis_results)
            
            self.end_time = datetime.now()
            
            # 모니터링 태스크 정리
            if monitoring_task:
                monitoring_task.cancel()
                try:
                    await monitoring_task
                except asyncio.CancelledError:
                    pass
                    
            self.logger.info("✅ 종합 통합 테스트 완료")
            return analysis_results
            
        except Exception as e:
            self.logger.error(f"❌ 통합 테스트 실행 중 오류 발생: {e}")
            raise
            
    async def _setup_test_environment(self):
        """테스트 환경 설정"""
        self.logger.info("📋 테스트 환경 준비 중...")
        
        start_time = time.time()
        
        try:
            # Docker 환경 확인 및 시작
            await self._setup_docker_environment()
            
            # 테스트 데이터베이스 초기화
            await self._initialize_test_database()
            
            # 테스트 사용자 및 데이터 생성
            await self._create_test_data()
            
            # 서비스 헬스 체크
            await self._verify_services_health()
            
            execution_time = time.time() - start_time
            
            result = TestResult(
                suite_name="environment_setup",
                status="success",
                execution_time=execution_time,
                total_tests=4,
                passed_tests=4,
                failed_tests=0,
                skipped_tests=0,
                error_details=[],
                performance_metrics={"setup_time": execution_time},
                coverage_data={}
            )
            self.results.append(result)
            
            self.logger.info(f"✅ 테스트 환경 준비 완료 ({execution_time:.2f}초)")
            
        except Exception as e:
            self.logger.error(f"❌ 테스트 환경 설정 실패: {e}")
            result = TestResult(
                suite_name="environment_setup",
                status="failure",
                execution_time=time.time() - start_time,
                total_tests=4,
                passed_tests=0,
                failed_tests=4,
                skipped_tests=0,
                error_details=[str(e)],
                performance_metrics={},
                coverage_data={}
            )
            self.results.append(result)
            raise
            
    async def _setup_docker_environment(self):
        """Docker 환경 설정"""
        self.logger.info("🐳 Docker 환경 설정 중...")
        
        # Docker Compose 실행
        result = subprocess.run(
            ['docker-compose', '-f', 'docker-compose.yml', 'up', '-d'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise Exception(f"Docker 환경 시작 실패: {result.stderr}")
            
        # 서비스 시작 대기
        await asyncio.sleep(30)
        
    async def _initialize_test_database(self):
        """테스트 데이터베이스 초기화"""
        self.logger.info("🗄️ 테스트 데이터베이스 초기화 중...")
        
        # MongoDB 초기화 스크립트 실행
        result = subprocess.run(
            ['python', 'scripts/init_test_database.py'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            env={**os.environ, **self.test_env}
        )
        
        if result.returncode != 0:
            raise Exception(f"데이터베이스 초기화 실패: {result.stderr}")
            
    async def _create_test_data(self):
        """테스트 데이터 생성"""
        self.logger.info("📊 테스트 데이터 생성 중...")
        
        # 테스트 사용자 생성
        result = subprocess.run(
            ['python', 'scripts/create_test_users.py'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            env={**os.environ, **self.test_env}
        )
        
        if result.returncode != 0:
            raise Exception(f"테스트 데이터 생성 실패: {result.stderr}")
            
    async def _verify_services_health(self):
        """서비스 헬스 체크"""
        self.logger.info("🏥 서비스 상태 확인 중...")
        
        services = [
            {'name': 'Frontend', 'url': 'http://localhost:3000'},
            {'name': 'Backend', 'url': 'http://localhost:8000/health'},
            {'name': 'MongoDB', 'url': 'http://localhost:8000/api/health/database'},
        ]
        
        async with aiohttp.ClientSession() as session:
            for service in services:
                try:
                    async with session.get(service['url'], timeout=10) as response:
                        if response.status == 200:
                            self.logger.info(f"✅ {service['name']} 서비스 정상")
                        else:
                            raise Exception(f"{service['name']} 응답 코드: {response.status}")
                except Exception as e:
                    raise Exception(f"{service['name']} 헬스 체크 실패: {e}")
                    
    async def _run_parallel_test_suites(self):
        """병렬 테스트 스위트 실행"""
        self.logger.info("🔄 병렬 테스트 스위트 실행 중...")
        
        test_suites = self.config.get('test_suites', {})
        
        # 병렬 실행할 테스트 정의
        parallel_tests = []
        
        if test_suites.get('functional_tests', {}).get('enabled', True):
            parallel_tests.append(self._run_functional_tests())
            
        if test_suites.get('performance_tests', {}).get('enabled', True):
            parallel_tests.append(self._run_performance_tests())
            
        if test_suites.get('security_tests', {}).get('enabled', True):
            parallel_tests.append(self._run_security_tests())
            
        if test_suites.get('ui_e2e_tests', {}).get('enabled', True):
            parallel_tests.append(self._run_ui_e2e_tests())
            
        # 모든 테스트 병렬 실행
        if parallel_tests:
            await asyncio.gather(*parallel_tests, return_exceptions=True)
            
    async def _run_functional_tests(self):
        """기능 테스트 실행"""
        self.logger.info("🔧 기능 테스트 실행 중...")
        
        start_time = time.time()
        
        try:
            # Pytest 기능 테스트 실행
            result = subprocess.run(
                ['python', '-m', 'pytest', 'tests/', '-v', '--junit-xml=test-results/functional.xml', '--cov=backend', '--cov-report=json:test-results/functional-coverage.json'],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                env={**os.environ, **self.test_env},
                timeout=1800  # 30분
            )
            
            execution_time = time.time() - start_time
            
            # 결과 파싱
            passed_tests, failed_tests, skipped_tests = self._parse_pytest_output(result.stdout)
            
            # 커버리지 데이터 로드
            coverage_data = self._load_coverage_data('test-results/functional-coverage.json')
            
            test_result = TestResult(
                suite_name="functional_tests",
                status="success" if result.returncode == 0 else "failure",
                execution_time=execution_time,
                total_tests=passed_tests + failed_tests + skipped_tests,
                passed_tests=passed_tests,
                failed_tests=failed_tests,
                skipped_tests=skipped_tests,
                error_details=[] if result.returncode == 0 else [result.stderr],
                performance_metrics={"execution_time": execution_time},
                coverage_data=coverage_data
            )
            
            self.results.append(test_result)
            self.logger.info(f"✅ 기능 테스트 완료: {passed_tests}개 성공, {failed_tests}개 실패")
            
        except subprocess.TimeoutExpired:
            self.logger.error("❌ 기능 테스트 타임아웃")
            self.results.append(TestResult(
                suite_name="functional_tests",
                status="error",
                execution_time=time.time() - start_time,
                total_tests=0,
                passed_tests=0,
                failed_tests=0,
                skipped_tests=0,
                error_details=["Test timeout"],
                performance_metrics={},
                coverage_data={}
            ))
            
    async def _run_performance_tests(self):
        """성능 테스트 실행"""
        self.logger.info("📊 성능 테스트 실행 중...")
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                ['python', 'performance_tests/python/performance_test_runner.py', '--users', '50', '--duration', '600'],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                env={**os.environ, **self.test_env},
                timeout=900  # 15분
            )
            
            execution_time = time.time() - start_time
            
            # 성능 메트릭 파싱
            performance_metrics = self._parse_performance_results()
            
            test_result = TestResult(
                suite_name="performance_tests",
                status="success" if result.returncode == 0 else "failure",
                execution_time=execution_time,
                total_tests=1,
                passed_tests=1 if result.returncode == 0 else 0,
                failed_tests=0 if result.returncode == 0 else 1,
                skipped_tests=0,
                error_details=[] if result.returncode == 0 else [result.stderr],
                performance_metrics=performance_metrics,
                coverage_data={}
            )
            
            self.results.append(test_result)
            self.logger.info("✅ 성능 테스트 완료")
            
        except subprocess.TimeoutExpired:
            self.logger.error("❌ 성능 테스트 타임아웃")
            self.results.append(TestResult(
                suite_name="performance_tests",
                status="error",
                execution_time=time.time() - start_time,
                total_tests=1,
                passed_tests=0,
                failed_tests=1,
                skipped_tests=0,
                error_details=["Performance test timeout"],
                performance_metrics={},
                coverage_data={}
            ))
            
    async def _run_security_tests(self):
        """보안 테스트 실행"""
        self.logger.info("🔒 보안 테스트 실행 중...")
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                ['python', 'security_tests/run_security_tests.py', '--test-mode', 'safe'],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                env={**os.environ, **self.test_env},
                timeout=600  # 10분
            )
            
            execution_time = time.time() - start_time
            
            # 보안 결과 파싱
            security_metrics = self._parse_security_results()
            
            test_result = TestResult(
                suite_name="security_tests",
                status="success" if result.returncode == 0 else "failure",
                execution_time=execution_time,
                total_tests=1,
                passed_tests=1 if result.returncode == 0 else 0,
                failed_tests=0 if result.returncode == 0 else 1,
                skipped_tests=0,
                error_details=[] if result.returncode == 0 else [result.stderr],
                performance_metrics=security_metrics,
                coverage_data={}
            )
            
            self.results.append(test_result)
            self.logger.info("✅ 보안 테스트 완료")
            
        except subprocess.TimeoutExpired:
            self.logger.error("❌ 보안 테스트 타임아웃")
            self.results.append(TestResult(
                suite_name="security_tests",
                status="error",
                execution_time=time.time() - start_time,
                total_tests=1,
                passed_tests=0,
                failed_tests=1,
                skipped_tests=0,
                error_details=["Security test timeout"],
                performance_metrics={},
                coverage_data={}
            ))
            
    async def _run_ui_e2e_tests(self):
        """UI/E2E 테스트 실행"""
        self.logger.info("🌐 UI/E2E 테스트 실행 중...")
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                ['npx', 'playwright', 'test', '--reporter=junit'],
                cwd=PROJECT_ROOT / 'frontend',
                capture_output=True,
                text=True,
                env={**os.environ, **self.test_env},
                timeout=1200  # 20분
            )
            
            execution_time = time.time() - start_time
            
            # Playwright 결과 파싱
            passed_tests, failed_tests, skipped_tests = self._parse_playwright_output(result.stdout)
            
            test_result = TestResult(
                suite_name="ui_e2e_tests",
                status="success" if result.returncode == 0 else "failure",
                execution_time=execution_time,
                total_tests=passed_tests + failed_tests + skipped_tests,
                passed_tests=passed_tests,
                failed_tests=failed_tests,
                skipped_tests=skipped_tests,
                error_details=[] if result.returncode == 0 else [result.stderr],
                performance_metrics={"execution_time": execution_time},
                coverage_data={}
            )
            
            self.results.append(test_result)
            self.logger.info(f"✅ UI/E2E 테스트 완료: {passed_tests}개 성공, {failed_tests}개 실패")
            
        except subprocess.TimeoutExpired:
            self.logger.error("❌ UI/E2E 테스트 타임아웃")
            self.results.append(TestResult(
                suite_name="ui_e2e_tests",
                status="error",
                execution_time=time.time() - start_time,
                total_tests=0,
                passed_tests=0,
                failed_tests=0,
                skipped_tests=0,
                error_details=["UI/E2E test timeout"],
                performance_metrics={},
                coverage_data={}
            ))
            
    async def _monitor_system_metrics(self):
        """시스템 메트릭 모니터링"""
        interval = self.config.get('system_monitoring', {}).get('interval', 10)
        
        while True:
            try:
                # CPU 사용률
                cpu_usage = psutil.cpu_percent(interval=1)
                
                # 메모리 사용률
                memory = psutil.virtual_memory()
                
                # 디스크 사용률
                disk = psutil.disk_usage('/')
                
                # 네트워크 I/O
                network = psutil.net_io_counters()
                
                # 활성 연결 수
                connections = len(psutil.net_connections())
                
                metrics = SystemMetrics(
                    timestamp=datetime.now(),
                    cpu_usage=cpu_usage,
                    memory_usage=memory.percent,
                    memory_total=memory.total,
                    disk_usage=disk.percent,
                    network_io={
                        'bytes_sent': network.bytes_sent,
                        'bytes_recv': network.bytes_recv
                    },
                    active_connections=connections
                )
                
                self.system_metrics.append(metrics)
                
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.warning(f"시스템 메트릭 수집 오류: {e}")
                await asyncio.sleep(interval)
                
    def _parse_pytest_output(self, output: str) -> tuple:
        """Pytest 출력 파싱"""
        import re
        
        # Pytest 결과 패턴 매칭
        pattern = r'(\d+) passed'
        passed_match = re.search(pattern, output)
        passed_tests = int(passed_match.group(1)) if passed_match else 0
        
        pattern = r'(\d+) failed'
        failed_match = re.search(pattern, output)
        failed_tests = int(failed_match.group(1)) if failed_match else 0
        
        pattern = r'(\d+) skipped'
        skipped_match = re.search(pattern, output)
        skipped_tests = int(skipped_match.group(1)) if skipped_match else 0
        
        return passed_tests, failed_tests, skipped_tests
        
    def _parse_playwright_output(self, output: str) -> tuple:
        """Playwright 출력 파싱"""
        import re
        
        lines = output.split('\n')
        passed_tests = 0
        failed_tests = 0
        skipped_tests = 0
        
        for line in lines:
            if '✓' in line or 'passed' in line.lower():
                passed_tests += 1
            elif '✗' in line or 'failed' in line.lower():
                failed_tests += 1
            elif 'skipped' in line.lower():
                skipped_tests += 1
                
        return passed_tests, failed_tests, skipped_tests
        
    def _load_coverage_data(self, coverage_file: str) -> Dict[str, float]:
        """커버리지 데이터 로드"""
        try:
            with open(coverage_file, 'r') as f:
                coverage_data = json.load(f)
                return {
                    'line_coverage': coverage_data.get('totals', {}).get('percent_covered', 0),
                    'branch_coverage': coverage_data.get('totals', {}).get('percent_covered_display', 0)
                }
        except FileNotFoundError:
            return {'line_coverage': 0, 'branch_coverage': 0}
            
    def _parse_performance_results(self) -> Dict[str, Any]:
        """성능 테스트 결과 파싱"""
        try:
            # 최신 성능 테스트 결과 파일 찾기
            import glob
            files = glob.glob('performance_results_*.json')
            if files:
                latest_file = max(files, key=os.path.getctime)
                with open(latest_file, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
            
        return {
            'avg_response_time': 0,
            'p95_response_time': 0,
            'throughput': 0,
            'error_rate': 0
        }
        
    def _parse_security_results(self) -> Dict[str, Any]:
        """보안 테스트 결과 파싱"""
        try:
            # 최신 보안 테스트 결과 파일 찾기
            import glob
            files = glob.glob('comprehensive_security_report_*.json')
            if files:
                latest_file = max(files, key=os.path.getctime)
                with open(latest_file, 'r') as f:
                    data = json.load(f)
                    return {
                        'security_score': data.get('summary', {}).get('overall_security_score', 0),
                        'critical_issues': data.get('summary', {}).get('critical_issues', 0),
                        'high_issues': data.get('summary', {}).get('high_issues', 0)
                    }
        except Exception:
            pass
            
        return {
            'security_score': 0,
            'critical_issues': 0,
            'high_issues': 0
        }
        
    async def _analyze_test_results(self) -> Dict[str, Any]:
        """테스트 결과 분석"""
        self.logger.info("📈 테스트 결과 분석 중...")
        
        total_tests = sum(r.total_tests for r in self.results)
        total_passed = sum(r.passed_tests for r in self.results)
        total_failed = sum(r.failed_tests for r in self.results)
        total_skipped = sum(r.skipped_tests for r in self.results)
        
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        total_execution_time = sum(r.execution_time for r in self.results)
        
        # 커버리지 통합
        coverage_data = {}
        for result in self.results:
            if result.coverage_data:
                coverage_data.update(result.coverage_data)
                
        # 시스템 메트릭 분석
        system_analysis = self._analyze_system_metrics()
        
        # 성능 분석
        performance_analysis = self._analyze_performance_metrics()
        
        # 보안 분석
        security_analysis = self._analyze_security_metrics()
        
        analysis = {
            'overall_summary': {
                'total_tests': total_tests,
                'passed_tests': total_passed,
                'failed_tests': total_failed,
                'skipped_tests': total_skipped,
                'success_rate': success_rate,
                'total_execution_time': total_execution_time,
                'test_efficiency': total_tests / total_execution_time if total_execution_time > 0 else 0
            },
            'suite_results': [asdict(r) for r in self.results],
            'coverage_analysis': coverage_data,
            'system_metrics': system_analysis,
            'performance_analysis': performance_analysis,
            'security_analysis': security_analysis,
            'recommendations': self._generate_recommendations()
        }
        
        return analysis
        
    def _analyze_system_metrics(self) -> Dict[str, Any]:
        """시스템 메트릭 분석"""
        if not self.system_metrics:
            return {}
            
        cpu_values = [m.cpu_usage for m in self.system_metrics]
        memory_values = [m.memory_usage for m in self.system_metrics]
        
        return {
            'cpu_usage': {
                'avg': sum(cpu_values) / len(cpu_values),
                'max': max(cpu_values),
                'min': min(cpu_values)
            },
            'memory_usage': {
                'avg': sum(memory_values) / len(memory_values),
                'max': max(memory_values),
                'min': min(memory_values)
            },
            'monitoring_duration': len(self.system_metrics) * self.config.get('system_monitoring', {}).get('interval', 10)
        }
        
    def _analyze_performance_metrics(self) -> Dict[str, Any]:
        """성능 메트릭 분석"""
        performance_results = [r for r in self.results if r.suite_name == 'performance_tests']
        
        if not performance_results:
            return {}
            
        perf_result = performance_results[0]
        metrics = perf_result.performance_metrics
        
        return {
            'response_time_analysis': {
                'avg_response_time': metrics.get('avg_response_time', 0),
                'p95_response_time': metrics.get('p95_response_time', 0),
                'performance_grade': self._get_performance_grade(metrics.get('avg_response_time', 0))
            },
            'throughput_analysis': {
                'requests_per_second': metrics.get('throughput', 0),
                'error_rate': metrics.get('error_rate', 0)
            }
        }
        
    def _analyze_security_metrics(self) -> Dict[str, Any]:
        """보안 메트릭 분석"""
        security_results = [r for r in self.results if r.suite_name == 'security_tests']
        
        if not security_results:
            return {}
            
        sec_result = security_results[0]
        metrics = sec_result.performance_metrics
        
        return {
            'security_score': metrics.get('security_score', 0),
            'vulnerability_count': {
                'critical': metrics.get('critical_issues', 0),
                'high': metrics.get('high_issues', 0)
            },
            'security_grade': self._get_security_grade(metrics.get('security_score', 0))
        }
        
    def _get_performance_grade(self, avg_response_time: float) -> str:
        """성능 등급 산정"""
        if avg_response_time <= 1.0:
            return "A+"
        elif avg_response_time <= 2.0:
            return "A"
        elif avg_response_time <= 3.0:
            return "B"
        elif avg_response_time <= 5.0:
            return "C"
        else:
            return "D"
            
    def _get_security_grade(self, security_score: float) -> str:
        """보안 등급 산정"""
        if security_score >= 95:
            return "A+"
        elif security_score >= 90:
            return "A"
        elif security_score >= 80:
            return "B"
        elif security_score >= 70:
            return "C"
        else:
            return "D"
            
    def _generate_recommendations(self) -> List[Dict[str, str]]:
        """개선 권장사항 생성"""
        recommendations = []
        
        # 실패한 테스트 기반 권장사항
        failed_suites = [r for r in self.results if r.failed_tests > 0]
        for suite in failed_suites:
            recommendations.append({
                'category': 'test_failures',
                'priority': 'high',
                'title': f'{suite.suite_name} 테스트 실패 수정',
                'description': f'{suite.failed_tests}개의 실패한 테스트가 있습니다.',
                'action': '실패한 테스트를 분석하고 수정하세요.'
            })
            
        # 성능 기반 권장사항
        performance_results = [r for r in self.results if r.suite_name == 'performance_tests']
        if performance_results:
            perf_metrics = performance_results[0].performance_metrics
            if perf_metrics.get('avg_response_time', 0) > 3.0:
                recommendations.append({
                    'category': 'performance',
                    'priority': 'medium',
                    'title': '응답 시간 최적화',
                    'description': f'평균 응답시간이 {perf_metrics.get("avg_response_time", 0):.2f}초입니다.',
                    'action': '데이터베이스 쿼리 최적화 및 캐싱 전략을 검토하세요.'
                })
                
        # 커버리지 기반 권장사항
        total_coverage = 0
        coverage_count = 0
        for result in self.results:
            if result.coverage_data:
                total_coverage += result.coverage_data.get('line_coverage', 0)
                coverage_count += 1
                
        avg_coverage = total_coverage / coverage_count if coverage_count > 0 else 0
        if avg_coverage < 80:
            recommendations.append({
                'category': 'coverage',
                'priority': 'low',
                'title': '테스트 커버리지 향상',
                'description': f'현재 커버리지가 {avg_coverage:.1f}%입니다.',
                'action': '추가적인 테스트 케이스를 작성하여 커버리지를 80% 이상으로 높이세요.'
            })
            
        return recommendations
        
    async def _generate_comprehensive_reports(self, analysis: Dict[str, Any]):
        """종합 리포트 생성"""
        self.logger.info("📄 종합 리포트 생성 중...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON 리포트
        json_report = {
            'test_execution': {
                'start_time': self.start_time.isoformat() if self.start_time else None,
                'end_time': self.end_time.isoformat() if self.end_time else None,
                'total_duration': (self.end_time - self.start_time).total_seconds() if self.start_time and self.end_time else 0
            },
            'analysis': analysis,
            'raw_data': {
                'test_results': [asdict(r) for r in self.results],
                'system_metrics': [asdict(m) for m in self.system_metrics]
            }
        }
        
        json_filename = f"comprehensive_test_report_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(json_report, f, indent=2, ensure_ascii=False, default=str)
            
        # HTML 리포트
        html_report = self._generate_html_report(analysis)
        html_filename = f"comprehensive_test_report_{timestamp}.html"
        with open(html_filename, 'w', encoding='utf-8') as f:
            f.write(html_report)
            
        # JUnit XML 리포트
        junit_report = self._generate_junit_report()
        junit_filename = f"comprehensive_test_report_{timestamp}.xml"
        with open(junit_filename, 'w', encoding='utf-8') as f:
            f.write(junit_report)
            
        self.logger.info(f"📊 리포트 생성 완료:")
        self.logger.info(f"   JSON: {json_filename}")
        self.logger.info(f"   HTML: {html_filename}")
        self.logger.info(f"   JUnit: {junit_filename}")
        
    def _generate_html_report(self, analysis: Dict[str, Any]) -> str:
        """HTML 리포트 생성"""
        summary = analysis['overall_summary']
        success_rate = summary['success_rate']
        
        # 성공률에 따른 색상 결정
        if success_rate >= 95:
            color = "#28a745"  # 녹색
        elif success_rate >= 90:
            color = "#ffc107"  # 노란색
        else:
            color = "#dc3545"  # 빨간색
            
        html = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI 모델 관리 시스템 - 통합 테스트 리포트</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background: #f5f7fa; }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; text-align: center; margin-bottom: 30px; }}
        .success-rate {{ font-size: 72px; font-weight: bold; color: {color}; margin: 20px 0; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .card {{ background: white; border-radius: 10px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        .metric {{ text-align: center; }}
        .metric-value {{ font-size: 36px; font-weight: bold; margin: 10px 0; }}
        .metric-label {{ color: #666; font-size: 14px; }}
        .suite-result {{ margin: 10px 0; padding: 15px; border-radius: 5px; }}
        .suite-success {{ background: #d4edda; border-left: 4px solid #28a745; }}
        .suite-failure {{ background: #f8d7da; border-left: 4px solid #dc3545; }}
        .suite-error {{ background: #fff3cd; border-left: 4px solid #ffc107; }}
        .recommendations {{ background: #e7f3ff; border: 1px solid #b3d9ff; padding: 20px; border-radius: 10px; }}
        .chart-container {{ position: relative; height: 300px; margin: 20px 0; }}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔧 AI 모델 관리 시스템</h1>
            <h2>통합 테스트 리포트</h2>
            <p>실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="card" style="text-align: center; margin-bottom: 30px;">
            <h2>전체 성공률</h2>
            <div class="success-rate">{success_rate:.1f}%</div>
            <p>총 {summary['total_tests']}개 테스트 중 {summary['passed_tests']}개 성공</p>
        </div>
        
        <div class="grid">
            <div class="card metric">
                <div class="metric-value" style="color: #28a745;">{summary['passed_tests']}</div>
                <div class="metric-label">성공한 테스트</div>
            </div>
            <div class="card metric">
                <div class="metric-value" style="color: #dc3545;">{summary['failed_tests']}</div>
                <div class="metric-label">실패한 테스트</div>
            </div>
            <div class="card metric">
                <div class="metric-value" style="color: #ffc107;">{summary['skipped_tests']}</div>
                <div class="metric-label">건너뛴 테스트</div>
            </div>
            <div class="card metric">
                <div class="metric-value" style="color: #6c757d;">{summary['total_execution_time']:.1f}s</div>
                <div class="metric-label">총 실행 시간</div>
            </div>
        </div>
        
        <div class="card">
            <h3>📋 테스트 스위트별 결과</h3>
        """
        
        # 테스트 스위트 결과
        for result in self.results:
            status_class = "suite-success" if result.status == "success" else "suite-failure" if result.status == "failure" else "suite-error"
            status_icon = "✅" if result.status == "success" else "❌" if result.status == "failure" else "⚠️"
            
            html += f"""
            <div class="suite-result {status_class}">
                <h4>{status_icon} {result.suite_name}</h4>
                <p>성공: {result.passed_tests} | 실패: {result.failed_tests} | 실행시간: {result.execution_time:.2f}초</p>
            </div>
            """
            
        html += """
        </div>
        
        <div class="grid">
        """
        
        # 성능 분석
        perf_analysis = analysis.get('performance_analysis', {})
        if perf_analysis:
            response_time = perf_analysis.get('response_time_analysis', {})
            html += f"""
            <div class="card">
                <h3>📊 성능 분석</h3>
                <p><strong>평균 응답시간:</strong> {response_time.get('avg_response_time', 0):.2f}초</p>
                <p><strong>95% 응답시간:</strong> {response_time.get('p95_response_time', 0):.2f}초</p>
                <p><strong>성능 등급:</strong> {response_time.get('performance_grade', 'N/A')}</p>
            </div>
            """
            
        # 보안 분석
        sec_analysis = analysis.get('security_analysis', {})
        if sec_analysis:
            html += f"""
            <div class="card">
                <h3>🔒 보안 분석</h3>
                <p><strong>보안 점수:</strong> {sec_analysis.get('security_score', 0)}/100</p>
                <p><strong>치명적 취약점:</strong> {sec_analysis.get('vulnerability_count', {}).get('critical', 0)}개</p>
                <p><strong>보안 등급:</strong> {sec_analysis.get('security_grade', 'N/A')}</p>
            </div>
            """
            
        html += """
        </div>
        
        <div class="recommendations">
            <h3>💡 개선 권장사항</h3>
        """
        
        # 권장사항
        recommendations = analysis.get('recommendations', [])
        for i, rec in enumerate(recommendations[:5], 1):
            priority_color = "#dc3545" if rec['priority'] == 'high' else "#ffc107" if rec['priority'] == 'medium' else "#28a745"
            html += f"""
            <div style="margin: 15px 0; padding: 10px; border-left: 4px solid {priority_color}; background: rgba(255,255,255,0.5);">
                <h4>[{rec['priority'].upper()}] {rec['title']}</h4>
                <p>{rec['description']}</p>
                <p><strong>조치:</strong> {rec['action']}</p>
            </div>
            """
            
        html += """
        </div>
        
        <div style="text-align: center; margin-top: 40px; color: #666;">
            <p>이 리포트는 AI 모델 관리 시스템 통합 테스트 도구에 의해 자동 생성되었습니다.</p>
        </div>
    </div>
</body>
</html>
        """
        
        return html
        
    def _generate_junit_report(self) -> str:
        """JUnit XML 리포트 생성"""
        total_tests = sum(r.total_tests for r in self.results)
        total_failures = sum(r.failed_tests for r in self.results)
        total_time = sum(r.execution_time for r in self.results)
        
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="AI Model Management Integration Tests" 
           tests="{total_tests}" 
           failures="{total_failures}" 
           time="{total_time:.2f}">
"""
        
        for result in self.results:
            xml += f"""  <testcase name="{result.suite_name}" 
                    classname="IntegrationTest" 
                    time="{result.execution_time:.2f}">"""
            
            if result.failed_tests > 0:
                xml += f"""
    <failure message="Test failures detected">
      Failed tests: {result.failed_tests}
      Error details: {'; '.join(result.error_details)}
    </failure>"""
                    
            xml += """
  </testcase>"""
            
        xml += """
</testsuite>"""
        
        return xml

async def main():
    """메인 함수"""
    orchestrator = ComprehensiveTestOrchestrator()
    
    try:
        results = await orchestrator.run_comprehensive_tests()
        
        # 결과 요약 출력
        summary = results['overall_summary']
        print(f"\n{'='*60}")
        print(f"🎯 AI 모델 관리 시스템 통합 테스트 완료")
        print(f"{'='*60}")
        print(f"📊 전체 성공률: {summary['success_rate']:.1f}%")
        print(f"✅ 성공한 테스트: {summary['passed_tests']}개")
        print(f"❌ 실패한 테스트: {summary['failed_tests']}개")
        print(f"⏱️ 총 실행 시간: {summary['total_execution_time']:.1f}초")
        
        # 실패 시 종료 코드 1 반환
        if summary['failed_tests'] > 0:
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ 통합 테스트 실행 실패: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())