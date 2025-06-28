"""
서비스 레지스트리 모듈
==================

서비스 정의, 메타데이터, 의존성 관리를 담당하는 모듈
다양한 프로젝트 구조와 서비스 조합을 지원
"""

import json
import yaml
from typing import Dict, List, Optional, Set, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

@dataclass
class ServiceDefinition:
    """서비스 정의"""
    name: str
    type: str
    port: Optional[int] = None
    internal_port: Optional[int] = None
    protocol: str = "tcp"
    environment: Dict[str, str] = None
    volumes: List[str] = None
    depends_on: List[str] = None
    health_check: Optional[str] = None
    description: str = ""
    
    def __post_init__(self):
        if self.environment is None:
            self.environment = {}
        if self.volumes is None:
            self.volumes = []
        if self.depends_on is None:
            self.depends_on = []

@dataclass
class ProjectTemplate:
    """프로젝트 템플릿"""
    name: str
    description: str
    services: List[ServiceDefinition]
    requirements: List[str] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.requirements is None:
            self.requirements = []
        if self.tags is None:
            self.tags = []

class ServiceRegistry:
    """
    서비스 레지스트리
    
    기능:
    - 서비스 정의 관리
    - 프로젝트 템플릿 관리
    - 서비스 의존성 해석
    - 서비스 자동 검색
    """
    
    def __init__(self, config_dir: str = None):
        """
        서비스 레지스트리 초기화
        
        Args:
            config_dir: 설정 디렉토리 경로
        """
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = Path.home() / '.port-manager'
            
        self.config_dir.mkdir(exist_ok=True)
        
        self.services_file = self.config_dir / 'services.json'
        self.templates_file = self.config_dir / 'templates.json'
        
        self.services = self._load_services()
        self.templates = self._load_templates()
    
    def _get_default_services(self) -> Dict[str, ServiceDefinition]:
        """기본 서비스 정의 반환"""
        return {
            # Frontend Services
            'react': ServiceDefinition(
                name='react',
                type='frontend',
                internal_port=3000,
                environment={'NODE_ENV': 'development'},
                description='React development server'
            ),
            'vue': ServiceDefinition(
                name='vue', 
                type='frontend',
                internal_port=8080,
                environment={'NODE_ENV': 'development'},
                description='Vue.js development server'
            ),
            'angular': ServiceDefinition(
                name='angular',
                type='frontend', 
                internal_port=4200,
                environment={'NODE_ENV': 'development'},
                description='Angular development server'
            ),
            'nextjs': ServiceDefinition(
                name='nextjs',
                type='frontend',
                internal_port=3000,
                environment={'NODE_ENV': 'development'},
                description='Next.js application'
            ),
            
            # Backend Services
            'fastapi': ServiceDefinition(
                name='fastapi',
                type='backend',
                internal_port=8000,
                environment={'PYTHONPATH': '/app'},
                health_check='/health',
                description='FastAPI backend server'
            ),
            'express': ServiceDefinition(
                name='express',
                type='backend',
                internal_port=3000,
                environment={'NODE_ENV': 'development'},
                health_check='/health',
                description='Express.js backend server'
            ),
            'django': ServiceDefinition(
                name='django',
                type='backend',
                internal_port=8000,
                environment={'DJANGO_SETTINGS_MODULE': 'settings'},
                health_check='/health',
                description='Django backend server'
            ),
            'flask': ServiceDefinition(
                name='flask',
                type='backend',
                internal_port=5000,
                environment={'FLASK_ENV': 'development'},
                health_check='/health',
                description='Flask backend server'
            ),
            
            # Database Services
            'mongodb': ServiceDefinition(
                name='mongodb',
                type='mongodb',
                internal_port=27017,
                volumes=['mongodb_data:/data/db'],
                environment={
                    'MONGO_INITDB_ROOT_USERNAME': 'admin',
                    'MONGO_INITDB_ROOT_PASSWORD': 'password123'
                },
                description='MongoDB database'
            ),
            'postgresql': ServiceDefinition(
                name='postgresql',
                type='database',
                internal_port=5432,
                volumes=['postgres_data:/var/lib/postgresql/data'],
                environment={
                    'POSTGRES_DB': 'app',
                    'POSTGRES_USER': 'admin',
                    'POSTGRES_PASSWORD': 'password123'
                },
                description='PostgreSQL database'
            ),
            'mysql': ServiceDefinition(
                name='mysql',
                type='database',
                internal_port=3306,
                volumes=['mysql_data:/var/lib/mysql'],
                environment={
                    'MYSQL_DATABASE': 'app',
                    'MYSQL_USER': 'admin',
                    'MYSQL_PASSWORD': 'password123',
                    'MYSQL_ROOT_PASSWORD': 'root123'
                },
                description='MySQL database'
            ),
            
            # Cache Services
            'redis': ServiceDefinition(
                name='redis',
                type='redis',
                internal_port=6379,
                volumes=['redis_data:/data'],
                description='Redis cache server'
            ),
            'memcached': ServiceDefinition(
                name='memcached',
                type='cache',
                internal_port=11211,
                description='Memcached server'
            ),
            
            # Search Services
            'elasticsearch': ServiceDefinition(
                name='elasticsearch',
                type='elasticsearch',
                internal_port=9200,
                volumes=['elasticsearch_data:/usr/share/elasticsearch/data'],
                environment={
                    'discovery.type': 'single-node',
                    'ES_JAVA_OPTS': '-Xms512m -Xmx512m'
                },
                description='Elasticsearch search engine'
            ),
            
            # Monitoring Services
            'prometheus': ServiceDefinition(
                name='prometheus',
                type='monitoring',
                internal_port=9090,
                volumes=['./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml'],
                description='Prometheus monitoring'
            ),
            'grafana': ServiceDefinition(
                name='grafana',
                type='monitoring', 
                internal_port=3000,
                volumes=['grafana_data:/var/lib/grafana'],
                environment={
                    'GF_SECURITY_ADMIN_PASSWORD': 'admin'
                },
                description='Grafana dashboard'
            ),
            
            # Web Servers
            'nginx': ServiceDefinition(
                name='nginx',
                type='nginx',
                internal_port=80,
                volumes=['./nginx.conf:/etc/nginx/nginx.conf'],
                depends_on=['frontend', 'backend'],
                description='Nginx reverse proxy'
            ),
        }
    
    def _get_default_templates(self) -> Dict[str, ProjectTemplate]:
        """기본 프로젝트 템플릿 반환"""
        return {
            'fullstack-react-fastapi': ProjectTemplate(
                name='fullstack-react-fastapi',
                description='Full-stack application with React frontend and FastAPI backend',
                services=[
                    ServiceDefinition(name='frontend', type='frontend'),
                    ServiceDefinition(name='backend', type='backend'), 
                    ServiceDefinition(name='mongodb', type='mongodb'),
                    ServiceDefinition(name='redis', type='redis')
                ],
                tags=['fullstack', 'react', 'fastapi', 'mongodb']
            ),
            'microservices': ProjectTemplate(
                name='microservices',
                description='Microservices architecture with multiple backend services',
                services=[
                    ServiceDefinition(name='gateway', type='nginx'),
                    ServiceDefinition(name='user-service', type='backend'),
                    ServiceDefinition(name='auth-service', type='backend'),
                    ServiceDefinition(name='data-service', type='backend'),
                    ServiceDefinition(name='database', type='database'),
                    ServiceDefinition(name='cache', type='redis'),
                    ServiceDefinition(name='monitoring', type='monitoring')
                ],
                tags=['microservices', 'distributed', 'scalable']
            ),
            'simple-webapp': ProjectTemplate(
                name='simple-webapp',
                description='Simple web application with frontend and backend',
                services=[
                    ServiceDefinition(name='frontend', type='frontend'),
                    ServiceDefinition(name='backend', type='backend'),
                    ServiceDefinition(name='database', type='database')
                ],
                tags=['simple', 'webapp', 'basic']
            ),
            'data-analytics': ProjectTemplate(
                name='data-analytics',
                description='Data analytics platform with search and visualization',
                services=[
                    ServiceDefinition(name='api', type='backend'),
                    ServiceDefinition(name='elasticsearch', type='elasticsearch'),
                    ServiceDefinition(name='database', type='database'),
                    ServiceDefinition(name='dashboard', type='frontend'),
                    ServiceDefinition(name='monitoring', type='monitoring')
                ],
                tags=['analytics', 'data', 'elasticsearch', 'visualization']
            )
        }
    
    def _load_services(self) -> Dict[str, ServiceDefinition]:
        """서비스 정의 로드"""
        if self.services_file.exists():
            try:
                with open(self.services_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    services = {}
                    for name, service_data in data.items():
                        services[name] = ServiceDefinition(**service_data)
                    return services
            except Exception as e:
                logger.error(f"서비스 정의 로드 실패: {e}")
        
        # 기본 서비스 생성 및 저장
        default_services = self._get_default_services()
        self._save_services(default_services)
        return default_services
    
    def _save_services(self, services: Dict[str, ServiceDefinition]):
        """서비스 정의 저장"""
        try:
            data = {}
            for name, service in services.items():
                data[name] = asdict(service)
            
            with open(self.services_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"서비스 정의 저장 실패: {e}")
    
    def _load_templates(self) -> Dict[str, ProjectTemplate]:
        """프로젝트 템플릿 로드"""
        if self.templates_file.exists():
            try:
                with open(self.templates_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    templates = {}
                    for name, template_data in data.items():
                        services = []
                        for service_data in template_data['services']:
                            services.append(ServiceDefinition(**service_data))
                        
                        templates[name] = ProjectTemplate(
                            name=template_data['name'],
                            description=template_data['description'],
                            services=services,
                            requirements=template_data.get('requirements', []),
                            tags=template_data.get('tags', [])
                        )
                    return templates
            except Exception as e:
                logger.error(f"템플릿 로드 실패: {e}")
        
        # 기본 템플릿 생성 및 저장
        default_templates = self._get_default_templates()
        self._save_templates(default_templates)
        return default_templates
    
    def _save_templates(self, templates: Dict[str, ProjectTemplate]):
        """프로젝트 템플릿 저장"""
        try:
            data = {}
            for name, template in templates.items():
                template_data = asdict(template)
                data[name] = template_data
            
            with open(self.templates_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"템플릿 저장 실패: {e}")
    
    def register_service(self, service: ServiceDefinition) -> bool:
        """새로운 서비스 등록"""
        try:
            self.services[service.name] = service
            self._save_services(self.services)
            logger.info(f"서비스 등록 완료: {service.name}")
            return True
        except Exception as e:
            logger.error(f"서비스 등록 실패: {e}")
            return False
    
    def register_template(self, template: ProjectTemplate) -> bool:
        """새로운 프로젝트 템플릿 등록"""
        try:
            self.templates[template.name] = template
            self._save_templates(self.templates)
            logger.info(f"템플릿 등록 완료: {template.name}")
            return True
        except Exception as e:
            logger.error(f"템플릿 등록 실패: {e}")
            return False
    
    def get_service(self, name: str) -> Optional[ServiceDefinition]:
        """서비스 정의 조회"""
        return self.services.get(name)
    
    def get_template(self, name: str) -> Optional[ProjectTemplate]:
        """프로젝트 템플릿 조회"""
        return self.templates.get(name)
    
    def find_services_by_type(self, service_type: str) -> List[ServiceDefinition]:
        """타입별 서비스 검색"""
        return [service for service in self.services.values() 
                if service.type == service_type]
    
    def find_templates_by_tag(self, tag: str) -> List[ProjectTemplate]:
        """태그별 템플릿 검색"""
        return [template for template in self.templates.values()
                if tag in template.tags]
    
    def detect_project_services(self, project_path: str) -> List[ServiceDefinition]:
        """
        프로젝트 디렉토리에서 서비스 자동 감지
        
        Args:
            project_path: 프로젝트 디렉토리 경로
            
        Returns:
            감지된 서비스 정의 목록
        """
        project_dir = Path(project_path)
        detected_services = []
        
        # Docker Compose 파일 분석
        compose_files = list(project_dir.glob('docker-compose*.yml')) + \
                      list(project_dir.glob('docker-compose*.yaml'))
        
        if compose_files:
            detected_services.extend(self._detect_from_docker_compose(compose_files[0]))
        
        # package.json 분석 (Node.js 프로젝트)
        package_json = project_dir / 'package.json'
        if package_json.exists():
            detected_services.extend(self._detect_from_package_json(package_json))
        
        # requirements.txt 분석 (Python 프로젝트)
        requirements_txt = project_dir / 'requirements.txt'
        if requirements_txt.exists():
            detected_services.extend(self._detect_from_requirements(requirements_txt))
        
        # 디렉토리 구조 분석
        detected_services.extend(self._detect_from_directory_structure(project_dir))
        
        return detected_services
    
    def _detect_from_docker_compose(self, compose_file: Path) -> List[ServiceDefinition]:
        """Docker Compose 파일에서 서비스 감지"""
        services = []
        
        try:
            with open(compose_file, 'r', encoding='utf-8') as f:
                compose_data = yaml.safe_load(f)
            
            if 'services' in compose_data:
                for service_name, service_config in compose_data['services'].items():
                    # 포트 정보 추출
                    ports = service_config.get('ports', [])
                    internal_port = None
                    
                    if ports:
                        # "3000:3000" 형식 파싱
                        port_mapping = str(ports[0])
                        if ':' in port_mapping:
                            internal_port = int(port_mapping.split(':')[-1])
                    
                    # 이미지에서 서비스 타입 추론
                    image = service_config.get('image', '')
                    build = service_config.get('build', '')
                    
                    service_type = self._infer_service_type_from_image(image, build)
                    
                    # 환경 변수 추출
                    environment = service_config.get('environment', {})
                    if isinstance(environment, list):
                        env_dict = {}
                        for env_var in environment:
                            if '=' in env_var:
                                key, value = env_var.split('=', 1)
                                env_dict[key] = value
                        environment = env_dict
                    
                    services.append(ServiceDefinition(
                        name=service_name,
                        type=service_type,
                        internal_port=internal_port,
                        environment=environment,
                        description=f"Detected from docker-compose: {image or build}"
                    ))
                    
        except Exception as e:
            logger.error(f"Docker Compose 파일 분석 실패: {e}")
        
        return services
    
    def _infer_service_type_from_image(self, image: str, build: str) -> str:
        """이미지 이름에서 서비스 타입 추론"""
        image_lower = image.lower()
        build_lower = build.lower()
        
        if any(term in image_lower for term in ['node', 'react', 'vue', 'angular', 'nginx']):
            return 'frontend'
        elif any(term in image_lower for term in ['python', 'fastapi', 'django', 'flask']):
            return 'backend'
        elif 'mongo' in image_lower:
            return 'mongodb'
        elif 'redis' in image_lower:
            return 'redis'
        elif any(term in image_lower for term in ['postgres', 'mysql', 'mariadb']):
            return 'database'
        elif 'elasticsearch' in image_lower:
            return 'elasticsearch'
        elif 'prometheus' in image_lower:
            return 'monitoring'
        elif 'grafana' in image_lower:
            return 'monitoring'
        elif 'nginx' in image_lower:
            return 'nginx'
        else:
            return 'development'
    
    def _detect_from_package_json(self, package_json: Path) -> List[ServiceDefinition]:
        """package.json에서 서비스 감지"""
        services = []
        
        try:
            with open(package_json, 'r', encoding='utf-8') as f:
                package_data = json.load(f)
            
            dependencies = package_data.get('dependencies', {})
            dev_dependencies = package_data.get('devDependencies', {})
            all_deps = {**dependencies, **dev_dependencies}
            
            # React 프로젝트 감지
            if any(dep in all_deps for dep in ['react', 'react-dom', '@types/react']):
                services.append(ServiceDefinition(
                    name='frontend',
                    type='frontend',
                    internal_port=3000,
                    description='React application detected from package.json'
                ))
            
            # Vue 프로젝트 감지  
            elif 'vue' in all_deps:
                services.append(ServiceDefinition(
                    name='frontend',
                    type='frontend',
                    internal_port=8080,
                    description='Vue application detected from package.json'
                ))
            
            # Express 백엔드 감지
            if 'express' in all_deps:
                services.append(ServiceDefinition(
                    name='backend',
                    type='backend',
                    internal_port=3000,
                    description='Express backend detected from package.json'
                ))
                
        except Exception as e:
            logger.error(f"package.json 분석 실패: {e}")
        
        return services
    
    def _detect_from_requirements(self, requirements_txt: Path) -> List[ServiceDefinition]:
        """requirements.txt에서 서비스 감지"""
        services = []
        
        try:
            with open(requirements_txt, 'r', encoding='utf-8') as f:
                requirements = f.read().lower()
            
            # FastAPI 감지
            if 'fastapi' in requirements:
                services.append(ServiceDefinition(
                    name='backend',
                    type='backend',
                    internal_port=8000,
                    description='FastAPI backend detected from requirements.txt'
                ))
            
            # Django 감지
            elif 'django' in requirements:
                services.append(ServiceDefinition(
                    name='backend',
                    type='backend',
                    internal_port=8000,
                    description='Django backend detected from requirements.txt'
                ))
            
            # Flask 감지
            elif 'flask' in requirements:
                services.append(ServiceDefinition(
                    name='backend',
                    type='backend',
                    internal_port=5000,
                    description='Flask backend detected from requirements.txt'
                ))
                
        except Exception as e:
            logger.error(f"requirements.txt 분석 실패: {e}")
        
        return services
    
    def _detect_from_directory_structure(self, project_dir: Path) -> List[ServiceDefinition]:
        """디렉토리 구조에서 서비스 감지"""
        services = []
        
        # 일반적인 디렉토리 이름과 서비스 타입 매핑
        dir_mappings = {
            'frontend': 'frontend',
            'backend': 'backend',
            'api': 'backend',
            'server': 'backend',
            'client': 'frontend',
            'web': 'frontend',
            'ui': 'frontend'
        }
        
        for subdir in project_dir.iterdir():
            if subdir.is_dir() and subdir.name.lower() in dir_mappings:
                service_type = dir_mappings[subdir.name.lower()]
                
                services.append(ServiceDefinition(
                    name=subdir.name,
                    type=service_type,
                    description=f'Detected from directory structure: {subdir.name}'
                ))
        
        return services
    
    def resolve_service_dependencies(self, services: List[ServiceDefinition]) -> List[ServiceDefinition]:
        """서비스 의존성 해석 및 정렬"""
        # 간단한 토폴로지 정렬 구현
        result = []
        visited = set()
        visiting = set()
        
        def visit(service: ServiceDefinition):
            if service.name in visiting:
                raise ValueError(f"순환 의존성 감지: {service.name}")
            
            if service.name in visited:
                return
            
            visiting.add(service.name)
            
            # 의존성 먼저 처리
            for dep_name in service.depends_on:
                dep_service = next((s for s in services if s.name == dep_name), None)
                if dep_service:
                    visit(dep_service)
            
            visiting.remove(service.name)
            visited.add(service.name)
            result.append(service)
        
        for service in services:
            visit(service)
        
        return result
    
    def get_service_suggestions(self, partial_name: str) -> List[str]:
        """서비스 이름 자동완성 제안"""
        suggestions = []
        partial_lower = partial_name.lower()
        
        for service_name in self.services.keys():
            if partial_lower in service_name.lower():
                suggestions.append(service_name)
        
        return sorted(suggestions)
    
    def export_services(self, file_path: str, format: str = 'json'):
        """서비스 정의 내보내기"""
        data = {name: asdict(service) for name, service in self.services.items()}
        
        if format.lower() == 'json':
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        elif format.lower() == 'yaml':
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
        else:
            raise ValueError(f"지원하지 않는 형식: {format}")
    
    def import_services(self, file_path: str, format: str = 'json'):
        """서비스 정의 가져오기"""
        if format.lower() == 'json':
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        elif format.lower() == 'yaml':
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        else:
            raise ValueError(f"지원하지 않는 형식: {format}")
        
        for name, service_data in data.items():
            service = ServiceDefinition(**service_data)
            self.register_service(service)