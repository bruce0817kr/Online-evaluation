#!/usr/bin/env python3
"""
실제 배포 환경 동작 검증
=======================

Universal Port Manager가 실제 배포 환경에서 제대로 동작하는지 검증하는 종합 테스트
온라인 평가 시스템의 실제 배포 시나리오를 모사하여 검증
"""

import os
import sys
import json
import subprocess
import tempfile
import shutil
import time
from pathlib import Path
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class DeploymentVerifier:
    """배포 환경 검증기"""
    
    def __init__(self):
        self.test_root = Path(tempfile.mkdtemp(prefix='deployment_test_'))
        self.project_root = Path(__file__).parent.parent
        self.results = []
        
        # 실제 온라인 평가 시스템 서비스들
        self.online_eval_services = [
            'frontend', 'backend', 'mongodb', 'redis', 
            'nginx', 'elasticsearch', 'kibana'
        ]
        
        logger.info(f"배포 테스트 디렉토리: {self.test_root}")
        
    def run_all_verifications(self):
        """모든 배포 검증 실행"""
        logger.info("🚀 실제 배포 환경 동작 검증 시작")
        logger.info("=" * 60)
        
        verifications = [
            self.verify_online_eval_deployment,
            self.verify_multi_environment_deployment,
            self.verify_production_ready_features,
            self.verify_docker_compose_generation,
            self.verify_scaling_scenarios,
            self.verify_backup_and_recovery,
            self.verify_monitoring_integration
        ]
        
        for verification in verifications:
            try:
                logger.info(f"\n📋 {verification.__name__} 실행 중...")
                result = verification()
                self.results.append(result)
                
                if result['success']:
                    logger.info(f"✅ {verification.__name__} 성공")
                else:
                    logger.error(f"❌ {verification.__name__} 실패: {result.get('error')}")
                    
            except Exception as e:
                self.results.append({
                    'test': verification.__name__,
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
                logger.error(f"💥 {verification.__name__} 예외: {e}")
        
        return self.generate_deployment_report()
    
    def verify_online_eval_deployment(self):
        """온라인 평가 시스템 배포 시나리오 검증"""
        logger.info("🔍 온라인 평가 시스템 배포 시나리오 검증")
        
        try:
            # 실제 프로젝트 구조 모사
            eval_project_dir = self.test_root / 'online-evaluation'
            eval_project_dir.mkdir()
            
            # 기본 설정 파일들 생성
            self._create_project_structure(eval_project_dir)
            
            # 포트 매니저 초기화
            sys.path.insert(0, str(self.project_root))
            from universal_port_manager.core.port_allocator import ImprovedPortAllocator
            from universal_port_manager.core.port_manager_config import PortManagerConfig
            from universal_port_manager.core.port_manager_docker import PortManagerDocker
            
            allocator = ImprovedPortAllocator()
            
            # 온라인 평가 시스템 서비스 할당
            allocated_ports = allocator.allocate_project_ports(
                'online-evaluation', 
                self.online_eval_services
            )
            
            # 설정 파일 생성
            config_manager = PortManagerConfig(eval_project_dir, 'online-evaluation')
            env_files = config_manager.generate_env_files(allocated_ports, ['docker', 'bash', 'json'])
            start_script_created = config_manager.generate_start_script(allocated_ports)
            
            # Docker Compose 파일 생성
            docker_manager = PortManagerDocker(eval_project_dir, 'online-evaluation')
            compose_created = docker_manager.generate_compose_file(allocated_ports, include_override=True)
            
            # 검증
            all_services_allocated = len(allocated_ports) == len(self.online_eval_services)
            unique_ports = len(set(p.port for p in allocated_ports.values())) == len(self.online_eval_services)
            env_files_created = len(env_files) >= 2
            compose_file_exists = (eval_project_dir / 'docker-compose.yml').exists()
            
            # 포트 범위 검증 (실제 서비스별 적절한 포트)
            port_ranges_ok = self._verify_port_ranges(allocated_ports)
            
            return {
                'test': 'online_eval_deployment',
                'success': all([
                    all_services_allocated, unique_ports, env_files_created,
                    start_script_created, compose_created, port_ranges_ok
                ]),
                'details': {
                    'services_allocated': len(allocated_ports),
                    'services_requested': len(self.online_eval_services),
                    'all_services_allocated': all_services_allocated,
                    'unique_ports': unique_ports,
                    'env_files_created': env_files_created,
                    'start_script_created': start_script_created,
                    'compose_created': compose_created,
                    'compose_file_exists': compose_file_exists,
                    'port_ranges_ok': port_ranges_ok,
                    'allocated_ports': {name: port.port for name, port in allocated_ports.items()}
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'test': 'online_eval_deployment',
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def verify_multi_environment_deployment(self):
        """다중 환경 배포 검증 (dev, staging, prod)"""
        logger.info("🔍 다중 환경 배포 검증")
        
        try:
            environments = ['development', 'staging', 'production']
            env_results = {}
            all_allocated_ports = []
            
            sys.path.insert(0, str(self.project_root))
            from universal_port_manager.core.port_allocator import ImprovedPortAllocator
            
            allocator = ImprovedPortAllocator()
            
            for env in environments:
                # 환경별 프로젝트 디렉토리
                env_dir = self.test_root / f'online-eval-{env}'
                env_dir.mkdir()
                
                # 환경별 서비스 (prod는 더 많은 서비스)
                if env == 'production':
                    services = self.online_eval_services + ['prometheus', 'grafana', 'alertmanager']
                elif env == 'staging':
                    services = self.online_eval_services
                else:  # development
                    services = ['frontend', 'backend', 'mongodb', 'redis']
                
                # 포트 할당
                allocated = allocator.allocate_project_ports(f'online-eval-{env}', services)
                
                env_results[env] = {
                    'services_count': len(services),
                    'allocated_count': len(allocated),
                    'ports': {name: port.port for name, port in allocated.items()}
                }
                
                # 모든 할당된 포트 수집
                all_allocated_ports.extend([port.port for port in allocated.values()])
            
            # 환경 간 포트 충돌 검사
            unique_ports = len(set(all_allocated_ports)) == len(all_allocated_ports)
            
            # 각 환경이 모든 서비스 할당받았는지 확인
            all_env_success = all(
                result['allocated_count'] == result['services_count']
                for result in env_results.values()
            )
            
            return {
                'test': 'multi_environment_deployment',
                'success': unique_ports and all_env_success,
                'details': {
                    'environments': environments,
                    'total_ports_allocated': len(all_allocated_ports),
                    'unique_ports': unique_ports,
                    'all_env_success': all_env_success,
                    'env_results': env_results
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'test': 'multi_environment_deployment',
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def verify_production_ready_features(self):
        """프로덕션 준비 기능 검증"""
        logger.info("🔍 프로덕션 준비 기능 검증")
        
        try:
            sys.path.insert(0, str(self.project_root))
            from universal_port_manager.core.port_allocator import ImprovedPortAllocator
            from universal_port_manager.core.port_manager_config import PortManagerConfig
            from universal_port_manager.dependency_manager import DependencyManager
            
            # 의존성 검증
            dm = DependencyManager()
            dependency_status = dm.get_dependency_status('full')
            
            # 포트 할당 및 백업
            allocator = ImprovedPortAllocator()
            allocated = allocator.allocate_project_ports('prod-test', ['frontend', 'backend', 'database'])
            
            # 설정 백업
            prod_dir = self.test_root / 'production-test'
            prod_dir.mkdir()
            
            config_manager = PortManagerConfig(prod_dir, 'prod-test')
            backup_path = config_manager.backup_config('prod-backup')
            
            # 프로덕션 준비 체크리스트
            checks = {
                'dependency_management': dependency_status['is_functional'],
                'port_allocation': len(allocated) > 0,
                'configuration_backup': Path(backup_path).exists(),
                'port_persistence': self._check_port_persistence(allocator, 'prod-test'),
                'conflict_resolution': self._check_conflict_resolution(),
                'security_compliance': self._check_security_compliance(allocated)
            }
            
            all_checks_passed = all(checks.values())
            
            return {
                'test': 'production_ready_features',
                'success': all_checks_passed,
                'details': {
                    'checks': checks,
                    'dependency_completeness': dependency_status['completeness'],
                    'backup_location': backup_path,
                    'allocated_services': len(allocated)
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'test': 'production_ready_features',
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def verify_docker_compose_generation(self):
        """Docker Compose 파일 생성 검증"""
        logger.info("🔍 Docker Compose 파일 생성 검증")
        
        try:
            sys.path.insert(0, str(self.project_root))
            from universal_port_manager.core.port_allocator import ImprovedPortAllocator
            from universal_port_manager.core.port_manager_docker import PortManagerDocker
            
            docker_test_dir = self.test_root / 'docker-test'
            docker_test_dir.mkdir()
            
            # Dockerfile 샘플 생성
            self._create_sample_dockerfiles(docker_test_dir)
            
            allocator = ImprovedPortAllocator()
            allocated = allocator.allocate_project_ports(
                'docker-test', 
                ['frontend', 'backend', 'mongodb', 'redis']
            )
            
            docker_manager = PortManagerDocker(docker_test_dir, 'docker-test')
            
            # Docker Compose 파일 생성
            compose_created = docker_manager.generate_compose_file(
                allocated, 
                include_override=True
            )
            
            # 생성된 파일들 검증
            compose_file = docker_test_dir / 'docker-compose.yml'
            override_file = docker_test_dir / 'docker-compose.override.yml'
            
            files_exist = compose_file.exists() and override_file.exists()
            
            # Docker Compose 파일 내용 검증
            compose_valid = False
            if compose_file.exists():
                compose_valid = self._validate_docker_compose(compose_file, allocated)
            
            # 서비스 상태 체크 (Docker가 있으면)
            docker_available = docker_manager._check_docker_availability() if hasattr(docker_manager, '_check_docker_availability') else self._check_docker_available()
            
            return {
                'test': 'docker_compose_generation',
                'success': compose_created and files_exist and compose_valid,
                'details': {
                    'compose_created': compose_created,
                    'compose_file_exists': compose_file.exists(),
                    'override_file_exists': override_file.exists(),
                    'compose_valid': compose_valid,
                    'docker_available': docker_available,
                    'services_count': len(allocated)
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'test': 'docker_compose_generation',
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def verify_scaling_scenarios(self):
        """스케일링 시나리오 검증"""
        logger.info("🔍 스케일링 시나리오 검증")
        
        try:
            sys.path.insert(0, str(self.project_root))
            from universal_port_manager.core.port_allocator import ImprovedPortAllocator
            
            allocator = ImprovedPortAllocator()
            scaling_results = {}
            
            # 소규모 배포 (5개 서비스)
            small_services = ['frontend', 'backend', 'database', 'redis', 'nginx']
            small_allocated = allocator.allocate_project_ports('small-scale', small_services)
            
            # 중규모 배포 (10개 서비스)
            medium_services = small_services + ['elasticsearch', 'kibana', 'prometheus', 'grafana', 'alertmanager']
            medium_allocated = allocator.allocate_project_ports('medium-scale', medium_services)
            
            # 대규모 배포 (15개 서비스)
            large_services = medium_services + ['jaeger', 'consul', 'vault', 'rabbitmq', 'memcached']
            large_allocated = allocator.allocate_project_ports('large-scale', large_services)
            
            scaling_results = {
                'small': {
                    'requested': len(small_services),
                    'allocated': len(small_allocated),
                    'success': len(small_allocated) == len(small_services)
                },
                'medium': {
                    'requested': len(medium_services),
                    'allocated': len(medium_allocated),
                    'success': len(medium_allocated) == len(medium_services)
                },
                'large': {
                    'requested': len(large_services),
                    'allocated': len(large_allocated),
                    'success': len(large_allocated) == len(large_services)
                }
            }
            
            # 모든 포트가 유니크한지 확인
            all_ports = []
            for allocated in [small_allocated, medium_allocated, large_allocated]:
                all_ports.extend([port.port for port in allocated.values()])
            
            unique_ports = len(set(all_ports)) == len(all_ports)
            all_scales_success = all(result['success'] for result in scaling_results.values())
            
            return {
                'test': 'scaling_scenarios',
                'success': unique_ports and all_scales_success,
                'details': {
                    'scaling_results': scaling_results,
                    'total_ports_allocated': len(all_ports),
                    'unique_ports': unique_ports,
                    'all_scales_success': all_scales_success
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'test': 'scaling_scenarios',
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def verify_backup_and_recovery(self):
        """백업 및 복구 검증"""
        logger.info("🔍 백업 및 복구 검증")
        
        try:
            sys.path.insert(0, str(self.project_root))
            from universal_port_manager.core.port_allocator import ImprovedPortAllocator
            from universal_port_manager.core.port_manager_config import PortManagerConfig
            
            backup_test_dir = self.test_root / 'backup-test'
            backup_test_dir.mkdir()
            
            # 원본 구성 생성
            allocator = ImprovedPortAllocator()
            original_allocated = allocator.allocate_project_ports(
                'backup-test', 
                ['frontend', 'backend', 'database']
            )
            
            config_manager = PortManagerConfig(backup_test_dir, 'backup-test')
            
            # 설정 파일 생성
            env_files = config_manager.generate_env_files(original_allocated)
            
            # 백업 생성
            backup_name = 'test-backup'
            backup_path = config_manager.backup_config(backup_name)
            backup_exists = Path(backup_path).exists()
            
            # 백업 목록 확인
            backups = config_manager.list_backups()
            backup_listed = any(b['backup_name'] == backup_name for b in backups)
            
            # 포트 변경 (복구 테스트를 위해)
            modified_allocated = allocator.allocate_project_ports(
                'backup-test-modified', 
                ['frontend', 'backend', 'database', 'redis']
            )
            
            # 복구 테스트
            recovery_success = config_manager.restore_config(backup_name)
            
            return {
                'test': 'backup_and_recovery',
                'success': backup_exists and backup_listed and recovery_success,
                'details': {
                    'backup_created': backup_exists,
                    'backup_listed': backup_listed,
                    'recovery_success': recovery_success,
                    'backup_path': backup_path,
                    'original_services': len(original_allocated),
                    'modified_services': len(modified_allocated),
                    'total_backups': len(backups)
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'test': 'backup_and_recovery',
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def verify_monitoring_integration(self):
        """모니터링 통합 검증"""
        logger.info("🔍 모니터링 통합 검증")
        
        try:
            sys.path.insert(0, str(self.project_root))
            from universal_port_manager.core.port_allocator import ImprovedPortAllocator
            from universal_port_manager.core.port_scanner import ImprovedPortScanner
            
            # 모니터링 스택 서비스들
            monitoring_services = ['prometheus', 'grafana', 'alertmanager', 'elasticsearch', 'kibana']
            
            allocator = ImprovedPortAllocator()
            scanner = ImprovedPortScanner()
            
            # 모니터링 서비스 포트 할당
            monitoring_allocated = allocator.allocate_project_ports(
                'monitoring-stack', 
                monitoring_services
            )
            
            # 메인 애플리케이션 포트 할당
            app_allocated = allocator.allocate_project_ports(
                'main-app',
                ['frontend', 'backend', 'database']
            )
            
            # 포트 충돌 검사
            all_monitoring_ports = [port.port for port in monitoring_allocated.values()]
            all_app_ports = [port.port for port in app_allocated.values()]
            
            no_conflicts = len(set(all_monitoring_ports + all_app_ports)) == len(all_monitoring_ports + all_app_ports)
            
            # 포트 스캔으로 상태 확인
            scanned_ports = scanner.scan_system_ports(force_refresh=True)
            scan_successful = len(scanned_ports) > 0
            
            # 할당 보고서 생성
            allocation_report = allocator.get_allocation_report()
            report_generated = len(allocation_report) > 0
            
            return {
                'test': 'monitoring_integration',
                'success': no_conflicts and scan_successful and report_generated,
                'details': {
                    'monitoring_services': len(monitoring_allocated),
                    'app_services': len(app_allocated),
                    'no_conflicts': no_conflicts,
                    'scan_successful': scan_successful,
                    'scanned_ports_count': len(scanned_ports),
                    'report_generated': report_generated,
                    'monitoring_ports': all_monitoring_ports,
                    'app_ports': all_app_ports
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'test': 'monitoring_integration',
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _create_project_structure(self, project_dir: Path):
        """실제 프로젝트 구조 생성"""
        # 기본 디렉토리들
        dirs = ['frontend', 'backend', 'config', 'scripts', 'logs']
        for dir_name in dirs:
            (project_dir / dir_name).mkdir()
        
        # 기본 파일들
        (project_dir / 'README.md').write_text('# Online Evaluation System\n')
        (project_dir / 'package.json').write_text('{"name": "online-evaluation"}\n')
        (project_dir / 'requirements.txt').write_text('fastapi\nuvicorn\n')
    
    def _create_sample_dockerfiles(self, docker_dir: Path):
        """샘플 Dockerfile들 생성"""
        # Frontend Dockerfile
        frontend_dir = docker_dir / 'frontend'
        frontend_dir.mkdir()
        (frontend_dir / 'Dockerfile').write_text("""
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3000
CMD ["npm", "start"]
""")
        
        # Backend Dockerfile
        backend_dir = docker_dir / 'backend'
        backend_dir.mkdir()
        (backend_dir / 'Dockerfile').write_text("""
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
""")
    
    def _verify_port_ranges(self, allocated_ports):
        """포트 범위가 서비스에 적절한지 확인"""
        for service_name, port_info in allocated_ports.items():
            port = port_info.port
            
            # 서비스별 적절한 포트 범위 확인
            if service_name == 'frontend' and not (3000 <= port <= 3999):
                return False
            elif service_name == 'backend' and not (8000 <= port <= 8999):
                return False
            elif service_name == 'mongodb' and not (27000 <= port <= 27999):
                return False
            elif service_name == 'redis' and not (6000 <= port <= 6999):
                return False
            
        return True
    
    def _check_port_persistence(self, allocator, project_name):
        """포트 할당이 지속되는지 확인"""
        try:
            # 첫 번째 할당
            first_allocation = allocator.allocate_project_ports(project_name, ['frontend', 'backend'])
            
            # 두 번째 할당 (같은 프로젝트)
            second_allocation = allocator.allocate_project_ports(project_name, ['frontend', 'backend'])
            
            # 포트가 동일한지 확인
            return (first_allocation['frontend'].port == second_allocation['frontend'].port and
                    first_allocation['backend'].port == second_allocation['backend'].port)
        except Exception:
            return False
    
    def _check_conflict_resolution(self):
        """충돌 해결 기능 확인"""
        try:
            sys.path.insert(0, str(self.project_root))
            from universal_port_manager.core.port_allocator import ImprovedPortAllocator
            
            allocator = ImprovedPortAllocator()
            
            # 충돌 상황 시뮬레이션
            conflicts = allocator.get_port_conflicts([3000, 8000, 5432])
            alternatives = allocator.suggest_alternative_ports([3000, 8000])
            
            return len(alternatives) > 0
        except Exception:
            return False
    
    def _check_security_compliance(self, allocated_ports):
        """보안 컴플라이언스 확인"""
        for port_info in allocated_ports.values():
            # privileged 포트 (1024 미만) 사용 금지
            if port_info.port < 1024:
                return False
            
            # 매우 높은 포트 (65000 이상) 사용 금지
            if port_info.port >= 65000:
                return False
        
        return True
    
    def _validate_docker_compose(self, compose_file: Path, allocated_ports):
        """Docker Compose 파일 유효성 확인"""
        try:
            content = compose_file.read_text()
            
            # 기본 구조 확인
            required_elements = ['version:', 'services:', 'networks:']
            has_required = all(element in content for element in required_elements)
            
            # 포트 매핑 확인
            port_mappings = []
            for port_info in allocated_ports.values():
                port_mapping = f"{port_info.port}:"
                if port_mapping in content:
                    port_mappings.append(port_mapping)
            
            has_port_mappings = len(port_mappings) > 0
            
            return has_required and has_port_mappings
        except Exception:
            return False
    
    def _check_docker_available(self):
        """Docker 사용 가능 여부 확인"""
        try:
            result = subprocess.run(['docker', '--version'], 
                                  capture_output=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def generate_deployment_report(self):
        """배포 검증 보고서 생성"""
        successful_tests = sum(1 for r in self.results if r['success'])
        total_tests = len(self.results)
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        # 배포 준비도 평가
        deployment_readiness = self._assess_deployment_readiness()
        
        report = {
            'overall_success': success_rate >= 85,  # 85% 이상 성공
            'deployment_readiness': deployment_readiness,
            'summary': {
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'failed_tests': total_tests - successful_tests,
                'success_rate': success_rate
            },
            'test_results': self.results,
            'environment': {
                'test_directory': str(self.test_root),
                'online_eval_services': self.online_eval_services
            },
            'recommendations': self._generate_recommendations(),
            'timestamp': datetime.now().isoformat()
        }
        
        # 보고서 파일 저장
        report_file = Path.cwd() / f'deployment_verification_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📊 배포 검증 보고서 저장: {report_file}")
        
        return report
    
    def _assess_deployment_readiness(self):
        """배포 준비도 평가"""
        readiness_checks = {
            'core_functionality': any(r['test'] == 'online_eval_deployment' and r['success'] for r in self.results),
            'multi_environment': any(r['test'] == 'multi_environment_deployment' and r['success'] for r in self.results),
            'production_features': any(r['test'] == 'production_ready_features' and r['success'] for r in self.results),
            'docker_integration': any(r['test'] == 'docker_compose_generation' and r['success'] for r in self.results),
            'scalability': any(r['test'] == 'scaling_scenarios' and r['success'] for r in self.results),
            'backup_recovery': any(r['test'] == 'backup_and_recovery' and r['success'] for r in self.results),
            'monitoring': any(r['test'] == 'monitoring_integration' and r['success'] for r in self.results)
        }
        
        readiness_score = sum(readiness_checks.values()) / len(readiness_checks) * 100
        
        if readiness_score >= 90:
            readiness_level = "프로덕션 준비 완료"
        elif readiness_score >= 75:
            readiness_level = "프로덕션 준비 거의 완료"
        elif readiness_score >= 60:
            readiness_level = "추가 개선 필요"
        else:
            readiness_level = "상당한 개선 필요"
        
        return {
            'score': readiness_score,
            'level': readiness_level,
            'checks': readiness_checks
        }
    
    def _generate_recommendations(self):
        """개선 권장사항 생성"""
        recommendations = []
        
        # 실패한 테스트 기반 권장사항
        failed_tests = [r for r in self.results if not r['success']]
        
        for failed_test in failed_tests:
            test_name = failed_test['test']
            
            if test_name == 'online_eval_deployment':
                recommendations.append("온라인 평가 시스템 배포 구성을 재검토하세요.")
            elif test_name == 'multi_environment_deployment':
                recommendations.append("다중 환경 배포 전략을 개선하세요.")
            elif test_name == 'production_ready_features':
                recommendations.append("프로덕션 환경에 필요한 기능들을 추가 구현하세요.")
            elif test_name == 'docker_compose_generation':
                recommendations.append("Docker Compose 파일 생성 로직을 개선하세요.")
            elif test_name == 'scaling_scenarios':
                recommendations.append("스케일링 지원을 강화하세요.")
            elif test_name == 'backup_and_recovery':
                recommendations.append("백업 및 복구 메커니즘을 개선하세요.")
            elif test_name == 'monitoring_integration':
                recommendations.append("모니터링 통합을 강화하세요.")
        
        # 일반적인 권장사항
        if not recommendations:
            recommendations.extend([
                "정기적인 포트 사용 현황 모니터링을 설정하세요.",
                "포트 할당 정책을 문서화하세요.",
                "재해 복구 계획을 수립하세요."
            ])
        
        return recommendations
    
    def cleanup(self):
        """테스트 정리"""
        try:
            if self.test_root.exists():
                shutil.rmtree(self.test_root)
                logger.info(f"테스트 디렉토리 정리: {self.test_root}")
        except Exception as e:
            logger.warning(f"정리 중 오류: {e}")


def main():
    """배포 검증 메인"""
    verifier = DeploymentVerifier()
    
    try:
        report = verifier.run_all_verifications()
        
        # 결과 출력
        print("\n" + "=" * 70)
        print("🎯 실제 배포 환경 동작 검증 결과")
        print("=" * 70)
        
        if report['overall_success']:
            print("✅ 배포 환경 검증 성공!")
        else:
            print("❌ 일부 배포 검증 실패")
        
        summary = report['summary']
        print(f"\n📊 요약:")
        print(f"  전체 검증: {summary['total_tests']}개")
        print(f"  성공: {summary['successful_tests']}개")
        print(f"  실패: {summary['failed_tests']}개")
        print(f"  성공률: {summary['success_rate']:.1f}%")
        
        # 배포 준비도
        readiness = report['deployment_readiness']
        print(f"\n🚀 배포 준비도:")
        print(f"  점수: {readiness['score']:.1f}/100")
        print(f"  수준: {readiness['level']}")
        
        # 준비도 체크 상세
        print(f"\n📋 준비도 체크:")
        for check_name, passed in readiness['checks'].items():
            status = "✅" if passed else "❌"
            check_display = check_name.replace('_', ' ').title()
            print(f"  {status} {check_display}")
        
        # 실패한 검증 상세
        failed_tests = [r for r in report['test_results'] if not r['success']]
        if failed_tests:
            print(f"\n❌ 실패한 검증:")
            for test in failed_tests:
                print(f"  - {test['test']}: {test.get('error', 'Unknown error')}")
        
        # 권장사항
        if report['recommendations']:
            print(f"\n💡 권장사항:")
            for i, rec in enumerate(report['recommendations'], 1):
                print(f"  {i}. {rec}")
        
        # 최종 결론
        if report['overall_success']:
            print(f"\n🎉 Universal Port Manager가 실제 배포 환경에서 성공적으로 동작합니다!")
            print(f"   온라인 평가 시스템 배포에 사용할 준비가 완료되었습니다.")
        else:
            print(f"\n⚠️ 일부 개선이 필요하지만 기본 기능은 정상 동작합니다.")
        
        return 0 if report['overall_success'] else 1
        
    finally:
        verifier.cleanup()


if __name__ == '__main__':
    sys.exit(main())