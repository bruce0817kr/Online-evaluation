"""
원클릭 배포 매니저
Docker Compose 기반 자동 배포 및 환경 설정 관리
"""

import os
import subprocess
import json
import yaml
import logging
import shutil
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import platform
import asyncio
from port_manager_service import port_manager

logger = logging.getLogger(__name__)

class DeploymentManager:
    """배포 관리자"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.docker_compose_file = self.project_root / "docker-compose.yml"
        self.env_file = self.project_root / ".env"
        self.deployment_log_file = self.project_root / "deployment.log"
        self.supported_environments = ['development', 'staging', 'production']
        
    def check_prerequisites(self) -> Dict[str, bool]:
        """배포 전제 조건 확인"""
        prerequisites = {
            'docker': self._check_docker(),
            'docker_compose': self._check_docker_compose(),
            'env_file': self.env_file.exists(),
            'docker_compose_file': self.docker_compose_file.exists(),
            'port_availability': self._check_ports(),
            'disk_space': self._check_disk_space(),
            'memory': self._check_memory()
        }
        
        return prerequisites
    
    def _check_docker(self) -> bool:
        """Docker 설치 및 실행 확인"""
        try:
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                # Docker 데몬 실행 확인
                result = subprocess.run(['docker', 'info'], capture_output=True, text=True)
                return result.returncode == 0
            return False
        except:
            return False
    
    def _check_docker_compose(self) -> bool:
        """Docker Compose 설치 확인"""
        try:
            result = subprocess.run(['docker-compose', '--version'], capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False
    
    def _check_ports(self) -> bool:
        """필요한 포트 사용 가능 여부 확인"""
        service_config = port_manager.get_service_config()
        conflicts = port_manager.check_port_conflicts()
        return len(conflicts) == 0
    
    def _check_disk_space(self, min_gb: int = 10) -> bool:
        """디스크 공간 확인"""
        import shutil
        total, used, free = shutil.disk_usage("/")
        free_gb = free // (2**30)
        return free_gb >= min_gb
    
    def _check_memory(self, min_gb: int = 4) -> bool:
        """메모리 확인"""
        import psutil
        memory = psutil.virtual_memory()
        available_gb = memory.available // (2**30)
        return available_gb >= min_gb
    
    def generate_env_file(self, environment: str = 'development') -> bool:
        """환경 변수 파일 생성"""
        try:
            service_config = port_manager.get_service_config()
            
            env_content = f"""# Auto-generated environment file
# Generated at: {datetime.utcnow().isoformat()}
# Environment: {environment}

# Application Settings
NODE_ENV={environment}
ENVIRONMENT={environment}

# Service Ports
FRONTEND_PORT={service_config['frontend']['port']}
BACKEND_PORT={service_config['backend']['port']}
MONGODB_PORT={service_config['mongodb']['port']}
REDIS_PORT={service_config['redis']['port']}
NGINX_PORT={service_config['nginx']['port']}

# Database Settings
MONGODB_URI=mongodb://mongodb:{service_config['mongodb']['port']}/evaluation_system
MONGODB_DB_NAME=evaluation_system

# Redis Settings
REDIS_URL=redis://redis:{service_config['redis']['port']}/0

# Backend Settings
BACKEND_URL=http://backend:{service_config['backend']['port']}
API_PREFIX=/api

# Frontend Settings
REACT_APP_BACKEND_URL=http://localhost:{service_config['nginx']['port']}
REACT_APP_API_URL=http://localhost:{service_config['nginx']['port']}/api

# Security Settings
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# CORS Settings
CORS_ORIGINS=["http://localhost:{service_config['frontend']['port']}", "http://localhost:{service_config['nginx']['port']}"]

# Monitoring Settings
PROMETHEUS_PORT={service_config['prometheus']['port']}
GRAFANA_PORT={service_config['grafana']['port']}

# Logging Settings
ELASTICSEARCH_PORT={service_config['elasticsearch']['port']}
KIBANA_PORT={service_config['kibana']['port']}
LOG_LEVEL=INFO

# Admin User Settings
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
ADMIN_EMAIL=admin@example.com
"""
            
            # 프로덕션 환경의 경우 추가 설정
            if environment == 'production':
                env_content += """
# Production Settings
DEBUG=false
SECURE_COOKIES=true
HTTPS_ONLY=true
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=100
"""
            
            with open(self.env_file, 'w') as f:
                f.write(env_content)
            
            logger.info(f"환경 변수 파일 생성 완료: {self.env_file}")
            return True
            
        except Exception as e:
            logger.error(f"환경 변수 파일 생성 실패: {e}")
            return False
    
    def generate_docker_compose(self, environment: str = 'development') -> bool:
        """Docker Compose 파일 생성"""
        try:
            service_config = port_manager.get_service_config()
            port_mappings = port_manager.generate_docker_compose_ports()
            
            compose_config = {
                'version': '3.8',
                'services': {
                    'frontend': {
                        'build': {
                            'context': './frontend',
                            'dockerfile': 'Dockerfile'
                        },
                        'container_name': 'evaluation-frontend',
                        'ports': port_mappings.get('frontend', []),
                        'environment': [
                            'NODE_ENV=${NODE_ENV}',
                            'REACT_APP_BACKEND_URL=${REACT_APP_BACKEND_URL}',
                            'REACT_APP_API_URL=${REACT_APP_API_URL}'
                        ],
                        'volumes': [
                            './frontend:/app',
                            '/app/node_modules'
                        ],
                        'depends_on': ['backend'],
                        'networks': ['evaluation-network']
                    },
                    'backend': {
                        'build': {
                            'context': './backend',
                            'dockerfile': 'Dockerfile'
                        },
                        'container_name': 'evaluation-backend',
                        'ports': port_mappings.get('backend', []),
                        'environment': [
                            'MONGODB_URI=${MONGODB_URI}',
                            'REDIS_URL=${REDIS_URL}',
                            'JWT_SECRET_KEY=${JWT_SECRET_KEY}',
                            'CORS_ORIGINS=${CORS_ORIGINS}',
                            'LOG_LEVEL=${LOG_LEVEL}'
                        ],
                        'volumes': [
                            './backend:/app',
                            './uploads:/app/uploads',
                            './logs:/app/logs'
                        ],
                        'depends_on': ['mongodb', 'redis'],
                        'networks': ['evaluation-network']
                    },
                    'mongodb': {
                        'image': 'mongo:6.0',
                        'container_name': 'evaluation-mongodb',
                        'ports': port_mappings.get('mongodb', []),
                        'volumes': [
                            'mongodb_data:/data/db',
                            './scripts/init-mongo.js:/docker-entrypoint-initdb.d/init-mongo.js'
                        ],
                        'environment': [
                            'MONGO_INITDB_DATABASE=evaluation_system'
                        ],
                        'networks': ['evaluation-network']
                    },
                    'redis': {
                        'image': 'redis:7-alpine',
                        'container_name': 'evaluation-redis',
                        'ports': port_mappings.get('redis', []),
                        'volumes': [
                            'redis_data:/data'
                        ],
                        'networks': ['evaluation-network']
                    },
                    'nginx': {
                        'image': 'nginx:alpine',
                        'container_name': 'evaluation-nginx',
                        'ports': port_mappings.get('nginx', []),
                        'volumes': [
                            './nginx.conf:/etc/nginx/nginx.conf:ro',
                            './nginx-upstream.conf:/etc/nginx/conf.d/upstream.conf:ro'
                        ],
                        'depends_on': ['frontend', 'backend'],
                        'networks': ['evaluation-network']
                    }
                },
                'volumes': {
                    'mongodb_data': {},
                    'redis_data': {},
                    'prometheus_data': {},
                    'grafana_data': {},
                    'elasticsearch_data': {}
                },
                'networks': {
                    'evaluation-network': {
                        'driver': 'bridge'
                    }
                }
            }
            
            # 모니터링 서비스 추가 (프로덕션/스테이징)
            if environment in ['staging', 'production']:
                compose_config['services'].update({
                    'prometheus': {
                        'image': 'prom/prometheus:latest',
                        'container_name': 'evaluation-prometheus',
                        'ports': port_mappings.get('prometheus', []),
                        'volumes': [
                            './monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml',
                            'prometheus_data:/prometheus'
                        ],
                        'networks': ['evaluation-network']
                    },
                    'grafana': {
                        'image': 'grafana/grafana:latest',
                        'container_name': 'evaluation-grafana',
                        'ports': port_mappings.get('grafana', []),
                        'volumes': [
                            'grafana_data:/var/lib/grafana',
                            './monitoring/grafana/provisioning:/etc/grafana/provisioning'
                        ],
                        'environment': [
                            'GF_SECURITY_ADMIN_PASSWORD=admin'
                        ],
                        'networks': ['evaluation-network']
                    }
                })
            
            # 로깅 서비스 추가 (프로덕션)
            if environment == 'production':
                compose_config['services'].update({
                    'elasticsearch': {
                        'image': 'docker.elastic.co/elasticsearch/elasticsearch:8.10.2',
                        'container_name': 'evaluation-elasticsearch',
                        'ports': port_mappings.get('elasticsearch', []),
                        'volumes': [
                            'elasticsearch_data:/usr/share/elasticsearch/data'
                        ],
                        'environment': [
                            'discovery.type=single-node',
                            'xpack.security.enabled=false'
                        ],
                        'networks': ['evaluation-network']
                    },
                    'kibana': {
                        'image': 'docker.elastic.co/kibana/kibana:8.10.2',
                        'container_name': 'evaluation-kibana',
                        'ports': port_mappings.get('kibana', []),
                        'environment': [
                            'ELASTICSEARCH_HOSTS=http://elasticsearch:9200'
                        ],
                        'depends_on': ['elasticsearch'],
                        'networks': ['evaluation-network']
                    }
                })
            
            # Nginx upstream 설정 생성
            upstream_config = port_manager.generate_nginx_upstream()
            with open(self.project_root / 'nginx-upstream.conf', 'w') as f:
                f.write(upstream_config)
            
            # Docker Compose 파일 저장
            with open(self.docker_compose_file, 'w') as f:
                yaml.dump(compose_config, f, default_flow_style=False, sort_keys=False)
            
            logger.info(f"Docker Compose 파일 생성 완료: {self.docker_compose_file}")
            return True
            
        except Exception as e:
            logger.error(f"Docker Compose 파일 생성 실패: {e}")
            return False
    
    def create_deployment_script(self, environment: str = 'development') -> bool:
        """배포 스크립트 생성"""
        try:
            script_content = f"""#!/bin/bash
# Auto-generated deployment script
# Environment: {environment}
# Generated at: {datetime.utcnow().isoformat()}

set -e  # Exit on error

echo "🚀 Starting deployment for {environment} environment..."

# Check prerequisites
echo "📋 Checking prerequisites..."
docker --version || {{ echo "❌ Docker not installed"; exit 1; }}
docker-compose --version || {{ echo "❌ Docker Compose not installed"; exit 1; }}

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p uploads logs mongodb_data redis_data

# Load environment variables
echo "🔧 Loading environment variables..."
if [ -f .env ]; then
    source .env
else
    echo "❌ .env file not found"
    exit 1
fi

# Pull latest images
echo "🐳 Pulling Docker images..."
docker-compose pull

# Build services
echo "🔨 Building services..."
docker-compose build --no-cache

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose down

# Start services
echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Health checks
echo "🏥 Running health checks..."
"""
            
            # 서비스별 헬스체크 추가
            service_config = port_manager.get_service_config()
            for service_name, config in service_config.items():
                if config['healthcheck'] and config['port']:
                    script_content += f"""
# Check {service_name}
curl -f http://localhost:{config['port']}{config['healthcheck']} || echo "⚠️  {service_name} health check failed"
"""
            
            script_content += """
# Show running containers
echo "📊 Running containers:"
docker-compose ps

# Show logs
echo "📜 Recent logs:"
docker-compose logs --tail=50

echo "✅ Deployment complete!"
echo "🌐 Access the application at:"
"""
            
            # 접속 URL 추가
            for service_name, config in service_config.items():
                if config['url'] and service_name in ['frontend', 'nginx']:
                    script_content += f'echo "   - {config["name"]}: {config["url"]}"\n'
            
            # 스크립트 파일 저장
            script_file = self.project_root / 'deploy.sh'
            with open(script_file, 'w') as f:
                f.write(script_content)
            
            # 실행 권한 부여
            os.chmod(script_file, 0o755)
            
            # Windows용 배치 파일도 생성
            if platform.system() == 'Windows':
                self._create_windows_deployment_script(environment)
            
            logger.info(f"배포 스크립트 생성 완료: {script_file}")
            return True
            
        except Exception as e:
            logger.error(f"배포 스크립트 생성 실패: {e}")
            return False
    
    def _create_windows_deployment_script(self, environment: str):
        """Windows용 배포 스크립트 생성"""
        service_config = port_manager.get_service_config()
        
        batch_content = f"""@echo off
REM Auto-generated deployment script for Windows
REM Environment: {environment}
REM Generated at: {datetime.utcnow().isoformat()}

echo Starting deployment for {environment} environment...

REM Check prerequisites
echo Checking prerequisites...
docker --version >nul 2>&1 || (echo Docker not installed && exit /b 1)
docker-compose --version >nul 2>&1 || (echo Docker Compose not installed && exit /b 1)

REM Create necessary directories
echo Creating directories...
if not exist uploads mkdir uploads
if not exist logs mkdir logs

REM Pull latest images
echo Pulling Docker images...
docker-compose pull

REM Build services
echo Building services...
docker-compose build --no-cache

REM Stop existing containers
echo Stopping existing containers...
docker-compose down

REM Start services
echo Starting services...
docker-compose up -d

REM Wait for services
echo Waiting for services to be ready...
timeout /t 10 /nobreak >nul

REM Show running containers
echo Running containers:
docker-compose ps

echo.
echo Deployment complete!
echo Access the application at:
"""
        
        # 접속 URL 추가
        for service_name, config in service_config.items():
            if config['url'] and service_name in ['frontend', 'nginx']:
                batch_content += f'echo    - {config["name"]}: {config["url"]}\n'
        
        batch_content += """
echo.
pause
"""
        
        batch_file = self.project_root / 'deploy.bat'
        with open(batch_file, 'w') as f:
            f.write(batch_content)
        
        logger.info(f"Windows 배포 스크립트 생성 완료: {batch_file}")
    
    async def deploy(self, environment: str = 'development', force: bool = False) -> Dict[str, any]:
        """배포 실행"""
        deployment_result = {
            'status': 'pending',
            'environment': environment,
            'started_at': datetime.utcnow().isoformat(),
            'steps': {}
        }
        
        try:
            # 1. 전제 조건 확인
            logger.info("배포 전제 조건 확인 중...")
            prerequisites = self.check_prerequisites()
            deployment_result['steps']['prerequisites'] = prerequisites
            
            if not all(prerequisites.values()) and not force:
                failed_checks = [k for k, v in prerequisites.items() if not v]
                raise Exception(f"전제 조건 미충족: {', '.join(failed_checks)}")
            
            # 2. 환경 변수 파일 생성
            logger.info("환경 변수 파일 생성 중...")
            if not self.generate_env_file(environment):
                raise Exception("환경 변수 파일 생성 실패")
            deployment_result['steps']['env_file'] = True
            
            # 3. Docker Compose 파일 생성
            logger.info("Docker Compose 파일 생성 중...")
            if not self.generate_docker_compose(environment):
                raise Exception("Docker Compose 파일 생성 실패")
            deployment_result['steps']['docker_compose'] = True
            
            # 4. 배포 스크립트 생성
            logger.info("배포 스크립트 생성 중...")
            if not self.create_deployment_script(environment):
                raise Exception("배포 스크립트 생성 실패")
            deployment_result['steps']['deployment_script'] = True
            
            # 5. 포트 매핑 정보 내보내기
            logger.info("포트 매핑 정보 저장 중...")
            port_manager.export_port_mapping()
            deployment_result['steps']['port_mapping'] = True
            
            # 6. 배포 실행
            logger.info("배포 실행 중...")
            if platform.system() == 'Windows':
                result = subprocess.run(['cmd', '/c', 'deploy.bat'], capture_output=True, text=True)
            else:
                result = subprocess.run(['./deploy.sh'], capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"배포 실행 실패: {result.stderr}")
            
            deployment_result['steps']['deployment'] = True
            deployment_result['status'] = 'success'
            deployment_result['completed_at'] = datetime.utcnow().isoformat()
            
            # 7. 서비스 상태 확인
            service_status = await self._check_service_status()
            deployment_result['service_status'] = service_status
            
            # 배포 로그 저장
            self._save_deployment_log(deployment_result)
            
            logger.info("배포 완료!")
            return deployment_result
            
        except Exception as e:
            logger.error(f"배포 실패: {e}")
            deployment_result['status'] = 'failed'
            deployment_result['error'] = str(e)
            deployment_result['completed_at'] = datetime.utcnow().isoformat()
            self._save_deployment_log(deployment_result)
            return deployment_result
    
    async def _check_service_status(self) -> Dict[str, Dict[str, any]]:
        """서비스 상태 확인"""
        service_config = port_manager.get_service_config()
        service_status = {}
        
        for service_name, config in service_config.items():
            status = {
                'name': config['name'],
                'port': config['port'],
                'url': config['url'],
                'running': False,
                'healthy': False
            }
            
            # Docker 컨테이너 상태 확인
            try:
                result = subprocess.run(
                    ['docker', 'ps', '--filter', f'name=evaluation-{service_name}', '--format', '{{.Status}}'],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0 and result.stdout.strip():
                    status['running'] = True
                    status['container_status'] = result.stdout.strip()
                    
                    # 헬스체크
                    if config['healthcheck'] and config['port']:
                        import aiohttp
                        try:
                            async with aiohttp.ClientSession() as session:
                                async with session.get(f"http://localhost:{config['port']}{config['healthcheck']}") as resp:
                                    status['healthy'] = resp.status == 200
                        except:
                            pass
            except:
                pass
            
            service_status[service_name] = status
        
        return service_status
    
    def _save_deployment_log(self, deployment_result: Dict):
        """배포 로그 저장"""
        try:
            logs = []
            if self.deployment_log_file.exists():
                with open(self.deployment_log_file, 'r') as f:
                    logs = json.load(f)
            
            logs.append(deployment_result)
            
            # 최근 50개만 유지
            logs = logs[-50:]
            
            with open(self.deployment_log_file, 'w') as f:
                json.dump(logs, f, indent=2)
        except Exception as e:
            logger.error(f"배포 로그 저장 실패: {e}")
    
    def get_deployment_history(self, limit: int = 10) -> List[Dict]:
        """배포 이력 조회"""
        if not self.deployment_log_file.exists():
            return []
        
        try:
            with open(self.deployment_log_file, 'r') as f:
                logs = json.load(f)
                return logs[-limit:]
        except:
            return []
    
    def rollback(self, target_deployment_id: Optional[str] = None):
        """이전 배포로 롤백"""
        logger.info(f"롤백 시작: {target_deployment_id or '이전 버전'}")
        
        try:
            # Docker 이미지 태그 기반 롤백
            subprocess.run(['docker-compose', 'down'], check=True)
            
            if target_deployment_id:
                # 특정 버전으로 롤백
                # TODO: 구현 필요
                pass
            else:
                # 이전 버전으로 롤백
                subprocess.run(['docker-compose', 'up', '-d'], check=True)
            
            logger.info("롤백 완료")
            return True
            
        except Exception as e:
            logger.error(f"롤백 실패: {e}")
            return False

# 싱글톤 인스턴스
deployment_manager = DeploymentManager()