#!/usr/bin/env python3
"""
CLI 통합 테스트
===============

실제 CLI 명령어들을 실행하여 전체 워크플로우가 정상 동작하는지 검증
"""

import os
import sys
import json
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class CLIIntegrationTest:
    """CLI 통합 테스트"""
    
    def __init__(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix='cli_test_'))
        self.project_root = Path(__file__).parent.parent
        self.results = []
        
        # 환경 설정
        os.environ['PYTHONPATH'] = str(self.project_root)
        
    def run_cli_command(self, args, timeout=30):
        """CLI 명령어 실행"""
        cmd = [sys.executable, '-m', 'universal_port_manager.cli'] + args
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.test_dir,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=os.environ
            )
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Command timeout'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def test_workflow_scenario(self):
        """전체 워크플로우 시나리오 테스트"""
        logger.info("🔄 전체 워크플로우 시나리오 테스트")
        
        workflow_steps = [
            {
                'name': 'doctor_check',
                'cmd': ['doctor'],
                'description': '시스템 진단'
            },
            {
                'name': 'port_scan',
                'cmd': ['scan', '--range', '3000-3010'],
                'description': '포트 스캔'
            },
            {
                'name': 'port_allocation',
                'cmd': ['--project', 'test-workflow', 'allocate', 'frontend', 'backend', '--dry-run'],
                'description': '포트 할당 (미리보기)'
            },
            {
                'name': 'actual_allocation',
                'cmd': ['--project', 'test-workflow', 'allocate', 'frontend', 'backend'],
                'description': '실제 포트 할당'
            },
            {
                'name': 'status_check',
                'cmd': ['--project', 'test-workflow', 'status'],
                'description': '상태 확인'
            },
            {
                'name': 'generate_configs',
                'cmd': ['--project', 'test-workflow', 'generate'],
                'description': '설정 파일 생성'
            },
            {
                'name': 'cleanup',
                'cmd': ['--project', 'test-workflow', 'cleanup'],
                'description': '정리 작업'
            }
        ]
        
        workflow_results = []
        
        for step in workflow_steps:
            logger.info(f"  🔹 {step['description']}")
            
            result = self.run_cli_command(step['cmd'])
            
            step_result = {
                'name': step['name'],
                'description': step['description'],
                'success': result['success'],
                'has_output': len(result.get('stdout', '')) > 0
            }
            
            if not result['success']:
                step_result['error'] = result.get('error') or result.get('stderr')
            
            workflow_results.append(step_result)
            
            # 실패한 단계가 있으면 로그 출력
            if not result['success']:
                logger.warning(f"    ❌ 실패: {step_result.get('error')}")
            else:
                logger.info(f"    ✅ 성공")
        
        # 워크플로우 평가
        successful_steps = sum(1 for step in workflow_results if step['success'])
        total_steps = len(workflow_steps)
        
        return {
            'test': 'workflow_scenario',
            'success': successful_steps >= total_steps * 0.8,  # 80% 이상 성공
            'details': {
                'total_steps': total_steps,
                'successful_steps': successful_steps,
                'success_rate': successful_steps / total_steps * 100,
                'step_results': workflow_results
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def test_multi_project_scenario(self):
        """다중 프로젝트 시나리오 테스트"""
        logger.info("🔄 다중 프로젝트 시나리오 테스트")
        
        projects = ['project-alpha', 'project-beta', 'project-gamma']
        project_results = []
        
        for project in projects:
            logger.info(f"  🔹 프로젝트: {project}")
            
            # 각 프로젝트에 포트 할당
            result = self.run_cli_command([
                '--project', project, 
                'allocate', 'frontend', 'backend'
            ])
            
            project_result = {
                'project': project,
                'allocation_success': result['success'],
                'has_output': len(result.get('stdout', '')) > 0
            }
            
            if result['success']:
                # 상태 확인
                status_result = self.run_cli_command([
                    '--project', project, 'status'
                ])
                project_result['status_check'] = status_result['success']
                
                logger.info(f"    ✅ {project} 할당 및 상태 확인 성공")
            else:
                project_result['error'] = result.get('error') or result.get('stderr')
                logger.warning(f"    ❌ {project} 할당 실패")
            
            project_results.append(project_result)
        
        # 다중 프로젝트 결과 평가
        successful_projects = sum(
            1 for p in project_results 
            if p['allocation_success']
        )
        
        return {
            'test': 'multi_project_scenario',
            'success': successful_projects >= len(projects) * 0.7,  # 70% 이상 성공
            'details': {
                'total_projects': len(projects),
                'successful_projects': successful_projects,
                'project_results': project_results
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def test_error_handling(self):
        """오류 처리 시나리오 테스트"""
        logger.info("🔄 오류 처리 시나리오 테스트")
        
        error_scenarios = [
            {
                'name': 'invalid_port_range',
                'cmd': ['scan', '--range', 'invalid'],
                'should_fail': True,
                'description': '잘못된 포트 범위'
            },
            {
                'name': 'invalid_json',
                'cmd': ['allocate', 'frontend', '--preferred-ports', '{invalid}'],
                'should_fail': True,
                'description': '잘못된 JSON 형식'
            },
            {
                'name': 'unknown_command',
                'cmd': ['unknown_command'],
                'should_fail': True,
                'description': '존재하지 않는 명령어'
            },
            {
                'name': 'status_without_allocation',
                'cmd': ['--project', 'nonexistent', 'status'],
                'should_fail': False,  # 할당이 없어도 상태는 확인 가능해야 함
                'description': '할당 없는 프로젝트 상태 확인'
            }
        ]
        
        error_results = []
        
        for scenario in error_scenarios:
            logger.info(f"  🔹 {scenario['description']}")
            
            result = self.run_cli_command(scenario['cmd'])
            
            # 예상 결과와 실제 결과 비교
            expected_success = not scenario['should_fail']
            actual_success = result['success']
            correct_handling = (expected_success == actual_success)
            
            error_result = {
                'name': scenario['name'],
                'description': scenario['description'],
                'should_fail': scenario['should_fail'],
                'actual_success': actual_success,
                'correct_handling': correct_handling
            }
            
            if correct_handling:
                logger.info(f"    ✅ 올바른 처리")
            else:
                logger.warning(f"    ❌ 예상과 다른 결과")
                error_result['error'] = result.get('error') or result.get('stderr')
            
            error_results.append(error_result)
        
        # 오류 처리 평가
        correct_handling_count = sum(
            1 for r in error_results 
            if r['correct_handling']
        )
        
        return {
            'test': 'error_handling',
            'success': correct_handling_count == len(error_scenarios),
            'details': {
                'total_scenarios': len(error_scenarios),
                'correct_handling': correct_handling_count,
                'scenario_results': error_results
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def test_dependency_scenarios(self):
        """의존성 시나리오 테스트"""
        logger.info("🔄 의존성 시나리오 테스트")
        
        dependency_tests = [
            {
                'name': 'doctor_basic',
                'cmd': ['doctor'],
                'description': '기본 진단'
            },
            {
                'name': 'doctor_minimal',
                'cmd': ['doctor', '--group', 'minimal'],
                'description': '최소 의존성 진단'
            },
            {
                'name': 'doctor_full',
                'cmd': ['doctor', '--group', 'full'],
                'description': '전체 의존성 진단'
            },
            {
                'name': 'doctor_report',
                'cmd': ['doctor', '--report'],
                'description': '상세 보고서'
            }
        ]
        
        dependency_results = []
        
        for test in dependency_tests:
            logger.info(f"  🔹 {test['description']}")
            
            result = self.run_cli_command(test['cmd'])
            
            test_result = {
                'name': test['name'],
                'description': test['description'],
                'success': result['success'],
                'has_dependency_info': '의존성' in result.get('stdout', '') or 'dependency' in result.get('stdout', '').lower()
            }
            
            if result['success']:
                logger.info(f"    ✅ 성공")
            else:
                test_result['error'] = result.get('error') or result.get('stderr')
                logger.warning(f"    ❌ 실패")
            
            dependency_results.append(test_result)
        
        # 의존성 테스트 평가
        successful_tests = sum(
            1 for t in dependency_results 
            if t['success']
        )
        
        return {
            'test': 'dependency_scenarios',
            'success': successful_tests >= len(dependency_tests) * 0.8,
            'details': {
                'total_tests': len(dependency_tests),
                'successful_tests': successful_tests,
                'test_results': dependency_results
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def run_all_tests(self):
        """모든 CLI 통합 테스트 실행"""
        logger.info("🚀 CLI 통합 테스트 시작")
        logger.info("=" * 50)
        
        tests = [
            self.test_workflow_scenario,
            self.test_multi_project_scenario,
            self.test_error_handling,
            self.test_dependency_scenarios
        ]
        
        for test in tests:
            try:
                logger.info(f"\n📋 {test.__name__} 실행 중...")
                result = test()
                self.results.append(result)
                
                if result['success']:
                    logger.info(f"✅ {test.__name__} 성공")
                else:
                    logger.error(f"❌ {test.__name__} 실패")
                    
            except Exception as e:
                self.results.append({
                    'test': test.__name__,
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
                logger.error(f"💥 {test.__name__} 예외: {e}")
        
        return self.generate_report()
    
    def generate_report(self):
        """통합 테스트 보고서 생성"""
        successful_tests = sum(1 for r in self.results if r['success'])
        total_tests = len(self.results)
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        report = {
            'overall_success': success_rate >= 80,  # 80% 이상 성공
            'summary': {
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'failed_tests': total_tests - successful_tests,
                'success_rate': success_rate
            },
            'test_results': self.results,
            'environment': {
                'test_directory': str(self.test_dir),
                'project_root': str(self.project_root)
            },
            'timestamp': datetime.now().isoformat()
        }
        
        # 보고서 파일 저장
        report_file = Path.cwd() / f'cli_integration_test_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📊 CLI 통합 테스트 보고서 저장: {report_file}")
        
        return report
    
    def cleanup(self):
        """테스트 정리"""
        try:
            import shutil
            if self.test_dir.exists():
                shutil.rmtree(self.test_dir)
        except Exception as e:
            logger.warning(f"정리 중 오류: {e}")


def main():
    """CLI 통합 테스트 메인"""
    test_suite = CLIIntegrationTest()
    
    try:
        report = test_suite.run_all_tests()
        
        # 결과 출력
        print("\n" + "=" * 60)
        print("🎯 CLI 통합 테스트 결과")
        print("=" * 60)
        
        if report['overall_success']:
            print("✅ 전체 테스트 성공!")
        else:
            print("❌ 일부 테스트 실패")
        
        summary = report['summary']
        print(f"\n📊 요약:")
        print(f"  전체 테스트: {summary['total_tests']}개")
        print(f"  성공: {summary['successful_tests']}개")
        print(f"  실패: {summary['failed_tests']}개")
        print(f"  성공률: {summary['success_rate']:.1f}%")
        
        # 실패한 테스트 상세
        failed_tests = [r for r in report['test_results'] if not r['success']]
        if failed_tests:
            print(f"\n❌ 실패한 테스트:")
            for test in failed_tests:
                print(f"  - {test['test']}: {test.get('error', 'Unknown error')}")
        else:
            print(f"\n🎉 모든 CLI 테스트가 성공했습니다!")
        
        return 0 if report['overall_success'] else 1
        
    finally:
        test_suite.cleanup()


if __name__ == '__main__':
    sys.exit(main())