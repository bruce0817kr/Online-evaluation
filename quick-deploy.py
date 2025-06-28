#!/usr/bin/env python3
"""
온라인 평가 시스템 - 원클릭 배포 (Python 크로스 플랫폼)
=======================================================

포트 스캔 → 할당 → 도커 실행 → 웹페이지 오픈까지 자동화
"""

import os
import sys
import json
import time
import subprocess
import webbrowser
import platform
from pathlib import Path
from datetime import datetime
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class Colors:
    """ANSI 색상 코드"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

class OneClickDeployer:
    """원클릭 배포 관리자"""
    
    def __init__(self):
        self.project_name = "online-evaluation"
        self.services = ["frontend", "backend", "mongodb", "redis", "nginx"]
        self.max_wait_time = 120
        self.check_interval = 5
        self.project_root = Path.cwd()
        
        # 할당된 포트 정보
        self.frontend_port = 3001
        self.backend_port = 8001
        
    def print_colored(self, message, color=Colors.WHITE):
        """색상이 포함된 메시지 출력"""
        print(f"{color}{message}{Colors.END}")
    
    def print_step(self, step, total, message):
        """단계별 메시지 출력"""
        self.print_colored(f"📋 단계 {step}/{total}: {message}", Colors.PURPLE)
    
    def print_success(self, message):
        """성공 메시지 출력"""
        self.print_colored(f"✅ {message}", Colors.GREEN)
    
    def print_error(self, message):
        """오류 메시지 출력"""
        self.print_colored(f"❌ {message}", Colors.RED)
    
    def print_warning(self, message):
        """경고 메시지 출력"""
        self.print_colored(f"⚠️ {message}", Colors.YELLOW)
    
    def print_info(self, message):
        """정보 메시지 출력"""
        self.print_colored(f"ℹ️ {message}", Colors.CYAN)
    
    def run_command(self, command, shell=True, capture_output=True, timeout=60):
        """명령어 실행"""
        try:
            if isinstance(command, str):
                cmd = command
            else:
                cmd = ' '.join(command) if shell else command
                
            result = subprocess.run(
                cmd if shell else command,
                shell=shell,
                capture_output=capture_output,
                text=True,
                timeout=timeout,
                cwd=self.project_root
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
        self.print_info("🔍 사전 요구사항 확인 중...")
        
        # Python 확인
        if sys.version_info < (3, 7):
            self.print_error("Python 3.7 이상이 필요합니다.")
            return False
        
        # Docker 확인
        docker_result = self.run_command("docker --version")
        if not docker_result['success']:
            self.print_error("Docker가 설치되지 않았습니다.")
            return False
        
        # Docker Compose 확인
        compose_result = self.run_command("docker-compose --version")
        if not compose_result['success']:
            self.print_error("Docker Compose가 설치되지 않았습니다.")
            return False
        
        # Docker 데몬 확인
        daemon_result = self.run_command("docker info")
        if not daemon_result['success']:
            self.print_error("Docker 데몬이 실행되지 않았습니다.")
            return False
        
        self.print_success("모든 사전 요구사항 확인 완료")
        return True
    
    def system_diagnosis(self):
        """시스템 진단"""
        self.print_step(1, 7, "시스템 진단 중...")
        
        result = self.run_command([
            sys.executable, "-m", "universal_port_manager.cli", 
            "doctor", "--quiet"
        ], shell=False)
        
        if not result['success']:
            self.print_error("시스템 진단 실패")
            return False
            
        self.print_success("시스템 진단 완료")
        return True
    
    def port_scan(self):
        """포트 사용 현황 스캔"""
        self.print_step(2, 7, "포트 사용 현황 스캔 중...")
        
        result = self.run_command([
            sys.executable, "-m", "universal_port_manager.cli",
            "scan", "--range", "3000-9000", "--format", "json"
        ], shell=False)
        
        if not result['success']:
            self.print_error("포트 스캔 실패")
            return False
        
        # 스캔 결과 저장
        try:
            with open(self.project_root / "port_scan_result.json", "w") as f:
                f.write(result['stdout'])
        except Exception as e:
            self.print_warning(f"포트 스캔 결과 저장 실패: {e}")
        
        self.print_success("포트 스캔 완료")
        return True
    
    def allocate_ports(self):
        """포트 할당"""
        self.print_step(3, 7, "서비스 포트 할당 중...")
        
        result = self.run_command([
            sys.executable, "-m", "universal_port_manager.cli",
            "--project", self.project_name,
            "allocate"
        ] + self.services, shell=False)
        
        if not result['success']:
            self.print_error("포트 할당 실패")
            return False
        
        self.print_success("포트 할당 완료")
        return True
    
    def generate_configs(self):
        """설정 파일 생성"""
        self.print_step(4, 7, "설정 파일 생성 중...")
        
        result = self.run_command([
            sys.executable, "-m", "universal_port_manager.cli",
            "--project", self.project_name,
            "generate"
        ], shell=False)
        
        if not result['success']:
            self.print_error("설정 파일 생성 실패")
            return False
        
        # 포트 정보 읽기
        self.load_port_info()
        
        self.print_success("설정 파일 생성 완료")
        return True
    
    def load_port_info(self):
        """할당된 포트 정보 로드"""
        try:
            ports_file = self.project_root / "ports.json"
            if ports_file.exists():
                with open(ports_file, 'r') as f:
                    ports_data = json.load(f)
                
                # 포트 정보 추출
                if 'frontend' in ports_data and 'port' in ports_data['frontend']:
                    self.frontend_port = ports_data['frontend']['port']
                
                if 'backend' in ports_data and 'port' in ports_data['backend']:
                    self.backend_port = ports_data['backend']['port']
                
                self.print_info(f"📊 할당된 포트 정보:")
                self.print_info(f"  프론트엔드: {self.frontend_port}")
                self.print_info(f"  백엔드: {self.backend_port}")
                
        except Exception as e:
            self.print_warning(f"포트 정보 로드 실패: {e}")
    
    def start_containers(self):
        """Docker 컨테이너 실행"""
        self.print_step(5, 7, "Docker 컨테이너 실행 중...")
        
        # 기존 컨테이너 정리
        self.print_info("🧹 기존 컨테이너 정리 중...")
        cleanup_result = self.run_command([
            "docker-compose", "-p", self.project_name, 
            "down", "--remove-orphans"
        ], shell=False)
        
        # Docker Compose 파일 확인
        compose_file = self.project_root / "docker-compose.yml"
        if not compose_file.exists():
            self.print_error("docker-compose.yml 파일을 찾을 수 없습니다.")
            return False
        
        # 서비스 시작
        self.print_info("🐳 Docker Compose로 서비스 시작 중...")
        result = self.run_command([
            "docker-compose", "-p", self.project_name,
            "up", "--build", "-d"
        ], shell=False)
        
        if not result['success']:
            self.print_error("Docker Compose 실행 실패")
            self.print_error(f"에러: {result.get('stderr', 'Unknown error')}")
            return False
        
        self.print_success("Docker 컨테이너 실행 완료")
        return True
    
    def wait_for_services(self):
        """서비스 준비 상태 확인"""
        self.print_step(6, 7, "서비스 준비 상태 확인 중...")
        
        wait_time = 0
        while wait_time < self.max_wait_time:
            self.print_info(f"⏳ 서비스 준비 확인 중... ({wait_time}/{self.max_wait_time}초)")
            
            # 백엔드 헬스체크
            backend_ready = self.check_service_health(self.backend_port, "/health")
            
            # 프론트엔드 확인
            frontend_ready = self.check_service_health(self.frontend_port)
            
            if backend_ready and frontend_ready:
                self.print_success("모든 서비스 준비 완료!")
                return True
            
            time.sleep(self.check_interval)
            wait_time += self.check_interval
        
        self.print_warning(f"서비스 준비 시간 초과 ({self.max_wait_time}초)")
        self.print_warning("그래도 웹페이지를 열어보겠습니다...")
        return True
    
    def check_service_health(self, port, endpoint=""):
        """서비스 헬스체크"""
        try:
            import urllib.request
            
            url = f"http://localhost:{port}{endpoint}"
            req = urllib.request.Request(url)
            
            with urllib.request.urlopen(req, timeout=3) as response:
                return response.getcode() == 200
                
        except Exception:
            return False
    
    def open_web_pages(self):
        """웹페이지 오픈"""
        self.print_step(7, 7, "웹페이지 오픈 중...")
        
        frontend_url = f"http://localhost:{self.frontend_port}"
        backend_docs_url = f"http://localhost:{self.backend_port}/docs"
        
        try:
            self.print_info(f"🌐 웹페이지 열기: {frontend_url}")
            webbrowser.open(frontend_url)
            
            time.sleep(2)
            
            self.print_info(f"📚 API 문서 열기: {backend_docs_url}")
            webbrowser.open(backend_docs_url)
            
        except Exception as e:
            self.print_warning(f"브라우저 자동 열기 실패: {e}")
            self.print_info("수동으로 브라우저에서 다음 주소를 열어주세요:")
            self.print_info(f"  프론트엔드: {frontend_url}")
            self.print_info(f"  API 문서: {backend_docs_url}")
        
        return True
    
    def show_final_info(self):
        """최종 정보 표시"""
        print()
        self.print_colored("=" * 60, Colors.GREEN)
        self.print_colored("🎉 원클릭 배포 완료!", Colors.GREEN + Colors.BOLD)
        self.print_colored("=" * 60, Colors.GREEN)
        print()
        
        self.print_info("📱 서비스 접속 정보:")
        print(f"    프론트엔드: http://localhost:{self.frontend_port}")
        print(f"    백엔드 API: http://localhost:{self.backend_port}")
        print(f"    API 문서:   http://localhost:{self.backend_port}/docs")
        print()
        
        self.print_info("🛠️ 관리 명령어:")
        print(f"    서비스 상태: docker-compose -p {self.project_name} ps")
        print(f"    로그 확인:   docker-compose -p {self.project_name} logs -f")
        print(f"    서비스 중지: docker-compose -p {self.project_name} down")
        print()
        
        self.print_info("💡 문제가 있다면 로그를 확인하세요:")
        print(f"    docker-compose -p {self.project_name} logs --tail=50")
        print()
    
    def show_debug_info(self):
        """디버깅 정보 표시"""
        print()
        self.print_colored("=" * 60, Colors.RED)
        self.print_colored("❌ 배포 중 오류가 발생했습니다!", Colors.RED + Colors.BOLD)
        self.print_colored("=" * 60, Colors.RED)
        print()
        
        self.print_info("🔧 문제 해결을 위한 디버깅 정보:")
        print()
        
        # 포트 상태 확인
        self.print_info("📊 현재 포트 상태:")
        port_status = self.run_command([
            sys.executable, "-m", "universal_port_manager.cli",
            "--project", self.project_name, "status"
        ], shell=False)
        if port_status['success']:
            print(port_status['stdout'])
        
        # Docker 상태 확인
        self.print_info("🐳 Docker 상태:")
        docker_status = self.run_command([
            "docker-compose", "-p", self.project_name, "ps"
        ], shell=False)
        if docker_status['success']:
            print(docker_status['stdout'])
        
        # 로그 확인
        self.print_info("📝 최근 로그 (마지막 10줄):")
        logs = self.run_command([
            "docker-compose", "-p", self.project_name, "logs", "--tail=10"
        ], shell=False)
        if logs['success']:
            print(logs['stdout'])
        
        print()
        self.print_info("💡 수동 복구 명령어:")
        print(f"  1. 포트 재할당: python3 -m universal_port_manager.cli --project {self.project_name} allocate {' '.join(self.services)}")
        print(f"  2. 서비스 재시작: docker-compose -p {self.project_name} up --build -d")
        print(f"  3. 로그 확인: docker-compose -p {self.project_name} logs -f")
        print()
    
    def deploy(self):
        """전체 배포 프로세스 실행"""
        try:
            print()
            self.print_colored("=" * 60, Colors.BLUE)
            self.print_colored("🚀 온라인 평가 시스템 원클릭 배포 시작", Colors.BLUE + Colors.BOLD)
            self.print_colored("=" * 60, Colors.BLUE)
            print()
            
            # 사전 요구사항 확인
            if not self.check_prerequisites():
                return False
            print()
            
            # 배포 단계 실행
            steps = [
                self.system_diagnosis,
                self.port_scan,
                self.allocate_ports,
                self.generate_configs,
                self.start_containers,
                self.wait_for_services,
                self.open_web_pages
            ]
            
            for step in steps:
                if not step():
                    self.show_debug_info()
                    return False
                print()
            
            self.show_final_info()
            return True
            
        except KeyboardInterrupt:
            print()
            self.print_warning("사용자에 의해 배포가 중단되었습니다.")
            return False
        except Exception as e:
            print()
            self.print_error(f"예상치 못한 오류: {e}")
            self.show_debug_info()
            return False

def main():
    """메인 함수"""
    deployer = OneClickDeployer()
    
    try:
        success = deployer.deploy()
        
        if platform.system() != "Windows":
            input("\n아무 키나 누르세요...")
        else:
            os.system("pause")
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"Fatal error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())