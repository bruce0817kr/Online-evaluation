"""
개선된 포트 할당자 모듈
=====================

현실적인 포트 충돌 상황을 고려한 지능형 포트 할당 시스템
개선된 port_scanner와의 완벽한 호환성 보장
"""

import json
import os
from typing import Dict, List, Set, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
from pathlib import Path

# 개선된 scanner 임포트 (호환성 보장)
try:
    from .port_scanner import ImprovedPortScanner as PortScanner, PortStatus
except ImportError:
    from .port_scanner import PortScanner, PortStatus

logger = logging.getLogger(__name__)

@dataclass
class ServiceType:
    """서비스 타입 정의"""
    name: str
    port_range: Tuple[int, int]
    default_port: Optional[int] = None
    description: str = ""
    priority: int = 1  # 우선순위 (낮을수록 높은 우선순위)
    
@dataclass 
class AllocatedPort:
    """할당된 포트 정보"""
    port: int
    service_name: str
    service_type: str
    project_name: str
    allocated_at: str
    last_used: str
    is_active: bool = True
    conflict_resolution: Optional[str] = None  # 충돌 해결 방법 기록
    
@dataclass
class ProjectPorts:
    """프로젝트별 포트 그룹"""
    project_name: str
    ports: Dict[str, AllocatedPort]  # service_name -> AllocatedPort
    created_at: str
    updated_at: str

class ImprovedPortAllocator:
    """
    개선된 포트 할당자
    
    주요 개선사항:
    - 현실적인 포트 범위 정의
    - 충돌 자동 해결 기능
    - 개선된 scanner와의 완벽한 호환성
    - 더 유연한 할당 알고리즘
    """
    
    def __init__(self, config_dir: str = None, global_mode: bool = True):
        """
        포트 할당자 초기화
        
        Args:
            config_dir: 설정 파일 저장 디렉토리 (None이면 홈 디렉토리 사용)
            global_mode: 전역 모드 (True면 시스템 전역, False면 프로젝트 로컬)
        """
        self.global_mode = global_mode
        
        if config_dir:
            self.config_dir = Path(config_dir)
        elif global_mode:
            # 전역 모드: 홈 디렉토리에 .port-manager 생성
            self.config_dir = Path.home() / '.port-manager'
        else:
            # 로컬 모드: 현재 디렉토리에 .port-manager 생성
            self.config_dir = Path.cwd() / '.port-manager'
            
        self.config_dir.mkdir(exist_ok=True)
        
        self.allocations_file = self.config_dir / 'port_allocations.json'
        self.service_types_file = self.config_dir / 'service_types.json'
        
        # 개선된 스캐너 사용 (충돌 회피를 위한 실용적인 범위)
        self.scanner = PortScanner(scan_range=(3000, 10000))
        self.service_types = self._load_service_types()
        self.allocations = self._load_allocations()
        
        logger.info(f"개선된 포트 할당자 초기화 완료 (모드: {'전역' if global_mode else '로컬'})")
        
    def _get_default_service_types(self) -> Dict[str, ServiceType]:
        """현실적인 기본 서비스 타입 정의"""
        return {
            'frontend': ServiceType(
                name='frontend',
                port_range=(3000, 3999),
                default_port=3001,  # 3000은 보통 다른 앱에서 사용
                description='Frontend web applications (React, Vue, Angular, etc.)',
                priority=1
            ),
            'backend': ServiceType(
                name='backend', 
                port_range=(8000, 8999),
                default_port=8001,  # 8000도 자주 사용됨
                description='Backend API servers (FastAPI, Express, Django, etc.)',
                priority=1
            ),
            'database': ServiceType(
                name='database',
                port_range=(5400, 5499),  # 5432 피하기
                default_port=5433,
                description='Database servers (PostgreSQL, MySQL, etc.)',
                priority=2
            ),
            'mongodb': ServiceType(
                name='mongodb',
                port_range=(27018, 27117),  # 27017 피하기
                default_port=27018,
                description='MongoDB database',
                priority=2
            ),
            'redis': ServiceType(
                name='redis',
                port_range=(6380, 6399),  # 6379 피하기
                default_port=6381,
                description='Redis cache server',
                priority=2
            ),
            'elasticsearch': ServiceType(
                name='elasticsearch',
                port_range=(9201, 9250),  # 9200 피하기
                default_port=9201,
                description='Elasticsearch search engine',
                priority=3
            ),
            'nginx': ServiceType(
                name='nginx',
                port_range=(8080, 8089),  # 현실적인 범위
                default_port=8081,
                description='Nginx web server',
                priority=2
            ),
            'monitoring': ServiceType(
                name='monitoring',
                port_range=(9091, 9150),  # 9090 피하기
                default_port=9091,
                description='Monitoring services (Prometheus, Grafana, etc.)',
                priority=3
            ),
            'development': ServiceType(
                name='development',
                port_range=(4000, 4099),
                default_port=4000,
                description='Development tools and services',
                priority=4
            ),
            'testing': ServiceType(
                name='testing',
                port_range=(7000, 7099),
                default_port=7000,
                description='Testing and QA services',
                priority=4
            ),
            'proxy': ServiceType(
                name='proxy',
                port_range=(8090, 8099),
                default_port=8090,
                description='Proxy and gateway services',
                priority=3
            )
        }
    
    def _load_service_types(self) -> Dict[str, ServiceType]:
        """서비스 타입 설정 로드"""
        if self.service_types_file.exists():
            try:
                with open(self.service_types_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    service_types = {}
                    for name, info in data.items():
                        service_types[name] = ServiceType(
                            name=info['name'],
                            port_range=tuple(info['port_range']),
                            default_port=info.get('default_port'),
                            description=info.get('description', ''),
                            priority=info.get('priority', 1)
                        )
                    return service_types
            except Exception as e:
                logger.error(f"서비스 타입 설정 로드 실패: {e}")
        
        # 기본 설정 생성 및 저장
        default_types = self._get_default_service_types()
        self._save_service_types(default_types)
        return default_types
    
    def _save_service_types(self, service_types: Dict[str, ServiceType]):
        """서비스 타입 설정 저장"""
        try:
            data = {}
            for name, stype in service_types.items():
                data[name] = asdict(stype)
            
            with open(self.service_types_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"서비스 타입 설정 저장 실패: {e}")
    
    def _load_allocations(self) -> Dict[str, ProjectPorts]:
        """포트 할당 정보 로드"""
        if self.allocations_file.exists():
            try:
                with open(self.allocations_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    allocations = {}
                    
                    for project_name, project_data in data.items():
                        ports = {}
                        for service_name, port_data in project_data['ports'].items():
                            ports[service_name] = AllocatedPort(**port_data)
                        
                        allocations[project_name] = ProjectPorts(
                            project_name=project_data['project_name'],
                            ports=ports,
                            created_at=project_data['created_at'],
                            updated_at=project_data['updated_at']
                        )
                    
                    return allocations
                    
            except Exception as e:
                logger.error(f"포트 할당 정보 로드 실패: {e}")
        
        return {}
    
    def _save_allocations(self):
        """포트 할당 정보 저장"""
        try:
            data = {}
            for project_name, project_ports in self.allocations.items():
                ports_data = {}
                for service_name, allocated_port in project_ports.ports.items():
                    ports_data[service_name] = asdict(allocated_port)
                
                data[project_name] = {
                    'project_name': project_ports.project_name,
                    'ports': ports_data,
                    'created_at': project_ports.created_at,
                    'updated_at': project_ports.updated_at
                }
            
            with open(self.allocations_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"포트 할당 정보 저장 실패: {e}")
    
    def get_service_type(self, service_name: str) -> Optional[ServiceType]:
        """서비스 이름으로 서비스 타입 추론 (개선된 매핑)"""
        # 정확한 매치 확인
        if service_name in self.service_types:
            return self.service_types[service_name]
        
        # 부분 매치 확인 (더 정교한 매핑)
        service_lower = service_name.lower()
        
        type_mappings = {
            # Frontend 관련
            'front': 'frontend',
            'web': 'frontend', 
            'ui': 'frontend',
            'react': 'frontend',
            'vue': 'frontend',
            'angular': 'frontend',
            'svelte': 'frontend',
            'next': 'frontend',
            'nuxt': 'frontend',
            
            # Backend 관련
            'back': 'backend',
            'api': 'backend',
            'server': 'backend',
            'fastapi': 'backend',
            'express': 'backend',
            'django': 'backend',
            'flask': 'backend',
            'spring': 'backend',
            'nest': 'backend',
            
            # Database 관련
            'db': 'database',
            'postgres': 'database',
            'postgresql': 'database',
            'mysql': 'database',
            'mariadb': 'database',
            'sqlite': 'database',
            
            # MongoDB
            'mongo': 'mongodb',
            
            # Cache/Redis
            'cache': 'redis',
            'redis': 'redis',
            
            # Search
            'search': 'elasticsearch',
            'elastic': 'elasticsearch',
            'solr': 'elasticsearch',
            
            # Proxy/Gateway
            'proxy': 'proxy',
            'gateway': 'proxy',
            'nginx': 'nginx',
            'apache': 'nginx',
            'traefik': 'proxy',
            
            # Monitoring
            'monitor': 'monitoring',
            'metrics': 'monitoring',
            'prometheus': 'monitoring',
            'grafana': 'monitoring',
            'kibana': 'monitoring',
            
            # Development/Testing
            'test': 'testing',
            'dev': 'development',
            'debug': 'development'
        }
        
        for keyword, service_type in type_mappings.items():
            if keyword in service_lower:
                return self.service_types.get(service_type)
        
        # 기본값으로 development 타입 반환
        return self.service_types.get('development')
    
    def allocate_port(self, project_name: str, service_name: str, 
                     preferred_port: Optional[int] = None,
                     service_type: Optional[str] = None,
                     auto_resolve_conflicts: bool = True) -> Optional[AllocatedPort]:
        """
        단일 포트 할당 (개선된 충돌 해결 포함)
        
        Args:
            project_name: 프로젝트 이름
            service_name: 서비스 이름
            preferred_port: 선호하는 포트 번호
            service_type: 강제 지정할 서비스 타입
            auto_resolve_conflicts: 충돌 시 자동 해결 여부
            
        Returns:
            할당된 포트 정보 또는 None
        """
        # 서비스 타입 결정
        if service_type:
            stype = self.service_types.get(service_type)
        else:
            stype = self.get_service_type(service_name)
        
        if not stype:
            logger.error(f"서비스 타입을 결정할 수 없음: {service_name}")
            return None
        
        # 이미 할당된 포트가 있는지 확인
        existing_allocation = self._get_existing_allocation(project_name, service_name)
        if existing_allocation:
            # 기존 포트가 여전히 사용 가능한지 확인
            if self.scanner.is_port_available(existing_allocation.port):
                existing_allocation.last_used = datetime.now().isoformat()
                self._save_allocations()
                logger.info(f"기존 포트 재사용: {project_name}/{service_name} -> {existing_allocation.port}")
                return existing_allocation
            else:
                # 기존 포트가 사용 불가능하면 비활성화
                existing_allocation.is_active = False
                logger.warning(f"기존 포트 {existing_allocation.port} 사용 불가, 새로 할당")
        
        # 포트 할당 시도 순서
        allocation_attempts = []
        
        # 1. 선호 포트
        if preferred_port:
            allocation_attempts.append(('preferred', preferred_port))
        
        # 2. 기본 포트
        if stype.default_port:
            allocation_attempts.append(('default', stype.default_port))
        
        # 3. 범위 내 사용 가능한 포트들
        available_ports = self._find_available_ports_in_range(stype.port_range)
        for port in available_ports[:5]:  # 최대 5개까지만 시도
            allocation_attempts.append(('range', port))
        
        # 할당 시도
        for attempt_type, port in allocation_attempts:
            if self._is_port_allocatable(port, project_name, service_name):
                allocated_port = self._create_allocated_port(
                    port, service_name, stype.name, project_name,
                    conflict_resolution=f"allocated_via_{attempt_type}"
                )
                self._save_allocation(project_name, service_name, allocated_port)
                logger.info(f"포트 할당 성공 ({attempt_type}): {project_name}/{service_name} -> {port}")
                return allocated_port
            else:
                logger.debug(f"포트 {port} 할당 불가 ({attempt_type})")
        
        # 모든 시도 실패 시 자동 충돌 해결
        if auto_resolve_conflicts:
            return self._resolve_port_conflict(project_name, service_name, stype)
        
        logger.error(f"포트 할당 실패: {project_name}/{service_name}")
        return None
    
    def _get_existing_allocation(self, project_name: str, service_name: str) -> Optional[AllocatedPort]:
        """기존 할당 정보 조회"""
        if project_name in self.allocations:
            existing_port = self.allocations[project_name].ports.get(service_name)
            if existing_port and existing_port.is_active:
                return existing_port
        return None
    
    def _find_available_ports_in_range(self, port_range: Tuple[int, int]) -> List[int]:
        """범위 내 사용 가능한 포트 찾기 (개선된 scanner 호환)"""
        start_port, end_port = port_range
        
        # 현재 사용 중인 포트들 확인
        occupied_ports = set()
        port_info = self.scanner.scan_system_ports()
        for port, info in port_info.items():
            if start_port <= port <= end_port and info.status != PortStatus.AVAILABLE:
                occupied_ports.add(port)
        
        # 이미 할당된 포트들도 제외
        for project_ports in self.allocations.values():
            for allocated_port in project_ports.ports.values():
                if (allocated_port.is_active and 
                    start_port <= allocated_port.port <= end_port):
                    occupied_ports.add(allocated_port.port)
        
        # 사용 가능한 포트 목록 생성
        available_ports = []
        for port in range(start_port, end_port + 1):
            if port not in occupied_ports:
                if self.scanner.is_port_available(port):
                    available_ports.append(port)
        
        return available_ports
    
    def _resolve_port_conflict(self, project_name: str, service_name: str, 
                              stype: ServiceType) -> Optional[AllocatedPort]:
        """포트 충돌 자동 해결"""
        logger.info(f"포트 충돌 자동 해결 시도: {project_name}/{service_name}")
        
        # 더 넓은 범위에서 포트 찾기
        extended_range = (3000, 9999)
        available_ports = self.scanner.find_available_ports(
            count=1, 
            start_port=extended_range[0]
        )
        
        if available_ports:
            port = available_ports[0]
            allocated_port = self._create_allocated_port(
                port, service_name, stype.name, project_name,
                conflict_resolution="auto_resolved_extended_range"
            )
            self._save_allocation(project_name, service_name, allocated_port)
            logger.info(f"충돌 해결 완료: {project_name}/{service_name} -> {port} (확장 범위)")
            return allocated_port
        
        logger.error(f"포트 충돌 해결 실패: {project_name}/{service_name}")
        return None
    
    def _is_port_allocatable(self, port: int, project_name: str, service_name: str) -> bool:
        """포트가 할당 가능한지 확인"""
        # 시스템에서 사용 중인지 확인
        if not self.scanner.is_port_available(port):
            return False
        
        # 다른 프로젝트/서비스에서 할당했는지 확인
        for proj_name, project_ports in self.allocations.items():
            for svc_name, allocated_port in project_ports.ports.items():
                if (allocated_port.port == port and 
                    allocated_port.is_active and
                    not (proj_name == project_name and svc_name == service_name)):
                    return False
        
        return True
    
    def _create_allocated_port(self, port: int, service_name: str, 
                              service_type: str, project_name: str,
                              conflict_resolution: str = None) -> AllocatedPort:
        """할당된 포트 객체 생성"""
        now = datetime.now().isoformat()
        return AllocatedPort(
            port=port,
            service_name=service_name,
            service_type=service_type,
            project_name=project_name,
            allocated_at=now,
            last_used=now,
            is_active=True,
            conflict_resolution=conflict_resolution
        )
    
    def _save_allocation(self, project_name: str, service_name: str, 
                        allocated_port: AllocatedPort):
        """할당 정보 저장"""
        if project_name not in self.allocations:
            now = datetime.now().isoformat()
            self.allocations[project_name] = ProjectPorts(
                project_name=project_name,
                ports={},
                created_at=now,
                updated_at=now
            )
        
        self.allocations[project_name].ports[service_name] = allocated_port
        self.allocations[project_name].updated_at = datetime.now().isoformat()
        self._save_allocations()
    
    def allocate_project_ports(self, project_name: str, 
                              services: List[Union[str, Dict]], 
                              preferred_ports: Dict[str, int] = None,
                              auto_resolve_conflicts: bool = True) -> Dict[str, AllocatedPort]:
        """
        프로젝트의 여러 서비스에 대해 포트 일괄 할당 (개선된 버전)
        
        Args:
            project_name: 프로젝트 이름
            services: 서비스 목록 (문자열 또는 {name, type} 딕셔너리)
            preferred_ports: 서비스별 선호 포트 매핑
            auto_resolve_conflicts: 충돌 시 자동 해결 여부
            
        Returns:
            서비스 이름을 키로 하는 할당된 포트 딕셔너리
        """
        preferred_ports = preferred_ports or {}
        allocated_ports = {}
        failed_allocations = []
        
        logger.info(f"프로젝트 '{project_name}'의 {len(services)}개 서비스 포트 할당 시작")
        
        # 우선순위별로 서비스 정렬 (중요한 서비스부터 할당)
        sorted_services = self._sort_services_by_priority(services)
        
        for service in sorted_services:
            if isinstance(service, str):
                service_name = service
                service_type = None
            else:
                service_name = service.get('name')
                service_type = service.get('type')
            
            preferred_port = preferred_ports.get(service_name)
            
            allocated_port = self.allocate_port(
                project_name=project_name,
                service_name=service_name,
                preferred_port=preferred_port,
                service_type=service_type,
                auto_resolve_conflicts=auto_resolve_conflicts
            )
            
            if allocated_port:
                allocated_ports[service_name] = allocated_port
            else:
                failed_allocations.append(service_name)
        
        # 결과 요약
        success_count = len(allocated_ports)
        total_count = len(services)
        
        if failed_allocations:
            logger.warning(f"일부 서비스 포트 할당 실패: {failed_allocations}")
        
        logger.info(f"포트 할당 완료: {success_count}/{total_count} 성공")
        
        return allocated_ports
    
    def _sort_services_by_priority(self, services: List[Union[str, Dict]]) -> List[Union[str, Dict]]:
        """서비스 우선순위별 정렬"""
        def get_priority(service):
            if isinstance(service, str):
                stype = self.get_service_type(service)
            else:
                service_type = service.get('type')
                if service_type:
                    stype = self.service_types.get(service_type)
                else:
                    stype = self.get_service_type(service.get('name', ''))
            
            return stype.priority if stype else 999
        
        return sorted(services, key=get_priority)
    
    def get_port_conflicts(self, desired_ports: List[int]) -> Dict[int, str]:
        """포트 충돌 확인 및 대안 제시"""
        port_info = self.scanner.scan_system_ports()
        conflicts = {}
        
        for port in desired_ports:
            if port in port_info and port_info[port].status != PortStatus.AVAILABLE:
                conflicts[port] = port_info[port].description or "Occupied"
        
        return conflicts
    
    def suggest_alternative_ports(self, conflicted_ports: List[int]) -> Dict[int, int]:
        """충돌 포트에 대한 대안 제시 (개선된 scanner 활용)"""
        alternatives = {}
        
        # 현재 시스템의 충돌 정보를 확인하고 대안 제시
        existing_conflicts = self.scanner.get_port_conflicts(conflicted_ports)
        suggested_alternatives = self.scanner.suggest_alternative_ports(existing_conflicts)
        
        for original_port, alternative_port in suggested_alternatives.items():
            alternatives[original_port] = alternative_port
        
        return alternatives
    
    def release_port(self, project_name: str, service_name: str) -> bool:
        """포트 해제"""
        if project_name in self.allocations:
            project_ports = self.allocations[project_name]
            if service_name in project_ports.ports:
                allocated_port = project_ports.ports[service_name]
                allocated_port.is_active = False
                project_ports.updated_at = datetime.now().isoformat()
                self._save_allocations()
                
                logger.info(f"포트 해제: {project_name}/{service_name} (포트 {allocated_port.port})")
                return True
        
        return False
    
    def release_project_ports(self, project_name: str) -> int:
        """프로젝트의 모든 포트 해제"""
        released_count = 0
        
        if project_name in self.allocations:
            project_ports = self.allocations[project_name]
            for service_name, allocated_port in project_ports.ports.items():
                if allocated_port.is_active:
                    allocated_port.is_active = False
                    released_count += 1
            
            project_ports.updated_at = datetime.now().isoformat()
            self._save_allocations()
            
            logger.info(f"프로젝트 '{project_name}' 포트 {released_count}개 해제")
        
        return released_count
    
    def get_allocation_report(self) -> Dict:
        """할당 현황 보고서 생성"""
        active_allocations = {}
        inactive_allocations = {}
        
        for project_name, project_ports in self.allocations.items():
            for service_name, allocated_port in project_ports.ports.items():
                port_info = {
                    'project': project_name,
                    'service': service_name,
                    'port': allocated_port.port,
                    'service_type': allocated_port.service_type,
                    'allocated_at': allocated_port.allocated_at,
                    'last_used': allocated_port.last_used,
                    'conflict_resolution': allocated_port.conflict_resolution
                }
                
                if allocated_port.is_active:
                    active_allocations[f"{project_name}/{service_name}"] = port_info
                else:
                    inactive_allocations[f"{project_name}/{service_name}"] = port_info
        
        # 포트 충돌 검사
        all_active_ports = [info['port'] for info in active_allocations.values()]
        conflicts = self.get_port_conflicts(all_active_ports)
        
        return {
            'summary': {
                'total_projects': len(self.allocations),
                'active_allocations': len(active_allocations),
                'inactive_allocations': len(inactive_allocations),
                'total_conflicts': len(conflicts),
                'scanner_methods': self.scanner.available_methods
            },
            'active_allocations': active_allocations,
            'inactive_allocations': inactive_allocations,
            'current_conflicts': conflicts,
            'service_types': {name: asdict(stype) for name, stype in self.service_types.items()}
        }

# 기존 PortAllocator와의 호환성을 위한 별칭
PortAllocator = ImprovedPortAllocator