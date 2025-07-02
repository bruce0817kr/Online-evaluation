#!/usr/bin/env python3
"""
Instant Fix - Frontend 문제 즉시 해결
===================================

Frontend 컨테이너 재시작 문제 해결
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

class InstantFixer:
    """즉시 수정 도구"""
    
    def __init__(self):
        self.project_name = "online-evaluation"
        self.project_root = Path.cwd()
        
        print("=" * 60)
        print("    Instant Fix - Frontend 문제 해결")
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
    
    def get_current_ports(self):
        """현재 포트 가져오기"""
        try:
            ports_file = self.project_root / 'ports.json'
            if ports_file.exists():
                with open(ports_file, 'r') as f:
                    return json.load(f)
        except:
            pass
        
        # 기본값
        return {
            'frontend': 3002,
            'backend': 8002,
            'mongodb': 27018,
            'redis': 6382
        }
    
    def create_fixed_config(self, ports):
        """수정된 설정 생성"""
        print("수정된 Frontend 설정 생성 중...")
        
        # Frontend 문제 해결된 설정
        fixed_config = f"""services:
  mongodb:
    image: mongo:7
    container_name: instant-mongodb
    restart: unless-stopped
    ports:
      - "{ports['mongodb']}:27017"
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: password123
      MONGO_INITDB_DATABASE: online_evaluation
    volumes:
      - instant_mongodb:/data/db
    networks:
      - instant-net

  redis:
    image: redis:7-alpine
    container_name: instant-redis
    restart: unless-stopped
    ports:
      - "{ports['redis']}:6379"
    command: redis-server --appendonly yes
    volumes:
      - instant_redis:/data
    networks:
      - instant-net

  backend:
    image: python:3.11-slim
    container_name: instant-backend
    restart: unless-stopped
    ports:
      - "{ports['backend']}:8000"
    environment:
      MONGO_URL: "mongodb://admin:password123@mongodb:27017/online_evaluation?authSource=admin"
      JWT_SECRET: "instant-secret-{int(time.time())}"
      CORS_ORIGINS: "http://localhost:{ports['frontend']}"
      REDIS_URL: "redis://redis:6379"
    volumes:
      - ./backend:/app
      - ./uploads:/app/uploads
    working_dir: /app
    command: >
      bash -c "
        pip install --no-cache-dir --quiet fastapi uvicorn motor pymongo pydantic 'python-jose[cryptography]' 'passlib[bcrypt]' python-multipart &&
        python3 -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload
      "
    depends_on:
      - mongodb
      - redis
    networks:
      - instant-net

  frontend:
    image: node:18-alpine
    container_name: instant-frontend
    restart: unless-stopped
    ports:
      - "{ports['frontend']}:3000"
    environment:
      REACT_APP_BACKEND_URL: "http://localhost:{ports['backend']}"
      NODE_ENV: development
      PORT: "3000"
      WATCHPACK_POLLING: "true"
    volumes:
      - ./frontend:/app
      - instant_nodemodules:/app/node_modules
    working_dir: /app
    command: >
      sh -c "
        echo 'Frontend 시작...' &&
        apk add --no-cache git &&
        if [ ! -f package.json ]; then
          echo 'package.json 없음 - 기본 React 앱 생성'
          npx create-react-app . --template typescript
        fi &&
        echo 'Dependencies 설치...' &&
        npm install --legacy-peer-deps --no-audit --no-fund &&
        echo 'React 앱 시작...' &&
        npm start
      "
    depends_on:
      - backend
    networks:
      - instant-net
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:3000"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 60s

networks:
  instant-net:
    driver: bridge

volumes:
  instant_mongodb:
    driver: local
  instant_redis:
    driver: local
  instant_nodemodules:
    driver: local
"""
        
        try:
            config_path = self.project_root / 'docker-compose.instant.yml'
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(fixed_config)
            print("[OK] 수정된 설정 생성완료")
            return True
        except Exception as e:
            print(f"[ERROR] 설정 생성 실패: {e}")
            return False
    
    def stop_existing_services(self):
        """기존 서비스 중지"""
        print("기존 서비스 중지 중...")
        
        commands = [
            "docker-compose -f docker-compose.quick.yml -p quick down",
            "docker-compose -f docker-compose.instant.yml -p instant down",
            "docker-compose down"
        ]
        
        for cmd in commands:
            try:
                subprocess.run(cmd.split(), capture_output=True, timeout=10)
            except:
                pass
        
        print("[OK] 기존 서비스 중지완료")
    
    def start_fixed_services(self):
        """수정된 서비스 시작"""
        print("수정된 서비스 시작 중...")
        
        start_cmd = "docker-compose -f docker-compose.instant.yml -p instant up -d"
        
        try:
            result = subprocess.run(start_cmd.split(), 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print("[OK] 수정된 서비스 시작완료")
                return True
            else:
                print(f"[ERROR] 서비스 시작 실패: {result.stderr}")
                return False
        except Exception as e:
            print(f"[ERROR] 예외 발생: {e}")
            return False
    
    def wait_for_services(self, ports):
        """서비스 대기"""
        print("서비스 준비 대기 중...")
        print("참고: Frontend는 처음 시작시 3-5분 소요될 수 있습니다")
        
        max_wait = 300  # 5분
        wait_time = 0
        
        while wait_time < max_wait:
            backend_ready = not self.check_port_available(ports['backend'])
            frontend_ready = not self.check_port_available(ports['frontend'])
            
            status = []
            if backend_ready:
                status.append("Backend ✓")
            if frontend_ready:
                status.append("Frontend ✓")
            
            if backend_ready and frontend_ready:
                print(f"[OK] 모든 서비스 준비완료 ({wait_time}초)")
                return True
            
            if wait_time % 30 == 0:
                print(f"  대기 중... {' '.join(status)} ({wait_time}s)")
            
            time.sleep(5)
            wait_time += 5
        
        print(f"[WARNING] 시간초과 - Backend만 사용 가능할 수 있습니다")
        return True
    
    def open_services(self, ports):
        """서비스 열기"""
        frontend_url = f"http://localhost:{ports['frontend']}"
        backend_url = f"http://localhost:{ports['backend']}/docs"
        
        print(f"브라우저 열기 시도...")
        
        try:
            # Backend는 즉시 열기
            print(f"API 문서: {backend_url}")
            webbrowser.open(backend_url)
            
            # Frontend 포트 확인 후 열기
            if not self.check_port_available(ports['frontend']):
                time.sleep(2)
                print(f"Frontend: {frontend_url}")
                webbrowser.open(frontend_url)
            else:
                print(f"Frontend 아직 준비 안됨: {frontend_url}")
                print("몇 분 후 수동으로 열어보세요")
                
        except Exception as e:
            print(f"수동으로 열어주세요:")
            print(f"  Frontend: {frontend_url}")
            print(f"  Backend:  {backend_url}")
    
    def show_status(self, ports):
        """상태 표시"""
        print()
        print("=" * 60)
        print("    Instant Fix 완료!")
        print("=" * 60)
        print()
        print("🌐 서비스 URL:")
        print(f"   Frontend:  http://localhost:{ports['frontend']}")
        print(f"   Backend:   http://localhost:{ports['backend']}")
        print(f"   API Docs:  http://localhost:{ports['backend']}/docs")
        print()
        print("ℹ️  참고사항:")
        print("   - Backend는 즉시 사용 가능")
        print("   - Frontend는 처음 시작시 3-5분 소요")
        print("   - npm install이 완료되면 자동으로 시작됩니다")
        print()
        print("🔧 상태 확인:")
        print("   docker-compose -f docker-compose.instant.yml -p instant ps")
        print("   docker-compose -f docker-compose.instant.yml -p instant logs -f frontend")
        print()
    
    def fix(self):
        """즉시 수정 실행"""
        try:
            print("Frontend 재시작 문제 해결 중...")
            print()
            
            # 1. 현재 포트 가져오기
            ports = self.get_current_ports()
            print(f"사용할 포트: {ports}")
            print()
            
            # 2. 수정된 설정 생성
            if not self.create_fixed_config(ports):
                return False
            print()
            
            # 3. 기존 서비스 중지
            self.stop_existing_services()
            print()
            
            # 4. 수정된 서비스 시작
            if not self.start_fixed_services():
                return False
            print()
            
            # 5. 서비스 대기
            self.wait_for_services(ports)
            print()
            
            # 6. 서비스 열기
            self.open_services(ports)
            print()
            
            # 7. 상태 표시
            self.show_status(ports)
            
            return True
            
        except KeyboardInterrupt:
            print("\n[INFO] 수정 작업 취소됨")
            return False
        except Exception as e:
            print(f"\n[ERROR] 수정 실패: {e}")
            return False

def main():
    """메인 함수"""
    print("Instant Fix - Frontend 재시작 문제 해결")
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
    
    # 즉시 수정 실행
    fixer = InstantFixer()
    success = fixer.fix()
    
    input("\nEnter를 눌러 종료...")
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())