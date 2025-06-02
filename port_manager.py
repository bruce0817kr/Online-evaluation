#!/usr/bin/env python3
"""
포트 충돌 해결 및 자동 포트 할당 스크립트
"""

import socket
import subprocess
import json
import yaml
import os
import sys
from typing import Dict, List, Tuple

class PortManager:
    def __init__(self):
        self.default_ports = {
            'frontend': 3000,
            'backend': 8080,
            'mongodb': 27017,
            'redis': 6379,
            'nginx': 80
        }
        self.allocated_ports = {}
        
    def is_port_available(self, port: int) -> bool:
        """포트가 사용 가능한지 확인"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', port))
                return result != 0
        except Exception:
            return False
            
    def find_available_port(self, start_port: int, max_attempts: int = 100) -> int:
        """사용 가능한 포트 찾기"""
        for i in range(max_attempts):
            port = start_port + i
            if self.is_port_available(port):
                return port
        raise Exception(f"포트 {start_port}부터 {max_attempts}개 범위에서 사용 가능한 포트를 찾을 수 없습니다.")
        
    def get_used_ports(self) -> List[int]:
        """현재 사용 중인 포트 목록 가져오기"""
        used_ports = []
        try:
            # netstat 명령으로 사용 중인 포트 확인
            if os.name == 'nt':  # Windows
                result = subprocess.run(['netstat', '-an'], 
                                      capture_output=True, text=True)
            else:  # Linux/Mac
                result = subprocess.run(['netstat', '-tuln'], 
                                      capture_output=True, text=True)
            
            for line in result.stdout.split('\n'):
                if ':' in line and 'LISTENING' in line or 'LISTEN' in line:
                    try:
                        parts = line.split()
                        addr_port = parts[1] if len(parts) > 1 else parts[0]
                        port = int(addr_port.split(':')[-1])
                        used_ports.append(port)
                    except (ValueError, IndexError):
                        continue
                        
        except Exception as e:
            print(f"포트 확인 중 오류: {e}")
            
        return list(set(used_ports))
        
    def allocate_ports(self) -> Dict[str, int]:
        """모든 서비스에 대해 사용 가능한 포트 할당"""
        used_ports = self.get_used_ports()
        print(f"현재 사용 중인 포트: {sorted(used_ports)}")
        
        for service, default_port in self.default_ports.items():
            if self.is_port_available(default_port):
                self.allocated_ports[service] = default_port
                print(f"✅ {service}: 기본 포트 {default_port} 사용")
            else:
                try:
                    new_port = self.find_available_port(default_port + 1000)
                    self.allocated_ports[service] = new_port
                    print(f"⚠️ {service}: 포트 충돌로 {new_port}로 변경")
                except Exception as e:
                    print(f"❌ {service}: 포트 할당 실패 - {e}")
                    sys.exit(1)
                    
        return self.allocated_ports
        
    def update_docker_compose(self, ports: Dict[str, int]):
        """Docker Compose 파일의 포트 설정 업데이트"""
        try:
            with open('docker-compose.yml', 'r', encoding='utf-8') as f:
                compose_content = f.read()
                
            # 포트 매핑 업데이트
            updates = {
                f'"3000:80"': f'"{ports["frontend"]}:80"',
                f'"8080:8080"': f'"{ports["backend"]}:8080"',
                f'"27017:27017"': f'"{ports["mongodb"]}:27017"',
                f'"6379:6379"': f'"{ports["redis"]}:6379"',
                f'"80:80"': f'"{ports["nginx"]}:80"'
            }
            
            for old, new in updates.items():
                compose_content = compose_content.replace(old, new)
                
            # 백업 생성
            with open('docker-compose.yml.backup', 'w', encoding='utf-8') as f:
                f.write(open('docker-compose.yml', 'r', encoding='utf-8').read())
                
            # 새 설정 저장
            with open('docker-compose.yml', 'w', encoding='utf-8') as f:
                f.write(compose_content)
                
            print("✅ docker-compose.yml 포트 설정 업데이트 완료")
            
        except Exception as e:
            print(f"❌ Docker Compose 파일 업데이트 실패: {e}")
            sys.exit(1)
            
    def update_env_file(self, ports: Dict[str, int]):
        """환경변수 파일의 URL 업데이트"""
        try:
            env_files = ['.env', '.env.production', '.env.development']
            
            for env_file in env_files:
                if os.path.exists(env_file):
                    with open(env_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # URL 업데이트
                    content = content.replace(
                        'REACT_APP_API_URL=http://localhost:8080',
                        f'REACT_APP_API_URL=http://localhost:{ports["backend"]}'
                    )
                    content = content.replace(
                        'REACT_APP_WS_URL=ws://localhost:8080',
                        f'REACT_APP_WS_URL=ws://localhost:{ports["backend"]}'
                    )
                    
                    with open(env_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                        
                    print(f"✅ {env_file} URL 설정 업데이트 완료")
                    
        except Exception as e:
            print(f"❌ 환경변수 파일 업데이트 실패: {e}")
            
    def stop_conflicting_containers(self):
        """충돌하는 컨테이너 정리"""
        try:
            print("🧹 기존 컨테이너 정리 중...")
            subprocess.run(['docker-compose', 'down'], check=True)
            
            # 개별 컨테이너도 확인하여 정리
            result = subprocess.run(['docker', 'ps', '-q', '--filter', 'name=online-evaluation'], 
                                  capture_output=True, text=True)
            
            container_ids = result.stdout.strip().split('\n')
            for container_id in container_ids:
                if container_id.strip():
                    subprocess.run(['docker', 'stop', container_id.strip()], 
                                 capture_output=True)
                    subprocess.run(['docker', 'rm', container_id.strip()], 
                                 capture_output=True)
                                 
            print("✅ 기존 컨테이너 정리 완료")
            
        except Exception as e:
            print(f"⚠️ 컨테이너 정리 중 오류 (무시 가능): {e}")

def main():
    """메인 함수"""
    print("🔧 포트 충돌 해결 및 자동 할당 시작")
    print("=" * 50)
    
    manager = PortManager()
    
    # 1. 기존 컨테이너 정리
    manager.stop_conflicting_containers()
    
    # 2. 포트 할당
    ports = manager.allocate_ports()
    
    # 3. 설정 파일 업데이트
    manager.update_docker_compose(ports)
    manager.update_env_file(ports)
    
    # 4. 결과 출력
    print("\n📊 할당된 포트 정보")
    print("=" * 30)
    for service, port in ports.items():
        print(f"{service:12}: {port}")
        
    print(f"\n🌐 서비스 접속 URL")
    print("=" * 30)
    print(f"웹 애플리케이션: http://localhost:{ports['frontend']}")
    print(f"API 서버:     http://localhost:{ports['backend']}")
    print(f"MongoDB:      mongodb://localhost:{ports['mongodb']}")
    print(f"Redis:        redis://localhost:{ports['redis']}")
    
    # 5. 포트 정보를 파일로 저장
    with open('allocated_ports.json', 'w') as f:
        json.dump(ports, f, indent=2)
        
    print(f"\n💾 포트 정보가 allocated_ports.json에 저장되었습니다.")
    print("🚀 이제 docker-compose up -d 명령으로 서비스를 시작할 수 있습니다.")

if __name__ == "__main__":
    main()
