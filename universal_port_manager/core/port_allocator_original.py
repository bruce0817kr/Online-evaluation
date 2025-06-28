"""
포트 할당자 모듈
===============

지능형 포트 할당 및 관리 시스템
서비스 타입별 포트 범위, 프로젝트별 그룹화, 충돌 방지 등을 담당
"""

import json
import os
from typing import Dict, List, Set, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
from pathlib import Path

from .port_scanner import PortScanner, PortStatus

logger = logging.getLogger(__name__)

@dataclass
class ServiceType:
    """서비스 타입 정의"""
    name: str
    port_range: Tuple[int, int]
    default_port: Optional[int] = None
    description: str = ""
    
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
    
@dataclass
class ProjectPorts:
    """프로젝트별 포트 그룹"""
    project_name: str
    ports: Dict[str, AllocatedPort]  # service_name -> AllocatedPort
    created_at: str
    updated_at: str

class PortAllocator:
    """
    지능형 포트 할당자
    
    기능:
    - 서비스 타입별 포트 범위 관리
    - 프로젝트별 포트 그룹화  
    - 포트 할당 영속화
    - 충돌 방지 알고리즘
    - 포트 해제 및 재사용
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
        
        self.scanner = PortScanner()
        self.service_types = self._load_service_types()
        self.allocations = self._load_allocations()
        
    def _get_default_service_types(self) -> Dict[str, ServiceType]:
        """기본 서비스 타입 정의"""
        return {
            'frontend': ServiceType(
                name='frontend',
                port_range=(3000, 3999),
                default_port=3000,
                description='Frontend web applications (React, Vue, Angular, etc.)'
            ),
            'backend': ServiceType(
                name='backend', 
                port_range=(8000, 8999),
                default_port=8080,
                description='Backend API servers (FastAPI, Express, Django, etc.)'
            ),
            'database': ServiceType(
                name='database',
                port_range=(5000, 5999),
                default_port=5432,
                description='Database servers (PostgreSQL, MySQL, etc.)'
            ),
            'mongodb': ServiceType(
                name='mongodb',
                port_range=(27000, 27999),
                default_port=27017,
                description='MongoDB database'
            ),
            'redis': ServiceType(
                name='redis',
                port_range=(6000, 6999), 
                default_port=6379,
                description='Redis cache server'
            ),
            'elasticsearch': ServiceType(
                name='elasticsearch',
                port_range=(9200, 9299),
                default_port=9200,
                description='Elasticsearch search engine'
            ),
            'nginx': ServiceType(
                name='nginx',
                port_range=(80, 8080),
                default_port=80,
                description='Nginx web server'
            ),
            'monitoring': ServiceType(
                name='monitoring',
                port_range=(9000, 9199),
                default_port=9090,
                description='Monitoring services (Prometheus, Grafana, etc.)'
            ),
            'development': ServiceType(
                name='development',
                port_range=(4000, 4999),
                default_port=4000,
                description='Development tools and services'
            ),
            'testing': ServiceType(
                name='testing',
                port_range=(7000, 7999),
                default_port=7000,
                description='Testing and QA services'
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
                            description=info.get('description', '')
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
        """서비스 이름으로 서비스 타입 추론"""
        # 정확한 매치 확인
        if service_name in self.service_types:
            return self.service_types[service_name]
        
        # 부분 매치 확인 (예: 'mysql-db' -> 'database')
        service_lower = service_name.lower()
        
        type_mappings = {
            'front': 'frontend',
            'web': 'frontend', 
            'ui': 'frontend',
            'react': 'frontend',
            'vue': 'frontend',
            'angular': 'frontend',
            
            'back': 'backend',
            'api': 'backend',
            'server': 'backend',
            'fastapi': 'backend',
            'express': 'backend',
            'django': 'backend',
            
            'db': 'database',
            'postgres': 'database',
            'mysql': 'database',
            'mariadb': 'database',
            
            'mongo': 'mongodb',
            'cache': 'redis',
            'search': 'elasticsearch',
            'elastic': 'elasticsearch',
            
            'proxy': 'nginx',
            'gateway': 'nginx',
            
            'monitor': 'monitoring',
            'metrics': 'monitoring',
            'prometheus': 'monitoring',
            'grafana': 'monitoring',
            
            'test': 'testing',
            'dev': 'development'
        }
        
        for keyword, service_type in type_mappings.items():
            if keyword in service_lower:
                return self.service_types.get(service_type)
        
        # 기본값으로 development 타입 반환
        return self.service_types.get('development')
    
    def allocate_port(self, project_name: str, service_name: str, 
                     preferred_port: Optional[int] = None,
                     service_type: Optional[str] = None) -> Optional[AllocatedPort]:
        """
        단일 포트 할당
        
        Args:
            project_name: 프로젝트 이름
            service_name: 서비스 이름
            preferred_port: 선호하는 포트 번호
            service_type: 강제 지정할 서비스 타입
            
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
        if project_name in self.allocations:
            existing_port = self.allocations[project_name].ports.get(service_name)
            if existing_port and existing_port.is_active:
                # 기존 포트가 여전히 사용 가능한지 확인
                if self.scanner.is_port_available(existing_port.port):
                    existing_port.last_used = datetime.now().isoformat()
                    self._save_allocations()
                    return existing_port
                else:
                    # 기존 포트가 사용 불가능하면 새로 할당
                    existing_port.is_active = False
        
        # 포트 범위 결정
        port_range = stype.port_range
        
        # 선호 포트 확인
        if preferred_port:
            if (port_range[0] <= preferred_port <= port_range[1] and 
                self._is_port_allocatable(preferred_port, project_name, service_name)):
                allocated_port = self._create_allocated_port(
                    preferred_port, service_name, stype.name, project_name
                )
                self._save_allocation(project_name, service_name, allocated_port)
                return allocated_port
        
        # 기본 포트 확인
        if (stype.default_port and 
            self._is_port_allocatable(stype.default_port, project_name, service_name)):
            allocated_port = self._create_allocated_port(
                stype.default_port, service_name, stype.name, project_name
            )
            self._save_allocation(project_name, service_name, allocated_port)
            return allocated_port
        
        # 범위 내에서 사용 가능한 포트 찾기
        available_ports = self.scanner.find_available_ports(
            count=1, 
            port_range=port_range
        )
        
        # 이미 할당된 포트 제외
        for port in available_ports:
            if self._is_port_allocatable(port, project_name, service_name):
                allocated_port = self._create_allocated_port(
                    port, service_name, stype.name, project_name
                )
                self._save_allocation(project_name, service_name, allocated_port)
                return allocated_port
        
        logger.error(f"포트 할당 실패: {project_name}/{service_name}")
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
                              service_type: str, project_name: str) -> AllocatedPort:
        """할당된 포트 객체 생성"""
        now = datetime.now().isoformat()
        return AllocatedPort(
            port=port,
            service_name=service_name,
            service_type=service_type,
            project_name=project_name,
            allocated_at=now,
            last_used=now,
            is_active=True
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
                              preferred_ports: Dict[str, int] = None) -> Dict[str, AllocatedPort]:
        """
        프로젝트의 여러 서비스에 대해 포트 일괄 할당
        
        Args:
            project_name: 프로젝트 이름
            services: 서비스 목록 (문자열 또는 {name, type} 딕셔너리)
            preferred_ports: 서비스별 선호 포트 매핑
            
        Returns:
            서비스 이름을 키로 하는 할당된 포트 딕셔너리
        """
        preferred_ports = preferred_ports or {}
        allocated_ports = {}
        
        logger.info(f"프로젝트 '{project_name}'의 {len(services)}개 서비스 포트 할당 시작")
        
        for service in services:
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
                service_type=service_type
            )
            
            if allocated_port:
                allocated_ports[service_name] = allocated_port
                logger.info(f"  ✅ {service_name}: {allocated_port.port}")
            else:
                logger.error(f"  ❌ {service_name}: 포트 할당 실패")
        
        return allocated_ports
    
    def release_port(self, project_name: str, service_name: str) -> bool:
        """특정 서비스의 포트 해제"""
        if (project_name in self.allocations and 
            service_name in self.allocations[project_name].ports):
            
            self.allocations[project_name].ports[service_name].is_active = False
            self.allocations[project_name].updated_at = datetime.now().isoformat()
            self._save_allocations()
            
            logger.info(f"포트 해제: {project_name}/{service_name}")
            return True
        
        return False
    
    def release_project_ports(self, project_name: str) -> int:
        """프로젝트의 모든 포트 해제"""
        if project_name not in self.allocations:
            return 0
        
        count = 0
        for service_name in self.allocations[project_name].ports:
            if self.release_port(project_name, service_name):
                count += 1
        
        return count
    
    def get_project_ports(self, project_name: str) -> Dict[str, AllocatedPort]:
        """프로젝트의 할당된 포트 조회"""
        if project_name in self.allocations:
            return {k: v for k, v in self.allocations[project_name].ports.items() 
                   if v.is_active}
        return {}
    
    def get_all_allocations(self) -> Dict[str, ProjectPorts]:
        """모든 포트 할당 정보 조회"""
        return self.allocations
    
    def cleanup_inactive_ports(self) -> int:
        """비활성 포트 정리"""
        cleanup_count = 0
        
        for project_name, project_ports in self.allocations.items():
            services_to_remove = []
            
            for service_name, allocated_port in project_ports.ports.items():
                if not allocated_port.is_active:
                    services_to_remove.append(service_name)
            
            for service_name in services_to_remove:
                del project_ports.ports[service_name]
                cleanup_count += 1
        
        if cleanup_count > 0:
            self._save_allocations()
            logger.info(f"비활성 포트 {cleanup_count}개 정리 완료")
        
        return cleanup_count
    
    def generate_allocation_report(self) -> Dict:
        """포트 할당 보고서 생성"""
        active_allocations = 0
        inactive_allocations = 0
        projects_count = len(self.allocations)
        
        service_type_stats = {}
        port_usage = {}
        
        for project_ports in self.allocations.values():
            for allocated_port in project_ports.ports.values():
                if allocated_port.is_active:
                    active_allocations += 1
                    
                    # 서비스 타입별 통계
                    stype = allocated_port.service_type
                    service_type_stats[stype] = service_type_stats.get(stype, 0) + 1
                    
                    # 포트 사용 현황
                    port_usage[allocated_port.port] = {
                        'project': allocated_port.project_name,
                        'service': allocated_port.service_name,
                        'type': allocated_port.service_type
                    }
                else:
                    inactive_allocations += 1
        
        return {
            'summary': {
                'total_projects': projects_count,
                'active_allocations': active_allocations,
                'inactive_allocations': inactive_allocations,
                'total_allocated_ports': len(port_usage)
            },
            'service_type_distribution': service_type_stats,
            'port_usage': port_usage,
            'allocation_details': {
                project_name: {
                    'services': len(project_ports.ports),
                    'active_services': len([p for p in project_ports.ports.values() if p.is_active]),
                    'created_at': project_ports.created_at,
                    'updated_at': project_ports.updated_at
                }
                for project_name, project_ports in self.allocations.items()
            }
        }