#!/usr/bin/env python3
"""
🚀 Gemini AI 협업 기반 최적화된 테스트 러너
온라인 평가 시스템의 모든 테스트를 효율적으로 실행하는 스크립트
"""

import asyncio
import json
import logging
import multiprocessing
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_runner.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """테스트 결과 데이터 클래스"""
    name: str
    status: str  # 'passed', 'failed', 'skipped'
    duration: float
    output: str
    error: Optional[str] = None
    coverage: Optional[float] = None

class OptimizedTestRunner:
    """Gemini AI 피드백 기반 최적화된 테스트 러너"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root or os.getcwd())
        self.results: List[TestResult] = []
        self.start_time = None
        self.parallel_workers = min(multiprocessing.cpu_count(), 4)
        self.cache_dir = self.project_root / '.test_cache'
        self.cache_dir.mkdir(exist_ok=True)
        
    def run_command(self, command: List[str], cwd: str = None, timeout: int = 300) -> Tuple[int, str, str]:
        """명령어 실행 (타임아웃 및 에러 처리 포함)"""
        try:
            process = subprocess.Popen(
                command,
                cwd=cwd or self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            stdout, stderr = process.communicate(timeout=timeout)
            return process.returncode, stdout, stderr
            
        except subprocess.TimeoutExpired:
            process.kill()
            return -1, "", f"Command timed out after {timeout} seconds"
        except Exception as e:
            return -1, "", str(e)

    def check_dependencies(self) -> Dict[str, bool]:
        """필수 의존성 확인"""
        dependencies = {
            'node': ['node', '--version'],
            'npm': ['npm', '--version'],
            'python': ['python3', '--version'],
            'playwright': ['npx', 'playwright', '--version']
        }
        
        status = {}
        for name, cmd in dependencies.items():
            try:
                returncode, _, _ = self.run_command(cmd, timeout=30)
                status[name] = returncode == 0
                logger.info(f"✅ {name}: {'Available' if status[name] else 'Not available'}")
            except Exception:
                status[name] = False
                logger.error(f"❌ {name}: Not available")
                
        return status

    def setup_frontend_environment(self) -> bool:
        """프론트엔드 환경 설정 (의존성 설치)"""
        frontend_dir = self.project_root / 'frontend'
        if not frontend_dir.exists():
            logger.error("Frontend directory not found")
            return False
            
        logger.info("🔧 Setting up frontend environment...")
        
        # package-lock.json과 node_modules 제거 (깨끗한 설치)
        lock_file = frontend_dir / 'package-lock.json'
        node_modules = frontend_dir / 'node_modules'
        
        if lock_file.exists():
            lock_file.unlink()
        if node_modules.exists():
            import shutil
            shutil.rmtree(node_modules, ignore_errors=True)
        
        # 의존성 설치 (호환성 옵션 적용)
        install_cmd = ['npm', 'install', '--legacy-peer-deps', '--no-fund', '--no-audit']
        returncode, stdout, stderr = self.run_command(install_cmd, cwd=frontend_dir, timeout=600)
        
        if returncode != 0:
            logger.error(f"Frontend dependency installation failed: {stderr}")
            return False
            
        logger.info("✅ Frontend environment ready")
        return True

    def run_frontend_tests(self) -> TestResult:
        """프론트엔드 테스트 실행"""
        start_time = time.time()
        frontend_dir = self.project_root / 'frontend'
        
        logger.info("🧪 Running frontend unit tests...")
        
        # Jest 테스트 실행 (CI 모드)
        test_cmd = ['npm', 'run', 'test:ci']
        returncode, stdout, stderr = self.run_command(test_cmd, cwd=frontend_dir, timeout=300)
        
        duration = time.time() - start_time
        
        if returncode == 0:
            # 커버리지 정보 추출
            coverage = self.extract_coverage_info(stdout)
            return TestResult(
                name="Frontend Unit Tests",
                status="passed",
                duration=duration,
                output=stdout,
                coverage=coverage
            )
        else:
            return TestResult(
                name="Frontend Unit Tests",
                status="failed",
                duration=duration,
                output=stdout,
                error=stderr
            )

    def run_e2e_tests(self) -> TestResult:
        """E2E 테스트 실행"""
        start_time = time.time()
        frontend_dir = self.project_root / 'frontend'
        
        logger.info("🎭 Running E2E tests...")
        
        # Playwright 브라우저 설치 확인
        install_cmd = ['npx', 'playwright', 'install', '--with-deps']
        self.run_command(install_cmd, cwd=frontend_dir, timeout=300)
        
        # E2E 테스트 실행 (헤드리스 모드)
        test_cmd = ['npx', 'playwright', 'test', '--reporter=json']
        returncode, stdout, stderr = self.run_command(test_cmd, cwd=frontend_dir, timeout=600)
        
        duration = time.time() - start_time
        
        if returncode == 0:
            return TestResult(
                name="E2E Tests",
                status="passed",
                duration=duration,
                output=stdout
            )
        else:
            return TestResult(
                name="E2E Tests",
                status="failed",
                duration=duration,
                output=stdout,
                error=stderr
            )

    def run_api_tests(self) -> TestResult:
        """API 테스트 실행 (Newman)"""
        start_time = time.time()
        api_dir = self.project_root / 'tests' / 'api'
        
        logger.info("🔌 Running API tests...")
        
        if not (api_dir / 'postman-collection.json').exists():
            return TestResult(
                name="API Tests",
                status="skipped",
                duration=0,
                output="Postman collection not found"
            )
        
        # Newman 테스트 실행
        test_cmd = [
            'newman', 'run', 'postman-collection.json',
            '--reporters', 'json',
            '--reporter-json-export', 'newman-results.json'
        ]
        returncode, stdout, stderr = self.run_command(test_cmd, cwd=api_dir, timeout=300)
        
        duration = time.time() - start_time
        
        if returncode == 0:
            return TestResult(
                name="API Tests",
                status="passed",
                duration=duration,
                output=stdout
            )
        else:
            return TestResult(
                name="API Tests",
                status="failed",
                duration=duration,
                output=stdout,
                error=stderr
            )

    def run_performance_tests(self) -> TestResult:
        """성능 테스트 실행"""
        start_time = time.time()
        perf_dir = self.project_root / 'tests' / 'performance'
        
        logger.info("⚡ Running performance tests...")
        
        if not perf_dir.exists():
            return TestResult(
                name="Performance Tests",
                status="skipped",
                duration=0,
                output="Performance test directory not found"
            )
        
        # Lighthouse 감사 실행
        test_cmd = ['npx', 'playwright', 'test', 'lighthouse-audit.spec.js']
        returncode, stdout, stderr = self.run_command(test_cmd, cwd=perf_dir, timeout=300)
        
        duration = time.time() - start_time
        
        if returncode == 0:
            return TestResult(
                name="Performance Tests",
                status="passed",
                duration=duration,
                output=stdout
            )
        else:
            return TestResult(
                name="Performance Tests",
                status="failed",
                duration=duration,
                output=stdout,
                error=stderr
            )

    def extract_coverage_info(self, output: str) -> Optional[float]:
        """테스트 출력에서 커버리지 정보 추출"""
        try:
            lines = output.split('\n')
            for line in lines:
                if 'All files' in line and '%' in line:
                    # Jest 커버리지 라인에서 퍼센트 추출
                    parts = line.split()
                    for part in parts:
                        if part.endswith('%'):
                            return float(part.replace('%', ''))
        except Exception:
            pass
        return None

    def run_parallel_tests(self) -> List[TestResult]:
        """병렬로 테스트 실행"""
        test_functions = [
            self.run_frontend_tests,
            self.run_e2e_tests,
            self.run_api_tests,
            self.run_performance_tests
        ]
        
        results = []
        with ThreadPoolExecutor(max_workers=self.parallel_workers) as executor:
            # 테스트 함수들을 병렬로 실행
            future_to_test = {executor.submit(test_func): test_func.__name__ 
                             for test_func in test_functions}
            
            for future in as_completed(future_to_test):
                test_name = future_to_test[future]
                try:
                    result = future.result()
                    results.append(result)
                    logger.info(f"✅ {result.name} completed: {result.status}")
                except Exception as exc:
                    logger.error(f"❌ {test_name} generated an exception: {exc}")
                    results.append(TestResult(
                        name=test_name,
                        status="failed",
                        duration=0,
                        output="",
                        error=str(exc)
                    ))
        
        return results

    def generate_report(self) -> Dict:
        """종합 테스트 보고서 생성"""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.status == 'passed')
        failed_tests = sum(1 for r in self.results if r.status == 'failed')
        skipped_tests = sum(1 for r in self.results if r.status == 'skipped')
        
        total_duration = sum(r.duration for r in self.results)
        
        # 커버리지 계산
        coverage_results = [r.coverage for r in self.results if r.coverage is not None]
        avg_coverage = sum(coverage_results) / len(coverage_results) if coverage_results else 0
        
        report = {
            'test_run_id': f'optimized_test_{int(time.time())}',
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'skipped': skipped_tests,
                'success_rate': passed_tests / total_tests if total_tests > 0 else 0,
                'total_duration': total_duration,
                'average_coverage': avg_coverage
            },
            'results': [
                {
                    'name': r.name,
                    'status': r.status,
                    'duration': r.duration,
                    'coverage': r.coverage,
                    'error': r.error
                }
                for r in self.results
            ],
            'gemini_recommendations': self.generate_gemini_recommendations(),
            'performance_metrics': self.calculate_performance_metrics()
        }
        
        return report

    def generate_gemini_recommendations(self) -> List[str]:
        """Gemini AI 스타일 개선 권장사항 생성"""
        recommendations = []
        
        # 실패한 테스트 분석
        failed_tests = [r for r in self.results if r.status == 'failed']
        if failed_tests:
            recommendations.append("🔧 실패한 테스트들을 우선적으로 수정하여 안정성을 향상시키세요.")
        
        # 커버리지 분석
        coverage_results = [r.coverage for r in self.results if r.coverage is not None]
        if coverage_results:
            avg_coverage = sum(coverage_results) / len(coverage_results)
            if avg_coverage < 80:
                recommendations.append(f"📈 현재 코드 커버리지가 {avg_coverage:.1f}%입니다. 80% 이상을 목표로 단위 테스트를 추가하세요.")
        
        # 성능 분석
        total_duration = sum(r.duration for r in self.results)
        if total_duration > 600:  # 10분 이상
            recommendations.append("⚡ 테스트 실행 시간이 길어 병렬화나 캐싱을 통한 최적화를 권장합니다.")
        
        # 스킵된 테스트 분석
        skipped_tests = [r for r in self.results if r.status == 'skipped']
        if skipped_tests:
            recommendations.append("⚠️ 스킵된 테스트들을 활성화하여 더 포괄적인 테스트 커버리지를 달성하세요.")
        
        return recommendations

    def calculate_performance_metrics(self) -> Dict:
        """성능 메트릭 계산"""
        if not self.results:
            return {}
        
        durations = [r.duration for r in self.results if r.duration > 0]
        
        return {
            'total_execution_time': sum(durations),
            'average_test_time': sum(durations) / len(durations) if durations else 0,
            'fastest_test': min(durations) if durations else 0,
            'slowest_test': max(durations) if durations else 0,
            'parallel_efficiency': self.parallel_workers / max(1, len(durations)) if durations else 0
        }

    def save_report(self, report: Dict) -> str:
        """보고서를 JSON 파일로 저장"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'gemini_optimized_test_report_{timestamp}.json'
        filepath = self.project_root / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📄 Test report saved to: {filepath}")
        return str(filepath)

    def run_all_tests(self) -> Dict:
        """모든 테스트 실행 및 보고서 생성"""
        self.start_time = time.time()
        
        logger.info("🚀 Starting Gemini AI Optimized Test Run...")
        logger.info(f"🔧 Using {self.parallel_workers} parallel workers")
        
        # 의존성 확인
        deps = self.check_dependencies()
        if not all(deps.values()):
            logger.warning("⚠️ Some dependencies are missing. Tests may fail.")
        
        # 프론트엔드 환경 설정
        if not self.setup_frontend_environment():
            logger.error("❌ Frontend environment setup failed")
            return {}
        
        # 병렬 테스트 실행
        self.results = self.run_parallel_tests()
        
        # 보고서 생성
        report = self.generate_report()
        
        # 보고서 저장
        report_path = self.save_report(report)
        
        # 결과 출력
        self.print_summary(report)
        
        return report

    def print_summary(self, report: Dict):
        """테스트 결과 요약 출력"""
        summary = report['summary']
        
        print("\n" + "="*80)
        print("🎯 GEMINI AI 최적화 테스트 결과 요약")
        print("="*80)
        print(f"📊 총 테스트: {summary['total_tests']}")
        print(f"✅ 성공: {summary['passed']}")
        print(f"❌ 실패: {summary['failed']}")
        print(f"⏭️  스킵: {summary['skipped']}")
        print(f"📈 성공률: {summary['success_rate']:.1%}")
        print(f"⏱️  총 실행 시간: {summary['total_duration']:.1f}초")
        print(f"📋 평균 커버리지: {summary['average_coverage']:.1f}%")
        
        # Gemini 권장사항 출력
        if report.get('gemini_recommendations'):
            print("\n🤖 Gemini AI 개선 권장사항:")
            for i, rec in enumerate(report['gemini_recommendations'], 1):
                print(f"   {i}. {rec}")
        
        print("="*80)

def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Gemini AI 최적화 테스트 러너')
    parser.add_argument('--project-root', help='프로젝트 루트 디렉토리')
    parser.add_argument('--workers', type=int, help='병렬 워커 수')
    parser.add_argument('--verbose', '-v', action='store_true', help='상세 출력')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    runner = OptimizedTestRunner(args.project_root)
    
    if args.workers:
        runner.parallel_workers = args.workers
    
    try:
        report = runner.run_all_tests()
        
        # 성공적으로 완료된 경우 종료 코드 0
        failed_tests = sum(1 for r in runner.results if r.status == 'failed')
        sys.exit(0 if failed_tests == 0 else 1)
        
    except KeyboardInterrupt:
        logger.info("🛑 Test run interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()