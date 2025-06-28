"""
포트 매니저 서비스
사용 가능한 포트를 자동으로 할당하고 관리하는 시스템
"""

import asyncio
import socket
import json
import logging
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import psutil
from pathlib import Path

logger = logging.getLogger(__name__)

class PortManagerService:
    """포트 관리 서비스"""
    
    def __init__(self, config_file: str = "port_config.json"):
        self.config_file = config_file
        self.allocated_ports = {}
        self.reserved_ports = set()
        self.port_range = (8000, 9999)  # 기본 포트 범위
        self.load_config()
    
    def load_config(self):
        """설정 파일에서 포트 할당 정보 로드"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.allocated_ports = config.get('allocated_ports', {})
                    self.reserved_ports = set(config.get('reserved_ports', []))
                    self.port_range = tuple(config.get('port_range', [8000, 9999]))
            except Exception as e:
                logger.error(f"설정 파일 로드 오류: {e}")
    
    def save_config(self):
        """현재 포트 할당 정보를 설정 파일에 저장"""
        try:
            config = {
                'allocated_ports': self.allocated_ports,
                'reserved_ports': list(self.reserved_ports),
                'port_range': list(self.port_range),
                'last_updated': datetime.utcnow().isoformat()
            }
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logger.error(f"설정 파일 저장 오류: {e}")
    
    def is_port_available(self, port: int) -> bool:
        """특정 포트가 사용 가능한지 확인"""
        if port in self.allocated_ports.values() or port in self.reserved_ports:
            return False
        
        # 실제 포트 사용 여부 확인
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('', port))
                return True
            except:
                return False
    
    def find_available_port(self, start_port: Optional[int] = None) -> Optional[int]:
        """사용 가능한 포트 찾기"""
        start = start_port or self.port_range[0]
        end = self.port_range[1]
        
        for port in range(start, end + 1):
            if self.is_port_available(port):
                return port
        
        return None
    
    def allocate_port(self, service_name: str, preferred_port: Optional[int] = None) -> Optional[int]:
        """서비스에 포트 할당"""
        # 이미 할당된 포트가 있는지 확인
        if service_name in self.allocated_ports:
            port = self.allocated_ports[service_name]
            if self.is_port_available(port):
                return port
        
        # 선호 포트가 있고 사용 가능한 경우
        if preferred_port and self.is_port_available(preferred_port):
            self.allocated_ports[service_name] = preferred_port
            self.save_config()
            return preferred_port
        
        # 새로운 포트 찾기
        port = self.find_available_port()
        if port:
            self.allocated_ports[service_name] = port
            self.save_config()
            return port
        
        return None
    
    def release_port(self, service_name: str):
        """서비스의 포트 할당 해제"""
        if service_name in self.allocated_ports:
            del self.allocated_ports[service_name]
            self.save_config()
    
    def reserve_port(self, port: int):
        """특정 포트를 예약 (수동 할당용)"""
        self.reserved_ports.add(port)
        self.save_config()
    
    def get_port_status(self) -> Dict[str, any]:
        """현재 포트 할당 상태 조회"""
        # 실제 사용 중인 포트 확인
        active_connections = []
        for conn in psutil.net_connections():
            if conn.status == 'LISTEN':
                active_connections.append({
                    'port': conn.laddr.port,
                    'pid': conn.pid,
                    'status': 'LISTENING'
                })
        
        return {
            'allocated_ports': self.allocated_ports,
            'reserved_ports': list(self.reserved_ports),
            'active_connections': active_connections,
            'port_range': self.port_range
        }
    
    def get_service_config(self) -> Dict[str, Dict[str, any]]:
        """서비스별 포트 설정 생성"""
        base_url = os.getenv('BASE_URL', 'localhost')
        
        services = {
            'frontend': {
                'name': 'Frontend (React)',
                'port': self.allocate_port('frontend', 3000),
                'url': f'http://{base_url}:3000',
                'healthcheck': '/health',
                'environment': 'development'
            },
            'backend': {
                'name': 'Backend (FastAPI)',
                'port': self.allocate_port('backend', 8080),
                'url': f'http://{base_url}:8080',
                'healthcheck': '/api/health',
                'environment': 'development'
            },
            'mongodb': {
                'name': 'MongoDB',
                'port': self.allocate_port('mongodb', 27017),
                'url': f'mongodb://{base_url}:27017',
                'healthcheck': None,
                'environment': 'development'
            },
            'redis': {
                'name': 'Redis Cache',
                'port': self.allocate_port('redis', 6379),
                'url': f'redis://{base_url}:6379',
                'healthcheck': None,
                'environment': 'development'
            },
            'nginx': {
                'name': 'Nginx Proxy',
                'port': self.allocate_port('nginx', 80),
                'url': f'http://{base_url}',
                'healthcheck': '/health',
                'environment': 'production'
            },
            'prometheus': {
                'name': 'Prometheus Monitoring',
                'port': self.allocate_port('prometheus', 9090),
                'url': f'http://{base_url}:9090',
                'healthcheck': '/-/healthy',
                'environment': 'monitoring'
            },
            'grafana': {
                'name': 'Grafana Dashboard',
                'port': self.allocate_port('grafana', 3001),
                'url': f'http://{base_url}:3001',
                'healthcheck': '/api/health',
                'environment': 'monitoring'
            },
            'elasticsearch': {
                'name': 'Elasticsearch',
                'port': self.allocate_port('elasticsearch', 9200),
                'url': f'http://{base_url}:9200',
                'healthcheck': '/_cluster/health',
                'environment': 'logging'
            },
            'kibana': {
                'name': 'Kibana',
                'port': self.allocate_port('kibana', 5601),
                'url': f'http://{base_url}:5601',
                'healthcheck': '/api/status',
                'environment': 'logging'
            }
        }
        
        return services
    
    def check_port_conflicts(self) -> List[Dict[str, any]]:
        """포트 충돌 검사"""
        conflicts = []
        service_config = self.get_service_config()
        
        # 서비스 간 포트 충돌 확인
        used_ports = {}
        for service_name, config in service_config.items():
            port = config['port']
            if port in used_ports:
                conflicts.append({
                    'type': 'service_conflict',
                    'port': port,
                    'services': [used_ports[port], service_name]
                })
            else:
                used_ports[port] = service_name
        
        # 시스템 포트와의 충돌 확인
        for conn in psutil.net_connections():
            if conn.status == 'LISTEN' and conn.laddr.port in used_ports:
                if conn.pid:
                    try:
                        process = psutil.Process(conn.pid)
                        conflicts.append({
                            'type': 'system_conflict',
                            'port': conn.laddr.port,
                            'service': used_ports[conn.laddr.port],
                            'process': process.name(),
                            'pid': conn.pid
                        })
                    except:
                        pass
        
        return conflicts
    
    async def wait_for_port(self, port: int, timeout: int = 30) -> bool:
        """특정 포트가 사용 가능해질 때까지 대기"""
        start_time = asyncio.get_event_loop().time()
        
        while (asyncio.get_event_loop().time() - start_time) < timeout:
            if self.is_port_available(port):
                return True
            await asyncio.sleep(1)
        
        return False
    
    def generate_docker_compose_ports(self) -> Dict[str, List[str]]:
        """Docker Compose용 포트 매핑 생성"""
        service_config = self.get_service_config()
        port_mappings = {}
        
        for service_name, config in service_config.items():
            if config['port']:
                # 외부포트:내부포트 형식
                internal_ports = {
                    'frontend': 3000,
                    'backend': 8000,
                    'mongodb': 27017,
                    'redis': 6379,
                    'nginx': 80,
                    'prometheus': 9090,
                    'grafana': 3000,
                    'elasticsearch': 9200,
                    'kibana': 5601
                }
                
                internal_port = internal_ports.get(service_name, config['port'])
                port_mappings[service_name] = [f"{config['port']}:{internal_port}"]
        
        return port_mappings
    
    def generate_nginx_upstream(self) -> str:
        """Nginx upstream 설정 생성"""
        service_config = self.get_service_config()
        
        upstream_config = """
# Auto-generated Nginx upstream configuration
upstream backend {
    server backend:%(backend_port)s;
}

upstream frontend {
    server frontend:%(frontend_port)s;
}

upstream grafana {
    server grafana:%(grafana_port)s;
}

upstream kibana {
    server kibana:%(kibana_port)s;
}
""" % {
    'backend_port': service_config['backend']['port'],
    'frontend_port': service_config['frontend']['port'],
    'grafana_port': service_config['grafana']['port'],
    'kibana_port': service_config['kibana']['port']
}
        
        return upstream_config
    
    def cleanup_stale_allocations(self):
        """사용하지 않는 포트 할당 정리"""
        stale_services = []
        
        for service_name, port in self.allocated_ports.items():
            # Docker 컨테이너가 실행 중인지 확인
            if not self._is_service_running(service_name):
                stale_services.append(service_name)
        
        for service in stale_services:
            logger.info(f"미사용 포트 할당 해제: {service}")
            self.release_port(service)
    
    def _is_service_running(self, service_name: str) -> bool:
        """서비스가 실행 중인지 확인"""
        try:
            # Docker 컨테이너 확인
            import subprocess
            result = subprocess.run(
                ['docker', 'ps', '--filter', f'name={service_name}', '--format', '{{.Names}}'],
                capture_output=True,
                text=True
            )
            return service_name in result.stdout
        except:
            # Docker가 설치되지 않은 경우 포트 확인
            port = self.allocated_ports.get(service_name)
            return port and not self.is_port_available(port)
    
    def export_port_mapping(self, output_file: str = "port_mapping.json"):
        """포트 매핑 정보를 파일로 내보내기"""
        service_config = self.get_service_config()
        conflicts = self.check_port_conflicts()
        
        export_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'services': service_config,
            'conflicts': conflicts,
            'port_range': self.port_range,
            'reserved_ports': list(self.reserved_ports)
        }
        
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"포트 매핑 정보 내보내기 완료: {output_file}")

# 싱글톤 인스턴스
port_manager = PortManagerService()