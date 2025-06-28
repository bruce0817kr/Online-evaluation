"""
배포 관리 API 엔드포인트
포트 매니저와 원클릭 배포 기능을 제공하는 REST API
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import List, Dict, Optional
import logging
import asyncio
import subprocess
from pydantic import BaseModel, Field
from datetime import datetime

from models import User
from security import get_current_user
from port_manager_service import port_manager
from deployment_manager import deployment_manager

async def get_container_status(container_name: str) -> Dict[str, any]:
    """Docker 컨테이너 상태 확인 with enhanced error handling"""
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            # 컨테이너 실행 상태 확인
            result = subprocess.run(
                ['docker', 'inspect', container_name, '--format', '{{.State.Running}}:{{.State.Status}}:{{.State.Health.Status}}'],
                capture_output=True,
                text=True,
                timeout=15  # Increased timeout
            )
            
            if result.returncode == 0:
                output = result.stdout.strip()
                parts = output.split(':')
                running = parts[0].lower() == 'true'
                status = parts[1] if len(parts) > 1 else 'unknown'
                health = parts[2] if len(parts) > 2 and parts[2] != '<no value>' else None
                
                # 헬스체크가 있으면 healthy 상태 확인, 없으면 running 상태를 healthy로 간주
                healthy = health == 'healthy' if health else running
                
                return {
                    'running': running,
                    'healthy': healthy,
                    'status': status,
                    'health': health,
                    'last_check': datetime.utcnow().isoformat()
                }
            elif result.returncode == 1 and 'No such object' in result.stderr:
                return {
                    'running': False,
                    'healthy': False,
                    'status': 'not_found',
                    'health': None,
                    'error': f'Container {container_name} not found'
                }
            else:
                raise subprocess.CalledProcessError(result.returncode, result.args, result.stderr)
                
        except subprocess.TimeoutExpired:
            logger.warning(f"Docker inspect timeout for {container_name}, attempt {attempt + 1}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
                continue
            else:
                return {
                    'running': False,
                    'healthy': False,
                    'status': 'timeout',
                    'health': None,
                    'error': 'Docker command timeout'
                }
        except subprocess.CalledProcessError as e:
            logger.error(f"Docker command failed for {container_name}: {e.stderr}")
            return {
                'running': False,
                'healthy': False,
                'status': 'docker_error',
                'health': None,
                'error': f'Docker command failed: {e.stderr}'
            }
        except Exception as e:
            logger.error(f"Unexpected error checking {container_name}: {e}")
            return {
                'running': False,
                'healthy': False,
                'status': 'error',
                'health': None,
                'error': str(e)
            }

logger = logging.getLogger(__name__)

# 배포 관리 라우터 생성
deployment_router = APIRouter(prefix="/api/deployment", tags=["배포 관리"])

# 요청/응답 모델
class PortAllocationRequest(BaseModel):
    """포트 할당 요청"""
    service_name: str = Field(..., description="서비스 이름")
    preferred_port: Optional[int] = Field(None, description="선호 포트 번호")

class DeploymentRequest(BaseModel):
    """배포 요청"""
    environment: str = Field("development", description="배포 환경 (development, staging, production)")
    force: bool = Field(False, description="전제 조건 무시 여부")

class ServiceStatusResponse(BaseModel):
    """서비스 상태 응답"""
    name: str
    port: Optional[int]
    url: Optional[str]
    running: bool
    healthy: bool
    container_status: Optional[str] = None

def check_admin_role(user: User):
    """관리자 권한 확인"""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다"
        )

@deployment_router.get("/ports/status")
async def get_port_status(current_user: User = Depends(get_current_user)):
    """현재 포트 할당 상태 조회"""
    try:
        check_admin_role(current_user)
        
        status_info = port_manager.get_port_status()
        
        return {
            "success": True,
            "port_status": status_info,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"포트 상태 조회 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="포트 상태 조회 중 오류가 발생했습니다"
        )

@deployment_router.get("/ports/services")
async def get_service_ports(current_user: User = Depends(get_current_user)):
    """서비스별 포트 설정 조회"""
    try:
        check_admin_role(current_user)
        
        service_config = port_manager.get_service_config()
        
        return {
            "success": True,
            "services": service_config,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"서비스 포트 조회 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="서비스 포트 조회 중 오류가 발생했습니다"
        )

@deployment_router.post("/ports/allocate")
async def allocate_port(
    request: PortAllocationRequest,
    current_user: User = Depends(get_current_user)
):
    """서비스에 포트 할당"""
    try:
        check_admin_role(current_user)
        
        allocated_port = port_manager.allocate_port(
            request.service_name,
            request.preferred_port
        )
        
        if not allocated_port:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="사용 가능한 포트가 없습니다"
            )
        
        logger.info(f"포트 할당: {request.service_name} -> {allocated_port}", extra={
            'user_id': current_user.id,
            'service': request.service_name,
            'port': allocated_port
        })
        
        return {
            "success": True,
            "service_name": request.service_name,
            "allocated_port": allocated_port,
            "message": f"{request.service_name}에 포트 {allocated_port}이(가) 할당되었습니다"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"포트 할당 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="포트 할당 중 오류가 발생했습니다"
        )

@deployment_router.delete("/ports/{service_name}")
async def release_port(
    service_name: str,
    current_user: User = Depends(get_current_user)
):
    """서비스의 포트 할당 해제"""
    try:
        check_admin_role(current_user)
        
        port_manager.release_port(service_name)
        
        logger.info(f"포트 할당 해제: {service_name}", extra={
            'user_id': current_user.id,
            'service': service_name
        })
        
        return {
            "success": True,
            "message": f"{service_name}의 포트 할당이 해제되었습니다"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"포트 해제 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="포트 해제 중 오류가 발생했습니다"
        )

@deployment_router.get("/ports/conflicts")
async def check_port_conflicts(current_user: User = Depends(get_current_user)):
    """포트 충돌 검사"""
    try:
        check_admin_role(current_user)
        
        conflicts = port_manager.check_port_conflicts()
        
        return {
            "success": True,
            "conflicts": conflicts,
            "has_conflicts": len(conflicts) > 0,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"포트 충돌 검사 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="포트 충돌 검사 중 오류가 발생했습니다"
        )

@deployment_router.get("/prerequisites")
async def check_deployment_prerequisites(current_user: User = Depends(get_current_user)):
    """배포 전제 조건 확인"""
    try:
        check_admin_role(current_user)
        
        prerequisites = deployment_manager.check_prerequisites()
        
        return {
            "success": True,
            "prerequisites": prerequisites,
            "ready": all(prerequisites.values()),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"전제 조건 확인 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="전제 조건 확인 중 오류가 발생했습니다"
        )

@deployment_router.post("/deploy")
async def deploy_system(
    request: DeploymentRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """시스템 배포 실행"""
    try:
        check_admin_role(current_user)
        
        # 배포 환경 검증
        if request.environment not in deployment_manager.supported_environments:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"지원하지 않는 환경입니다: {request.environment}"
            )
        
        # 백그라운드에서 배포 실행
        background_tasks.add_task(
            deployment_manager.deploy,
            request.environment,
            request.force
        )
        
        logger.info(f"배포 시작: {request.environment}", extra={
            'user_id': current_user.id,
            'environment': request.environment,
            'force': request.force
        })
        
        return {
            "success": True,
            "message": f"{request.environment} 환경으로 배포가 시작되었습니다",
            "environment": request.environment,
            "started_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"배포 실행 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="배포 실행 중 오류가 발생했습니다"
        )

@deployment_router.get("/status")
async def get_deployment_status(current_user: User = Depends(get_current_user)):
    """현재 배포 상태 조회"""
    try:
        check_admin_role(current_user)
        
        # 실제 서비스 상태 확인
        service_status = {}
        
        # 실제 컨테이너 기반 서비스 상태 확인
        # 환경변수에서 동적으로 포트 가져오기
        backend_port = os.getenv('BACKEND_PORT', '8002')
        mongodb_port = os.getenv('MONGODB_PORT', '27018')
        
        actual_services = {
            'backend': {
                'name': 'Backend (FastAPI)',
                'container_name': 'online-evaluation-backend',
                'port': int(backend_port),
                'url': f'http://localhost:{backend_port}',
                'healthcheck': '/health'
            },
            'mongodb': {
                'name': 'MongoDB',
                'container_name': 'online-evaluation-mongodb', 
                'port': int(mongodb_port),
                'url': f'mongodb://localhost:{mongodb_port}',
                'healthcheck': None
            }
        }
        
        for service_name, config in actual_services.items():
            container_status = await get_container_status(config['container_name'])
            is_running = container_status['running']
            is_healthy = container_status['healthy'] if is_running else False
            
            service_status[service_name] = ServiceStatusResponse(
                name=config['name'],
                port=config['port'],
                url=config['url'],
                running=is_running,
                healthy=is_healthy,
                container_status=container_status.get('status', 'unknown')
            )
        
        return {
            "success": True,
            "services": service_status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"배포 상태 조회 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="배포 상태 조회 중 오류가 발생했습니다"
        )

@deployment_router.get("/history")
async def get_deployment_history(
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """배포 이력 조회"""
    try:
        check_admin_role(current_user)
        
        history = deployment_manager.get_deployment_history(limit)
        
        return {
            "success": True,
            "history": history,
            "total": len(history),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"배포 이력 조회 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="배포 이력 조회 중 오류가 발생했습니다"
        )

@deployment_router.post("/rollback")
async def rollback_deployment(
    target_deployment_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """이전 배포로 롤백"""
    try:
        check_admin_role(current_user)
        
        success = deployment_manager.rollback(target_deployment_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="롤백 실행에 실패했습니다"
            )
        
        logger.info(f"배포 롤백 실행", extra={
            'user_id': current_user.id,
            'target_deployment': target_deployment_id
        })
        
        return {
            "success": True,
            "message": "롤백이 성공적으로 완료되었습니다",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"롤백 실행 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="롤백 실행 중 오류가 발생했습니다"
        )

@deployment_router.post("/generate-scripts")
async def generate_deployment_scripts(
    environment: str = "development",
    current_user: User = Depends(get_current_user)
):
    """배포 스크립트 생성"""
    try:
        check_admin_role(current_user)
        
        # 환경 변수 파일 생성
        env_success = deployment_manager.generate_env_file(environment)
        
        # Docker Compose 파일 생성
        compose_success = deployment_manager.generate_docker_compose(environment)
        
        # 배포 스크립트 생성
        script_success = deployment_manager.create_deployment_script(environment)
        
        if not all([env_success, compose_success, script_success]):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="일부 스크립트 생성에 실패했습니다"
            )
        
        logger.info(f"배포 스크립트 생성 완료: {environment}", extra={
            'user_id': current_user.id,
            'environment': environment
        })
        
        return {
            "success": True,
            "message": "배포 스크립트가 성공적으로 생성되었습니다",
            "environment": environment,
            "files_created": [
                ".env",
                "docker-compose.yml",
                "deploy.sh",
                "deploy.bat" if deployment_manager._is_windows() else None
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"스크립트 생성 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="스크립트 생성 중 오류가 발생했습니다"
        )

@deployment_router.get("/docker-compose")
async def get_docker_compose_config(current_user: User = Depends(get_current_user)):
    """Docker Compose 설정 조회"""
    try:
        check_admin_role(current_user)
        
        port_mappings = port_manager.generate_docker_compose_ports()
        
        return {
            "success": True,
            "port_mappings": port_mappings,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Docker Compose 설정 조회 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Docker Compose 설정 조회 중 오류가 발생했습니다"
        )

# Windows 여부 확인 헬퍼 함수 추가
def _is_windows():
    import platform
    return platform.system() == 'Windows'

deployment_manager._is_windows = _is_windows