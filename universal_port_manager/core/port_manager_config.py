"""
포트 매니저 설정 파일 생성기
=========================

환경 파일, 설정 파일, 시작 스크립트 등 생성 담당 모듈
"""

import json
import logging
from typing import Dict, List
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class PortManagerConfig:
    """
    설정 파일 생성 관리자
    
    담당 기능:
    - 환경 파일 생성 (.env, bash, python, json)
    - 시작 스크립트 생성
    - 설정 백업 및 복원
    """
    
    def __init__(self, project_dir: Path, project_name: str):
        """
        설정 관리자 초기화
        
        Args:
            project_dir: 프로젝트 디렉토리
            project_name: 프로젝트 이름
        """
        self.project_dir = project_dir
        self.project_name = project_name
        
        logger.info(f"설정 파일 관리자 초기화: {project_name}")
    
    def generate_env_files(self, allocated_ports: Dict, 
                          formats: List[str] = None) -> Dict[str, str]:
        """
        환경 파일 생성
        
        Args:
            allocated_ports: 할당된 포트 정보
            formats: 생성할 형식 목록 ['docker', 'bash', 'python', 'json']
            
        Returns:
            생성된 파일 경로 딕셔너리
        """
        if formats is None:
            formats = ['docker', 'bash']
        
        generated_files = {}
        
        try:
            # Docker .env 파일
            if 'docker' in formats:
                generated_files['docker'] = self._generate_docker_env(allocated_ports)
            
            # Bash 스크립트
            if 'bash' in formats:
                generated_files['bash'] = self._generate_bash_env(allocated_ports)
            
            # Python 설정
            if 'python' in formats:
                generated_files['python'] = self._generate_python_env(allocated_ports)
            
            # JSON 설정
            if 'json' in formats:
                generated_files['json'] = self._generate_json_env(allocated_ports)
            
            logger.info(f"환경 파일 생성 완료: {list(generated_files.keys())}")
            
        except Exception as e:
            logger.error(f"환경 파일 생성 실패: {e}")
        
        return generated_files
    
    def _generate_docker_env(self, allocated_ports: Dict) -> str:
        """Docker .env 파일 생성"""
        env_path = self.project_dir / '.env'
        
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(f"# {self.project_name} 포트 설정\n")
            f.write(f"# 생성일시: {datetime.now().isoformat()}\n")
            f.write("# 개선된 포트 매니저로 생성됨\n\n")
            
            for service_name, allocated_port in allocated_ports.items():
                var_name = f"{service_name.upper()}_PORT"
                f.write(f"{var_name}={allocated_port.port}\n")
            
            f.write(f"\n# 프로젝트 설정\n")
            f.write(f"PROJECT_NAME={self.project_name}\n")
            f.write(f"COMPOSE_PROJECT_NAME={self.project_name}\n")
            
            # 추가 유용한 환경 변수들
            f.write(f"\n# 추가 설정\n")
            f.write(f"NODE_ENV=development\n")
            f.write(f"PYTHONPATH=/app\n")
        
        logger.info(f"Docker .env 파일 생성: {env_path}")
        return str(env_path)
    
    def _generate_bash_env(self, allocated_ports: Dict) -> str:
        """Bash 환경 스크립트 생성"""
        bash_path = self.project_dir / 'set_ports.sh'
        
        with open(bash_path, 'w', encoding='utf-8') as f:
            f.write("#!/bin/bash\n")
            f.write(f"# {self.project_name} 포트 설정\n")
            f.write(f"# 생성일시: {datetime.now().isoformat()}\n")
            f.write("# 개선된 포트 매니저로 생성됨\n\n")
            
            f.write("# 포트 환경 변수 설정\n")
            for service_name, allocated_port in allocated_ports.items():
                var_name = f"{service_name.upper()}_PORT"
                f.write(f"export {var_name}={allocated_port.port}\n")
            
            f.write(f"\n# 프로젝트 설정\n")
            f.write(f"export PROJECT_NAME={self.project_name}\n")
            f.write(f"export NODE_ENV=development\n")
            f.write(f"export PYTHONPATH=/app\n")
            
            f.write(f"\n# 포트 정보 출력\n")
            f.write(f'echo "📋 {self.project_name} 포트 설정:"\n')
            for service_name, allocated_port in allocated_ports.items():
                f.write(f'echo "  {service_name}: {allocated_port.port}"\n')
        
        # 실행 권한 부여
        try:
            bash_path.chmod(0o755)
        except Exception as e:
            logger.warning(f"실행 권한 설정 실패: {e}")
        
        logger.info(f"Bash 환경 스크립트 생성: {bash_path}")
        return str(bash_path)
    
    def _generate_python_env(self, allocated_ports: Dict) -> str:
        """Python 설정 파일 생성"""
        py_path = self.project_dir / 'port_config.py'
        
        with open(py_path, 'w', encoding='utf-8') as f:
            f.write(f'"""\n{self.project_name} 포트 설정\n')
            f.write(f'생성일시: {datetime.now().isoformat()}\n')
            f.write('개선된 포트 매니저로 생성됨\n"""\n\n')
            
            # 포트 딕셔너리
            f.write("# 포트 설정 딕셔너리\n")
            f.write("PORTS = {\n")
            for service_name, allocated_port in allocated_ports.items():
                f.write(f"    '{service_name}': {allocated_port.port},\n")
            f.write("}\n\n")
            
            # 프로젝트 설정
            f.write("# 프로젝트 설정\n")
            f.write(f"PROJECT_NAME = '{self.project_name}'\n")
            f.write("NODE_ENV = 'development'\n")
            f.write("PYTHONPATH = '/app'\n\n")
            
            # 개별 포트 상수
            f.write("# 개별 포트 상수\n")
            for service_name, allocated_port in allocated_ports.items():
                var_name = f"{service_name.upper()}_PORT"
                f.write(f"{var_name} = {allocated_port.port}\n")
            
            # 유틸리티 함수들
            f.write(f"\n# 유틸리티 함수들\n")
            f.write("def get_service_url(service_name: str, protocol: str = 'http') -> str:\n")
            f.write('    """서비스 URL 생성"""\n')
            f.write("    if service_name in PORTS:\n")
            f.write("        return f'{protocol}://localhost:{PORTS[service_name]}'\n")
            f.write("    return None\n\n")
            
            f.write("def get_all_urls() -> dict:\n")
            f.write('    """모든 서비스 URL 반환"""\n')
            f.write("    return {name: get_service_url(name) for name in PORTS.keys()}\n")
        
        logger.info(f"Python 설정 파일 생성: {py_path}")
        return str(py_path)
    
    def _generate_json_env(self, allocated_ports: Dict) -> str:
        """JSON 설정 파일 생성"""
        json_path = self.project_dir / 'ports.json'
        
        config_data = {
            'project_name': self.project_name,
            'generated_at': datetime.now().isoformat(),
            'generator': 'improved_port_manager',
            'ports': {},
            'urls': {},
            'metadata': {
                'total_services': len(allocated_ports),
                'port_range': {
                    'min': min(p.port for p in allocated_ports.values()) if allocated_ports else 0,
                    'max': max(p.port for p in allocated_ports.values()) if allocated_ports else 0
                }
            }
        }
        
        # 포트 정보 추가
        for service_name, allocated_port in allocated_ports.items():
            config_data['ports'][service_name] = {
                'port': allocated_port.port,
                'service_type': allocated_port.service_type,
                'allocated_at': allocated_port.allocated_at,
                'last_used': allocated_port.last_used,
                'conflict_resolution': allocated_port.conflict_resolution
            }
            
            # URL 생성
            if allocated_port.service_type in ['frontend', 'backend', 'nginx', 'monitoring']:
                config_data['urls'][service_name] = f"http://localhost:{allocated_port.port}"
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"JSON 설정 파일 생성: {json_path}")
        return str(json_path)
    
    def generate_start_script(self, allocated_ports: Dict) -> bool:
        """시작 스크립트 생성"""
        try:
            script_path = self.project_dir / 'start.sh'
            
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write("#!/bin/bash\n")
                f.write(f"# {self.project_name} 시작 스크립트\n")
                f.write(f"# 생성일시: {datetime.now().isoformat()}\n")
                f.write("# 개선된 포트 매니저로 생성됨\n\n")
                
                f.write("echo '🚀 개선된 포트 관리자로 서비스 시작'\n")
                f.write("echo '========================================'\n\n")
                
                # 포트 정보 표시
                f.write("echo '📋 할당된 포트:'\n")
                for service_name, allocated_port in allocated_ports.items():
                    f.write(f"echo '  {service_name}: {allocated_port.port}'\n")
                
                f.write("\necho ''\n")
                
                # 환경 변수 로드
                f.write("echo '⚙️  환경 변수 로드 중...'\n")
                f.write("if [ -f './set_ports.sh' ]; then\n")
                f.write("    source ./set_ports.sh\n")
                f.write("    echo '✅ 포트 환경 변수 로드 완료'\n")
                f.write("else\n")
                f.write("    echo '⚠️  set_ports.sh 파일을 찾을 수 없음'\n")
                f.write("fi\n\n")
                
                # Docker Compose 시작
                f.write("echo '⏳ Docker Compose 시작 중...'\n")
                f.write("if [ -f 'docker-compose.yml' ]; then\n")
                f.write("    docker-compose down\n")
                f.write("    docker-compose up -d\n")
                f.write("    echo ''\n")
                f.write("    echo '✅ 서비스 시작 완료!'\n")
                f.write("    echo ''\n")
                f.write("    echo '📊 컨테이너 상태:'\n")
                f.write("    docker-compose ps\n")
                f.write("else\n")
                f.write("    echo '⚠️  docker-compose.yml 파일을 찾을 수 없음'\n")
                f.write("fi\n\n")
                
                # 서비스 URL 표시
                f.write("echo ''\n")
                f.write("echo '🌐 서비스 URL:'\n")
                for service_name, allocated_port in allocated_ports.items():
                    if allocated_port.service_type in ['frontend', 'backend', 'nginx', 'monitoring']:
                        f.write(f"echo '  {service_name}: http://localhost:{allocated_port.port}'\n")
                
                f.write("\necho ''\n")
                f.write("echo '🎉 시작 완료! 위 URL로 서비스에 접속할 수 있습니다.'\n")
            
            # 실행 권한 부여
            try:
                script_path.chmod(0o755)
            except Exception as e:
                logger.warning(f"실행 권한 설정 실패: {e}")
            
            logger.info(f"시작 스크립트 생성: {script_path}")
            return True
            
        except Exception as e:
            logger.error(f"시작 스크립트 생성 실패: {e}")
            return False
    
    def backup_config(self, backup_name: str = None) -> str:
        """설정 파일 백업"""
        if backup_name is None:
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        backup_dir = self.project_dir / '.port-manager' / 'backups' / backup_name
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 백업할 파일들
        config_files = [
            '.env',
            'set_ports.sh',
            'port_config.py',
            'ports.json',
            'start.sh',
            'docker-compose.yml',
            'docker-compose.override.yml'
        ]
        
        backed_up_files = []
        for file_name in config_files:
            source_file = self.project_dir / file_name
            if source_file.exists():
                dest_file = backup_dir / file_name
                dest_file.write_text(source_file.read_text(encoding='utf-8'), encoding='utf-8')
                backed_up_files.append(file_name)
        
        # 백업 메타데이터 생성
        metadata = {
            'backup_name': backup_name,
            'created_at': datetime.now().isoformat(),
            'project_name': self.project_name,
            'backed_up_files': backed_up_files
        }
        
        metadata_file = backup_dir / 'backup_metadata.json'
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        logger.info(f"설정 백업 완료: {backup_dir}")
        return str(backup_dir)
    
    def restore_config(self, backup_name: str) -> bool:
        """설정 파일 복원"""
        backup_dir = self.project_dir / '.port-manager' / 'backups' / backup_name
        
        if not backup_dir.exists():
            logger.error(f"백업을 찾을 수 없음: {backup_name}")
            return False
        
        metadata_file = backup_dir / 'backup_metadata.json'
        if not metadata_file.exists():
            logger.error(f"백업 메타데이터를 찾을 수 없음: {backup_name}")
            return False
        
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            restored_files = []
            for file_name in metadata['backed_up_files']:
                source_file = backup_dir / file_name
                dest_file = self.project_dir / file_name
                
                if source_file.exists():
                    dest_file.write_text(source_file.read_text(encoding='utf-8'), encoding='utf-8')
                    restored_files.append(file_name)
            
            logger.info(f"설정 복원 완료: {len(restored_files)}개 파일")
            return True
            
        except Exception as e:
            logger.error(f"설정 복원 실패: {e}")
            return False
    
    def list_backups(self) -> List[Dict]:
        """백업 목록 조회"""
        backups_dir = self.project_dir / '.port-manager' / 'backups'
        backups = []
        
        if not backups_dir.exists():
            return backups
        
        for backup_dir in backups_dir.iterdir():
            if backup_dir.is_dir():
                metadata_file = backup_dir / 'backup_metadata.json'
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        backups.append(metadata)
                    except Exception as e:
                        logger.warning(f"백업 메타데이터 읽기 실패: {e}")
        
        return sorted(backups, key=lambda x: x['created_at'], reverse=True)