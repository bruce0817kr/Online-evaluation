"""
Universal Port Manager (UPM)
=============================

범용 포트 매니저 모듈 - 여러 프로젝트 간 포트 충돌 방지 및 자동 할당

주요 기능:
- 지능형 포트 스캔 및 할당
- 프로젝트별 포트 그룹 관리
- Docker 컨테이너 포트 충돌 방지
- 자동 설정 파일 생성 (docker-compose, .env 등)
- 다른 프로젝트에 쉽게 통합 가능

사용법:
    from universal_port_manager import PortManager
    
    pm = PortManager(project_name="my-project")
    ports = pm.allocate_service_ports(['frontend', 'backend', 'mongodb'])
    pm.generate_docker_compose()
    pm.generate_env_files()

Author: AI Assistant
Version: 1.0.0
License: MIT
"""

__version__ = "1.0.0"
__author__ = "AI Assistant"

# 선택적 임포트 - 의존성이 없을 때도 모듈을 로드할 수 있도록 함
try:
    from .core.port_manager import PortManager
    from .core.service_registry import ServiceRegistry  
    from .core.port_scanner import PortScanner
    from .core.port_allocator import PortAllocator
    __all__ = ['PortManager', 'ServiceRegistry', 'PortScanner', 'PortAllocator']
except ImportError:
    # 의존성이 없을 때는 빈 리스트
    __all__ = []