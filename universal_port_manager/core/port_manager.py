"""
개선된 범용 포트 매니저 - 메인 클래스
=========================================

현실적인 포트 충돌 상황에 대응하는 완전히 개선된 통합 매니저
의존성 문제 해결, 향상된 충돌 해결, 개선된 하위 모듈들과의 완벽한 호환성
"""

import os
import json
from typing import Dict, List, Optional, Union, Tuple
from pathlib import Path
from dataclasses import asdict
import logging
from datetime import datetime
import subprocess

# 선택적 YAML 의존성
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    yaml = None
    print("⚠️ PyYAML 없음 - YAML 파일 생성 기능 비활성화")

# 개선된 모듈들 임포트 (호환성 보장)
try:
    from .port_scanner import ImprovedPortScanner as PortScanner, PortInfo, PortStatus
except ImportError:
    try:
        from .port_scanner import PortScanner, PortInfo, PortStatus
    except ImportError:
        print("⚠️ PortScanner 모듈 로드 실패")
        PortScanner = None

try:
    from .port_allocator import ImprovedPortAllocator as PortAllocator, AllocatedPort, ServiceType
except ImportError:
    try:
        from .port_allocator import PortAllocator, AllocatedPort, ServiceType
    except ImportError:
        print("⚠️ PortAllocator 모듈 로드 실패")
        PortAllocator = None

try:
    from .service_registry import ImprovedServiceRegistry as ServiceRegistry, ServiceDefinition, ProjectTemplate
except ImportError:
    try:
        from .service_registry import ServiceRegistry, ServiceDefinition, ProjectTemplate
    except ImportError:
        print("⚠️ ServiceRegistry 모듈 로드 실패")
        ServiceRegistry = None

# 모듈화된 컴포넌트들 임포트
from .port_manager_fallback import PortManagerFallback
from .port_manager_config import PortManagerConfig
from .port_manager_docker import PortManagerDocker

logger = logging.getLogger(__name__)

class PortManager:
    """
    개선된 범용 포트 매니저 (모듈화된 버전)
    
    주요 개선사항:
    - 의존성 문제 완전 해결 (YAML, psutil 등)
    - 모듈화된 아키텍처로 유지보수성 향상
    - 강화된 포트 충돌 자동 해결
    - 더 견고한 에러 처리 및 복구 시스템
    
    모듈 구성:
    - PortManagerFallback: 대체 시스템 (의존성 없이 동작)
    - PortManagerConfig: 설정 파일 생성 관리
    - PortManagerDocker: Docker Compose 관련 기능
    """
    
    def __init__(self, 
                 project_name: str,
                 project_dir: str = None,
                 global_mode: bool = True,
                 config_dir: str = None,
                 scan_range: Tuple[int, int] = (3000, 9999)):
        """
        개선된 포트 매니저 초기화
        
        Args:
            project_name: 프로젝트 이름
            project_dir: 프로젝트 디렉토리 (None이면 현재 디렉토리)
            global_mode: 전역 모드 (True면 시스템 전역 포트 관리)
            config_dir: 설정 디렉토리 (None이면 자동 설정)
            scan_range: 포트 스캔 범위
        """
        self.project_name = project_name
        self.project_dir = Path(project_dir) if project_dir else Path.cwd()
        self.global_mode = global_mode
        self.scan_range = scan_range
        
        # 초기화 상태 추적
        self.initialization_success = True
        self.available_features = {
            'yaml_support': YAML_AVAILABLE,
            'port_scanner': PortScanner is not None,
            'port_allocator': PortAllocator is not None,
            'service_registry': ServiceRegistry is not None
        }
        
        # 모듈화된 컴포넌트 초기화
        self.fallback = PortManagerFallback()
        self.config_manager = PortManagerConfig(self.project_dir, self.project_name)
        self.docker_manager = PortManagerDocker(self.project_dir, self.project_name)
        
        # 핵심 컴포넌트 초기화 (안전한 초기화)
        try:
            if PortScanner:
                self.scanner = PortScanner(scan_range=scan_range)
            else:
                self.scanner = None
                logger.warning("포트 스캐너 사용 불가")
                
            if PortAllocator:
                self.allocator = PortAllocator(config_dir=config_dir, global_mode=global_mode)
            else:
                self.allocator = None
                logger.warning("포트 할당자 사용 불가")
                
            if ServiceRegistry:
                self.registry = ServiceRegistry(config_dir=config_dir)
            else:
                self.registry = None
                logger.warning("서비스 레지스트리 사용 불가")
                
        except Exception as e:
            logger.error(f"컴포넌트 초기화 실패: {e}")
            self.initialization_success = False
        
        # 프로젝트 설정 디렉토리
        try:
            self.project_config_dir = self.project_dir / '.port-manager'
            self.project_config_dir.mkdir(exist_ok=True)
        except Exception as e:
            logger.error(f"설정 디렉토리 생성 실패: {e}")
        
        logger.info(f"개선된 포트 매니저 초기화: {project_name} (전역모드: {global_mode})")
        if not self.initialization_success:
            logger.warning("일부 기능이 제한될 수 있습니다")
    
    def get_system_status(self) -> Dict:
        """시스템 상태 확인"""
        status = {
            'project_name': self.project_name,
            'project_dir': str(self.project_dir),
            'global_mode': self.global_mode,
            'initialization_success': self.initialization_success,
            'available_features': self.available_features,
            'components_status': {}
        }
        
        # 각 컴포넌트 상태 확인
        if self.scanner:
            try:
                available_methods = getattr(self.scanner, 'available_methods', ['socket'])
                status['components_status']['scanner'] = {
                    'status': 'ok',
                    'methods': available_methods
                }
            except Exception as e:
                status['components_status']['scanner'] = {
                    'status': 'error',
                    'error': str(e)
                }
        else:
            status['components_status']['scanner'] = {'status': 'unavailable'}
        
        if self.allocator:
            status['components_status']['allocator'] = {'status': 'ok'}
        else:
            status['components_status']['allocator'] = {'status': 'unavailable'}
            
        if self.registry:
            status['components_status']['registry'] = {'status': 'ok'}
        else:
            status['components_status']['registry'] = {'status': 'unavailable'}
        
        return status
    
    def scan_system(self, force_refresh: bool = False) -> Dict[int, PortInfo]:
        """
        시스템 포트 스캔 (안전한 스캔)
        """
        if not self.scanner:
            logger.warning("포트 스캐너를 사용할 수 없어 제한적인 스캔 수행")
            return self.fallback.scan_ports()
        
        try:
            logger.info("시스템 포트 스캔 시작")
            return self.scanner.scan_system_ports(force_refresh=force_refresh)
        except Exception as e:
            logger.error(f"포트 스캔 실패: {e}, 대체 스캔 사용")
            return self.fallback.scan_ports()
    
    def allocate_services(self, 
                         services: List[Union[str, Dict]], 
                         preferred_ports: Dict[str, int] = None,
                         auto_detect: bool = True) -> Dict[str, AllocatedPort]:
        """
        서비스 목록에 대해 포트 할당 (개선된 안전한 할당)
        """
        preferred_ports = preferred_ports or {}
        
        # 컴포넌트가 사용 가능한 경우 정상 할당
        if self.allocator and self.registry:
            try:
                # 자동 감지된 서비스 추가
                if auto_detect:
                    try:
                        detected_services = self.registry.detect_project_services(str(self.project_dir))
                        logger.info(f"자동 감지된 서비스: {[s.name for s in detected_services]}")
                        
                        # 기존 서비스 목록과 병합 (중복 제거)
                        existing_names = set()
                        for service in services:
                            if isinstance(service, str):
                                existing_names.add(service)
                            else:
                                existing_names.add(service.get('name'))
                        
                        for detected in detected_services:
                            if detected.name not in existing_names:
                                services.append({
                                    'name': detected.name,
                                    'type': detected.type
                                })
                    except Exception as e:
                        logger.warning(f"자동 감지 실패: {e}")
                
                # 정상 포트 할당 실행
                return self.allocator.allocate_project_ports(
                    project_name=self.project_name,
                    services=services,
                    preferred_ports=preferred_ports
                )
                
            except Exception as e:
                logger.error(f"할당자를 통한 포트 할당 실패: {e}")
        
        # 대체 할당 시스템 사용
        logger.info("대체 포트 할당 시스템 사용")
        return self.fallback.allocate_ports(
            services, preferred_ports, self.project_name
        )
    
    def allocate_from_template(self, 
                              template_name: str,
                              service_overrides: Dict[str, Dict] = None) -> Dict[str, AllocatedPort]:
        """
        템플릿을 사용하여 포트 할당 (안전한 템플릿 사용)
        """
        if not self.registry:
            logger.error("서비스 레지스트리를 사용할 수 없어 템플릿 할당 불가")
            return {}
        
        try:
            template = self.registry.get_template_by_name(template_name)
            if not template:
                logger.error(f"템플릿을 찾을 수 없음: {template_name}")
                return {}
            
            logger.info(f"템플릿 '{template_name}' 사용하여 포트 할당")
            
            # 템플릿 서비스를 할당 형식으로 변환
            services = []
            preferred_ports = {}
            
            for service_def in template.services:
                service_info = {
                    'name': service_def.name,
                    'type': service_def.type
                }
                
                # 오버라이드 적용
                if service_overrides and service_def.name in service_overrides:
                    service_info.update(service_overrides[service_def.name])
                
                services.append(service_info)
                
                # 선호 포트 설정
                if service_def.port:
                    preferred_ports[service_def.name] = service_def.port
                elif service_def.internal_port:
                    preferred_ports[service_def.name] = service_def.internal_port
            
            return self.allocate_services(
                services=services,
                preferred_ports=preferred_ports,
                auto_detect=False  # 템플릿 사용 시 자동 감지 비활성화
            )
            
        except Exception as e:
            logger.error(f"템플릿 할당 실패: {e}")
            return {}
    
    def get_allocated_ports(self) -> Dict[str, AllocatedPort]:
        """현재 프로젝트의 할당된 포트 조회 (안전한 조회)"""
        if self.allocator:
            try:
                return self.allocator.get_project_ports(self.project_name)
            except Exception as e:
                logger.error(f"할당된 포트 조회 실패: {e}")
        
        return {}
    
    def check_conflicts(self, desired_ports: List[int] = None) -> Dict[int, PortInfo]:
        """
        포트 충돌 확인 (안전한 충돌 검사)
        """
        if desired_ports is None:
            allocated = self.get_allocated_ports()
            desired_ports = [port.port for port in allocated.values()]
        
        if not self.scanner:
            logger.warning("포트 스캐너를 사용할 수 없어 기본 충돌 검사 수행")
            return self.fallback.check_conflicts(desired_ports)
        
        try:
            return self.scanner.get_port_conflicts(desired_ports)
        except Exception as e:
            logger.error(f"충돌 검사 실패: {e}")
            return self.fallback.check_conflicts(desired_ports)
    
    def generate_docker_compose(self, 
                               output_file: str = 'docker-compose.yml',
                               include_override: bool = True,
                               template_name: str = None) -> bool:
        """
        Docker Compose 파일 생성 (모듈화된 생성)
        """
        allocated_ports = self.get_allocated_ports()
        if not allocated_ports:
            logger.warning("할당된 포트가 없어 Docker Compose 파일을 생성할 수 없음")
            return False
        
        return self.docker_manager.generate_compose_file(
            allocated_ports, output_file, include_override, template_name, self.registry
        )
    
    def generate_env_files(self, 
                          formats: List[str] = None) -> Dict[str, str]:
        """
        환경 파일 생성 (모듈화된 생성)
        """
        if formats is None:
            formats = ['docker', 'bash']
        
        allocated_ports = self.get_allocated_ports()
        if not allocated_ports:
            logger.warning("할당된 포트가 없어 환경 파일을 생성할 수 없음")
            return {}
        
        return self.config_manager.generate_env_files(allocated_ports, formats)
    
    def generate_all_configs(self) -> Dict[str, Union[bool, Dict[str, str]]]:
        """모든 설정 파일 생성 (모듈화된 생성)"""
        results = {}
        
        try:
            # Docker Compose 파일
            results['docker_compose'] = self.generate_docker_compose()
            
            # 환경 파일들
            results['env_files'] = self.generate_env_files(['docker', 'bash', 'python', 'json'])
            
            # 시작 스크립트
            allocated_ports = self.get_allocated_ports()
            results['start_script'] = self.config_manager.generate_start_script(allocated_ports)
            
        except Exception as e:
            logger.error(f"설정 파일 생성 중 오류: {e}")
            results['error'] = str(e)
        
        return results
    
    def start_services(self, build: bool = False) -> bool:
        """Docker Compose로 서비스 시작 (안전한 시작)"""
        return self.docker_manager.start_services(build)
    
    def stop_services(self) -> bool:
        """서비스 중지"""
        return self.docker_manager.stop_services()
    
    def get_service_urls(self) -> Dict[str, str]:
        """서비스 URL 목록 생성"""
        allocated_ports = self.get_allocated_ports()
        urls = {}
        
        for service_name, allocated_port in allocated_ports.items():
            if allocated_port.service_type in ['frontend', 'backend', 'nginx']:
                urls[service_name] = f"http://localhost:{allocated_port.port}"
            elif allocated_port.service_type == 'monitoring':
                urls[service_name] = f"http://localhost:{allocated_port.port}"
        
        return urls
    
    def get_status_report(self) -> Dict:
        """상태 보고서 생성 (완전한 보고서)"""
        allocated_ports = self.get_allocated_ports()
        
        # 포트 스캔 정보
        try:
            scan_info = self.scan_system()
        except Exception:
            scan_info = {}
        
        # 충돌 검사
        try:
            conflicts = self.check_conflicts()
        except Exception:
            conflicts = {}
        
        # 서비스 URL
        urls = self.get_service_urls()
        
        return {
            'project_name': self.project_name,
            'project_dir': str(self.project_dir),
            'global_mode': self.global_mode,
            'system_status': self.get_system_status(),
            'services': {
                service_name: {
                    'port': allocated_port.port,
                    'type': allocated_port.service_type,
                    'status': 'available' if allocated_port.port not in conflicts else 'conflict',
                    'url': urls.get(service_name),
                    'allocated_at': allocated_port.allocated_at,
                    'last_used': allocated_port.last_used,
                    'conflict_resolution': allocated_port.conflict_resolution
                }
                for service_name, allocated_port in allocated_ports.items()
            },
            'conflicts': {
                port: {
                    'description': getattr(info, 'description', 'Port in use'),
                    'status': getattr(info, 'status', 'OCCUPIED')
                }
                for port, info in conflicts.items()
            },
            'scan_summary': {
                'total_scanned': len(scan_info),
                'total_conflicts': len(conflicts)
            }
        }
    
    # 편의 메서드들
    def release_services(self, service_names: List[str] = None) -> int:
        """서비스 포트 해제"""
        if self.allocator:
            try:
                if service_names:
                    count = 0
                    for service_name in service_names:
                        if self.allocator.release_port(self.project_name, service_name):
                            count += 1
                    return count
                else:
                    return self.allocator.release_project_ports(self.project_name)
            except Exception as e:
                logger.error(f"포트 해제 실패: {e}")
        return 0
    
    def cleanup(self) -> Dict[str, int]:
        """정리 작업 수행"""
        results = {'cleaned_ports': 0, 'cleaned_files': 0}
        
        try:
            # 비활성 포트 정리
            if self.allocator:
                results['cleaned_ports'] = self.allocator.cleanup_inactive_ports()
            
            # 임시 파일 정리
            temp_files = [
                self.project_dir / 'docker-compose.override.yml',
                self.project_dir / '.port-manager' / 'temp'
            ]
            
            for temp_file in temp_files:
                if temp_file.exists():
                    temp_file.unlink()
                    results['cleaned_files'] += 1
            
        except Exception as e:
            logger.error(f"정리 작업 실패: {e}")
        
        logger.info(f"정리 완료: 포트 {results['cleaned_ports']}개, 파일 {results['cleaned_files']}개")
        return results