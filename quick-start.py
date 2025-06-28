#!/usr/bin/env python3
"""
Quick Start - 빠른 배포 + 포트 매니저
==================================

빌드 시간 최소화 + Universal Port Manager 통합
"""

import os
import sys
import time
import subprocess
import webbrowser
import socket
import json
from pathlib import Path

# Windows 인코딩 수정
if os.name == 'nt':
    try:
        os.system('chcp 65001 >nul 2>&1')
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

class QuickStarter:
    """빠른 시작 배포 시스템"""
    
    def __init__(self):
        self.project_name = "online-evaluation"
        self.project_root = Path.cwd()
        
        print("=" * 60)
        print("    Quick Start - 빠른 배포 + 포트 매니저")
        print("=" * 60)
        print()
        
    def check_port_available(self, port):
        """포트 사용 가능 확인"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            return result != 0
        except:
            return True
    
    def find_available_port(self, start_port, max_attempts=50):
        """사용 가능한 포트 찾기"""
        for i in range(max_attempts):
            port = start_port + i
            if self.check_port_available(port):
                return port
        return start_port
    
    def smart_port_allocation(self):
        """스마트 포트 할당 (UPM 통합)"""
        print("[Step 1/4] 스마트 포트 할당...")
        
        # UPM 시도
        try:
            # UPM 시도 1: 파일에서 기존 포트 읽기
            ports_file = self.project_root / 'ports.json'
            if ports_file.exists():
                print("  기존 ports.json 발견, 재사용 중...")
                with open(ports_file, 'r') as f:
                    existing_ports = json.load(f)
                
                # 기존 포트가 여전히 사용 가능한지 확인
                all_available = True
                for service, port in existing_ports.items():
                    if not self.check_port_available(port):
                        all_available = False
                        break
                
                if all_available:
                    print("  [OK] 기존 포트 재사용 가능")
                    return existing_ports
                else:
                    print("  [INFO] 기존 포트 중 일부 사용중, 새로 할당")
            
            # UPM 시도 2: 포트 매니저 CLI 사용
            print("  Universal Port Manager 시도...")
            upm_cmd = f"python -m universal_port_manager --project {self.project_name} allocate frontend backend mongodb redis"
            
            try:
                result = subprocess.run(ump_cmd.split(), 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    print("  [OK] UPM 포트 할당 성공")
                    
                    # 생성된 포트 파일 읽기
                    if ports_file.exists():
                        with open(ports_file, 'r') as f:
                            ports = json.load(f)
                        return ports
                else:
                    print(f"  [INFO] UPM CLI 실패: {result.stderr}")
            except:
                print("  [INFO] UMP CLI 시간초과 또는 오류")
                
        except Exception as e:
            print(f"  [INFO] UPM 사용 불가: {e}")
        
        # 폴백: 빠른 포트 할당
        print("  [Fallback] 빠른 포트 할당 사용...")
        ports = {
            'frontend': self.find_available_port(3001),
            'backend': self.find_available_port(8001),
            'mongodb': self.find_available_port(27018),
            'redis': self.find_available_port(6381)
        }
        
        # 포트 정보 저장
        try:
            with open(self.project_root / 'ports.json', 'w') as f:
                json.dump(ports, f, indent=2)
        except:
            pass
        
        print("  [OK] 할당된 포트:")
        for service, port in ports.items():
            print(f"    {service}: {port}")
        
        return ports
    
    def create_instant_config(self, ports):
        """즉시 실행 가능한 설정 생성 (빌드 없음)"""
        print("[Step 2/4] 빠른 실행 설정 생성...")
        
        # 빌드 없는 즉시 실행 설정
        quick_config = f"""services:
  mongodb:
    image: mongo:7
    container_name: quick-mongodb
    restart: unless-stopped
    ports:
      - "{ports['mongodb']}:27017"
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: password123
      MONGO_INITDB_DATABASE: online_evaluation
    volumes:
      - quick_mongodb:/data/db
    networks:
      - quick-net

  redis:
    image: redis:7-alpine
    container_name: quick-redis
    restart: unless-stopped
    ports:
      - "{ports['redis']}:6379"
    command: redis-server --appendonly yes
    volumes:
      - quick_redis:/data
    networks:
      - quick-net

  backend:
    image: python:3.11-slim
    container_name: quick-backend
    restart: unless-stopped
    ports:
      - "{ports['backend']}:8000"
    environment:
      MONGO_URL: "mongodb://admin:password123@mongodb:27017/online_evaluation?authSource=admin"
      JWT_SECRET: "quick-secret-{int(time.time())}"
      CORS_ORIGINS: "http://localhost:{ports['frontend']}"
      REDIS_URL: "redis://redis:6379"
    volumes:
      - ./backend:/app
      - ./uploads:/app/uploads
    working_dir: /app
    command: >
      bash -c "
        echo 'Backend 시작 중...' &&
        pip install --no-cache-dir --quiet fastapi uvicorn motor pymongo pydantic python-jose[cryptography] passlib[bcrypt] python-multipart &&
        echo 'Backend 의존성 설치 완료' &&
        python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload
      "
    depends_on:
      - mongodb
      - redis
    networks:
      - quick-net

  frontend:
    image: node:18-alpine
    container_name: quick-frontend
    restart: unless-stopped
    ports:
      - "{ports['frontend']}:3000"
    environment:
      REACT_APP_BACKEND_URL: "http://localhost:{ports['backend']}"
      NODE_ENV: development
    volumes:
      - ./frontend:/app
      - quick_nodemodules:/app/node_modules
    working_dir: /app
    command: >
      sh -c "
        echo 'Frontend 시작 중...' &&
        if [ ! -d node_modules ] || [ ! -f node_modules/.install-complete ]; then
          echo 'npm 의존성 설치 중...'
          npm install --silent --no-progress &&
          touch node_modules/.install-complete
        fi &&
        echo 'Frontend 의존성 준비 완료' &&
        npm start
      "
    depends_on:
      - backend
    networks:
      - quick-net

networks:
  quick-net:
    driver: bridge

volumes:
  quick_mongodb:
    driver: local
  quick_redis:
    driver: local
  quick_nodemodules:
    driver: local
"""
        
        try:
            config_path = self.project_root / 'docker-compose.quick.yml'
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(quick_config)
            print("  [OK] 빠른 실행 설정 생성됨")
            return True
        except Exception as e:
            print(f"  [ERROR] 설정 생성 실패: {e}")
            return False
    
    def start_quick_services(self):
        """빠른 서비스 시작"""
        print("[Step 3/4] 빠른 서비스 시작...")
        
        # 기존 정리
        print("  기존 컨테이너 정리...")
        cleanup_cmd = "docker-compose -f docker-compose.quick.yml -p quick down --remove-orphans"
        subprocess.run(cleanup_cmd.split(), capture_output=True)
        
        # 빠른 시작
        print("  서비스 시작 중...")
        start_cmd = "docker-compose -f docker-compose.quick.yml -p quick up -d"
        
        try:
            result = subprocess.run(start_cmd.split(), 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print("  [OK] 모든 서비스 시작됨")
                return True
            else:
                print(f"  [ERROR] 서비스 시작 실패: {result.stderr}")
                return False
        except Exception as e:
            print(f"  [ERROR] 예외 발생: {e}")
            return False
    
    def quick_wait_and_open(self, ports):
        """빠른 대기 및 브라우저 열기"""
        print("[Step 4/4] 서비스 준비 대기...")
        
        max_wait = 90  # 1.5분 최대 대기
        wait_time = 0
        
        print("  서비스 상태 확인 중...")
        print("  참고: 첫 실행시 npm install로 1-2분 소요")
        
        while wait_time < max_wait:
            ready_services = 0
            total_services = 2
            
            # Backend 확인
            if not self.check_port_available(ports['backend']):
                ready_services += 1
            
            # Frontend 확인  
            if not self.check_port_available(ports['frontend']):
                ready_services += 1
                
            if ready_services == total_services:
                print(f"  [OK] 모든 서비스 준비됨 ({wait_time}초)")
                break
                
            time.sleep(5)
            wait_time += 5
            
            if wait_time % 20 == 0:
                print(f"  대기 중... ({ready_services}/{total_services} 준비됨, {wait_time}s)")
        
        # 브라우저 열기
        frontend_url = f"http://localhost:{ports['frontend']}"
        backend_url = f"http://localhost:{ports['backend']}/docs"
        
        try:
            print(f"  브라우저 열기: {frontend_url}")
            webbrowser.open(frontend_url)
            time.sleep(3)
            print(f"  API 문서 열기: {backend_url}")
            webbrowser.open(backend_url)
        except Exception:
            print(f"  수동으로 열어주세요:")
            print(f"    Frontend: {frontend_url}")
            print(f"    API Docs: {backend_url}")
    
    def show_quick_results(self, ports):
        """결과 표시"""
        print()
        print("=" * 60)
        print("    Quick Start 배포 완료!")
        print("=" * 60)
        print()
        print("🚀 서비스 URL:")
        print(f"   Frontend:  http://localhost:{ports['frontend']}")
        print(f"   Backend:   http://localhost:{ports['backend']}")
        print(f"   API Docs:  http://localhost:{ports['backend']}/docs")
        print()
        print("📊 포트 매니저 정보:")
        print(f"   MongoDB:   localhost:{ports['mongodb']}")
        print(f"   Redis:     localhost:{ports['redis']}")
        print()
        print("⚡ 빠른 배포 특징:")
        print("   ✓ 빌드 시간 없음 (pre-built 이미지)")
        print("   ✓ 포트 매니저 통합")
        print("   ✓ npm 캐시 최적화")
        print("   ✓ 즉시 실행 가능")
        print()
        print("🔧 관리 명령어:")
        print("   상태: docker-compose -f docker-compose.quick.yml -p quick ps")
        print("   로그: docker-compose -f docker-compose.quick.yml -p quick logs -f")
        print("   중지: docker-compose -f docker-compose.quick.yml -p quick down")
        print()
    
    def deploy(self):
        """빠른 배포 실행"""
        try:
            # 1. 스마트 포트 할당
            ports = self.smart_port_allocation()
            print()
            
            # 2. 빠른 설정 생성
            if not self.create_instant_config(ports):
                return False
            print()
            
            # 3. 빠른 서비스 시작
            if not self.start_quick_services():
                return False
            print()
            
            # 4. 빠른 대기 및 열기
            self.quick_wait_and_open(ports)
            print()
            
            # 5. 결과 표시
            self.show_quick_results(ports)
            
            return True
            
        except KeyboardInterrupt:
            print("\n[INFO] 빠른 배포 취소됨")
            return False
        except Exception as e:
            print(f"\n[ERROR] 빠른 배포 실패: {e}")
            return False

def main():
    """메인 함수"""
    print("Quick Start - 빠른 배포 + 포트 매니저")
    print("빌드 시간 최소화 + Universal Port Manager 통합")
    print()
    
    # Docker 확인
    try:
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            print("[ERROR] Docker를 찾을 수 없습니다")
            input("Enter를 눌러 종료...")
            return 1
        print(f"[OK] Docker: {result.stdout.strip()}")
    except:
        print("[ERROR] Docker 확인 실패")
        input("Enter를 눌러 종료...")
        return 1
    
    # 빠른 배포 실행
    deployer = QuickStarter()
    success = deployer.deploy()
    
    input("\nEnter를 눌러 종료...")
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())