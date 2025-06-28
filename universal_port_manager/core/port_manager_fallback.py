"""
포트 매니저 대체 시스템
====================

의존성 없이 작동하는 기본적인 포트 관리 기능
psutil, YAML 등이 없어도 최소한의 포트 할당 및 스캔 기능 제공
"""

import socket
import logging
from typing import Dict, List, Union
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class FallbackPortInfo:
    """대체 포트 정보 클래스"""
    port: int
    status: str
    description: str

@dataclass
class FallbackAllocatedPort:
    """대체 할당 포트 클래스"""
    port: int
    service_name: str
    service_type: str
    project_name: str
    allocated_at: str
    last_used: str
    is_active: bool = True
    conflict_resolution: str = "fallback_allocation"

class PortManagerFallback:
    """
    포트 매니저 대체 시스템
    
    의존성 없이 동작하는 최소한의 포트 관리 기능:
    - 기본적인 포트 스캔 (socket 기반)
    - 단순한 포트 할당
    - 충돌 감지
    """
    
    def __init__(self):
        """대체 시스템 초기화"""
        self.fallback_ports = {
            'frontend': 3001,
            'backend': 8001,
            'database': 5433,
            'mongodb': 27018,
            'redis': 6381,
            'nginx': 8090,
            'monitoring': 9091
        }
        
        # 공통 포트들 (피해야 할 포트)
        self.common_occupied_ports = [
            3000,  # 많은 개발 서버
            8000,  # 일반적인 웹서버
            8080,  # HTTP 대체 포트
            5432,  # PostgreSQL
            27017, # MongoDB
            6379,  # Redis
            9090,  # Prometheus
            3306,  # MySQL
            80,    # HTTP
            443,   # HTTPS
            22,    # SSH
        ]
        
        logger.info("포트 매니저 대체 시스템 초기화")
    
    def scan_ports(self, port_range: tuple = (3000, 4000)) -> Dict[int, FallbackPortInfo]:
        """
        기본적인 포트 스캔 (socket 기반)
        
        Args:
            port_range: 스캔할 포트 범위
            
        Returns:
            점유된 포트 정보 딕셔너리
        """
        occupied_ports = {}
        start_port, end_port = port_range
        
        logger.info(f"기본 포트 스캔 시작: {start_port}-{end_port}")
        
        # 빠른 스캔을 위해 샘플링
        test_ports = list(range(start_port, min(start_port + 50, end_port)))
        test_ports.extend(self.common_occupied_ports)
        test_ports = list(set(test_ports))  # 중복 제거
        
        for port in test_ports:
            if self._is_port_occupied(port):
                occupied_ports[port] = FallbackPortInfo(
                    port=port,
                    status='OCCUPIED',
                    description=f'Port {port} in use'
                )
        
        logger.info(f"스캔 완료: {len(occupied_ports)}개 포트 점유됨")
        return occupied_ports
    
    def _is_port_occupied(self, port: int) -> bool:
        """단일 포트가 사용 중인지 확인"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.1)
        try:
            result = sock.connect_ex(('localhost', port))
            return result == 0  # 연결 성공 = 포트 사용 중
        except Exception:
            return False
        finally:
            sock.close()
    
    def allocate_ports(self, services: List[Union[str, Dict]], 
                      preferred_ports: Dict[str, int], 
                      project_name: str) -> Dict[str, FallbackAllocatedPort]:
        """
        기본적인 포트 할당
        
        Args:
            services: 서비스 목록
            preferred_ports: 선호 포트 매핑
            project_name: 프로젝트 이름
            
        Returns:
            할당된 포트 딕셔너리
        """
        allocated_ports = {}
        used_ports = set()
        
        # 현재 사용 중인 포트들 확인
        occupied_info = self.scan_ports()
        occupied_ports = set(occupied_info.keys())
        
        logger.info(f"대체 할당 시작: {len(services)}개 서비스")
        
        for service in services:
            if isinstance(service, str):
                service_name = service
                service_type = self._guess_service_type(service_name)
            else:
                service_name = service.get('name')
                service_type = service.get('type', self._guess_service_type(service_name))
            
            # 포트 결정
            port = self._find_available_port(
                service_name, service_type, preferred_ports, 
                occupied_ports, used_ports
            )
            
            if port:
                now = datetime.now().isoformat()
                allocated_port = FallbackAllocatedPort(
                    port=port,
                    service_name=service_name,
                    service_type=service_type,
                    project_name=project_name,
                    allocated_at=now,
                    last_used=now,
                    is_active=True,
                    conflict_resolution="fallback_allocation"
                )
                allocated_ports[service_name] = allocated_port
                used_ports.add(port)
                logger.info(f"대체 할당 성공: {service_name} -> {port}")
            else:
                logger.error(f"포트 할당 실패: {service_name}")
        
        return allocated_ports
    
    def _find_available_port(self, service_name: str, service_type: str,
                           preferred_ports: Dict[str, int], 
                           occupied_ports: set, used_ports: set) -> int:
        """사용 가능한 포트 찾기"""
        
        # 1. 선호 포트 확인
        if service_name in preferred_ports:
            preferred_port = preferred_ports[service_name]
            if (preferred_port not in occupied_ports and 
                preferred_port not in used_ports and
                not self._is_port_occupied(preferred_port)):
                return preferred_port
        
        # 2. 기본 포트 확인
        if service_type in self.fallback_ports:
            default_port = self.fallback_ports[service_type]
            if (default_port not in occupied_ports and 
                default_port not in used_ports and
                not self._is_port_occupied(default_port)):
                return default_port
        
        # 3. 서비스 타입별 범위에서 찾기
        search_ranges = {
            'frontend': (3001, 3100),
            'backend': (8001, 8100),
            'database': (5433, 5500),
            'mongodb': (27018, 27050),
            'redis': (6381, 6400),
            'nginx': (8090, 8110),
            'monitoring': (9091, 9150)
        }
        
        start_port, end_port = search_ranges.get(service_type, (4000, 4100))
        
        for port in range(start_port, end_port):
            if (port not in occupied_ports and 
                port not in used_ports and
                not self._is_port_occupied(port)):
                return port
        
        # 4. 일반 범위에서 찾기 (마지막 수단)
        for port in range(3001, 4000):
            if (port not in occupied_ports and 
                port not in used_ports and
                not self._is_port_occupied(port)):
                return port
        
        return None
    
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
        elif any(keyword in name_lower for keyword in ['nginx', 'proxy']):
            return 'nginx'
        elif any(keyword in name_lower for keyword in ['monitor', 'grafana', 'prometheus']):
            return 'monitoring'
        else:
            return 'backend'  # 기본값
    
    def check_conflicts(self, desired_ports: List[int]) -> Dict[int, FallbackPortInfo]:
        """기본적인 충돌 검사"""
        conflicts = {}
        
        for port in desired_ports:
            if self._is_port_occupied(port):
                conflicts[port] = FallbackPortInfo(
                    port=port,
                    status='OCCUPIED',
                    description=f'Port {port} is in use'
                )
        
        return conflicts
    
    def suggest_alternative_ports(self, conflicted_ports: List[int]) -> Dict[int, int]:
        """충돌 포트에 대한 대안 제시"""
        alternatives = {}
        
        for port in conflicted_ports:
            # 근처 포트에서 대안 찾기
            for offset in range(1, 20):
                alt_port = port + offset
                if alt_port < 65535 and not self._is_port_occupied(alt_port):
                    alternatives[port] = alt_port
                    break
        
        return alternatives
    
    def get_system_info(self) -> Dict:
        """시스템 정보 조회"""
        return {
            'type': 'fallback',
            'methods': ['socket'],
            'capabilities': ['basic_scan', 'simple_allocation', 'conflict_check'],
            'limitations': ['no_process_detection', 'no_docker_detection']
        }