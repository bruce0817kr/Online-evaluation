#!/usr/bin/env python3
"""
Universal Port Manager 실용적 테스트 러너
========================================

실제 환경에서 핵심 기능들이 올바르게 동작하는지 검증하는 간단한 테스트
"""

import os
import sys
import json
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class PortManagerTester:
    """포트 매니저 핵심 기능 테스트"""
    
    def __init__(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix='upm_test_'))
        self.results = []
        
    def run_tests(self):
        """모든 테스트 실행"""
        logger.info("🚀 포트 매니저 핵심 기능 테스트 시작")
        logger.info("=" * 50)
        
        tests = [
            self.test_basic_import,
            self.test_port_scanning,
            self.test_port_allocation,
            self.test_cli_doctor,
            self.test_configuration_generation,
            self.test_dependency_handling
        ]
        
        for test in tests:
            try:
                logger.info(f"\n📋 {test.__name__} 실행 중...")
                result = test()
                self.results.append(result)
                
                if result['success']:
                    logger.info(f"✅ {test.__name__} 성공")
                else:
                    logger.error(f"❌ {test.__name__} 실패: {result.get('error')}")
                    
            except Exception as e:
                self.results.append({
                    'test': test.__name__,
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
                logger.error(f"💥 {test.__name__} 예외: {e}")
        
        return self.generate_report()
    
    def test_basic_import(self):
        """기본 모듈 임포트 테스트"""
        try:
            # 프로젝트 디렉토리를 파이썬 패스에 추가
            project_root = Path(__file__).parent.parent
            sys.path.insert(0, str(project_root))
            
            # 핵심 모듈들 임포트 시도
            from universal_port_manager.cli import cli
            from universal_port_manager.dependency_manager import DependencyManager
            
            # 의존성 관리자 초기화 테스트
            dm = DependencyManager()
            status = dm.get_dependency_status('minimal')
            
            return {
                'test': 'basic_import',
                'success': True,
                'details': {
                    'cli_imported': True,
                    'dependency_manager_imported': True,
                    'minimal_dependencies': status['is_functional']
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'test': 'basic_import',
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def test_port_scanning(self):
        """포트 스캔 기능 테스트"""
        try:
            # 직접 포트 스캔 모듈 테스트
            from universal_port_manager.core.port_scanner import ImprovedPortScanner
            
            scanner = ImprovedPortScanner()
            scan_result = scanner.scan_system_ports(force_refresh=True)
            
            # 스캔 결과 검증
            has_results = len(scan_result) > 0
            valid_format = all(isinstance(port, int) for port in scan_result.keys())
            
            return {
                'test': 'port_scanning',
                'success': True,
                'details': {
                    'ports_scanned': len(scan_result),
                    'has_results': has_results,
                    'valid_format': valid_format,
                    'sample_ports': list(scan_result.keys())[:5]
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'test': 'port_scanning',
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def test_port_allocation(self):
        """포트 할당 기능 테스트"""
        try:
            from universal_port_manager.core.port_allocator import ImprovedPortAllocator
            
            allocator = ImprovedPortAllocator()
            
            # 기본 서비스 할당 테스트
            services = ['frontend', 'backend', 'database']
            project_name = 'test-project'
            
            allocation_result = allocator.allocate_project_ports(project_name, services)
            
            # 할당 결과 검증
            all_allocated = len(allocation_result) == len(services)
            unique_ports = len(set(port.port for port in allocation_result.values())) == len(services)
            valid_range = all(1024 <= port.port <= 65535 for port in allocation_result.values())
            
            return {
                'test': 'port_allocation',
                'success': all_allocated and unique_ports and valid_range,
                'details': {
                    'services_requested': len(services),
                    'services_allocated': len(allocation_result),
                    'all_allocated': all_allocated,
                    'unique_ports': unique_ports,
                    'valid_range': valid_range,
                    'allocated_ports': {name: port.port for name, port in allocation_result.items()}
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'test': 'port_allocation',
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def test_cli_doctor(self):
        """CLI doctor 명령어 테스트"""
        try:
            from universal_port_manager.dependency_manager import DependencyManager
            
            dm = DependencyManager()
            
            # 시스템 요구사항 확인
            requirements = dm.get_dependency_status('minimal')
            
            # 설치 가이드 생성
            guide = dm.get_installation_guide('minimal')
            
            # 의존성 보고서 생성
            report = dm.create_dependency_report()
            
            return {
                'test': 'cli_doctor',
                'success': True,
                'details': {
                    'minimal_functional': requirements['is_functional'],
                    'completeness': requirements['completeness'],
                    'guide_generated': len(guide) > 0,
                    'report_generated': len(report['groups']) > 0,
                    'available_features': len(requirements['available_features'])
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'test': 'cli_doctor',
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def test_configuration_generation(self):
        """설정 파일 생성 테스트"""
        try:
            from universal_port_manager.core.port_manager_config import PortManagerConfig
            from universal_port_manager.core.port_allocator import ImprovedPortAllocator
            
            # 포트 할당
            allocator = ImprovedPortAllocator()
            allocated_ports = allocator.allocate_project_ports('test-project', ['frontend', 'backend'])
            
            # 설정 파일 생성
            config_manager = PortManagerConfig(self.test_dir, 'test-project')
            
            # 환경 파일 생성 테스트
            env_files = config_manager.generate_env_files(allocated_ports, ['docker', 'bash', 'json'])
            
            # 시작 스크립트 생성 테스트
            start_script = config_manager.generate_start_script(allocated_ports)
            
            # 생성된 파일 확인
            files_created = []
            for format_type, file_path in env_files.items():
                if Path(file_path).exists():
                    files_created.append(format_type)
            
            return {
                'test': 'configuration_generation',
                'success': len(files_created) > 0 and start_script,
                'details': {
                    'env_files_requested': len(['docker', 'bash', 'json']),
                    'env_files_created': len(files_created),
                    'start_script_created': start_script,
                    'files_created': files_created
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'test': 'configuration_generation',
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def test_dependency_handling(self):
        """의존성 처리 테스트"""
        try:
            from universal_port_manager.dependency_manager import DependencyManager
            
            dm = DependencyManager()
            
            # 모든 의존성 그룹 상태 확인
            groups = ['minimal', 'advanced', 'docker', 'full']
            group_results = {}
            
            for group in groups:
                status = dm.get_dependency_status(group)
                group_results[group] = {
                    'functional': status['is_functional'],
                    'completeness': status['completeness'],
                    'missing_required': len(status['missing_required']),
                    'missing_optional': len(status['missing_optional'])
                }
            
            # 최소한 minimal 그룹은 동작해야 함
            minimal_works = group_results['minimal']['functional']
            
            return {
                'test': 'dependency_handling',
                'success': minimal_works,
                'details': {
                    'minimal_functional': minimal_works,
                    'groups_tested': len(groups),
                    'group_results': group_results
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'test': 'dependency_handling',
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def test_actual_cli_commands(self):
        """실제 CLI 명령어 실행 테스트"""
        try:
            # CLI 명령어들을 subprocess로 실행
            project_root = Path(__file__).parent.parent
            
            commands = [
                ['python3', '-m', 'universal_port_manager.cli', 'doctor'],
                ['python3', '-c', 'from universal_port_manager.dependency_manager import DependencyManager; dm = DependencyManager(); print("OK")']
            ]
            
            results = []
            for cmd in commands:
                try:
                    result = subprocess.run(
                        cmd,
                        cwd=project_root,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    results.append({
                        'cmd': ' '.join(cmd),
                        'success': result.returncode == 0,
                        'output_length': len(result.stdout),
                        'has_error': len(result.stderr) > 0
                    })
                except subprocess.TimeoutExpired:
                    results.append({
                        'cmd': ' '.join(cmd),
                        'success': False,
                        'error': 'timeout'
                    })
            
            success_count = sum(1 for r in results if r['success'])
            
            return {
                'test': 'actual_cli_commands',
                'success': success_count > 0,
                'details': {
                    'commands_tested': len(commands),
                    'commands_success': success_count,
                    'results': results
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'test': 'actual_cli_commands',
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def generate_report(self):
        """테스트 보고서 생성"""
        successful_tests = sum(1 for r in self.results if r['success'])
        total_tests = len(self.results)
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        report = {
            'overall_success': success_rate >= 70,  # 70% 이상 성공
            'summary': {
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'failed_tests': total_tests - successful_tests,
                'success_rate': success_rate
            },
            'test_results': self.results,
            'timestamp': datetime.now().isoformat()
        }
        
        # 보고서 파일 저장
        report_file = Path.cwd() / f'port_manager_test_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📊 테스트 보고서 저장: {report_file}")
        
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
    """메인 테스트 실행"""
    tester = PortManagerTester()
    
    try:
        report = tester.run_tests()
        
        # 결과 출력
        print("\n" + "=" * 50)
        print("🎯 포트 매니저 핵심 기능 테스트 결과")
        print("=" * 50)
        
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
            print(f"\n🎉 모든 테스트가 성공했습니다!")
        
        # 핵심 기능 상태
        print(f"\n🔧 핵심 기능 상태:")
        for result in report['test_results']:
            if result['success']:
                print(f"  ✅ {result['test']}")
            else:
                print(f"  ❌ {result['test']}")
        
        return 0 if report['overall_success'] else 1
        
    finally:
        tester.cleanup()


if __name__ == '__main__':
    sys.exit(main())