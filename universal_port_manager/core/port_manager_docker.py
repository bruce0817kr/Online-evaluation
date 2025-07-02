"""
포트 매니저 Docker 통합 모듈
===========================

Docker Compose 파일 생성 및 컨테이너 관리 기능
"""

import json
import logging
import subprocess
from typing import Dict, Optional
from pathlib import Path

# 선택적 YAML 의존성
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    yaml = None

logger = logging.getLogger(__name__)

class PortManagerDocker:
    """
    Docker 관련 기능 관리자
    
    담당 기능:
    - Docker Compose 파일 생성
    - 서비스 시작/중지
    - 컨테이너 상태 관리
    - YAML 의존성 안전 처리
    """
    
    def __init__(self, project_dir: Path, project_name: str):
        """
        Docker 관리자 초기화
        
        Args:
            project_dir: 프로젝트 디렉토리
            project_name: 프로젝트 이름
        """
        self.project_dir = project_dir
        self.project_name = project_name
        
        logger.info(f"Docker 관리자 초기화: {project_name} (YAML: {'활성화' if YAML_AVAILABLE else '비활성화'})")
    
    def generate_compose_file(self, allocated_ports: Dict, 
                             output_file: str = 'docker-compose.yml',
                             include_override: bool = True,
                             template_name: str = None,
                             registry = None) -> bool:
        """
        Docker Compose 파일 생성
        
        Args:
            allocated_ports: 할당된 포트 정보
            output_file: 출력 파일명
            include_override: override 파일도 생성할지 여부
            template_name: 사용할 서비스 템플릿
            registry: 서비스 레지스트리 (선택적)
            
        Returns:
            생성 성공 여부
        """
        if not YAML_AVAILABLE:
            logger.warning("PyYAML이 없어 Docker Compose 파일 생성 불가")
            return self._generate_compose_json(allocated_ports, output_file)
        
        try:
            # 기본 docker-compose.yml 구조
            compose_data = {
                'version': '3.8',
                'services': {},
                'volumes': {},
                'networks': {
                    f'{self.project_name}-network': {
                        'driver': 'bridge'
                    }
                }
            }
            
            # 서비스별 설정 생성
            for service_name, allocated_port in allocated_ports.items():
                service_config = self._generate_service_config(
                    service_name, allocated_port, registry
                )
                compose_data['services'][service_name] = service_config
                
                # 볼륨이 필요한 서비스는 볼륨 추가
                if allocated_port.service_type in ['mongodb', 'database', 'redis', 'elasticsearch']:
                    volume_name = f"{service_name}_data"
                    compose_data['volumes'][volume_name] = None
            
            # 파일 저장
            output_path = self.project_dir / output_file
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(compose_data, f, default_flow_style=False, sort_keys=False)
            
            logger.info(f"Docker Compose 파일 생성: {output_path}")
            
            # Override 파일 생성
            if include_override:
                self._generate_compose_override(allocated_ports)
            
            return True
            
        except Exception as e:
            logger.error(f"Docker Compose 파일 생성 실패: {e}")
            return False
    
    def _generate_compose_json(self, allocated_ports: Dict, output_file: str) -> bool:
        """YAML 없이 JSON 형식으로 Docker Compose 설정 생성"""
        try:
            compose_data = {
                'version': '3.8',
                'services': {},
                'volumes': {},
                'networks': {
                    f'{self.project_name}-network': {
                        'driver': 'bridge'
                    }
                }
            }
            
            for service_name, allocated_port in allocated_ports.items():
                service_config = self._generate_service_config(service_name, allocated_port)
                compose_data['services'][service_name] = service_config
                
                if allocated_port.service_type in ['mongodb', 'database', 'redis', 'elasticsearch']:
                    volume_name = f"{service_name}_data"
                    compose_data['volumes'][volume_name] = None
            
            # JSON 파일로 저장 (참고용)
            json_path = self.project_dir / f"{output_file}.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(compose_data, f, indent=2, ensure_ascii=False)
            
            # 기본적인 YAML 형태로도 저장 시도
            yaml_path = self.project_dir / output_file
            self._write_basic_yaml(compose_data, yaml_path)
            
            logger.info(f"Docker Compose 설정 생성: {json_path}, {yaml_path}")
            return True
            
        except Exception as e:
            logger.error(f"Docker Compose 설정 생성 실패: {e}")
            return False
    
    def _write_basic_yaml(self, data: dict, output_path: Path):
        """YAML 라이브러리 없이 기본적인 YAML 파일 작성"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"version: '{data['version']}'\n\n")
                
                # Services 섹션
                f.write("services:\n")
                for service_name, service_config in data['services'].items():
                    f.write(f"  {service_name}:\n")
                    for key, value in service_config.items():
                        if isinstance(value, list):
                            f.write(f"    {key}:\n")
                            for item in value:
                                f.write(f"      - {item}\n")
                        elif isinstance(value, dict):
                            f.write(f"    {key}:\n")
                            for k, v in value.items():
                                f.write(f"      {k}: {v}\n")
                        else:
                            f.write(f"    {key}: {value}\n")
                    f.write("\n")
                
                # Volumes 섹션
                if data['volumes']:
                    f.write("volumes:\n")
                    for volume_name in data['volumes']:
                        f.write(f"  {volume_name}:\n")
                    f.write("\n")
                
                # Networks 섹션
                f.write("networks:\n")
                for network_name, network_config in data['networks'].items():
                    f.write(f"  {network_name}:\n")
                    f.write(f"    driver: {network_config['driver']}\n")
            
            logger.info(f"기본 YAML 파일 생성: {output_path}")
            
        except Exception as e:
            logger.warning(f"기본 YAML 생성 실패: {e}")
    
    def _generate_service_config(self, service_name: str, allocated_port, registry=None) -> Dict:
        """개별 서비스 설정 생성"""
        service_type = allocated_port.service_type
        
        # 서비스 레지스트리에서 기본 설정 조회 (안전한 조회)
        service_def = None
        if registry:
            try:
                service_def = registry.get_service_by_name(service_type)
            except Exception:
                pass
        
        if not service_def:
            internal_port = allocated_port.port
        else:
            internal_port = getattr(service_def, 'internal_port', allocated_port.port) or allocated_port.port
        
        config = {
            'container_name': f"{self.project_name}-{service_name}",
            'restart': 'unless-stopped',
            'networks': [f'{self.project_name}-network']
        }
        
        # 포트 매핑
        config['ports'] = [f"{allocated_port.port}:{internal_port}"]
        
        # 서비스 타입별 특별 설정
        if service_type in ['frontend', 'backend']:
            # 빌드 설정 확인
            dockerfile_paths = [
                self.project_dir / service_name / 'Dockerfile',
                self.project_dir / f'Dockerfile.{service_name}',
                self.project_dir / 'Dockerfile'
            ]
            
            for dockerfile_path in dockerfile_paths:
                if dockerfile_path.exists():
                    if dockerfile_path.name == 'Dockerfile' and dockerfile_path.parent.name == service_name:
                        config['build'] = {
                            'context': '.',
                            'dockerfile': f'{service_name}/Dockerfile'
                        }
                    elif dockerfile_path.name.startswith('Dockerfile.'):
                        config['build'] = {
                            'context': '.',
                            'dockerfile': dockerfile_path.name
                        }
                    else:
                        config['build'] = '.'
                    break
            else:
                # Dockerfile이 없으면 기본 이미지 사용
                if service_type == 'frontend':
                    config['image'] = 'node:18-alpine'
                    config['command'] = 'npm run dev'
                elif service_type == 'backend':
                    config['image'] = 'python:3.11-slim'
                    config['command'] = 'python3 -m uvicorn main:app --host 0.0.0.0 --port 8000'
            
            # 환경 변수 추가
            config['environment'] = {
                'NODE_ENV': 'development',
                'PORT': str(internal_port)
            }
            
            # 볼륨 마운트 (개발 모드)
            config['volumes'] = [f'./{service_name}:/app']
            config['working_dir'] = '/app'
            
        elif service_type == 'mongodb':
            config['image'] = 'mongo:7'
            config['environment'] = {
                'MONGO_INITDB_ROOT_USERNAME': 'admin',
                'MONGO_INITDB_ROOT_PASSWORD': 'password123',
                'MONGO_INITDB_DATABASE': self.project_name
            }
            config['volumes'] = [f'{service_name}_data:/data/db']
            
        elif service_type == 'redis':
            config['image'] = 'redis:7-alpine'
            config['command'] = 'redis-server --appendonly yes'
            config['volumes'] = [f'{service_name}_data:/data']
            
        elif service_type == 'database':
            config['image'] = 'postgres:15-alpine'
            config['environment'] = {
                'POSTGRES_DB': self.project_name,
                'POSTGRES_USER': 'admin',
                'POSTGRES_PASSWORD': 'password123'
            }
            config['volumes'] = [f'{service_name}_data:/var/lib/postgresql/data']
            
        elif service_type == 'nginx':
            config['image'] = 'nginx:alpine'
            # nginx 설정 파일이 있으면 마운트
            nginx_conf = self.project_dir / 'nginx.conf'
            if nginx_conf.exists():
                config['volumes'] = ['./nginx.conf:/etc/nginx/nginx.conf:ro']
            # frontend, backend 서비스에 의존
            other_services = [name for name in config.get('depends_on', []) 
                            if name != service_name]
            if other_services:
                config['depends_on'] = other_services
        
        elif service_type == 'monitoring':
            # Grafana 기본 설정
            config['image'] = 'grafana/grafana:latest'
            config['environment'] = {
                'GF_SECURITY_ADMIN_PASSWORD': 'admin'
            }
            config['volumes'] = [f'{service_name}_data:/var/lib/grafana']
        
        # 서비스 정의에서 추가 설정 적용
        if service_def:
            # 환경 변수 추가
            if hasattr(service_def, 'environment') and service_def.environment:
                if 'environment' not in config:
                    config['environment'] = {}
                config['environment'].update(service_def.environment)
            
            # 헬스체크 추가
            if hasattr(service_def, 'health_check') and service_def.health_check:
                config['healthcheck'] = {
                    'test': f'curl -f http://localhost:{internal_port}{service_def.health_check} || exit 1',
                    'interval': '30s',
                    'timeout': '10s',
                    'retries': 3
                }
        
        return config
    
    def _generate_compose_override(self, allocated_ports: Dict):
        """Docker Compose override 파일 생성"""
        if not YAML_AVAILABLE:
            logger.warning("PyYAML이 없어 override 파일 생성 불가")
            return
        
        try:
            override_data = {
                'version': '3.8',
                'services': {}
            }
            
            for service_name, allocated_port in allocated_ports.items():
                service_config = {}
                
                if allocated_port.service_type in ['frontend', 'backend']:
                    # 개발 환경 특화 설정
                    service_config['environment'] = {
                        'NODE_ENV': 'development',
                        'DEBUG': 'true',
                        'HOT_RELOAD': 'true'
                    }
                    
                    # 개발 명령어
                    if allocated_port.service_type == 'frontend':
                        service_config['command'] = 'npm run dev'
                    elif allocated_port.service_type == 'backend':
                        service_config['command'] = 'python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload'
                
                if service_config:
                    override_data['services'][service_name] = service_config
            
            # override 파일 저장
            override_path = self.project_dir / 'docker-compose.override.yml'
            with open(override_path, 'w', encoding='utf-8') as f:
                yaml.dump(override_data, f, default_flow_style=False, sort_keys=False)
            
            logger.info(f"Docker Compose override 파일 생성: {override_path}")
            
        except Exception as e:
            logger.error(f"Docker Compose override 파일 생성 실패: {e}")
    
    def start_services(self, build: bool = False) -> bool:
        """Docker Compose로 서비스 시작"""
        try:
            # 기존 서비스 정리
            subprocess.run(['docker-compose', 'down'], 
                         cwd=self.project_dir, capture_output=True)
            
            # 서비스 시작
            cmd = ['docker-compose', 'up', '-d']
            if build:
                cmd.extend(['--build'])
            
            result = subprocess.run(cmd, cwd=self.project_dir, 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("Docker 서비스 시작 성공")
                return True
            else:
                logger.error(f"Docker 서비스 시작 실패: {result.stderr}")
                return False
                
        except FileNotFoundError:
            logger.error("docker-compose 명령을 찾을 수 없음. Docker Compose가 설치되어 있는지 확인하세요.")
            return False
        except Exception as e:
            logger.error(f"Docker 서비스 시작 중 오류: {e}")
            return False
    
    def stop_services(self) -> bool:
        """서비스 중지"""
        try:
            result = subprocess.run(['docker-compose', 'down'], 
                                  cwd=self.project_dir, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("Docker 서비스 중지 성공")
                return True
            else:
                logger.error(f"Docker 서비스 중지 실패: {result.stderr}")
                return False
                
        except FileNotFoundError:
            logger.error("docker-compose 명령을 찾을 수 없음")
            return False
        except Exception as e:
            logger.error(f"Docker 서비스 중지 중 오류: {e}")
            return False
    
    def get_service_status(self) -> Dict:
        """서비스 상태 조회"""
        try:
            result = subprocess.run(['docker-compose', 'ps', '--format', 'json'], 
                                  cwd=self.project_dir, capture_output=True, text=True)
            
            if result.returncode == 0:
                services = []
                for line in result.stdout.strip().split('\n'):
                    if line:
                        try:
                            service_info = json.loads(line)
                            services.append(service_info)
                        except json.JSONDecodeError:
                            continue
                
                return {
                    'status': 'success',
                    'services': services,
                    'total_services': len(services),
                    'running_services': len([s for s in services if s.get('State') == 'running'])
                }
            else:
                return {
                    'status': 'error',
                    'error': result.stderr,
                    'services': []
                }
                
        except FileNotFoundError:
            return {
                'status': 'error',
                'error': 'docker-compose not found',
                'services': []
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'services': []
            }
    
    def restart_service(self, service_name: str) -> bool:
        """특정 서비스 재시작"""
        try:
            result = subprocess.run(['docker-compose', 'restart', service_name], 
                                  cwd=self.project_dir, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"서비스 '{service_name}' 재시작 성공")
                return True
            else:
                logger.error(f"서비스 '{service_name}' 재시작 실패: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"서비스 재시작 중 오류: {e}")
            return False
    
    def get_service_logs(self, service_name: str, lines: int = 50) -> str:
        """서비스 로그 조회"""
        try:
            result = subprocess.run(['docker-compose', 'logs', '--tail', str(lines), service_name], 
                                  cwd=self.project_dir, capture_output=True, text=True)
            
            if result.returncode == 0:
                return result.stdout
            else:
                return f"로그 조회 실패: {result.stderr}"
                
        except Exception as e:
            return f"로그 조회 중 오류: {e}"