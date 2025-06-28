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

logger = logging.getLogger(__name__)

class ImprovedPortManager:
    """
    개선된 범용 포트 매니저
    
    주요 개선사항:
    - 의존성 문제 완전 해결 (YAML, psutil 등)
    - 개선된 하위 모듈들과의 완벽한 호환성
    - 강화된 포트 충돌 자동 해결
    - 더 견고한 에러 처리 및 복구 시스템
    - 현실적인 포트 관리 전략
    
    사용 예시:
        # 기본 사용법 (의존성 문제 없음)
        pm = ImprovedPortManager(project_name="my-project")
        ports = pm.allocate_services(['frontend', 'backend', 'mongodb'])
        pm.generate_all_configs()
        pm.start_services()
        
        # 고급 사용법 (충돌 회피)
        pm = ImprovedPortManager(project_name="my-project", global_mode=True)
        template = pm.get_template('fullstack-react-fastapi')
        ports = pm.allocate_from_template(template)
        pm.generate_all_configs()
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
        
        # 대체 포트 할당 시스템 (컴포넌트 실패 시 사용)
        self.fallback_ports = {
            'frontend': 3001,
            'backend': 8001,
            'database': 5433,
            'mongodb': 27018,
            'redis': 6381
        }
        
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
        
        Args:
            force_refresh: 캐시 무시하고 새로 스캔
            
        Returns:
            포트 정보 딕셔너리
        """
        if not self.scanner:
            logger.warning("포트 스캐너를 사용할 수 없어 제한적인 스캔 수행")
            return self._fallback_port_scan()
        
        try:
            logger.info("시스템 포트 스캔 시작")
            return self.scanner.scan_system_ports(force_refresh=force_refresh)
        except Exception as e:
            logger.error(f"포트 스캔 실패: {e}, 대체 스캔 사용")
            return self._fallback_port_scan()
    
    def _fallback_port_scan(self) -> Dict[int, PortInfo]:
        """포트 스캐너 없이 기본적인 포트 확인"""
        import socket
        
        occupied_ports = {}
        test_ports = [3000, 3001, 8000, 8001, 27017, 27018, 5432, 5433, 6379, 6381]
        
        for port in test_ports:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.1)
            try:
                result = sock.connect_ex(('localhost', port))
                if result == 0:
                    # 포트가 사용 중인 경우를 간단히 표현
                    occupied_ports[port] = type('PortInfo', (), {
                        'port': port,
                        'status': 'OCCUPIED',
                        'description': f'Port {port} in use'
                    })()
            except Exception:
                pass
            finally:
                sock.close()
        
        return occupied_ports
    
    def allocate_services(self, 
                         services: List[Union[str, Dict]], 
                         preferred_ports: Dict[str, int] = None,
                         auto_detect: bool = True) -> Dict[str, AllocatedPort]:
        """
        서비스 목록에 대해 포트 할당 (개선된 안전한 할당)
        
        Args:
            services: 서비스 목록 (문자열 또는 서비스 정의)
            preferred_ports: 선호 포트 매핑
            auto_detect: 프로젝트에서 자동 감지된 서비스 추가 여부
            
        Returns:
            할당된 포트 정보
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
        return self._fallback_port_allocation(services, preferred_ports)
    
    def _fallback_port_allocation(self, services: List[Union[str, Dict]], 
                                 preferred_ports: Dict[str, int]) -> Dict[str, AllocatedPort]:
        """컴포넌트 실패 시 사용하는 대체 포트 할당"""
        allocated_ports = {}
        used_ports = set()
        
        # 현재 사용 중인 포트들 확인
        occupied_info = self._fallback_port_scan()
        occupied_ports = set(occupied_info.keys())
        
        for service in services:
            if isinstance(service, str):
                service_name = service
                service_type = self._guess_service_type(service_name)
            else:
                service_name = service.get('name')
                service_type = service.get('type', self._guess_service_type(service_name))
            
            # 포트 결정
            port = None
            
            # 1. 선호 포트 사용
            if service_name in preferred_ports:
                preferred_port = preferred_ports[service_name]
                if preferred_port not in occupied_ports and preferred_port not in used_ports:
                    port = preferred_port
            
            # 2. 기본 포트 사용
            if port is None and service_type in self.fallback_ports:
                default_port = self.fallback_ports[service_type]
                if default_port not in occupied_ports and default_port not in used_ports:
                    port = default_port
            
            # 3. 범위에서 찾기
            if port is None:
                for test_port in range(3001, 4000):
                    if test_port not in occupied_ports and test_port not in used_ports:
                        port = test_port
                        break
            
            if port:
                now = datetime.now().isoformat()
                allocated_port = AllocatedPort(
                    port=port,
                    service_name=service_name,
                    service_type=service_type,
                    project_name=self.project_name,
                    allocated_at=now,
                    last_used=now,
                    is_active=True,
                    conflict_resolution="fallback_allocation"
                )
                allocated_ports[service_name] = allocated_port
                used_ports.add(port)
                logger.info(f"대체 할당: {service_name} -> {port}")
            else:
                logger.error(f"포트 할당 실패: {service_name}")
        
        return allocated_ports
    
    def _guess_service_type(self, service_name: str) -> str:
        """서비스 이름으로 타입 추측"""
        name_lower = service_name.lower()
        
        if any(keyword in name_lower for keyword in ['frontend', 'react', 'vue', 'angular', 'web', 'ui']):
            return 'frontend'
        elif any(keyword in name_lower for keyword in ['backend', 'api', 'server', 'fastapi', 'express']):
            return 'backend'
        elif any(keyword in name_lower for keyword in ['mongo', 'mongodb']):
            return 'mongodb'
        elif any(keyword in name_lower for keyword in ['postgres', 'database', 'db']):
            return 'database'
        elif any(keyword in name_lower for keyword in ['redis', 'cache']):
            return 'redis'
        else:
            return 'backend'  # 기본값
    
    def allocate_from_template(self, 
                              template_name: str,
                              service_overrides: Dict[str, Dict] = None) -> Dict[str, AllocatedPort]:
        """
        템플릿을 사용하여 포트 할당 (안전한 템플릿 사용)
        
        Args:
            template_name: 템플릿 이름
            service_overrides: 서비스별 설정 오버라이드
            
        Returns:
            할당된 포트 정보
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
        
        Args:
            desired_ports: 확인할 포트 목록 (None이면 할당된 포트들)
            
        Returns:
            충돌하는 포트 정보
        """
        if desired_ports is None:
            allocated = self.get_allocated_ports()
            desired_ports = [port.port for port in allocated.values()]
        
        if not self.scanner:
            logger.warning("포트 스캐너를 사용할 수 없어 기본 충돌 검사 수행")
            return self._fallback_conflict_check(desired_ports)
        
        try:
            return self.scanner.get_port_conflicts(desired_ports)
        except Exception as e:
            logger.error(f"충돌 검사 실패: {e}")
            return self._fallback_conflict_check(desired_ports)
    
    def _fallback_conflict_check(self, ports: List[int]) -> Dict[int, PortInfo]:
        """기본적인 충돌 검사"""
        occupied_info = self._fallback_port_scan()
        conflicts = {}
        
        for port in ports:
            if port in occupied_info:
                conflicts[port] = occupied_info[port]
        
        return conflicts
    
    def generate_docker_compose(self, 
                               output_file: str = 'docker-compose.yml',
                               include_override: bool = True,
                               template_name: str = None) -> bool:
        """
        Docker Compose 파일 생성 (YAML 의존성 안전 처리)
        
        Args:
            output_file: 출력 파일명
            include_override: override 파일도 생성할지 여부
            template_name: 사용할 서비스 템플릿
            
        Returns:
            생성 성공 여부
        """
        if not YAML_AVAILABLE:
            logger.warning("PyYAML이 없어 Docker Compose 파일 생성 불가")
            # JSON 형식으로 대체 생성
            return self._generate_docker_compose_json(output_file)
        
        try:
            allocated_ports = self.get_allocated_ports()
            if not allocated_ports:
                logger.warning("할당된 포트가 없어 Docker Compose 파일을 생성할 수 없음")
                return False
            
            # 기본 docker-compose.yml 구조
            compose_data = {
                'version': '3.8',
                'services': {},
                'volumes': {},
                'networks': {
                    f'{self.project_name}-network': {
                        'driver': 'bridge'
                    }
                }
            }
            
            # 서비스별 설정 생성
            for service_name, allocated_port in allocated_ports.items():
                service_config = self._generate_service_config(
                    service_name, allocated_port, template_name
                )
                compose_data['services'][service_name] = service_config
                
                # 볼륨이 필요한 서비스는 볼륨 추가
                if allocated_port.service_type in ['mongodb', 'database', 'redis', 'elasticsearch']:
                    volume_name = f"{service_name}_data"
                    compose_data['volumes'][volume_name] = None
            
            # 파일 저장
            output_path = self.project_dir / output_file
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(compose_data, f, default_flow_style=False, sort_keys=False)
            
            logger.info(f"Docker Compose 파일 생성: {output_path}")
            
            # Override 파일 생성
            if include_override:
                self._generate_docker_compose_override(allocated_ports)
            
            return True
            
        except Exception as e:
            logger.error(f"Docker Compose 파일 생성 실패: {e}")
            return False
    
    def _generate_docker_compose_json(self, output_file: str) -> bool:
        """YAML 없이 JSON 형식으로 Docker Compose 설정 생성"""
        try:
            allocated_ports = self.get_allocated_ports()
            if not allocated_ports:
                return False
            
            compose_data = {
                'version': '3.8',
                'services': {},
                'volumes': {},
                'networks': {
                    f'{self.project_name}-network': {
                        'driver': 'bridge'
                    }
                }
            }
            
            for service_name, allocated_port in allocated_ports.items():
                service_config = self._generate_service_config(service_name, allocated_port)
                compose_data['services'][service_name] = service_config
            
            # JSON 파일로 저장 (참고용)
            json_path = self.project_dir / f"{output_file}.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(compose_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Docker Compose JSON 파일 생성: {json_path}")
            return True
            
        except Exception as e:
            logger.error(f"Docker Compose JSON 파일 생성 실패: {e}")
            return False
    
    def _generate_service_config(self, 
                                service_name: str, 
                                allocated_port: AllocatedPort,
                                template_name: str = None) -> Dict:
        """개별 서비스 설정 생성 (개선된 버전)"""
        service_type = allocated_port.service_type
        
        # 서비스 레지스트리에서 기본 설정 조회 (안전한 조회)
        service_def = None
        if self.registry:
            try:
                service_def = self.registry.get_service_by_name(service_type)
            except Exception:
                pass
        
        if not service_def:
            # 기본 설정 생성
            internal_port = allocated_port.port
        else:
            internal_port = service_def.internal_port or allocated_port.port
        
        config = {
            'container_name': f"{self.project_name}-{service_name}",
            'restart': 'unless-stopped',
            'networks': [f'{self.project_name}-network']
        }
        
        # 포트 매핑
        config['ports'] = [f"{allocated_port.port}:{internal_port}"]
        
        # 서비스 타입별 특별 설정
        if service_type in ['frontend', 'backend']:
            # 빌드 설정
            if (self.project_dir / service_name / 'Dockerfile').exists():
                config['build'] = {
                    'context': '.',
                    'dockerfile': f'{service_name}/Dockerfile'
                }
            elif (self.project_dir / f'Dockerfile.{service_name}').exists():
                config['build'] = {
                    'context': '.',
                    'dockerfile': f'Dockerfile.{service_name}'
                }
            
        elif service_type == 'mongodb':
            config['image'] = 'mongo:7'
            config['environment'] = {
                'MONGO_INITDB_ROOT_USERNAME': 'admin',
                'MONGO_INITDB_ROOT_PASSWORD': 'password123',
                'MONGO_INITDB_DATABASE': self.project_name
            }
            config['volumes'] = [f'{service_name}_data:/data/db']
            
        elif service_type == 'redis':
            config['image'] = 'redis:7-alpine'
            config['command'] = 'redis-server --appendonly yes'
            config['volumes'] = [f'{service_name}_data:/data']
            
        elif service_type == 'database':
            config['image'] = 'postgres:15-alpine'
            config['environment'] = {
                'POSTGRES_DB': self.project_name,
                'POSTGRES_USER': 'admin',
                'POSTGRES_PASSWORD': 'password123'
            }
            config['volumes'] = [f'{service_name}_data:/var/lib/postgresql/data']
        
        # 서비스 정의에서 추가 설정 적용
        if service_def:
            if hasattr(service_def, 'environment') and service_def.environment:
                if 'environment' not in config:
                    config['environment'] = {}
                config['environment'].update(service_def.environment)
            
            if hasattr(service_def, 'health_check') and service_def.health_check:
                config['healthcheck'] = {
                    'test': f'curl -f http://localhost:{internal_port}{service_def.health_check} || exit 1',
                    'interval': '30s',
                    'timeout': '10s',
                    'retries': 3
                }
        
        return config
    
    def _generate_docker_compose_override(self, allocated_ports: Dict[str, AllocatedPort]):
        """Docker Compose override 파일 생성 (YAML 안전 처리)"""
        if not YAML_AVAILABLE:
            logger.warning("PyYAML이 없어 override 파일 생성 불가")
            return
        
        try:
            override_data = {
                'version': '3.8',
                'services': {}
            }
            
            for service_name, allocated_port in allocated_ports.items():
                # 개발 환경용 오버라이드 설정
                service_config = {}
                
                if allocated_port.service_type in ['frontend', 'backend']:
                    service_config['volumes'] = [f'./{service_name}:/app']
                    service_config['environment'] = ['NODE_ENV=development']
                    
                    if allocated_port.service_type == 'frontend':
                        service_config['command'] = 'npm run dev'
                    elif allocated_port.service_type == 'backend':
                        service_config['command'] = 'uvicorn main:app --host 0.0.0.0 --port 8000 --reload'
                
                if service_config:
                    override_data['services'][service_name] = service_config
            
            # override 파일 저장
            override_path = self.project_dir / 'docker-compose.override.yml'
            with open(override_path, 'w', encoding='utf-8') as f:
                yaml.dump(override_data, f, default_flow_style=False, sort_keys=False)
            
            logger.info(f"Docker Compose override 파일 생성: {override_path}")
            
        except Exception as e:
            logger.error(f"Docker Compose override 파일 생성 실패: {e}")
    
    def generate_env_files(self, 
                          formats: List[str] = None) -> Dict[str, str]:
        """
        환경 파일 생성 (안전한 파일 생성)
        
        Args:
            formats: 생성할 형식 목록 ['docker', 'bash', 'python', 'json']
            
        Returns:
            생성된 파일 경로 딕셔너리
        """
        if formats is None:
            formats = ['docker', 'bash']
        
        allocated_ports = self.get_allocated_ports()
        if not allocated_ports:
            logger.warning("할당된 포트가 없어 환경 파일을 생성할 수 없음")
            return {}
        
        generated_files = {}
        
        try:
            # Docker .env 파일
            if 'docker' in formats:
                env_path = self.project_dir / '.env'
                with open(env_path, 'w', encoding='utf-8') as f:
                    f.write(f"# {self.project_name} 포트 설정\n")
                    f.write(f"# 생성일시: {datetime.now().isoformat()}\n\n")
                    
                    for service_name, allocated_port in allocated_ports.items():
                        var_name = f"{service_name.upper()}_PORT"
                        f.write(f"{var_name}={allocated_port.port}\n")
                    
                    f.write(f"\nPROJECT_NAME={self.project_name}\n")
                    f.write(f"COMPOSE_PROJECT_NAME={self.project_name}\n")
                
                generated_files['docker'] = str(env_path)
            
            # Bash 스크립트
            if 'bash' in formats:
                bash_path = self.project_dir / 'set_ports.sh'
                with open(bash_path, 'w', encoding='utf-8') as f:
                    f.write("#!/bin/bash\n")
                    f.write(f"# {self.project_name} 포트 설정\n")
                    f.write(f"# 생성일시: {datetime.now().isoformat()}\n\n")
                    
                    for service_name, allocated_port in allocated_ports.items():
                        var_name = f"{service_name.upper()}_PORT"
                        f.write(f"export {var_name}={allocated_port.port}\n")
                    
                    f.write(f"\nexport PROJECT_NAME={self.project_name}\n")
                
                # 실행 권한 부여
                try:
                    bash_path.chmod(0o755)
                except Exception:
                    pass
                generated_files['bash'] = str(bash_path)
            
            # Python 설정
            if 'python' in formats:
                py_path = self.project_dir / 'port_config.py'
                with open(py_path, 'w', encoding='utf-8') as f:
                    f.write(f'"""\n{self.project_name} 포트 설정\n')
                    f.write(f'생성일시: {datetime.now().isoformat()}\n"""\n\n')
                    
                    f.write("PORTS = {\n")
                    for service_name, allocated_port in allocated_ports.items():
                        f.write(f"    '{service_name}': {allocated_port.port},\n")
                    f.write("}\n\n")
                    
                    f.write(f"PROJECT_NAME = '{self.project_name}'\n")
                    
                    # 개별 상수
                    for service_name, allocated_port in allocated_ports.items():
                        var_name = f"{service_name.upper()}_PORT"
                        f.write(f"{var_name} = {allocated_port.port}\n")
                
                generated_files['python'] = str(py_path)
            
            # JSON 설정
            if 'json' in formats:
                json_path = self.project_dir / 'ports.json'
                config_data = {
                    'project_name': self.project_name,
                    'generated_at': datetime.now().isoformat(),
                    'ports': {
                        service_name: {
                            'port': allocated_port.port,
                            'service_type': allocated_port.service_type,
                            'allocated_at': allocated_port.allocated_at
                        }
                        for service_name, allocated_port in allocated_ports.items()
                    }
                }
                
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, indent=2, ensure_ascii=False)
                
                generated_files['json'] = str(json_path)
            
            logger.info(f"환경 파일 생성 완료: {list(generated_files.keys())}")
            
        except Exception as e:
            logger.error(f"환경 파일 생성 실패: {e}")
        
        return generated_files
    
    def generate_all_configs(self) -> Dict[str, Union[bool, Dict[str, str]]]:
        """모든 설정 파일 생성 (안전한 생성)"""
        results = {}
        
        try:
            # Docker Compose 파일
            results['docker_compose'] = self.generate_docker_compose()
            
            # 환경 파일들
            results['env_files'] = self.generate_env_files(['docker', 'bash', 'python', 'json'])
            
            # 시작 스크립트
            results['start_script'] = self._generate_start_script()
            
        except Exception as e:
            logger.error(f"설정 파일 생성 중 오류: {e}")
            results['error'] = str(e)
        
        return results
    
    def _generate_start_script(self) -> bool:
        """시작 스크립트 생성 (안전한 생성)"""
        try:
            script_path = self.project_dir / 'start.sh'
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write("#!/bin/bash\n")
                f.write(f"# {self.project_name} 시작 스크립트\n")
                f.write(f"# 생성일시: {datetime.now().isoformat()}\n\n")
                
                f.write("echo '🚀 개선된 포트 관리자로 서비스 시작'\n")
                f.write("echo '========================================'\n\n")
                
                # 포트 정보 표시
                allocated_ports = self.get_allocated_ports()
                for service_name, allocated_port in allocated_ports.items():
                    f.write(f"echo '  {service_name}: {allocated_port.port}'\n")
                
                f.write("\necho ''\n")
                f.write("echo '⏳ Docker Compose 시작 중...'\n")
                f.write("docker-compose up -d\n\n")
                
                f.write("echo '✅ 서비스 시작 완료!'\n")
                f.write("echo ''\n")
                f.write("echo '📊 컨테이너 상태:'\n")
                f.write("docker-compose ps\n")
            
            script_path.chmod(0o755)
            logger.info(f"시작 스크립트 생성: {script_path}")
            return True
            
        except Exception as e:
            logger.error(f"시작 스크립트 생성 실패: {e}")
            return False
    
    def start_services(self, build: bool = False) -> bool:
        """Docker Compose로 서비스 시작 (안전한 시작)"""
        try:
            # 기존 서비스 정리
            subprocess.run(['docker-compose', 'down'], 
                         cwd=self.project_dir, capture_output=True)
            
            # 서비스 시작
            cmd = ['docker-compose', 'up', '-d']
            if build:
                cmd.extend(['--build'])
            
            result = subprocess.run(cmd, cwd=self.project_dir, 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("서비스 시작 성공")
                return True
            else:
                logger.error(f"서비스 시작 실패: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"서비스 시작 중 오류: {e}")
            return False
    
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
        urls = {}
        for service_name, allocated_port in allocated_ports.items():
            if allocated_port.service_type in ['frontend', 'backend', 'nginx']:
                urls[service_name] = f"http://localhost:{allocated_port.port}"
        
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

# 기존 PortManager와의 호환성을 위한 별칭
PortManager = ImprovedPortManager