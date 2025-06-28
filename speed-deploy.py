#!/usr/bin/env python3
"""
Speed Deploy with Universal Port Manager
=======================================

Fast deployment using pre-built images + Universal Port Manager integration
"""

import os
import sys
import time
import subprocess
import webbrowser
import socket
from pathlib import Path

# Windows encoding fix
if os.name == 'nt':
    try:
        os.system('chcp 65001 >nul 2>&1')
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

class SpeedDeployer:
    """Fast deployment with UPM integration"""
    
    def __init__(self):
        self.project_name = "online-evaluation"
        self.project_root = Path.cwd()
        
        print("=" * 60)
        print("    Speed Deploy - Fast Build + Port Manager")
        print("=" * 60)
        print()
        
    def check_port_available(self, port):
        """Check if port is available"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            return result != 0
        except:
            return True
    
    def find_available_port(self, start_port, max_attempts=100):
        """Find available port"""
        for i in range(max_attempts):
            port = start_port + i
            if self.check_port_available(port):
                return port
        return start_port
    
    def use_port_manager(self):
        """Try to use Universal Port Manager if available"""
        print("[Port Manager] Checking Universal Port Manager...")
        
        try:
            # Try to use existing UPM
            upm_path = self.project_root / 'universal_port_manager'
            if ump_path.exists():
                sys.path.insert(0, str(self.project_root))
                from universal_port_manager import PortManager
                
                pm = PortManager(project_name=self.project_name)
                ports = pm.allocate_services(['frontend', 'backend', 'mongodb', 'redis'])
                
                print("[OK] Universal Port Manager allocated ports:")
                for service, port in ports.items():
                    print(f"  {service}: {port}")
                
                return ports
                
        except Exception as e:
            print(f"[INFO] UPM not available: {e}")
        
        # Fallback to simple port allocation
        print("[Fallback] Using simple port allocation...")
        ports = {
            'frontend': self.find_available_port(3001),
            'backend': self.find_available_port(8001), 
            'mongodb': self.find_available_port(27018),
            'redis': self.find_available_port(6381)
        }
        
        print("[OK] Simple port allocation:")
        for service, port in ports.items():
            print(f"  {service}: {port}")
        
        return ports
    
    def create_speed_config(self, ports):
        """Create fast deployment config - no build time"""
        print("[Speed Config] Creating fast deployment configuration...")
        
        # Use pre-built images only - NO BUILDING
        speed_config = f"""services:
  mongodb:
    image: mongo:7
    container_name: speed-mongodb
    ports:
      - "{ports['mongodb']}:27017"
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: password123
    volumes:
      - speed_mongodb:/data/db
    networks:
      - speed-net

  redis:
    image: redis:7-alpine
    container_name: speed-redis
    ports:
      - "{ports['redis']}:6379"
    volumes:
      - speed_redis:/data
    networks:
      - speed-net

  backend:
    image: python:3.11-slim
    container_name: speed-backend
    ports:
      - "{ports['backend']}:8000"
    environment:
      MONGO_URL: "mongodb://admin:password123@mongodb:27017/online_evaluation?authSource=admin"
      JWT_SECRET: "speed-key-{int(time.time())}"
      CORS_ORIGINS: "http://localhost:{ports['frontend']}"
    volumes:
      - ./backend:/app
      - ./uploads:/app/uploads
    working_dir: /app
    command: >
      bash -c "
        pip install --no-cache-dir fastapi uvicorn motor pymongo pydantic python-jose passlib python-multipart &&
        python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload
      "
    depends_on:
      - mongodb
      - redis
    networks:
      - speed-net

  frontend:
    image: node:18-alpine
    container_name: speed-frontend
    ports:
      - "{ports['frontend']}:3000"
    environment:
      REACT_APP_BACKEND_URL: "http://localhost:{ports['backend']}"
    volumes:
      - ./frontend:/app
      - speed_nodemodules:/app/node_modules
    working_dir: /app
    command: >
      sh -c "
        npm install --production --silent &&
        npm start
      "
    depends_on:
      - backend
    networks:
      - speed-net

networks:
  speed-net:
    driver: bridge

volumes:
  speed_mongodb:
  speed_redis:
  speed_nodemodules:
"""
        
        try:
            config_path = self.project_root / 'docker-compose.speed.yml'
            with open(config_path, 'w', encoding='utf-8', newline='\n') as f:
                f.write(speed_config)
            print("[OK] Speed configuration created")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to create speed config: {e}")
            return False
    
    def start_speed_services(self):
        """Start services with speed configuration"""
        print("[Speed Start] Starting services...")
        
        # Clean up first
        print("  Cleaning up...")
        cleanup_cmd = f"docker-compose -f docker-compose.speed.yml -p speed down --remove-orphans"
        subprocess.run(cleanup_cmd.split(), capture_output=True)
        
        # Start with speed config
        print("  Starting speed services...")
        start_cmd = f"docker-compose -f docker-compose.speed.yml -p speed up -d"
        
        try:
            result = subprocess.run(start_cmd.split(), 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print("[OK] Speed services started")
                return True
            else:
                print(f"[ERROR] Speed start failed: {result.stderr}")
                return False
        except Exception as e:
            print(f"[ERROR] Exception: {e}")
            return False
    
    def wait_and_open(self, ports):
        """Quick wait and open"""
        print("[Quick Wait] Waiting for services...")
        
        # Shorter wait time
        max_wait = 60  # 1 minute max
        wait_time = 0
        
        while wait_time < max_wait:
            if not self.check_port_available(ports['frontend']):
                break
            time.sleep(3)
            wait_time += 3
            if wait_time % 15 == 0:
                print(f"  Waiting... ({wait_time}s)")
        
        # Open apps
        frontend_url = f"http://localhost:{ports['frontend']}"
        backend_url = f"http://localhost:{ports['backend']}/docs"
        
        try:
            print(f"  Opening: {frontend_url}")
            webbrowser.open(frontend_url)
            time.sleep(2)
            print(f"  Opening: {backend_url}")
            webbrowser.open(backend_url)
        except Exception as e:
            print(f"[INFO] Manual open: {frontend_url}")
            print(f"[INFO] Manual open: {backend_url}")
    
    def show_speed_results(self, ports):
        """Show results"""
        print()
        print("=" * 60)
        print("    Speed Deployment Complete!")
        print("=" * 60)
        print()
        print("URLs:")
        print(f"  Frontend: http://localhost:{ports['frontend']}")
        print(f"  Backend:  http://localhost:{ports['backend']}")
        print(f"  API Docs: http://localhost:{ports['backend']}/docs")
        print()
        print("Speed Features:")
        print("  ✓ No custom Docker builds")
        print("  ✓ Pre-built base images only")
        print("  ✓ Universal Port Manager integration")
        print("  ✓ Fast npm install with cache")
        print()
        print("Commands:")
        print("  Status: docker-compose -f docker-compose.speed.yml -p speed ps")
        print("  Logs:   docker-compose -f docker-compose.speed.yml -p speed logs -f")
        print("  Stop:   docker-compose -f docker-compose.speed.yml -p speed down")
        print()
    
    def deploy(self):
        """Execute speed deployment"""
        try:
            # 1. Use Port Manager
            ports = self.use_port_manager()
            print()
            
            # 2. Create speed config
            if not self.create_speed_config(ports):
                return False
            print()
            
            # 3. Start speed services
            if not self.start_speed_services():
                return False
            print()
            
            # 4. Quick wait and open
            self.wait_and_open(ports)
            print()
            
            # 5. Show results
            self.show_speed_results(ports)
            
            return True
            
        except KeyboardInterrupt:
            print("\n[INFO] Speed deployment cancelled")
            return False
        except Exception as e:
            print(f"\n[ERROR] Speed deployment failed: {e}")
            return False

def main():
    """Main function"""
    print("Speed Deploy - Fast build with Universal Port Manager")
    print("Uses pre-built images to eliminate build time")
    print()
    
    # Check Docker
    try:
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            print("[ERROR] Docker not available")
            input("Press Enter to exit...")
            return 1
        print(f"[OK] Docker: {result.stdout.strip()}")
    except:
        print("[ERROR] Docker check failed")
        input("Press Enter to exit...")
        return 1
    
    # Deploy
    deployer = SpeedDeployer()
    success = deployer.deploy()
    
    input("\nPress Enter to exit...")
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())