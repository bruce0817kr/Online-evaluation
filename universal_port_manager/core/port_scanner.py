"""
개선된 포트 스캐너 모듈
======================

psutil 의존성 없이도 동작 가능한 Graceful Degradation 적용
다양한 fallback 방식으로 포트 스캔 기능 제공
"""

import socket
import subprocess
import json
import os
import re
from typing import List, Dict, Set, Tuple, Optional, Union
import logging
from dataclasses import dataclass
from enum import Enum

# 선택적 의존성 import
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("⚠️ psutil 없음 - 기본 포트 스캔 방식 사용")

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
    detection_method: str = "unknown"

class ImprovedPortScanner:
    """
    개선된 포트 스캐너
    
    특징:
    - psutil 없이도 동작 (graceful degradation)
    - 다중 감지 방식 (socket, netstat, ss, lsof)
    - 성능 최적화된 스캔
    - 포트 충돌 자동 해결 제안
    """
    
    def __init__(self, scan_range: Tuple[int, int] = (3000, 10000)):
        """
        포트 스캐너 초기화
        
        Args:
            scan_range: 스캔할 포트 범위 (시작, 끝) - 기본적으로 실용적인 범위
        """
        self.scan_range = scan_range
        self.reserved_ports = self._get_system_reserved_ports()
        self._cached_scan_result = None
        self.available_methods = self._detect_available_methods()
        
        logger.info(f"포트 스캐너 초기화 완료")
        logger.info(f"사용 가능한 감지 방법: {self.available_methods}")
        
    def _detect_available_methods(self) -> List[str]:
        """시스템에서 사용 가능한 포트 감지 방법들 확인"""
        methods = ["socket"]  # socket은 항상 사용 가능
        
        # psutil 사용 가능 여부
        if PSUTIL_AVAILABLE:
            methods.append("psutil")
        
        # 시스템 명령어 사용 가능 여부 확인
        commands_to_check = [
            ("ss", "ss -tuln"),
            ("netstat", "netstat -tuln"),
            ("lsof", "lsof -i"),
            ("docker", "docker ps")
        ]
        
        for cmd_name, cmd in commands_to_check:
            try:
                result = subprocess.run(
                    cmd.split(), 
                    capture_output=True, 
                    timeout=2, 
                    text=True
                )
                if result.returncode == 0:
                    methods.append(cmd_name)
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
                pass
        
        return methods
        
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
        
        # 1024 미만의 privileged 포트들은 피하되, 스캔 범위에서 제외
        if self.scan_range[0] < 1024:
            reserved.update(range(1, min(1024, self.scan_range[1] + 1)))
        
        return reserved
    
    def scan_system_ports(self, force_refresh: bool = False) -> Dict[int, PortInfo]:
        """
        시스템 포트 스캔 (다중 방식 사용)
        
        Args:
            force_refresh: 캐시된 결과를 무시하고 새로 스캔할지 여부
            
        Returns:
            포트 번호를 키로 하는 PortInfo 딕셔너리
        """
        if not force_refresh and self._cached_scan_result:
            return self._cached_scan_result
            
        logger.info(f"시스템 포트 스캔 시작 (범위: {self.scan_range[0]}-{self.scan_range[1]})")
        
        port_info = {}
        
        # 다중 방식 병렬 스캔으로 정확도 향상
        scan_results = []
        
        # 1. psutil 방식 (가장 정확)
        if "psutil" in self.available_methods:
            psutil_result = self._scan_with_psutil()
            scan_results.append(("psutil", psutil_result))
            port_info.update(psutil_result)
        
        # 2. ss 명령어 방식 (Linux 표준)
        if "ss" in self.available_methods:
            ss_result = self._scan_with_ss()
            scan_results.append(("ss", ss_result))
            # 기존 결과와 병합 (중복 제거하면서 보완)
            for port, info in ss_result.items():
                if port not in port_info:
                    port_info[port] = info
        
        # 3. netstat 방식 (구버전 호환)
        if "netstat" in self.available_methods:
            netstat_result = self._scan_with_netstat()
            scan_results.append(("netstat", netstat_result))
            # 기존 결과와 병합
            for port, info in netstat_result.items():
                if port not in port_info:
                    port_info[port] = info
        
        # 4. Docker 컨테이너 포트 스캔
        if "docker" in self.available_methods:
            docker_ports = self._scan_docker_ports()
            scan_results.append(("docker", docker_ports))
            # Docker 포트는 우선적으로 추가 (컨테이너 포트는 확실)
            port_info.update(docker_ports)
        
        # 5. socket 기반 직접 검사 (fallback 및 검증)
        socket_result = self._supplement_with_socket_scan(port_info)
        scan_results.append(("socket", socket_result))
        
        # 6. 예약된 포트 표시
        self._add_reserved_ports(port_info)
        
        self._cached_scan_result = port_info
        logger.info(f"포트 스캔 완료: {len(port_info)}개 포트 분석됨")
        
        return port_info
    
    def _scan_with_psutil(self) -> Dict[int, PortInfo]:
        """psutil을 사용한 포트 스캔"""
        port_info = {}
        
        try:
            connections = psutil.net_connections(kind='inet')
            
            for conn in connections:
                if conn.laddr and conn.status == 'LISTEN':
                    port = conn.laddr.port
                    
                    if self.scan_range[0] <= port <= self.scan_range[1]:
                        process_info = self._get_process_info_psutil(conn.pid)
                        
                        port_info[port] = PortInfo(
                            port=port,
                            status=PortStatus.OCCUPIED_SYSTEM,
                            process_name=process_info.get('name'),
                            process_pid=conn.pid,
                            protocol='tcp',
                            description=f"System process: {process_info.get('name', 'Unknown')}",
                            detection_method="psutil"
                        )
                        
        except Exception as e:
            logger.error(f"psutil 포트 스캔 중 오류: {e}")
        
        return port_info
    
    def _scan_with_ss(self) -> Dict[int, PortInfo]:
        """ss 명령어를 사용한 포트 스캔"""
        port_info = {}
        
        try:
            result = subprocess.run(
                ['ss', '-tuln'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    # ss 출력 형식: State Recv-Q Send-Q Local Address:Port Peer Address:Port
                    # 또는: LISTEN 0 4096 *:3000 *:*
                    if 'LISTEN' in line or 'ESTAB' in line or ':' in line:
                        # 다양한 ss 출력 형식 처리
                        parts = line.split()
                        if len(parts) >= 4:
                            # Local Address:Port 찾기 (보통 4번째 또는 5번째 필드)
                            for i in range(3, min(6, len(parts))):
                                if ':' in parts[i]:
                                    local_addr = parts[i]
                                    try:
                                        # IPv6 주소 처리
                                        if local_addr.startswith('['):
                                            port_str = local_addr.split(']:')[-1]
                                        else:
                                            port_str = local_addr.split(':')[-1]
                                        
                                        # 와일드카드 포트 제외
                                        if port_str == '*':
                                            continue
                                            
                                        port = int(port_str)
                                        
                                        if self.scan_range[0] <= port <= self.scan_range[1]:
                                            # 프로토콜 감지
                                            protocol = 'tcp'
                                            if 'udp' in line.lower():
                                                protocol = 'udp'
                                            elif parts[0].lower() in ['tcp', 'udp']:
                                                protocol = parts[0].lower()
                                            
                                            port_info[port] = PortInfo(
                                                port=port,
                                                status=PortStatus.OCCUPIED_SYSTEM,
                                                protocol=protocol,
                                                description="System process (detected via ss)",
                                                detection_method="ss"
                                            )
                                            break  # 포트를 찾았으므로 다음 라인으로
                                    except (ValueError, IndexError):
                                        continue
                        
        except Exception as e:
            logger.error(f"ss 명령어 포트 스캔 중 오류: {e}")
        
        return port_info
    
    def _scan_with_netstat(self) -> Dict[int, PortInfo]:
        """netstat 명령어를 사용한 포트 스캔"""
        port_info = {}
        
        try:
            result = subprocess.run(
                ['netstat', '-tuln'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    # netstat 출력 형식: Proto Recv-Q Send-Q Local Address Foreign Address State
                    if 'LISTEN' in line or 'ESTABLISHED' in line or ':' in line:
                        parts = line.split()
                        if len(parts) >= 4:
                            # Local Address 찾기 (보통 3번째 또는 4번째 필드)
                            for i in range(2, min(5, len(parts))):
                                if ':' in parts[i]:
                                    local_addr = parts[i]
                                    try:
                                        # IPv6 주소 처리
                                        if '[' in local_addr and ']:' in local_addr:
                                            port = int(local_addr.split(']:')[-1])
                                        else:
                                            port = int(local_addr.split(':')[-1])
                                        
                                        if self.scan_range[0] <= port <= self.scan_range[1]:
                                            # 프로토콜 감지
                                            protocol = 'tcp'
                                            if parts[0].lower() in ['tcp', 'tcp6']:
                                                protocol = 'tcp'
                                            elif parts[0].lower() in ['udp', 'udp6']:
                                                protocol = 'udp'
                                            
                                            port_info[port] = PortInfo(
                                                port=port,
                                                status=PortStatus.OCCUPIED_SYSTEM,
                                                protocol=protocol,
                                                description="System process (detected via netstat)",
                                                detection_method="netstat"
                                            )
                                            break
                                    except (ValueError, IndexError):
                                        continue
                        
        except Exception as e:
            logger.error(f"netstat 명령어 포트 스캔 중 오류: {e}")
        
        return port_info
    
    def _scan_docker_ports(self) -> Dict[int, PortInfo]:
        """Docker 컨테이너 포트 스캔"""
        docker_ports = {}
        
        try:
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
                            
                            if ports:
                                host_ports = self._parse_docker_ports(ports)
                                for host_port in host_ports:
                                    if self.scan_range[0] <= host_port <= self.scan_range[1]:
                                        docker_ports[host_port] = PortInfo(
                                            port=host_port,
                                            status=PortStatus.OCCUPIED_DOCKER,
                                            container_name=container_name,
                                            protocol='tcp',
                                            description=f"Docker container: {container_name}",
                                            detection_method="docker"
                                        )
                                        
                        except json.JSONDecodeError:
                            continue
                            
        except Exception as e:
            logger.warning(f"Docker 포트 스캔 실패: {e}")
        
        return docker_ports
    
    def _parse_docker_ports(self, ports_string: str) -> List[int]:
        """Docker 포트 문자열 파싱 (개선된 버전)"""
        host_ports = []
        
        # 더 견고한 정규표현식 사용
        # 0.0.0.0:3000->3000/tcp, :::8080->8080/tcp 등 다양한 형태 처리
        port_pattern = r'(?:0\.0\.0\.0|:::|\[::\]):(\d+)->'
        
        matches = re.findall(port_pattern, ports_string)
        for match in matches:
            try:
                host_ports.append(int(match))
            except ValueError:
                continue
        
        return host_ports
    
    def _supplement_with_socket_scan(self, existing_ports: Dict[int, PortInfo]) -> Dict[int, PortInfo]:
        """socket을 사용한 보완 스캔 (기존 스캔에서 놓친 포트들 확인)"""
        socket_results = {}
        
        # 기존에 감지되지 않은 특정 포트들을 socket으로 직접 확인
        common_ports = [3000, 3001, 8000, 8001, 8080, 8081, 5432, 27017, 6379, 9090, 3013, 6346, 8811, 6380, 8013, 6333]
        
        # 스캔 범위 내의 모든 포트를 샘플링으로 확인 (성능 고려)
        sample_ports = list(range(self.scan_range[0], min(self.scan_range[1] + 1, self.scan_range[0] + 100), 10))
        test_ports = list(set(common_ports + sample_ports))
        
        for port in test_ports:
            if (self.scan_range[0] <= port <= self.scan_range[1] and 
                port not in existing_ports):
                
                # TCP와 UDP 모두 확인
                tcp_occupied = not self._is_port_available_socket(port, 'tcp')
                udp_occupied = not self._is_port_available_socket(port, 'udp')
                
                if tcp_occupied or udp_occupied:
                    protocol = 'tcp' if tcp_occupied else 'udp'
                    socket_results[port] = PortInfo(
                        port=port,
                        status=PortStatus.OCCUPIED_SYSTEM,
                        protocol=protocol,
                        description="Occupied (detected via socket)",
                        detection_method="socket"
                    )
                    existing_ports[port] = socket_results[port]
        
        return socket_results
    
    def _add_reserved_ports(self, port_info: Dict[int, PortInfo]):
        """예약된 포트 정보 추가"""
        for port in self.reserved_ports:
            if (self.scan_range[0] <= port <= self.scan_range[1] and 
                port not in port_info):
                port_info[port] = PortInfo(
                    port=port,
                    status=PortStatus.RESERVED,
                    protocol='tcp',
                    description="System reserved port",
                    detection_method="reserved"
                )
    
    def _get_process_info_psutil(self, pid: Optional[int]) -> Dict[str, str]:
        """psutil을 사용한 프로세스 정보 조회"""
        if not pid or not PSUTIL_AVAILABLE:
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
    
    def _is_port_available_socket(self, port: int, protocol: str = 'tcp') -> bool:
        """socket을 사용한 포트 가용성 확인 (개선된 버전)"""
        try:
            if protocol.lower() == 'tcp':
                # TCP 포트는 연결 시도로 확인
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.5)  # 빠른 응답을 위해 타임아웃 단축
                
                # 바인딩 시도로 더 정확한 확인
                try:
                    sock.bind(('127.0.0.1', port))
                    sock.close()
                    return True  # 바인딩 성공 시 포트 사용 가능
                except OSError:
                    sock.close()
                    return False  # 바인딩 실패 시 포트 사용 중
            else:
                # UDP 포트는 바인딩으로만 확인 가능
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                try:
                    sock.bind(('127.0.0.1', port))
                    sock.close()
                    return True
                except OSError:
                    sock.close()
                    return False
            
        except Exception:
            return False
    
    def is_port_available(self, port: int, protocol: str = 'tcp') -> bool:
        """포트 가용성 확인 (캐시 우선, 실시간 확인 보조)"""
        # 캐시된 스캔 결과 우선 확인
        if self._cached_scan_result and port in self._cached_scan_result:
            cached_info = self._cached_scan_result[port]
            return cached_info.status == PortStatus.AVAILABLE
        
        # 실시간 socket 테스트
        return self._is_port_available_socket(port, protocol)
    
    def find_available_ports(self, count: int, start_port: int = None, 
                           avoid_ports: List[int] = None) -> List[int]:
        """
        사용 가능한 포트 목록 찾기 (개선된 버전)
        
        Args:
            count: 필요한 포트 개수
            start_port: 시작 포트 (없으면 스캔 범위 시작)
            avoid_ports: 피해야 할 포트 목록
            
        Returns:
            사용 가능한 포트 번호 리스트
        """
        avoid_ports = avoid_ports or []
        start = start_port or self.scan_range[0]
        end = self.scan_range[1]
        
        available_ports = []
        current_port = start
        
        # 성능을 위해 일부 포트만 미리 스캔
        port_info = self.scan_system_ports()
        
        while len(available_ports) < count and current_port <= end:
            if current_port in avoid_ports:
                current_port += 1
                continue
                
            # 캐시된 정보 확인
            if current_port in port_info:
                if port_info[current_port].status == PortStatus.AVAILABLE:
                    available_ports.append(current_port)
            else:
                # 실시간 확인
                if self._is_port_available_socket(current_port):
                    available_ports.append(current_port)
            
            current_port += 1
        
        if len(available_ports) < count:
            logger.warning(f"요청한 {count}개 포트 중 {len(available_ports)}개만 찾음")
        
        return available_ports
    
    def get_port_conflicts(self, desired_ports: List[int]) -> Dict[int, PortInfo]:
        """포트 충돌 확인 및 대안 제시"""
        port_info = self.scan_system_ports()
        conflicts = {}
        
        for port in desired_ports:
            if port in port_info and port_info[port].status != PortStatus.AVAILABLE:
                conflicts[port] = port_info[port]
        
        return conflicts
    
    def suggest_alternative_ports(self, conflicted_ports: Dict[int, PortInfo]) -> Dict[int, int]:
        """충돌하는 포트에 대한 대안 포트 제안"""
        alternatives = {}
        
        for original_port in conflicted_ports.keys():
            # 원래 포트 근처에서 대안 찾기
            alternative_candidates = self.find_available_ports(
                count=1, 
                start_port=original_port + 1, 
                avoid_ports=list(conflicted_ports.keys())
            )
            
            if alternative_candidates:
                alternatives[original_port] = alternative_candidates[0]
            else:
                # 근처에서 못 찾으면 전체 범위에서 찾기
                fallback_candidates = self.find_available_ports(count=1)
                if fallback_candidates:
                    alternatives[original_port] = fallback_candidates[0]
        
        return alternatives
    
    def generate_detailed_report(self) -> Dict:
        """상세한 포트 스캔 보고서 생성"""
        port_info = self.scan_system_ports()
        
        occupied_system = [p for p in port_info.values() if p.status == PortStatus.OCCUPIED_SYSTEM]
        occupied_docker = [p for p in port_info.values() if p.status == PortStatus.OCCUPIED_DOCKER]
        reserved = [p for p in port_info.values() if p.status == PortStatus.RESERVED]
        
        report = {
            'scan_info': {
                'range': self.scan_range,
                'total_range_size': self.scan_range[1] - self.scan_range[0] + 1,
                'detection_methods': self.available_methods,
                'psutil_available': PSUTIL_AVAILABLE
            },
            'summary': {
                'total_scanned_ports': len(port_info),
                'occupied_system': len(occupied_system),
                'occupied_docker': len(occupied_docker),
                'reserved_ports': len(reserved),
                'estimated_available': self.scan_range[1] - self.scan_range[0] + 1 - len(port_info)
            },
            'docker_info': {
                'containers_found': len(set([p.container_name for p in occupied_docker if p.container_name])),
                'docker_ports': [p.port for p in occupied_docker]
            },
            'system_info': {
                'system_processes': len(set([p.process_name for p in occupied_system if p.process_name])),
                'system_ports': [p.port for p in occupied_system]
            },
            'port_details': {
                port: {
                    'status': info.status.value,
                    'process': info.process_name,
                    'container': info.container_name,
                    'description': info.description,
                    'detection_method': info.detection_method
                } for port, info in port_info.items()
            }
        }
        
        return report

# 기존 PortScanner와의 호환성을 위한 별칭
PortScanner = ImprovedPortScanner