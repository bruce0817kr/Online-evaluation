"""
포트 스캐너 모듈
===============

시스템에서 사용 중인 포트를 스캔하고 분석하는 모듈
Docker 컨테이너, 시스템 프로세스, 예약된 포트 등을 종합적으로 분석
"""

import socket
import subprocess
import json
import psutil
from typing import List, Dict, Set, Tuple, Optional
import logging
from dataclasses import dataclass
from enum import Enum

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PortStatus(Enum):
    """포트 상태 열거형"""
    AVAILABLE = "available"
    OCCUPIED_SYSTEM = "occupied_system" 
    OCCUPIED_DOCKER = "occupied_docker"
    RESERVED = "reserved"
    UNKNOWN = "unknown"

@dataclass
class PortInfo:
    """포트 정보 데이터 클래스"""
    port: int
    status: PortStatus
    process_name: Optional[str] = None
    process_pid: Optional[int] = None
    container_name: Optional[str] = None
    protocol: str = "tcp"
    description: Optional[str] = None

class PortScanner:
    """
    고급 포트 스캐너
    
    기능:
    - 시스템 포트 사용 현황 스캔
    - Docker 컨테이너 포트 분석
    - 포트 충돌 감지
    - 사용 가능한 포트 범위 분석
    """
    
    def __init__(self, scan_range: Tuple[int, int] = (1000, 65535)):
        """
        포트 스캐너 초기화
        
        Args:
            scan_range: 스캔할 포트 범위 (시작, 끝)
        """
        self.scan_range = scan_range
        self.reserved_ports = self._get_system_reserved_ports()
        self._cached_scan_result = None
        
    def _get_system_reserved_ports(self) -> Set[int]:
        """시스템 예약 포트 목록 반환"""
        # 잘 알려진 예약 포트들
        reserved = {
            22,    # SSH
            25,    # SMTP
            53,    # DNS
            80,    # HTTP
            110,   # POP3
            143,   # IMAP
            443,   # HTTPS
            993,   # IMAPS
            995,   # POP3S
        }
        
        # 1024 미만의 privileged 포트들도 기본적으로 예약
        reserved.update(range(1, 1024))
        
        return reserved
    
    def scan_system_ports(self, force_refresh: bool = False) -> Dict[int, PortInfo]:
        """
        시스템 포트 스캔
        
        Args:
            force_refresh: 캐시된 결과를 무시하고 새로 스캔할지 여부
            
        Returns:
            포트 번호를 키로 하는 PortInfo 딕셔너리
        """
        if not force_refresh and self._cached_scan_result:
            return self._cached_scan_result
            
        logger.info(f"시스템 포트 스캔 시작 (범위: {self.scan_range[0]}-{self.scan_range[1]})")
        
        port_info = {}
        
        # psutil을 사용한 네트워크 연결 스캔
        try:
            connections = psutil.net_connections(kind='inet')
            
            for conn in connections:
                if conn.laddr and conn.status == 'LISTEN':
                    port = conn.laddr.port
                    
                    # 스캔 범위 내의 포트만 처리
                    if self.scan_range[0] <= port <= self.scan_range[1]:
                        process_info = self._get_process_info(conn.pid)
                        
                        port_info[port] = PortInfo(
                            port=port,
                            status=PortStatus.OCCUPIED_SYSTEM,
                            process_name=process_info.get('name'),
                            process_pid=conn.pid,
                            protocol='tcp',
                            description=f"System process: {process_info.get('name', 'Unknown')}"
                        )
                        
        except Exception as e:
            logger.error(f"시스템 포트 스캔 중 오류: {e}")
        
        # Docker 컨테이너 포트 스캔
        docker_ports = self._scan_docker_ports()
        for port, container_name in docker_ports.items():
            if self.scan_range[0] <= port <= self.scan_range[1]:
                port_info[port] = PortInfo(
                    port=port,
                    status=PortStatus.OCCUPIED_DOCKER,
                    container_name=container_name,
                    protocol='tcp',
                    description=f"Docker container: {container_name}"
                )
        
        # 예약된 포트 표시
        for port in self.reserved_ports:
            if self.scan_range[0] <= port <= self.scan_range[1] and port not in port_info:
                port_info[port] = PortInfo(
                    port=port,
                    status=PortStatus.RESERVED,
                    protocol='tcp',
                    description="System reserved port"
                )
        
        self._cached_scan_result = port_info
        logger.info(f"포트 스캔 완료: {len(port_info)}개 포트 분석됨")
        
        return port_info
    
    def _get_process_info(self, pid: Optional[int]) -> Dict[str, str]:
        """프로세스 정보 조회"""
        if not pid:
            return {}
            
        try:
            process = psutil.Process(pid)
            return {
                'name': process.name(),
                'exe': process.exe(),
                'cmdline': ' '.join(process.cmdline())
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return {'name': 'Unknown'}
    
    def _scan_docker_ports(self) -> Dict[int, str]:
        """Docker 컨테이너 포트 스캔"""
        docker_ports = {}
        
        try:
            # Docker 명령어로 실행 중인 컨테이너의 포트 정보 조회
            result = subprocess.run(
                ['docker', 'ps', '--format', 'json'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line.strip():
                        try:
                            container_info = json.loads(line)
                            container_name = container_info.get('Names', 'unknown')
                            ports = container_info.get('Ports', '')
                            
                            # 포트 매핑 파싱 (예: "0.0.0.0:3000->3000/tcp")
                            if ports:
                                port_mappings = self._parse_docker_ports(ports)
                                for host_port in port_mappings:
                                    docker_ports[host_port] = container_name
                                    
                        except json.JSONDecodeError:
                            continue
                            
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            logger.warning("Docker 포트 스캔 실패 (Docker가 설치되지 않았거나 실행되지 않음)")
        
        return docker_ports
    
    def _parse_docker_ports(self, ports_string: str) -> List[int]:
        """Docker 포트 문자열 파싱"""
        host_ports = []
        
        # 포트 문자열 예시: "0.0.0.0:3000->3000/tcp, 0.0.0.0:8080->8000/tcp"
        port_mappings = ports_string.split(',')
        
        for mapping in port_mappings:
            mapping = mapping.strip()
            if '->' in mapping:
                # 호스트 포트 추출
                host_part = mapping.split('->')[0].strip()
                if ':' in host_part:
                    try:
                        host_port = int(host_part.split(':')[-1])
                        host_ports.append(host_port)
                    except ValueError:
                        continue
        
        return host_ports
    
    def is_port_available(self, port: int, protocol: str = 'tcp') -> bool:
        """
        특정 포트가 사용 가능한지 확인
        
        Args:
            port: 확인할 포트 번호
            protocol: 프로토콜 ('tcp' 또는 'udp')
            
        Returns:
            포트 사용 가능 여부
        """
        # 캐시된 스캔 결과 확인
        if self._cached_scan_result and port in self._cached_scan_result:
            return self._cached_scan_result[port].status == PortStatus.AVAILABLE
        
        # 실시간 포트 바인딩 테스트
        try:
            if protocol.lower() == 'tcp':
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            else:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            
            sock.settimeout(1)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            
            # 연결 실패 시 포트 사용 가능
            return result != 0
            
        except Exception:
            return False
    
    def find_available_ports(self, count: int, start_port: int = None, 
                           port_range: Tuple[int, int] = None) -> List[int]:
        """
        사용 가능한 포트 목록 찾기
        
        Args:
            count: 필요한 포트 개수
            start_port: 시작 포트 (없으면 스캔 범위 시작)
            port_range: 검색할 포트 범위 (없으면 기본 스캔 범위)
            
        Returns:
            사용 가능한 포트 번호 리스트
        """
        if port_range:
            start, end = port_range
        else:
            start, end = self.scan_range
            
        if start_port:
            start = max(start, start_port)
        
        available_ports = []
        current_port = start
        
        port_info = self.scan_system_ports()
        
        while len(available_ports) < count and current_port <= end:
            if current_port not in port_info or port_info[current_port].status == PortStatus.AVAILABLE:
                if self.is_port_available(current_port):
                    available_ports.append(current_port)
            
            current_port += 1
        
        if len(available_ports) < count:
            logger.warning(f"요청한 {count}개 포트 중 {len(available_ports)}개만 찾음")
        
        return available_ports
    
    def get_port_conflicts(self, desired_ports: List[int]) -> Dict[int, PortInfo]:
        """
        원하는 포트 목록에서 충돌하는 포트들 반환
        
        Args:
            desired_ports: 확인하고 싶은 포트 목록
            
        Returns:
            충돌하는 포트 정보
        """
        port_info = self.scan_system_ports()
        conflicts = {}
        
        for port in desired_ports:
            if port in port_info and port_info[port].status != PortStatus.AVAILABLE:
                conflicts[port] = port_info[port]
        
        return conflicts
    
    def generate_scan_report(self) -> Dict:
        """
        포트 스캔 보고서 생성
        
        Returns:
            스캔 결과 요약 보고서
        """
        port_info = self.scan_system_ports()
        
        report = {
            'scan_range': self.scan_range,
            'total_scanned': self.scan_range[1] - self.scan_range[0] + 1,
            'occupied_ports': len([p for p in port_info.values() 
                                 if p.status in [PortStatus.OCCUPIED_SYSTEM, PortStatus.OCCUPIED_DOCKER]]),
            'reserved_ports': len([p for p in port_info.values() if p.status == PortStatus.RESERVED]),
            'available_ports': self.scan_range[1] - self.scan_range[0] + 1 - len(port_info),
            'docker_containers': len(set([p.container_name for p in port_info.values() 
                                        if p.container_name])),
            'system_processes': len(set([p.process_name for p in port_info.values() 
                                       if p.process_name])),
            'port_details': {port: {
                'status': info.status.value,
                'process': info.process_name,
                'container': info.container_name,
                'description': info.description
            } for port, info in port_info.items()}
        }
        
        return report