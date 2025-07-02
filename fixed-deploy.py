#!/usr/bin/env python3
"""
수정된 배포 스크립트
==================

Dockerfile 경로 문제를 해결한 배포 스크립트
"""

import os
import sys
import json
import time
import subprocess
import webbrowser
import socket
from pathlib import Path

# Windows 인코딩 문제 해결
if os.name == 'nt':
    try:
        os.system('chcp 65001 >nul')
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

class FixedDeployer:
    """수정된 배포 관리자"""
    
    def __init__(self):
        self.project_name = "online-evaluation"
        self.project_root = Path.cwd()
        
        print("=" * 60)
        print("    Fixed Deploy - Dockerfile Issues Resolved")
        print("=" * 60)
        print()
        
    def check_port_available(self, port):
        """포트가 사용 가능한지 확인"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            return result != 0  # 연결 실패 = 사용 가능
        except:
            return True
    
    def find_available_port(self, start_port, max_attempts=100):
        """사용 가능한 포트 찾기"""
        for i in range(max_attempts):
            port = start_port + i
            if self.check_port_available(port):
                return port
        return start_port  # 찾지 못하면 기본값 반환
    
    def allocate_ports(self):
        """포트 할당"""
        print("[Step 1/4] Port allocation...")
        
        # 기본 포트에서 사용 가능한 포트 찾기
        ports = {
            'frontend': self.find_available_port(3001),
            'backend': self.find_available_port(8001),
            'mongodb': self.find_available_port(27018),
            'redis': self.find_available_port(6381)
        }
        
        print(f"[OK] Allocated ports:")
        for service, port in ports.items():
            print(f"  {service}: {port}")
        
        return ports
    
    def create_simple_override(self, ports):
        """간단한 override 파일 생성 (Dockerfile 문제 우회)"""
        print("[Step 2/4] Creating simplified Docker configuration...")
        
        # 간단한 설정으로 이미지 직접 사용
        override_content = f"""version: '3.8'

services:
  # MongoDB 데이터베이스
  mongodb:
    image: mongo:7
    container_name: online-evaluation-mongodb
    restart: unless-stopped
    ports:
      - "{ports['mongodb']}:27017"
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: password123
      MONGO_INITDB_DATABASE: online_evaluation
    volumes:
      - mongodb_data:/data/db
    networks:
      - app-network

  # Redis 캐시
  redis:
    image: redis:7-alpine
    container_name: online-evaluation-redis
    restart: unless-stopped
    ports:
      - "{ports['redis']}:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - app-network

  # 백엔드 (Python/FastAPI)
  backend:
    image: python:3.11-slim
    container_name: online-evaluation-backend
    restart: unless-stopped
    ports:
      - "{ports['backend']}:8000"
    environment:
      MONGO_URL: "mongodb://admin:password123@mongodb:27017/online_evaluation?authSource=admin"
      JWT_SECRET: "your-secret-key-here"
      CORS_ORIGINS: "http://localhost:{ports['frontend']}"
      REDIS_URL: "redis://redis:6379"
    volumes:
      - ./backend:/app
      - ./uploads:/app/uploads
    working_dir: /app
    command: >
      bash -c "
        pip install --no-cache-dir -r requirements.txt &&
        python3 -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload
      "
    depends_on:
      - mongodb
      - redis
    networks:
      - app-network

  # 프론트엔드 (Node.js/React)
  frontend:
    image: node:18-alpine
    container_name: online-evaluation-frontend
    restart: unless-stopped
    ports:
      - "{ports['frontend']}:3000"
    environment:
      REACT_APP_BACKEND_URL: "http://localhost:{ports['backend']}"
      NODE_ENV: development
    volumes:
      - ./frontend:/app
      - /app/node_modules
    working_dir: /app
    command: >
      sh -c "
        if [ ! -d node_modules ]; then npm install; fi &&
        npm start
      "
    depends_on:
      - backend
    networks:
      - app-network

networks:
  app-network:
    driver: bridge

volumes:
  mongodb_data:
    driver: local
  redis_data:
    driver: local
"""
        
        try:
            with open(self.project_root / 'docker-compose.override.yml', 'w') as f:
                f.write(override_content)
            print("[OK] Simplified Docker configuration created")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to create Docker override: {e}")
            return False
    
    def start_services(self, ports):
        """서비스 시작"""
        print("[Step 3/4] Starting services...")
        
        # 기존 컨테이너 정리
        print("  Cleaning up existing containers...")
        cleanup_cmd = f"docker-compose -p {self.project_name} down --remove-orphans --volumes"
        os.system(cleanup_cmd)
        
        # 새 컨테이너 시작 (빌드 없이)
        print("  Starting new containers...")
        start_cmd = f"docker-compose -p {self.project_name} up -d"
        result = os.system(start_cmd)
        
        if result == 0:
            print("[OK] Services started successfully")
            return True
        else:
            print("[ERROR] Failed to start services")
            return False
    
    def wait_and_open(self, ports):
        """서비스 대기 및 브라우저 열기"""
        print("[Step 4/4] Waiting for services and opening browser...")
        
        frontend_port = ports['frontend']
        backend_port = ports['backend']
        
        # 서비스 대기 (더 긴 시간)
        print("  Waiting for services to be ready...")
        print("  Note: First startup may take 2-3 minutes for npm install...")
        
        max_wait = 180  # 3분
        wait_time = 0
        
        while wait_time < max_wait:
            if not self.check_port_available(frontend_port):
                print(f"  Frontend ready on port {frontend_port}")
                break
            time.sleep(5)
            wait_time += 5
            if wait_time % 30 == 0:
                print(f"  Still waiting... ({wait_time}/{max_wait}s)")
        
        # 브라우저 열기
        frontend_url = f"http://localhost:{frontend_port}"
        backend_url = f"http://localhost:{backend_port}/docs"
        
        try:
            print(f"  Opening frontend: {frontend_url}")
            webbrowser.open(frontend_url)
            
            time.sleep(3)
            
            print(f"  Opening API docs: {backend_url}")
            webbrowser.open(backend_url)
            
        except Exception as e:
            print(f"[WARNING] Could not open browser: {e}")
            print("  Please manually open:")
            print(f"    Frontend: {frontend_url}")
            print(f"    API Docs: {backend_url}")
        
        return True
    
    def show_results(self, ports):
        """결과 표시"""
        print()
        print("=" * 60)
        print("    Deployment Completed!")
        print("=" * 60)
        print()
        print("Service URLs:")
        print(f"  Frontend:    http://localhost:{ports['frontend']}")
        print(f"  Backend API: http://localhost:{ports['backend']}")
        print(f"  API Docs:    http://localhost:{ports['backend']}/docs")
        print()
        print("Notes:")
        print("  - First startup may take 2-3 minutes")
        print("  - Frontend will auto-reload after npm install")
        print("  - If pages don't load immediately, wait a bit longer")
        print()
        print("Management Commands:")
        print(f"  Status: docker-compose -p {self.project_name} ps")
        print(f"  Logs:   docker-compose -p {self.project_name} logs -f")
        print(f"  Stop:   docker-compose -p {self.project_name} down")
        print()
    
    def deploy(self):
        """전체 배포 실행"""
        try:
            # 1. 포트 할당
            ports = self.allocate_ports()
            print()
            
            # 2. Docker 설정 생성
            if not self.create_simple_override(ports):
                return False
            print()
            
            # 3. 서비스 시작
            if not self.start_services(ports):
                return False
            print()
            
            # 4. 대기 및 브라우저 열기
            self.wait_and_open(ports)
            print()
            
            # 5. 결과 표시
            self.show_results(ports)
            
            return True
            
        except KeyboardInterrupt:
            print("\n[INFO] Deployment cancelled by user")
            return False
        except Exception as e:
            print(f"\n[ERROR] Deployment failed: {e}")
            return False

def main():
    """메인 함수"""
    print("Fixed Deployer - Dockerfile issues resolved")
    print("This script uses simplified Docker configuration")
    print()
    
    # Docker 확인
    try:
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            print("[ERROR] Docker not found or not working")
            input("Press Enter to exit...")
            return 1
        print(f"[OK] Docker found: {result.stdout.strip()}")
    except:
        print("[ERROR] Docker not available")
        input("Press Enter to exit...")
        return 1
    
    # 배포 실행
    deployer = FixedDeployer()
    success = deployer.deploy()
    
    input("\nPress Enter to exit...")
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())