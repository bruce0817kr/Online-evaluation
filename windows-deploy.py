#!/usr/bin/env python3
"""
Windows 전용 배포 스크립트
========================

Windows 환경에서 발생하는 인코딩 및 모듈 인식 문제를 해결한 배포 스크립트
"""

import os
import sys
import json
import time
import subprocess
import webbrowser
from pathlib import Path
from datetime import datetime
import logging

# Windows 인코딩 문제 해결
if os.name == 'nt':
    import locale
    try:
        # Windows에서 UTF-8 출력 강제 설정
        os.system('chcp 65001 >nul')
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class WindowsDeployer:
    """Windows 전용 배포 관리자"""
    
    def __init__(self):
        self.project_name = "online-evaluation"
        self.services = ["frontend", "backend", "mongodb", "redis", "nginx"]
        self.project_root = Path.cwd()
        
        # 기본 포트 설정
        self.frontend_port = 3001
        self.backend_port = 8001
        
        print("=" * 60)
        print("    Windows Online Evaluation System Deploy")
        print("=" * 60)
        print()
        
    def print_step(self, step, total, message):
        """단계별 메시지 출력"""
        print(f"[Step {step}/{total}] {message}")
    
    def print_success(self, message):
        """성공 메시지 출력"""
        print(f"[OK] {message}")
    
    def print_error(self, message):
        """오류 메시지 출력"""
        print(f"[ERROR] {message}")
    
    def print_info(self, message):
        """정보 메시지 출력"""
        print(f"[INFO] {message}")
    
    def run_command(self, command, shell=True, capture_output=True, timeout=60, encoding='utf-8'):
        """Windows 환경을 고려한 명령어 실행"""
        try:
            if isinstance(command, str):
                cmd = command
            else:
                cmd = ' '.join(command) if shell else command
            
            # Windows에서 인코딩 문제 해결
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            
            result = subprocess.run(
                cmd if shell else command,
                shell=shell,
                capture_output=capture_output,
                text=True,
                timeout=timeout,
                cwd=self.project_root,
                env=env,
                encoding='utf-8',
                errors='replace'  # 인코딩 오류 시 대체 문자 사용
            )
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Command timeout'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def check_prerequisites(self):
        """사전 요구사항 확인"""
        self.print_info("Checking prerequisites...")
        
        # Python 확인
        if sys.version_info < (3, 7):
            self.print_error("Python 3.7+ required")
            return False
        
        # Docker 확인
        docker_result = self.run_command("docker --version")
        if not docker_result['success']:
            self.print_error("Docker not installed or not running")
            return False
        
        # Docker 데몬 확인
        daemon_result = self.run_command("docker info")
        if not daemon_result['success']:
            self.print_error("Docker daemon not running")
            return False
        
        self.print_success("All prerequisites OK")
        return True
    
    def simple_port_allocation(self):
        """간단한 포트 할당 (UPM 없이)"""
        self.print_step(1, 5, "Simple port allocation...")
        
        # 사용 중인 포트 확인
        occupied_ports = self.get_occupied_ports()
        
        # 포트 할당
        port_mappings = {
            'frontend': 3001,
            'backend': 8001,
            'mongodb': 27018,
            'redis': 6381,
            'nginx': 8081
        }
        
        # 충돌 검사 및 대안 포트 찾기
        for service, port in port_mappings.items():
            while port in occupied_ports:
                port += 1
            port_mappings[service] = port
            if service == 'frontend':
                self.frontend_port = port
            elif service == 'backend':
                self.backend_port = port
        
        # 포트 정보 저장
        ports_data = {}
        for service, port in port_mappings.items():
            ports_data[service] = {'port': port, 'service': service}
        
        try:
            with open(self.project_root / 'ports.json', 'w') as f:
                json.dump(ports_data, f, indent=2)
        except Exception as e:
            self.print_error(f"Failed to save port info: {e}")
        
        self.print_success("Port allocation completed")
        self.print_info(f"Frontend: {self.frontend_port}, Backend: {self.backend_port}")
        return True
    
    def get_occupied_ports(self):
        """사용 중인 포트 목록 가져오기"""
        occupied = set()
        
        # netstat 사용
        result = self.run_command("netstat -an")
        if result['success']:
            for line in result['stdout'].split('\n'):
                if 'LISTENING' in line or 'LISTEN' in line:
                    try:
                        parts = line.split()
                        for part in parts:
                            if ':' in part:
                                port = int(part.split(':')[-1])
                                if 1024 <= port <= 65535:
                                    occupied.add(port)
                                    break
                    except (ValueError, IndexError):
                        continue
        
        return occupied
    
    def generate_docker_compose(self):
        """Docker Compose 파일 생성"""
        self.print_step(2, 5, "Generating Docker Compose configuration...")
        
        # 포트 정보 로드
        try:
            with open(self.project_root / 'ports.json', 'r') as f:
                ports_data = json.load(f)
        except:
            # 기본값 사용
            ports_data = {
                'frontend': {'port': self.frontend_port},
                'backend': {'port': self.backend_port},
                'mongodb': {'port': 27018},
                'redis': {'port': 6381},
                'nginx': {'port': 8081}
            }
        
        # 간단한 docker-compose override 생성
        override_content = f"""version: '3.8'

services:
  frontend:
    ports:
      - "{ports_data['frontend']['port']}:3000"
    environment:
      - REACT_APP_BACKEND_URL=http://localhost:{ports_data['backend']['port']}

  backend:
    ports:
      - "{ports_data['backend']['port']}:8000"
    environment:
      - MONGO_URL=mongodb://admin:password123@mongodb:{ports_data['mongodb']['port']}/online_evaluation

  mongodb:
    ports:
      - "{ports_data['mongodb']['port']}:27017"

  redis:
    ports:
      - "{ports_data['redis']['port']}:6379"

  nginx:
    ports:
      - "{ports_data['nginx']['port']}:80"
"""
        
        try:
            with open(self.project_root / 'docker-compose.override.yml', 'w') as f:
                f.write(override_content)
            self.print_success("Docker Compose configuration generated")
            return True
        except Exception as e:
            self.print_error(f"Failed to generate Docker Compose: {e}")
            return False
    
    def start_containers(self):
        """Docker 컨테이너 시작"""
        self.print_step(3, 5, "Starting Docker containers...")
        
        # 기존 컨테이너 정리
        self.print_info("Cleaning up existing containers...")
        cleanup_result = self.run_command(f"docker-compose -p {self.project_name} down --remove-orphans")
        
        # 컨테이너 시작
        self.print_info("Starting services...")
        result = self.run_command(f"docker-compose -p {self.project_name} up --build -d")
        
        if result['success']:
            self.print_success("Docker containers started")
            return True
        else:
            self.print_error("Failed to start containers")
            self.print_error(f"Error: {result.get('stderr', 'Unknown error')}")
            return False
    
    def wait_for_services(self):
        """서비스 준비 대기"""
        self.print_step(4, 5, "Waiting for services to be ready...")
        
        max_wait = 60  # 60초 대기
        wait_time = 0
        check_interval = 5
        
        while wait_time < max_wait:
            self.print_info(f"Checking services... ({wait_time}/{max_wait}s)")
            
            # 간단한 포트 체크
            frontend_ready = self.check_port(self.frontend_port)
            backend_ready = self.check_port(self.backend_port)
            
            if frontend_ready and backend_ready:
                self.print_success("All services ready!")
                return True
            
            time.sleep(check_interval)
            wait_time += check_interval
        
        self.print_info("Service check timeout, but will continue...")
        return True
    
    def check_port(self, port):
        """포트가 열려있는지 확인"""
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            return result == 0
        except:
            return False
    
    def open_web_pages(self):
        """웹페이지 열기"""
        self.print_step(5, 5, "Opening web pages...")
        
        frontend_url = f"http://localhost:{self.frontend_port}"
        backend_docs_url = f"http://localhost:{self.backend_port}/docs"
        
        try:
            self.print_info(f"Opening frontend: {frontend_url}")
            webbrowser.open(frontend_url)
            
            time.sleep(2)
            
            self.print_info(f"Opening API docs: {backend_docs_url}")
            webbrowser.open(backend_docs_url)
            
            return True
        except Exception as e:
            self.print_error(f"Failed to open browser: {e}")
            self.print_info("Manual URLs:")
            self.print_info(f"  Frontend: {frontend_url}")
            self.print_info(f"  API docs: {backend_docs_url}")
            return True
    
    def show_final_info(self):
        """최종 정보 표시"""
        print()
        print("=" * 60)
        print("    Deployment Completed Successfully!")
        print("=" * 60)
        print()
        print("[SERVICE ACCESS INFO]")
        print(f"  Frontend: http://localhost:{self.frontend_port}")
        print(f"  Backend API: http://localhost:{self.backend_port}")
        print(f"  API Docs: http://localhost:{self.backend_port}/docs")
        print()
        print("[MANAGEMENT COMMANDS]")
        print(f"  Service status: docker-compose -p {self.project_name} ps")
        print(f"  View logs: docker-compose -p {self.project_name} logs -f")
        print(f"  Stop services: docker-compose -p {self.project_name} down")
        print()
    
    def deploy(self):
        """전체 배포 프로세스"""
        try:
            # 사전 요구사항 확인
            if not self.check_prerequisites():
                return False
            
            print()
            
            # 배포 단계 실행
            steps = [
                self.simple_port_allocation,
                self.generate_docker_compose,
                self.start_containers,
                self.wait_for_services,
                self.open_web_pages
            ]
            
            for step in steps:
                if not step():
                    print()
                    print("[ERROR] Deployment failed at step:", step.__name__)
                    return False
                print()
            
            self.show_final_info()
            return True
            
        except KeyboardInterrupt:
            print()
            print("[INFO] Deployment cancelled by user")
            return False
        except Exception as e:
            print()
            print(f"[ERROR] Unexpected error: {e}")
            return False

def main():
    """메인 함수"""
    deployer = WindowsDeployer()
    
    try:
        success = deployer.deploy()
        
        input("\nPress any key to exit...")
        return 0 if success else 1
        
    except Exception as e:
        print(f"Fatal error: {e}")
        input("\nPress any key to exit...")
        return 1

if __name__ == "__main__":
    sys.exit(main())