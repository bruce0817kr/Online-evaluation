"""
개선된 서비스 레지스트리 모듈
===========================

포트 충돌 방지와 현실적인 서비스 정의를 적용한 서비스 레지스트리
YAML 의존성을 선택적으로 처리하여 안정성 향상
"""

import json
from typing import Dict, List, Optional, Set, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

# 선택적 YAML 의존성
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    yaml = None
    print("⚠️ PyYAML 없음 - YAML 파일 처리 기능 비활성화")

logger = logging.getLogger(__name__)

@dataclass
class ServiceDefinition:
    """서비스 정의 (개선된 버전)"""
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
    # 추가된 필드들
    priority: int = 1  # 서비스 우선순위 (낮을수록 중요)
    port_alternatives: List[int] = None  # 대안 포트 목록
    requires_privileged: bool = False  # 특권 포트 필요 여부
    
    def __post_init__(self):
        if self.environment is None:
            self.environment = {}
        if self.volumes is None:
            self.volumes = []
        if self.depends_on is None:
            self.depends_on = []
        if self.port_alternatives is None:
            self.port_alternatives = []

@dataclass
class ProjectTemplate:
    """프로젝트 템플릿 (개선된 버전)"""
    name: str
    description: str
    services: List[ServiceDefinition]
    requirements: List[str] = None
    tags: List[str] = None
    # 추가된 필드들
    architecture_type: str = "monolith"  # monolith, microservices, serverless
    complexity_level: str = "simple"  # simple, medium, complex
    recommended_resources: Dict[str, str] = None  # CPU, 메모리 권장 사항
    
    def __post_init__(self):
        if self.requirements is None:
            self.requirements = []
        if self.tags is None:
            self.tags = []
        if self.recommended_resources is None:
            self.recommended_resources = {}

class ImprovedServiceRegistry:
    """
    개선된 서비스 레지스트리
    
    주요 개선사항:
    - 포트 충돌 방지를 위한 현실적인 포트 설정
    - YAML 의존성을 선택적으로 처리
    - 서비스 우선순위 및 대안 포트 지원
    - 더 다양한 프로젝트 템플릿
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
        
        logger.info(f"개선된 서비스 레지스트리 초기화 완료 (YAML: {'활성화' if YAML_AVAILABLE else '비활성화'})")
    
    def _get_default_services(self) -> Dict[str, ServiceDefinition]:
        """포트 충돌을 고려한 현실적인 기본 서비스 정의"""
        return {
            # Frontend Services (포트 충돌 방지)
            'react': ServiceDefinition(
                name='react',
                type='frontend',
                internal_port=3001,  # 3000 대신 3001
                port_alternatives=[3002, 3003, 3004],
                environment={'NODE_ENV': 'development'},
                description='React development server',
                priority=1
            ),
            'vue': ServiceDefinition(
                name='vue', 
                type='frontend',
                internal_port=8081,  # 8080 대신 8081 (충돌 방지)
                port_alternatives=[8082, 8083, 8084],
                environment={'NODE_ENV': 'development'},
                description='Vue.js development server',
                priority=1
            ),
            'angular': ServiceDefinition(
                name='angular',
                type='frontend', 
                internal_port=4200,  # 기본값 유지 (충돌 가능성 낮음)
                port_alternatives=[4201, 4202, 4203],
                environment={'NODE_ENV': 'development'},
                description='Angular development server',
                priority=1
            ),
            'nextjs': ServiceDefinition(
                name='nextjs',
                type='frontend',
                internal_port=3005,  # React와 충돌 방지
                port_alternatives=[3006, 3007, 3008],
                environment={'NODE_ENV': 'development'},
                description='Next.js application',
                priority=1
            ),
            'svelte': ServiceDefinition(
                name='svelte',
                type='frontend',
                internal_port=5000,  # Svelte 기본값
                port_alternatives=[5001, 5002, 5003],
                environment={'NODE_ENV': 'development'},
                description='Svelte application',
                priority=1
            ),
            
            # Backend Services (포트 충돌 방지)
            'fastapi': ServiceDefinition(
                name='fastapi',
                type='backend',
                internal_port=8001,  # 8000 대신 8001
                port_alternatives=[8002, 8003, 8004],
                environment={'PYTHONPATH': '/app'},
                health_check='/health',
                description='FastAPI backend server',
                priority=1
            ),
            'express': ServiceDefinition(
                name='express',
                type='backend',
                internal_port=3010,  # frontend와 충돌 방지
                port_alternatives=[3011, 3012, 3013],
                environment={'NODE_ENV': 'development'},
                health_check='/health',
                description='Express.js backend server',
                priority=1
            ),
            'django': ServiceDefinition(
                name='django',
                type='backend',
                internal_port=8005,  # FastAPI와 충돌 방지
                port_alternatives=[8006, 8007, 8008],
                environment={'DJANGO_SETTINGS_MODULE': 'settings'},
                health_check='/health',
                description='Django backend server',
                priority=1
            ),
            'flask': ServiceDefinition(
                name='flask',
                type='backend',
                internal_port=5010,  # Svelte와 충돌 방지
                port_alternatives=[5011, 5012, 5013],
                environment={'FLASK_ENV': 'development'},
                health_check='/health',
                description='Flask backend server',
                priority=1
            ),
            'nestjs': ServiceDefinition(
                name='nestjs',
                type='backend',
                internal_port=3020,
                port_alternatives=[3021, 3022, 3023],
                environment={'NODE_ENV': 'development'},
                health_check='/health',
                description='NestJS backend server',
                priority=1
            ),
            
            # Database Services (기존 포트 회피)
            'mongodb': ServiceDefinition(
                name='mongodb',
                type='mongodb',
                internal_port=27018,  # 27017 대신 27018
                port_alternatives=[27019, 27020, 27021],
                volumes=['mongodb_data:/data/db'],
                environment={
                    'MONGO_INITDB_ROOT_USERNAME': 'admin',
                    'MONGO_INITDB_ROOT_PASSWORD': 'password123'
                },
                description='MongoDB database',
                priority=2
            ),
            'postgresql': ServiceDefinition(
                name='postgresql',
                type='database',
                internal_port=5433,  # 5432 대신 5433
                port_alternatives=[5434, 5435, 5436],
                volumes=['postgres_data:/var/lib/postgresql/data'],
                environment={
                    'POSTGRES_DB': 'app',
                    'POSTGRES_USER': 'admin',
                    'POSTGRES_PASSWORD': 'password123'
                },
                description='PostgreSQL database',
                priority=2
            ),
            'mysql': ServiceDefinition(
                name='mysql',
                type='database',
                internal_port=3307,  # 3306 대신 3307
                port_alternatives=[3308, 3309, 3310],
                volumes=['mysql_data:/var/lib/mysql'],
                environment={
                    'MYSQL_DATABASE': 'app',
                    'MYSQL_USER': 'admin',
                    'MYSQL_PASSWORD': 'password123',
                    'MYSQL_ROOT_PASSWORD': 'root123'
                },
                description='MySQL database',
                priority=2
            ),
            
            # Cache Services (기존 포트 회피)
            'redis': ServiceDefinition(
                name='redis',
                type='redis',
                internal_port=6381,  # 6379 대신 6381
                port_alternatives=[6382, 6383, 6384],
                volumes=['redis_data:/data'],
                description='Redis cache server',
                priority=2
            ),
            'memcached': ServiceDefinition(
                name='memcached',
                type='cache',
                internal_port=11212,  # 11211 대신 11212
                port_alternatives=[11213, 11214, 11215],
                description='Memcached server',
                priority=3
            ),
            
            # Search Services
            'elasticsearch': ServiceDefinition(
                name='elasticsearch',
                type='elasticsearch',
                internal_port=9201,  # 9200 대신 9201
                port_alternatives=[9202, 9203, 9204],
                volumes=['elasticsearch_data:/usr/share/elasticsearch/data'],
                environment={
                    'discovery.type': 'single-node',
                    'ES_JAVA_OPTS': '-Xms512m -Xmx512m'
                },
                description='Elasticsearch search engine',
                priority=3
            ),
            
            # Monitoring Services (포트 충돌 방지)
            'prometheus': ServiceDefinition(
                name='prometheus',
                type='monitoring',
                internal_port=9091,  # 9090 대신 9091
                port_alternatives=[9092, 9093, 9094],
                volumes=['./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml'],
                description='Prometheus monitoring',
                priority=3
            ),
            'grafana': ServiceDefinition(
                name='grafana',
                type='monitoring', 
                internal_port=3100,  # 3000 대신 3100 (React와 충돌 방지)
                port_alternatives=[3101, 3102, 3103],
                volumes=['grafana_data:/var/lib/grafana'],
                environment={
                    'GF_SECURITY_ADMIN_PASSWORD': 'admin'
                },
                description='Grafana dashboard',
                priority=3
            ),
            'kibana': ServiceDefinition(
                name='kibana',
                type='monitoring',
                internal_port=5601,  # 기본값 유지
                port_alternatives=[5602, 5603, 5604],
                depends_on=['elasticsearch'],
                description='Kibana visualization',
                priority=3
            ),
            
            # Web Servers
            'nginx': ServiceDefinition(
                name='nginx',
                type='nginx',
                internal_port=8090,  # 80 대신 8090 (비특권 포트)
                port_alternatives=[8091, 8092, 8093],
                volumes=['./nginx.conf:/etc/nginx/nginx.conf'],
                depends_on=['frontend', 'backend'],
                description='Nginx reverse proxy',
                priority=2
            ),
            'apache': ServiceDefinition(
                name='apache',
                type='nginx',  # nginx 타입으로 분류
                internal_port=8095,
                port_alternatives=[8096, 8097, 8098],
                description='Apache HTTP server',
                priority=2
            ),
            
            # Message Queues
            'rabbitmq': ServiceDefinition(
                name='rabbitmq',
                type='queue',
                internal_port=5672,
                port_alternatives=[15672, 25672, 35672],  # 관리 UI 포트도 포함
                volumes=['rabbitmq_data:/var/lib/rabbitmq'],
                environment={
                    'RABBITMQ_DEFAULT_USER': 'admin',
                    'RABBITMQ_DEFAULT_PASS': 'password123'
                },
                description='RabbitMQ message broker',
                priority=3
            ),
            
            # Development Tools
            'pgadmin': ServiceDefinition(
                name='pgadmin',
                type='development',
                internal_port=5050,
                port_alternatives=[5051, 5052, 5053],
                depends_on=['postgresql'],
                environment={
                    'PGADMIN_DEFAULT_EMAIL': 'admin@example.com',
                    'PGADMIN_DEFAULT_PASSWORD': 'admin'
                },
                description='PostgreSQL administration tool',
                priority=4
            ),
            'mongo-express': ServiceDefinition(
                name='mongo-express',
                type='development',
                internal_port=8088,
                port_alternatives=[8089, 8087, 8086],
                depends_on=['mongodb'],
                environment={
                    'ME_CONFIG_MONGODB_ADMINUSERNAME': 'admin',
                    'ME_CONFIG_MONGODB_ADMINPASSWORD': 'password123'
                },
                description='MongoDB administration interface',
                priority=4
            )
        }
    
    def _get_default_templates(self) -> Dict[str, ProjectTemplate]:
        """포트 충돌을 고려한 현실적인 프로젝트 템플릿"""
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
                tags=['fullstack', 'react', 'fastapi', 'mongodb'],
                architecture_type='monolith',
                complexity_level='medium',
                recommended_resources={'cpu': '2 cores', 'memory': '4GB'}
            ),
            'microservices-advanced': ProjectTemplate(
                name='microservices-advanced',
                description='Advanced microservices architecture with complete observability',
                services=[
                    ServiceDefinition(name='gateway', type='nginx'),
                    ServiceDefinition(name='user-service', type='backend'),
                    ServiceDefinition(name='auth-service', type='backend'),
                    ServiceDefinition(name='data-service', type='backend'),
                    ServiceDefinition(name='notification-service', type='backend'),
                    ServiceDefinition(name='database', type='database'),
                    ServiceDefinition(name='cache', type='redis'),
                    ServiceDefinition(name='queue', type='queue'),
                    ServiceDefinition(name='monitoring', type='monitoring'),
                    ServiceDefinition(name='metrics', type='monitoring'),
                    ServiceDefinition(name='search', type='elasticsearch')
                ],
                tags=['microservices', 'distributed', 'scalable', 'observability'],
                architecture_type='microservices',
                complexity_level='complex',
                recommended_resources={'cpu': '8 cores', 'memory': '16GB'}
            ),
            'simple-webapp': ProjectTemplate(
                name='simple-webapp',
                description='Simple web application with frontend and backend',
                services=[
                    ServiceDefinition(name='frontend', type='frontend'),
                    ServiceDefinition(name='backend', type='backend'),
                    ServiceDefinition(name='database', type='database')
                ],
                tags=['simple', 'webapp', 'basic'],
                architecture_type='monolith',
                complexity_level='simple',
                recommended_resources={'cpu': '1 core', 'memory': '2GB'}
            ),
            'data-analytics': ProjectTemplate(
                name='data-analytics',
                description='Data analytics platform with search and visualization',
                services=[
                    ServiceDefinition(name='api', type='backend'),
                    ServiceDefinition(name='elasticsearch', type='elasticsearch'),
                    ServiceDefinition(name='database', type='database'),
                    ServiceDefinition(name='dashboard', type='frontend'),
                    ServiceDefinition(name='monitoring', type='monitoring'),
                    ServiceDefinition(name='kibana', type='monitoring')
                ],
                tags=['analytics', 'data', 'elasticsearch', 'visualization'],
                architecture_type='monolith',
                complexity_level='medium',
                recommended_resources={'cpu': '4 cores', 'memory': '8GB'}
            ),
            'development-environment': ProjectTemplate(
                name='development-environment',
                description='Complete development environment with admin tools',
                services=[
                    ServiceDefinition(name='frontend', type='frontend'),
                    ServiceDefinition(name='backend', type='backend'),
                    ServiceDefinition(name='postgresql', type='database'),
                    ServiceDefinition(name='mongodb', type='mongodb'),
                    ServiceDefinition(name='redis', type='redis'),
                    ServiceDefinition(name='pgadmin', type='development'),
                    ServiceDefinition(name='mongo-express', type='development'),
                    ServiceDefinition(name='monitoring', type='monitoring')
                ],
                tags=['development', 'admin-tools', 'multi-database'],
                architecture_type='monolith',
                complexity_level='medium',
                recommended_resources={'cpu': '4 cores', 'memory': '6GB'}
            ),
            'api-gateway-pattern': ProjectTemplate(
                name='api-gateway-pattern',
                description='API Gateway pattern with multiple backend services',
                services=[
                    ServiceDefinition(name='gateway', type='nginx'),
                    ServiceDefinition(name='auth-api', type='backend'),
                    ServiceDefinition(name='user-api', type='backend'),
                    ServiceDefinition(name='product-api', type='backend'),
                    ServiceDefinition(name='order-api', type='backend'),
                    ServiceDefinition(name='database-auth', type='database'),
                    ServiceDefinition(name='database-main', type='database'),
                    ServiceDefinition(name='cache-session', type='redis'),
                    ServiceDefinition(name='cache-data', type='redis')
                ],
                tags=['api-gateway', 'pattern', 'multiple-services'],
                architecture_type='microservices',
                complexity_level='complex',
                recommended_resources={'cpu': '6 cores', 'memory': '12GB'}
            )
        }
    
    def _load_services(self) -> Dict[str, ServiceDefinition]:
        """서비스 정의 로드"""
        if self.services_file.exists():
            try:
                with open(self.services_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    services = {}
                    for name, info in data.items():
                        services[name] = ServiceDefinition(**info)
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
                    for name, info in data.items():
                        # services 리스트를 ServiceDefinition 객체로 변환
                        services = []
                        for service_data in info['services']:
                            services.append(ServiceDefinition(**service_data))
                        info['services'] = services
                        templates[name] = ProjectTemplate(**info)
                    return templates
            except Exception as e:
                logger.error(f"프로젝트 템플릿 로드 실패: {e}")
        
        # 기본 템플릿 생성 및 저장
        default_templates = self._get_default_templates()
        self._save_templates(default_templates)
        return default_templates
    
    def _save_templates(self, templates: Dict[str, ProjectTemplate]):
        """프로젝트 템플릿 저장"""
        try:
            data = {}
            for name, template in templates.items():
                data[name] = asdict(template)
            
            with open(self.templates_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"프로젝트 템플릿 저장 실패: {e}")
    
    def get_service_by_name(self, name: str) -> Optional[ServiceDefinition]:
        """이름으로 서비스 정의 조회"""
        return self.services.get(name)
    
    def get_services_by_type(self, service_type: str) -> List[ServiceDefinition]:
        """타입으로 서비스 목록 조회"""
        return [service for service in self.services.values() 
                if service.type == service_type]
    
    def get_template_by_name(self, name: str) -> Optional[ProjectTemplate]:
        """이름으로 프로젝트 템플릿 조회"""
        return self.templates.get(name)
    
    def get_templates_by_tag(self, tag: str) -> List[ProjectTemplate]:
        """태그로 프로젝트 템플릿 목록 조회"""
        return [template for template in self.templates.values() 
                if tag in template.tags]
    
    def suggest_services_for_stack(self, stack_keywords: List[str]) -> List[ServiceDefinition]:
        """기술 스택 키워드에 따른 서비스 추천"""
        suggested = []
        
        # 키워드 매핑
        keyword_mappings = {
            'react': ['react', 'nodejs'],
            'vue': ['vue', 'nodejs'],
            'angular': ['angular', 'nodejs'],
            'django': ['django', 'postgresql'],
            'fastapi': ['fastapi', 'postgresql', 'redis'],
            'flask': ['flask', 'postgresql'],
            'express': ['express', 'mongodb'],
            'mongodb': ['mongodb'],
            'postgresql': ['postgresql'],
            'mysql': ['mysql'],
            'redis': ['redis'],
            'elasticsearch': ['elasticsearch', 'kibana'],
            'microservices': ['nginx', 'monitoring'],
        }
        
        service_names = set()
        for keyword in stack_keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in keyword_mappings:
                service_names.update(keyword_mappings[keyword_lower])
        
        for service_name in service_names:
            service = self.get_service_by_name(service_name)
            if service:
                suggested.append(service)
        
        return suggested
    
    def validate_service_dependencies(self, services: List[ServiceDefinition]) -> Dict[str, List[str]]:
        """서비스 의존성 검증"""
        issues = {}
        service_names = [s.name for s in services]
        
        for service in services:
            missing_deps = []
            for dep in service.depends_on:
                if dep not in service_names:
                    missing_deps.append(dep)
            
            if missing_deps:
                issues[service.name] = missing_deps
        
        return issues
    
    def detect_port_conflicts(self, services: List[ServiceDefinition]) -> Dict[int, List[str]]:
        """서비스 간 포트 충돌 감지"""
        port_map = {}
        conflicts = {}
        
        for service in services:
            if service.internal_port:
                port = service.internal_port
                if port not in port_map:
                    port_map[port] = []
                port_map[port].append(service.name)
        
        for port, service_names in port_map.items():
            if len(service_names) > 1:
                conflicts[port] = service_names
        
        return conflicts
    
    def resolve_port_conflicts(self, services: List[ServiceDefinition]) -> List[ServiceDefinition]:
        """포트 충돌 자동 해결"""
        conflicts = self.detect_port_conflicts(services)
        resolved_services = []
        
        for service in services:
            if (service.internal_port and 
                service.internal_port in conflicts and 
                len(conflicts[service.internal_port]) > 1):
                
                # 대안 포트 사용
                if service.port_alternatives:
                    for alt_port in service.port_alternatives:
                        if not any(s.internal_port == alt_port for s in services):
                            service.internal_port = alt_port
                            logger.info(f"서비스 '{service.name}' 포트를 {alt_port}로 변경")
                            break
            
            resolved_services.append(service)
        
        return resolved_services
    
    def export_docker_compose(self, services: List[ServiceDefinition], 
                             output_file: str = None) -> Optional[str]:
        """Docker Compose 파일 생성"""
        if not YAML_AVAILABLE:
            logger.warning("PyYAML이 없어 Docker Compose 생성 불가")
            return None
        
        compose_data = {
            'version': '3.8',
            'services': {},
            'volumes': {},
            'networks': {
                'app-network': {
                    'driver': 'bridge'
                }
            }
        }
        
        # 볼륨 수집
        volumes = set()
        
        for service in services:
            service_config = {
                'networks': ['app-network']
            }
            
            if service.internal_port:
                service_config['ports'] = [f"{service.port or service.internal_port}:{service.internal_port}"]
            
            if service.environment:
                service_config['environment'] = service.environment
            
            if service.volumes:
                service_config['volumes'] = service.volumes
                # 명명된 볼륨 수집
                for vol in service.volumes:
                    if ':' in vol and not vol.startswith('./') and not vol.startswith('/'):
                        vol_name = vol.split(':')[0]
                        volumes.add(vol_name)
            
            if service.depends_on:
                service_config['depends_on'] = service.depends_on
            
            if service.health_check:
                service_config['healthcheck'] = {
                    'test': f"curl -f http://localhost:{service.internal_port}{service.health_check} || exit 1",
                    'interval': '30s',
                    'timeout': '10s',
                    'retries': 3
                }
            
            compose_data['services'][service.name] = service_config
        
        # 볼륨 정의 추가
        for volume in volumes:
            compose_data['volumes'][volume] = {}
        
        try:
            yaml_content = yaml.dump(compose_data, default_flow_style=False, indent=2)
            
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(yaml_content)
                logger.info(f"Docker Compose 파일 생성: {output_file}")
            
            return yaml_content
            
        except Exception as e:
            logger.error(f"Docker Compose 생성 실패: {e}")
            return None
    
    def get_registry_stats(self) -> Dict:
        """레지스트리 통계 정보"""
        service_types = {}
        for service in self.services.values():
            if service.type not in service_types:
                service_types[service.type] = 0
            service_types[service.type] += 1
        
        template_types = {}
        for template in self.templates.values():
            arch_type = template.architecture_type
            if arch_type not in template_types:
                template_types[arch_type] = 0
            template_types[arch_type] += 1
        
        return {
            'total_services': len(self.services),
            'total_templates': len(self.templates),
            'service_types': service_types,
            'template_architectures': template_types,
            'yaml_support': YAML_AVAILABLE
        }

# 기존 ServiceRegistry와의 호환성을 위한 별칭
ServiceRegistry = ImprovedServiceRegistry