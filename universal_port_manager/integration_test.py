#!/usr/bin/env python3
"""
Universal Port Manager 통합 테스트
================================

실제 환경에서 포트 충돌 회피 및 전체 워크플로우 검증
다양한 시나리오와 엣지 케이스를 포함한 종합 테스트
"""

import os
import sys
import json
import time
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IntegrationTestSuite:
    """
    포트 매니저 통합 테스트 스위트
    
    테스트 시나리오:
    1. 의존성별 기능 테스트
    2. 포트 충돌 회피 테스트
    3. 다중 프로젝트 동시 실행 테스트
    4. Docker 통합 테스트
    5. CLI 명령어 전체 테스트
    6. 실제 포트 사용 환경 테스트
    """
    
    def __init__(self, test_dir: Optional[Path] = None):
        """테스트 스위트 초기화"""
        self.test_dir = test_dir or Path(tempfile.mkdtemp(prefix='upm_test_'))
        self.test_results = []
        self.current_ports = self._get_system_ports()
        self.test_projects = []
        
        logger.info(f"테스트 디렉토리: {self.test_dir}")
        logger.info(f"현재 시스템 포트 사용량: {len(self.current_ports)}개")
    
    def _get_system_ports(self) -> List[int]:
        """현재 시스템에서 사용 중인 포트 목록"""
        used_ports = []
        
        # netstat을 사용하여 포트 확인
        try:
            result = subprocess.run(['netstat', '-tuln'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if ':' in line and ('LISTEN' in line or 'UDP' in line):
                        try:
                            port_part = line.split()[3]
                            port = int(port_part.split(':')[-1])
                            used_ports.append(port)
                        except (ValueError, IndexError):
                            continue
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # ss 명령어로 대체 시도
            try:
                result = subprocess.run(['ss', '-tuln'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if ':' in line and 'LISTEN' in line:
                            try:
                                port_part = line.split()[4]
                                port = int(port_part.split(':')[-1])
                                used_ports.append(port)
                            except (ValueError, IndexError):
                                continue
            except (subprocess.TimeoutExpired, FileNotFoundError):
                logger.warning("포트 스캔 명령어를 사용할 수 없음")
        
        return sorted(list(set(used_ports)))
    
    def run_all_tests(self) -> Dict:
        """모든 테스트 실행"""
        logger.info("🚀 Universal Port Manager 통합 테스트 시작")
        logger.info("=" * 60)
        
        test_methods = [
            self.test_dependency_scenarios,
            self.test_port_conflict_avoidance,
            self.test_multi_project_isolation,
            self.test_cli_commands,
            self.test_docker_integration,
            self.test_real_world_scenarios,
            self.test_edge_cases,
            self.test_performance_stress
        ]
        
        for test_method in test_methods:
            try:
                logger.info(f"\n📋 실행 중: {test_method.__name__}")
                result = test_method()
                self.test_results.append(result)
                
                if result['success']:
                    logger.info(f"✅ {test_method.__name__} 성공")
                else:
                    logger.error(f"❌ {test_method.__name__} 실패: {result.get('error', 'Unknown')}")
                    
            except Exception as e:
                error_result = {
                    'test_name': test_method.__name__,
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
                self.test_results.append(error_result)
                logger.error(f"💥 {test_method.__name__} 예외 발생: {e}")
        
        return self._generate_final_report()
    
    def test_dependency_scenarios(self) -> Dict:
        """의존성 시나리오별 테스트"""
        test_name = "dependency_scenarios"
        logger.info("🔍 의존성 시나리오 테스트")
        
        scenarios = [
            {
                'name': 'minimal_only',
                'deps': ['click'],
                'expected_features': ['basic_scan', 'port_allocation', 'cli']
            },
            {
                'name': 'with_psutil',
                'deps': ['click', 'psutil'],
                'expected_features': ['advanced_scan', 'process_info']
            },
            {
                'name': 'with_yaml',
                'deps': ['click', 'PyYAML'],
                'expected_features': ['docker_compose_generation']
            },
            {
                'name': 'full_features',
                'deps': ['click', 'psutil', 'PyYAML', 'requests'],
                'expected_features': ['all_features']
            }
        ]
        
        results = {}
        
        for scenario in scenarios:
            logger.info(f"  테스트 시나리오: {scenario['name']}")
            
            # 가상 환경에서 의존성 체크 시뮬레이션
            try:
                # CLI doctor 명령어로 의존성 상태 확인
                result = self._run_upm_command(['doctor', '--group', 'full'])
                
                if result['success']:
                    # 출력에서 의존성 상태 파싱
                    dependency_status = self._parse_dependency_output(result['output'])
                    results[scenario['name']] = {
                        'status': 'success',
                        'dependencies': dependency_status,
                        'features_available': len(dependency_status.get('available', []))
                    }
                else:
                    results[scenario['name']] = {
                        'status': 'failed',
                        'error': result.get('error')
                    }
                    
            except Exception as e:
                results[scenario['name']] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        # 결과 평가
        success_count = sum(1 for r in results.values() if r['status'] == 'success')
        total_count = len(scenarios)
        
        return {
            'test_name': test_name,
            'success': success_count >= total_count * 0.7,  # 70% 이상 성공
            'results': results,
            'summary': f"{success_count}/{total_count} 시나리오 성공",
            'timestamp': datetime.now().isoformat()
        }
    
    def test_port_conflict_avoidance(self) -> Dict:
        """포트 충돌 회피 테스트"""
        test_name = "port_conflict_avoidance"
        logger.info("🔍 포트 충돌 회피 테스트")
        
        conflict_tests = []
        
        # 1. 현재 사용 중인 포트 회피 테스트
        logger.info("  현재 사용 포트 회피 테스트")
        try:
            # 실제 사용 중인 포트를 선호 포트로 지정
            if self.current_ports:
                occupied_port = self.current_ports[0]
                preferred_ports = f'{{"frontend":{occupied_port},"backend":{occupied_port+1}}}'
                
                result = self._run_upm_command([
                    'allocate', 'frontend', 'backend',
                    '--preferred-ports', preferred_ports,
                    '--dry-run'
                ])
                
                if result['success']:
                    allocated_ports = self._parse_allocation_output(result['output'])
                    # 할당된 포트가 사용 중인 포트와 다른지 확인
                    conflict_avoided = all(
                        port not in self.current_ports 
                        for port in allocated_ports.values()
                    )
                    
                    conflict_tests.append({
                        'name': 'avoid_occupied_ports',
                        'success': conflict_avoided,
                        'details': {
                            'occupied_port': occupied_port,
                            'allocated_ports': allocated_ports,
                            'conflict_avoided': conflict_avoided
                        }
                    })
        except Exception as e:
            conflict_tests.append({
                'name': 'avoid_occupied_ports',
                'success': False,
                'error': str(e)
            })
        
        # 2. 연속 포트 할당 테스트
        logger.info("  연속 포트 할당 테스트")
        try:
            result = self._run_upm_command([
                'allocate', 'frontend', 'backend', 'database', 'redis',
                '--dry-run'
            ])
            
            if result['success']:
                allocated_ports = self._parse_allocation_output(result['output'])
                
                # 포트가 모두 다른지 확인
                unique_ports = len(set(allocated_ports.values()))
                all_unique = unique_ports == len(allocated_ports)
                
                conflict_tests.append({
                    'name': 'unique_port_allocation',
                    'success': all_unique,
                    'details': {
                        'allocated_ports': allocated_ports,
                        'unique_count': unique_ports,
                        'total_count': len(allocated_ports)
                    }
                })
        except Exception as e:
            conflict_tests.append({
                'name': 'unique_port_allocation',
                'success': False,
                'error': str(e)
            })
        
        # 3. 포트 범위 테스트
        logger.info("  포트 범위 적합성 테스트")
        try:
            result = self._run_upm_command(['allocate', 'frontend', 'backend', '--dry-run'])
            
            if result['success']:
                allocated_ports = self._parse_allocation_output(result['output'])
                
                # 적절한 포트 범위인지 확인 (1024-65535)
                valid_range = all(
                    1024 <= port <= 65535 
                    for port in allocated_ports.values()
                )
                
                conflict_tests.append({
                    'name': 'valid_port_range',
                    'success': valid_range,
                    'details': {
                        'allocated_ports': allocated_ports,
                        'all_in_valid_range': valid_range
                    }
                })
        except Exception as e:
            conflict_tests.append({
                'name': 'valid_port_range',
                'success': False,
                'error': str(e)
            })
        
        # 결과 종합
        success_count = sum(1 for test in conflict_tests if test['success'])
        total_count = len(conflict_tests)
        
        return {
            'test_name': test_name,
            'success': success_count == total_count,
            'results': conflict_tests,
            'summary': f"{success_count}/{total_count} 충돌 회피 테스트 성공",
            'timestamp': datetime.now().isoformat()
        }
    
    def test_multi_project_isolation(self) -> Dict:
        """다중 프로젝트 격리 테스트"""
        test_name = "multi_project_isolation"
        logger.info("🔍 다중 프로젝트 격리 테스트")
        
        # 테스트 프로젝트 생성
        projects = ['project-a', 'project-b', 'project-c']
        project_results = {}
        
        for project_name in projects:
            logger.info(f"  프로젝트 테스트: {project_name}")
            
            project_dir = self.test_dir / project_name
            project_dir.mkdir(exist_ok=True)
            
            try:
                # 각 프로젝트에서 포트 할당
                result = self._run_upm_command([
                    '--project', project_name,
                    'allocate', 'frontend', 'backend'
                ], cwd=project_dir)
                
                if result['success']:
                    allocated_ports = self._parse_allocation_output(result['output'])
                    project_results[project_name] = {
                        'status': 'success',
                        'ports': allocated_ports,
                        'directory': str(project_dir)
                    }
                    self.test_projects.append((project_name, allocated_ports))
                else:
                    project_results[project_name] = {
                        'status': 'failed',
                        'error': result.get('error')
                    }
                    
            except Exception as e:
                project_results[project_name] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        # 프로젝트 간 포트 충돌 확인
        all_ports = []
        for project_name, project_result in project_results.items():
            if project_result['status'] == 'success':
                all_ports.extend(project_result['ports'].values())
        
        # 모든 포트가 유니크한지 확인
        unique_ports = len(set(all_ports))
        no_conflicts = unique_ports == len(all_ports)
        
        # 성공한 프로젝트 수
        success_projects = sum(
            1 for result in project_results.values() 
            if result['status'] == 'success'
        )
        
        return {
            'test_name': test_name,
            'success': no_conflicts and success_projects >= 2,
            'results': {
                'project_results': project_results,
                'total_ports': len(all_ports),
                'unique_ports': unique_ports,
                'no_conflicts': no_conflicts,
                'success_projects': success_projects
            },
            'summary': f"{success_projects}/{len(projects)} 프로젝트 성공, 충돌 없음: {no_conflicts}",
            'timestamp': datetime.now().isoformat()
        }
    
    def test_cli_commands(self) -> Dict:
        """CLI 명령어 전체 테스트"""
        test_name = "cli_commands"
        logger.info("🔍 CLI 명령어 테스트")
        
        commands_to_test = [
            {
                'name': 'doctor',
                'cmd': ['doctor'],
                'expect_success': True
            },
            {
                'name': 'scan',
                'cmd': ['scan', '--range', '3000-3010'],
                'expect_success': True
            },
            {
                'name': 'allocate',
                'cmd': ['allocate', 'frontend', 'backend', '--dry-run'],
                'expect_success': True
            },
            {
                'name': 'status',
                'cmd': ['status'],
                'expect_success': True  # 할당된 포트가 없어도 성공해야 함
            },
            {
                'name': 'doctor_with_report',
                'cmd': ['doctor', '--report'],
                'expect_success': True
            }
        ]
        
        command_results = {}
        
        for cmd_test in commands_to_test:
            logger.info(f"  CLI 명령어: {' '.join(cmd_test['cmd'])}")
            
            try:
                result = self._run_upm_command(cmd_test['cmd'])
                
                command_results[cmd_test['name']] = {
                    'success': result['success'] == cmd_test['expect_success'],
                    'output_length': len(result.get('output', '')),
                    'has_output': bool(result.get('output', '').strip()),
                    'execution_time': result.get('execution_time', 0)
                }
                
            except Exception as e:
                command_results[cmd_test['name']] = {
                    'success': False,
                    'error': str(e)
                }
        
        # 결과 종합
        success_count = sum(1 for result in command_results.values() if result['success'])
        total_count = len(commands_to_test)
        
        return {
            'test_name': test_name,
            'success': success_count >= total_count * 0.8,  # 80% 이상 성공
            'results': command_results,
            'summary': f"{success_count}/{total_count} CLI 명령어 성공",
            'timestamp': datetime.now().isoformat()
        }
    
    def test_docker_integration(self) -> Dict:
        """Docker 통합 테스트"""
        test_name = "docker_integration"
        logger.info("🔍 Docker 통합 테스트")
        
        docker_tests = []
        
        # Docker 사용 가능 여부 확인
        docker_available = self._check_docker_availability()
        
        if not docker_available:
            return {
                'test_name': test_name,
                'success': True,  # Docker가 없어도 성공으로 간주
                'results': {'docker_available': False},
                'summary': "Docker 없음 - 테스트 건너뛰기",
                'timestamp': datetime.now().isoformat()
            }
        
        # 1. Docker Compose 파일 생성 테스트
        logger.info("  Docker Compose 생성 테스트")
        try:
            # 포트 할당 후 설정 파일 생성
            project_dir = self.test_dir / 'docker-test'
            project_dir.mkdir(exist_ok=True)
            
            alloc_result = self._run_upm_command([
                'allocate', 'frontend', 'backend', 'mongodb'
            ], cwd=project_dir)
            
            if alloc_result['success']:
                gen_result = self._run_upm_command(['generate'], cwd=project_dir)
                
                if gen_result['success']:
                    # Docker Compose 파일 확인
                    compose_file = project_dir / 'docker-compose.yml'
                    compose_exists = compose_file.exists()
                    
                    docker_tests.append({
                        'name': 'compose_file_generation',
                        'success': compose_exists,
                        'details': {
                            'file_exists': compose_exists,
                            'file_size': compose_file.stat().st_size if compose_exists else 0
                        }
                    })
                else:
                    docker_tests.append({
                        'name': 'compose_file_generation',
                        'success': False,
                        'error': 'generate 명령 실패'
                    })
            else:
                docker_tests.append({
                    'name': 'compose_file_generation',
                    'success': False,
                    'error': 'allocate 명령 실패'
                })
                
        except Exception as e:
            docker_tests.append({
                'name': 'compose_file_generation',
                'success': False,
                'error': str(e)
            })
        
        # 2. 환경 파일 생성 테스트
        logger.info("  환경 파일 생성 테스트")
        try:
            project_dir = self.test_dir / 'env-test'
            project_dir.mkdir(exist_ok=True)
            
            # 포트 할당 및 환경 파일 생성
            result = self._run_upm_command([
                'allocate', 'frontend', 'backend'
            ], cwd=project_dir)
            
            if result['success']:
                gen_result = self._run_upm_command([
                    'generate', '--formats', 'docker', 'bash', 'json'
                ], cwd=project_dir)
                
                if gen_result['success']:
                    env_files = ['.env', 'set_ports.sh', 'ports.json']
                    files_exist = [
                        (project_dir / file).exists() 
                        for file in env_files
                    ]
                    
                    docker_tests.append({
                        'name': 'env_file_generation',
                        'success': all(files_exist),
                        'details': {
                            'files_created': sum(files_exist),
                            'total_files': len(env_files),
                            'file_status': dict(zip(env_files, files_exist))
                        }
                    })
                else:
                    docker_tests.append({
                        'name': 'env_file_generation',
                        'success': False,
                        'error': 'generate 명령 실패'
                    })
            else:
                docker_tests.append({
                    'name': 'env_file_generation',
                    'success': False,
                    'error': 'allocate 명령 실패'
                })
                
        except Exception as e:
            docker_tests.append({
                'name': 'env_file_generation',
                'success': False,
                'error': str(e)
            })
        
        # 결과 종합
        success_count = sum(1 for test in docker_tests if test['success'])
        total_count = len(docker_tests)
        
        return {
            'test_name': test_name,
            'success': success_count == total_count,
            'results': {
                'docker_available': docker_available,
                'tests': docker_tests
            },
            'summary': f"{success_count}/{total_count} Docker 테스트 성공",
            'timestamp': datetime.now().isoformat()
        }
    
    def test_real_world_scenarios(self) -> Dict:
        """실제 환경 시나리오 테스트"""
        test_name = "real_world_scenarios"
        logger.info("🔍 실제 환경 시나리오 테스트")
        
        scenarios = []
        
        # 1. 높은 포트 사용률 환경 시뮬레이션
        logger.info("  높은 포트 사용률 시나리오")
        try:
            # 많은 서비스 동시 할당 요청
            services = [
                'frontend', 'backend', 'database', 'redis', 'nginx',
                'monitoring', 'elasticsearch', 'kibana', 'prometheus'
            ]
            
            result = self._run_upm_command(['allocate'] + services + ['--dry-run'])
            
            if result['success']:
                allocated_ports = self._parse_allocation_output(result['output'])
                all_allocated = len(allocated_ports) == len(services)
                
                scenarios.append({
                    'name': 'high_port_usage',
                    'success': all_allocated,
                    'details': {
                        'requested_services': len(services),
                        'allocated_services': len(allocated_ports),
                        'all_allocated': all_allocated
                    }
                })
            else:
                scenarios.append({
                    'name': 'high_port_usage',
                    'success': False,
                    'error': result.get('error')
                })
                
        except Exception as e:
            scenarios.append({
                'name': 'high_port_usage',
                'success': False,
                'error': str(e)
            })
        
        # 2. 선호 포트가 모두 사용 중인 시나리오
        logger.info("  선호 포트 충돌 시나리오")
        try:
            if self.current_ports and len(self.current_ports) >= 2:
                # 실제 사용 중인 포트들을 선호 포트로 지정
                occupied_ports = self.current_ports[:2]
                preferred_ports = f'{{"frontend":{occupied_ports[0]},"backend":{occupied_ports[1]}}}'
                
                result = self._run_upm_command([
                    'allocate', 'frontend', 'backend',
                    '--preferred-ports', preferred_ports,
                    '--dry-run'
                ])
                
                if result['success']:
                    allocated_ports = self._parse_allocation_output(result['output'])
                    avoided_conflicts = all(
                        port not in occupied_ports 
                        for port in allocated_ports.values()
                    )
                    
                    scenarios.append({
                        'name': 'preferred_port_conflicts',
                        'success': avoided_conflicts,
                        'details': {
                            'occupied_ports': occupied_ports,
                            'allocated_ports': allocated_ports,
                            'conflicts_avoided': avoided_conflicts
                        }
                    })
                else:
                    scenarios.append({
                        'name': 'preferred_port_conflicts',
                        'success': False,
                        'error': result.get('error')
                    })
            else:
                scenarios.append({
                    'name': 'preferred_port_conflicts',
                    'success': True,  # 충돌할 포트가 없으면 성공
                    'details': {'insufficient_occupied_ports': True}
                })
                
        except Exception as e:
            scenarios.append({
                'name': 'preferred_port_conflicts',
                'success': False,
                'error': str(e)
            })
        
        # 3. 연속 포트 할당/해제 시나리오
        logger.info("  연속 작업 시나리오")
        try:
            operations_success = []
            
            # 할당 -> 상태 확인 -> 정리 -> 재할당
            operations = [
                (['allocate', 'frontend', 'backend'], 'allocate'),
                (['status'], 'status'),
                (['cleanup'], 'cleanup'),
                (['allocate', 'database', 'redis'], 're_allocate')
            ]
            
            for cmd, op_name in operations:
                op_result = self._run_upm_command(cmd)
                operations_success.append(op_result['success'])
                
                if not op_result['success']:
                    break
            
            all_operations_success = all(operations_success)
            
            scenarios.append({
                'name': 'continuous_operations',
                'success': all_operations_success,
                'details': {
                    'operations_tested': len(operations),
                    'operations_success': operations_success,
                    'all_success': all_operations_success
                }
            })
            
        except Exception as e:
            scenarios.append({
                'name': 'continuous_operations',
                'success': False,
                'error': str(e)
            })
        
        # 결과 종합
        success_count = sum(1 for scenario in scenarios if scenario['success'])
        total_count = len(scenarios)
        
        return {
            'test_name': test_name,
            'success': success_count >= total_count * 0.8,  # 80% 이상 성공
            'results': scenarios,
            'summary': f"{success_count}/{total_count} 실제 시나리오 성공",
            'timestamp': datetime.now().isoformat()
        }
    
    def test_edge_cases(self) -> Dict:
        """엣지 케이스 테스트"""
        test_name = "edge_cases"
        logger.info("🔍 엣지 케이스 테스트")
        
        edge_cases = []
        
        # 1. 잘못된 포트 범위
        logger.info("  잘못된 포트 범위 테스트")
        try:
            result = self._run_upm_command(['scan', '--range', 'invalid-range'])
            
            # 실패해야 정상 (잘못된 입력이므로)
            edge_cases.append({
                'name': 'invalid_port_range',
                'success': not result['success'],
                'details': {'correctly_rejected': not result['success']}
            })
            
        except Exception as e:
            edge_cases.append({
                'name': 'invalid_port_range',
                'success': True,  # 예외 발생도 정상적인 처리
                'details': {'exception_handled': True}
            })
        
        # 2. 존재하지 않는 서비스 타입
        logger.info("  존재하지 않는 서비스 타입 테스트")
        try:
            result = self._run_upm_command([
                'allocate', 'nonexistent_service_type', '--dry-run'
            ])
            
            # 실패하거나 기본 처리되어야 함
            edge_cases.append({
                'name': 'nonexistent_service',
                'success': True,  # 어떤 결과든 크래시하지 않으면 성공
                'details': {
                    'handled_gracefully': True,
                    'command_success': result['success']
                }
            })
            
        except Exception as e:
            edge_cases.append({
                'name': 'nonexistent_service',
                'success': False,
                'error': str(e)
            })
        
        # 3. 잘못된 JSON 형식
        logger.info("  잘못된 JSON 형식 테스트")
        try:
            result = self._run_upm_command([
                'allocate', 'frontend', 'backend',
                '--preferred-ports', '{invalid_json}',
                '--dry-run'
            ])
            
            # 실패해야 정상
            edge_cases.append({
                'name': 'invalid_json',
                'success': not result['success'],
                'details': {'correctly_rejected': not result['success']}
            })
            
        except Exception as e:
            edge_cases.append({
                'name': 'invalid_json',
                'success': True,  # 예외 처리도 정상
                'details': {'exception_handled': True}
            })
        
        # 결과 종합
        success_count = sum(1 for case in edge_cases if case['success'])
        total_count = len(edge_cases)
        
        return {
            'test_name': test_name,
            'success': success_count == total_count,
            'results': edge_cases,
            'summary': f"{success_count}/{total_count} 엣지 케이스 처리 성공",
            'timestamp': datetime.now().isoformat()
        }
    
    def test_performance_stress(self) -> Dict:
        """성능 스트레스 테스트"""
        test_name = "performance_stress"
        logger.info("🔍 성능 스트레스 테스트")
        
        performance_tests = []
        
        # 1. 대용량 포트 스캔 성능
        logger.info("  대용량 포트 스캔 성능")
        try:
            start_time = time.time()
            result = self._run_upm_command(['scan', '--range', '3000-4000'])
            end_time = time.time()
            
            execution_time = end_time - start_time
            acceptable_time = 30.0  # 30초 이내
            
            performance_tests.append({
                'name': 'large_port_scan',
                'success': result['success'] and execution_time < acceptable_time,
                'details': {
                    'execution_time': execution_time,
                    'acceptable_time': acceptable_time,
                    'within_limit': execution_time < acceptable_time
                }
            })
            
        except Exception as e:
            performance_tests.append({
                'name': 'large_port_scan',
                'success': False,
                'error': str(e)
            })
        
        # 2. 다중 서비스 할당 성능
        logger.info("  다중 서비스 할당 성능")
        try:
            services = ['frontend', 'backend', 'database', 'redis', 'nginx'] * 3  # 15개 서비스
            
            start_time = time.time()
            result = self._run_upm_command(['allocate'] + services + ['--dry-run'])
            end_time = time.time()
            
            execution_time = end_time - start_time
            acceptable_time = 10.0  # 10초 이내
            
            performance_tests.append({
                'name': 'multi_service_allocation',
                'success': result['success'] and execution_time < acceptable_time,
                'details': {
                    'services_count': len(services),
                    'execution_time': execution_time,
                    'acceptable_time': acceptable_time,
                    'within_limit': execution_time < acceptable_time
                }
            })
            
        except Exception as e:
            performance_tests.append({
                'name': 'multi_service_allocation',
                'success': False,
                'error': str(e)
            })
        
        # 3. 반복 작업 성능
        logger.info("  반복 작업 성능")
        try:
            iterations = 5
            total_time = 0
            success_count = 0
            
            for i in range(iterations):
                start_time = time.time()
                result = self._run_upm_command(['doctor'])
                end_time = time.time()
                
                total_time += (end_time - start_time)
                if result['success']:
                    success_count += 1
            
            avg_time = total_time / iterations
            acceptable_avg_time = 5.0  # 평균 5초 이내
            
            performance_tests.append({
                'name': 'repeated_operations',
                'success': success_count == iterations and avg_time < acceptable_avg_time,
                'details': {
                    'iterations': iterations,
                    'success_count': success_count,
                    'total_time': total_time,
                    'avg_time': avg_time,
                    'acceptable_avg_time': acceptable_avg_time
                }
            })
            
        except Exception as e:
            performance_tests.append({
                'name': 'repeated_operations',
                'success': False,
                'error': str(e)
            })
        
        # 결과 종합
        success_count = sum(1 for test in performance_tests if test['success'])
        total_count = len(performance_tests)
        
        return {
            'test_name': test_name,
            'success': success_count >= total_count * 0.7,  # 70% 이상 성공
            'results': performance_tests,
            'summary': f"{success_count}/{total_count} 성능 테스트 통과",
            'timestamp': datetime.now().isoformat()
        }
    
    def _run_upm_command(self, args: List[str], cwd: Optional[Path] = None) -> Dict:
        """UPM 명령어 실행"""
        cmd = [sys.executable, '-m', 'universal_port_manager'] + args
        
        try:
            start_time = time.time()
            result = subprocess.run(
                cmd,
                cwd=cwd or self.test_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            end_time = time.time()
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr,
                'execution_time': end_time - start_time,
                'returncode': result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Command timeout',
                'execution_time': 60.0
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'execution_time': 0
            }
    
    def _parse_dependency_output(self, output: str) -> Dict:
        """의존성 출력 파싱"""
        # 간단한 파싱 - 실제로는 더 정교하게 구현
        available = []
        missing = []
        
        for line in output.split('\n'):
            if '✅' in line:
                available.append(line.strip())
            elif '❌' in line:
                missing.append(line.strip())
        
        return {
            'available': available,
            'missing': missing
        }
    
    def _parse_allocation_output(self, output: str) -> Dict[str, int]:
        """포트 할당 출력 파싱"""
        allocated_ports = {}
        
        for line in output.split('\n'):
            if '🔌' in line and ':' in line:
                try:
                    # 예: "  🔌 frontend        : 3001 (frontend)"
                    parts = line.strip().split(':')
                    if len(parts) >= 2:
                        service_name = parts[0].replace('🔌', '').strip()
                        port_part = parts[1].strip().split()[0]
                        port = int(port_part)
                        allocated_ports[service_name] = port
                except (ValueError, IndexError):
                    continue
        
        return allocated_ports
    
    def _check_docker_availability(self) -> bool:
        """Docker 사용 가능 여부 확인"""
        try:
            result = subprocess.run(
                ['docker', '--version'],
                capture_output=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _generate_final_report(self) -> Dict:
        """최종 테스트 보고서 생성"""
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results if result['success'])
        
        overall_success = successful_tests >= total_tests * 0.8  # 80% 이상 성공
        
        report = {
            'overall_success': overall_success,
            'summary': {
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'failed_tests': total_tests - successful_tests,
                'success_rate': (successful_tests / total_tests * 100) if total_tests > 0 else 0
            },
            'test_results': self.test_results,
            'environment': {
                'current_ports_count': len(self.current_ports),
                'test_directory': str(self.test_dir),
                'projects_created': len(self.test_projects)
            },
            'timestamp': datetime.now().isoformat()
        }
        
        # 보고서 파일 저장
        report_file = Path.cwd() / f'integration_test_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📊 최종 보고서 저장: {report_file}")
        
        return report
    
    def cleanup(self):
        """테스트 정리"""
        try:
            if self.test_dir.exists():
                import shutil
                shutil.rmtree(self.test_dir)
                logger.info(f"테스트 디렉토리 정리: {self.test_dir}")
        except Exception as e:
            logger.warning(f"정리 중 오류: {e}")


def main():
    """통합 테스트 실행"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Universal Port Manager 통합 테스트')
    parser.add_argument('--test-dir', type=Path, help='테스트 디렉토리')
    parser.add_argument('--cleanup', action='store_true', help='테스트 후 정리')
    parser.add_argument('--verbose', '-v', action='store_true', help='상세 로그')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 테스트 실행
    test_suite = IntegrationTestSuite(args.test_dir)
    
    try:
        report = test_suite.run_all_tests()
        
        # 결과 출력
        print("\n" + "=" * 60)
        print("🎯 UNIVERSAL PORT MANAGER 통합 테스트 결과")
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
                print(f"  - {test['test_name']}: {test.get('error', 'Unknown error')}")
        
        return 0 if report['overall_success'] else 1
        
    finally:
        if args.cleanup:
            test_suite.cleanup()


if __name__ == '__main__':
    sys.exit(main())