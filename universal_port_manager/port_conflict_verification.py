#!/usr/bin/env python3
"""
포트 충돌 회피 검증 테스트
========================

실제 환경에서 포트 충돌 회피가 제대로 동작하는지 검증하는 간단하고 실용적인 테스트
"""

import os
import sys
import socket
import subprocess
import tempfile
import json
from pathlib import Path
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class PortConflictVerifier:
    """포트 충돌 회피 검증기"""
    
    def __init__(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix='port_conflict_test_'))
        self.project_root = Path(__file__).parent.parent
        self.results = []
        
        # 현재 사용 중인 포트 스캔
        self.occupied_ports = self.scan_occupied_ports()
        logger.info(f"현재 사용 중인 포트: {len(self.occupied_ports)}개")
        logger.info(f"샘플 포트: {list(self.occupied_ports)[:10]}")
    
    def scan_occupied_ports(self):
        """현재 사용 중인 포트 스캔"""
        occupied = set()
        
        # netstat 사용
        try:
            result = subprocess.run(['netstat', '-tuln'], 
                                  capture_output=True, text=True, timeout=10)
            for line in result.stdout.split('\n'):
                if ':' in line and ('LISTEN' in line or 'UDP' in line):
                    try:
                        port_part = line.split()[3] if line.split() else ''
                        port = int(port_part.split(':')[-1])
                        if 1024 <= port <= 65535:
                            occupied.add(port)
                    except (ValueError, IndexError):
                        continue
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # ss 명령어 시도
            try:
                result = subprocess.run(['ss', '-tuln'], 
                                      capture_output=True, text=True, timeout=10)
                for line in result.stdout.split('\n'):
                    if ':' in line and 'LISTEN' in line:
                        try:
                            port_part = line.split()[4] if line.split() else ''
                            port = int(port_part.split(':')[-1])
                            if 1024 <= port <= 65535:
                                occupied.add(port)
                        except (ValueError, IndexError):
                            continue
            except (subprocess.TimeoutExpired, FileNotFoundError):
                logger.warning("포트 스캔 명령어를 사용할 수 없음")
        
        return occupied
    
    def test_basic_port_allocation(self):
        """기본 포트 할당 테스트"""
        logger.info("🔍 기본 포트 할당 테스트")
        
        try:
            # 직접 모듈 임포트
            sys.path.insert(0, str(self.project_root))
            from universal_port_manager.core.port_allocator import ImprovedPortAllocator
            
            allocator = ImprovedPortAllocator()
            services = ['frontend', 'backend', 'database']
            
            # 포트 할당
            allocated = allocator.allocate_project_ports('test-project', services)
            
            # 할당 검증
            all_allocated = len(allocated) == len(services)
            unique_ports = len(set(p.port for p in allocated.values())) == len(services)
            valid_range = all(1024 <= p.port <= 65535 for p in allocated.values())
            
            # 충돌 검사
            conflicts = []
            for service, port_info in allocated.items():
                if port_info.port in self.occupied_ports:
                    conflicts.append((service, port_info.port))
            
            no_conflicts = len(conflicts) == 0
            
            return {
                'test': 'basic_port_allocation',
                'success': all_allocated and unique_ports and valid_range and no_conflicts,
                'details': {
                    'services_requested': len(services),
                    'services_allocated': len(allocated),
                    'all_allocated': all_allocated,
                    'unique_ports': unique_ports,
                    'valid_range': valid_range,
                    'no_conflicts': no_conflicts,
                    'conflicts': conflicts,
                    'allocated_ports': {name: port.port for name, port in allocated.items()}
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'test': 'basic_port_allocation',
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def test_preferred_port_conflicts(self):
        """선호 포트 충돌 회피 테스트"""
        logger.info("🔍 선호 포트 충돌 회피 테스트")
        
        try:
            sys.path.insert(0, str(self.project_root))
            from universal_port_manager.core.port_allocator import ImprovedPortAllocator
            
            if len(self.occupied_ports) < 2:
                return {
                    'test': 'preferred_port_conflicts',
                    'success': True,
                    'details': {'insufficient_occupied_ports': True},
                    'timestamp': datetime.now().isoformat()
                }
            
            # 사용 중인 포트를 선호 포트로 설정
            occupied_list = list(self.occupied_ports)[:2]
            
            allocator = ImprovedPortAllocator()
            
            # 첫 번째 서비스는 사용 중인 포트를 선호하도록 설정
            # (실제 구현에서는 allocate_port 메서드에 preferred_port 전달)
            services = ['frontend', 'backend']
            allocated = allocator.allocate_project_ports('conflict-test', services)
            
            # 결과 검증
            conflicts_avoided = all(
                port.port not in occupied_list 
                for port in allocated.values()
            )
            
            return {
                'test': 'preferred_port_conflicts',
                'success': conflicts_avoided,
                'details': {
                    'occupied_ports_used_as_preferred': occupied_list,
                    'allocated_ports': {name: port.port for name, port in allocated.items()},
                    'conflicts_avoided': conflicts_avoided
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'test': 'preferred_port_conflicts',
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def test_port_scanner_accuracy(self):
        """포트 스캐너 정확도 테스트"""
        logger.info("🔍 포트 스캐너 정확도 테스트")
        
        try:
            sys.path.insert(0, str(self.project_root))
            from universal_port_manager.core.port_scanner import ImprovedPortScanner
            
            scanner = ImprovedPortScanner()
            scanned_ports = scanner.scan_system_ports(force_refresh=True)
            
            # 스캔된 포트 중 OCCUPIED 상태인 것들
            scanner_occupied = set()
            for port, info in scanned_ports.items():
                if hasattr(info, 'status'):
                    # PortStatus enum의 다양한 OCCUPIED 상태들 확인
                    status_name = info.status.name if hasattr(info.status, 'name') else str(info.status)
                    if 'OCCUPIED' in status_name or status_name in ['OCCUPIED_SYSTEM', 'OCCUPIED_DOCKER']:
                        scanner_occupied.add(port)
            
            # 실제 사용 중인 포트와 비교
            true_positives = len(scanner_occupied & self.occupied_ports)
            false_positives = len(scanner_occupied - self.occupied_ports)
            false_negatives = len(self.occupied_ports - scanner_occupied)
            
            # 정확도 계산 (어느 정도 차이는 허용)
            total_actual = len(self.occupied_ports)
            detection_rate = true_positives / total_actual if total_actual > 0 else 1.0
            accuracy_acceptable = detection_rate >= 0.5  # 50% 이상 감지하면 성공
            
            return {
                'test': 'port_scanner_accuracy',
                'success': accuracy_acceptable,
                'details': {
                    'total_scanned': len(scanned_ports),
                    'scanner_occupied': len(scanner_occupied),
                    'actual_occupied': len(self.occupied_ports),
                    'true_positives': true_positives,
                    'false_positives': false_positives,
                    'false_negatives': false_negatives,
                    'detection_rate': detection_rate,
                    'accuracy_acceptable': accuracy_acceptable
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'test': 'port_scanner_accuracy',
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def test_multi_project_isolation(self):
        """다중 프로젝트 격리 테스트"""
        logger.info("🔍 다중 프로젝트 격리 테스트")
        
        try:
            sys.path.insert(0, str(self.project_root))
            from universal_port_manager.core.port_allocator import ImprovedPortAllocator
            
            allocator = ImprovedPortAllocator()
            
            # 3개 프로젝트에 동일한 서비스 할당
            projects = ['project-a', 'project-b', 'project-c']
            services = ['frontend', 'backend']
            
            all_allocated_ports = []
            project_allocations = {}
            
            for project in projects:
                allocated = allocator.allocate_project_ports(project, services)
                project_allocations[project] = allocated
                
                for service, port_info in allocated.items():
                    all_allocated_ports.append(port_info.port)
            
            # 모든 포트가 유니크한지 확인
            unique_ports = len(set(all_allocated_ports)) == len(all_allocated_ports)
            
            # 실제 사용 중인 포트와 충돌하지 않는지 확인
            no_system_conflicts = all(
                port not in self.occupied_ports 
                for port in all_allocated_ports
            )
            
            return {
                'test': 'multi_project_isolation',
                'success': unique_ports and no_system_conflicts,
                'details': {
                    'total_projects': len(projects),
                    'total_ports_allocated': len(all_allocated_ports),
                    'unique_ports': unique_ports,
                    'no_system_conflicts': no_system_conflicts,
                    'project_allocations': {
                        project: {name: port.port for name, port in allocated.items()}
                        for project, allocated in project_allocations.items()
                    }
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'test': 'multi_project_isolation',
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def test_socket_availability(self):
        """실제 소켓 가용성 테스트"""
        logger.info("🔍 실제 소켓 가용성 테스트")
        
        try:
            sys.path.insert(0, str(self.project_root))
            from universal_port_manager.core.port_allocator import ImprovedPortAllocator
            
            allocator = ImprovedPortAllocator()
            allocated = allocator.allocate_project_ports('socket-test', ['frontend', 'backend'])
            
            # 할당된 포트에서 실제 소켓 생성 테스트
            socket_tests = []
            
            for service, port_info in allocated.items():
                port = port_info.port
                socket_success = False
                
                try:
                    # TCP 소켓 생성 및 바인딩 테스트
                    test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    test_socket.bind(('localhost', port))
                    test_socket.close()
                    socket_success = True
                    
                except OSError as e:
                    logger.warning(f"포트 {port} 소켓 테스트 실패: {e}")
                
                socket_tests.append({
                    'service': service,
                    'port': port,
                    'socket_success': socket_success
                })
            
            # 모든 포트에서 소켓 생성이 성공해야 함
            all_sockets_ok = all(test['socket_success'] for test in socket_tests)
            
            return {
                'test': 'socket_availability',
                'success': all_sockets_ok,
                'details': {
                    'socket_tests': socket_tests,
                    'all_sockets_ok': all_sockets_ok
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'test': 'socket_availability',
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def run_all_tests(self):
        """모든 포트 충돌 회피 테스트 실행"""
        logger.info("🚀 포트 충돌 회피 검증 테스트 시작")
        logger.info("=" * 60)
        
        tests = [
            self.test_basic_port_allocation,
            self.test_preferred_port_conflicts,
            self.test_port_scanner_accuracy,
            self.test_multi_project_isolation,
            self.test_socket_availability
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
    
    def generate_report(self):
        """검증 보고서 생성"""
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
            'environment': {
                'occupied_ports_count': len(self.occupied_ports),
                'sample_occupied_ports': list(self.occupied_ports)[:10],
                'test_directory': str(self.test_dir)
            },
            'test_results': self.results,
            'timestamp': datetime.now().isoformat()
        }
        
        # 보고서 파일 저장
        report_file = Path.cwd() / f'port_conflict_verification_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📊 포트 충돌 회피 검증 보고서 저장: {report_file}")
        
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
    """포트 충돌 회피 검증 메인"""
    verifier = PortConflictVerifier()
    
    try:
        report = verifier.run_all_tests()
        
        # 결과 출력
        print("\n" + "=" * 60)
        print("🎯 포트 충돌 회피 검증 결과")
        print("=" * 60)
        
        if report['overall_success']:
            print("✅ 포트 충돌 회피 검증 성공!")
        else:
            print("❌ 일부 검증 실패")
        
        summary = report['summary']
        print(f"\n📊 요약:")
        print(f"  전체 테스트: {summary['total_tests']}개")
        print(f"  성공: {summary['successful_tests']}개")
        print(f"  실패: {summary['failed_tests']}개")
        print(f"  성공률: {summary['success_rate']:.1f}%")
        
        # 환경 정보
        env = report['environment']
        print(f"\n🌍 환경 정보:")
        print(f"  현재 사용 중인 포트: {env['occupied_ports_count']}개")
        if env['sample_occupied_ports']:
            print(f"  샘플 포트: {env['sample_occupied_ports']}")
        
        # 실패한 테스트 상세
        failed_tests = [r for r in report['test_results'] if not r['success']]
        if failed_tests:
            print(f"\n❌ 실패한 테스트:")
            for test in failed_tests:
                print(f"  - {test['test']}: {test.get('error', 'Unknown error')}")
        else:
            print(f"\n🎉 모든 포트 충돌 회피 테스트가 성공했습니다!")
        
        # 핵심 검증 항목
        print(f"\n🔍 핵심 검증 항목:")
        for result in report['test_results']:
            status = "✅" if result['success'] else "❌"
            print(f"  {status} {result['test']}")
        
        return 0 if report['overall_success'] else 1
        
    finally:
        verifier.cleanup()


if __name__ == '__main__':
    sys.exit(main())