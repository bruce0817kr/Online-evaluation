"""
Universal Port Manager - 통합 가이드 예제
=======================================

다른 프로젝트에 통합하는 방법을 보여주는 실제 시나리오 예제
"""

import sys
from pathlib import Path
import json

# 모듈 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.port_manager import PortManager

def scenario_multiple_projects():
    """시나리오 1: 여러 프로젝트 동시 실행"""
    print("🎭 시나리오 1: 여러 프로젝트 동시 실행")
    print("=" * 60)
    print("상황: newsscout와 online-evaluation을 동시에 개발")
    print()
    
    # newsscout 프로젝트
    print("1️⃣ newsscout 프로젝트 설정")
    newsscout_pm = PortManager(project_name="newsscout")
    newsscout_ports = newsscout_pm.allocate_services([
        'frontend', 'backend', 'postgresql', 'redis'
    ])
    
    print("newsscout 할당 포트:")
    for service, port_info in newsscout_ports.items():
        print(f"  {service:<12}: {port_info.port}")
    
    # online-evaluation 프로젝트
    print("\n2️⃣ online-evaluation 프로젝트 설정")
    evaluation_pm = PortManager(project_name="online-evaluation")
    evaluation_ports = evaluation_pm.allocate_services([
        'frontend', 'backend', 'mongodb', 'redis'
    ])
    
    print("online-evaluation 할당 포트:")
    for service, port_info in evaluation_ports.items():
        print(f"  {service:<12}: {port_info.port}")
    
    print("\n✅ 두 프로젝트 모두 충돌 없이 실행 가능!")
    
    # 각각 설정 파일 생성
    print("\n3️⃣ 설정 파일 생성")
    newsscout_pm.generate_all_configs()
    evaluation_pm.generate_all_configs()
    
    print("각 프로젝트 디렉토리에 설정 파일 생성 완료")
    
    return newsscout_pm, evaluation_pm

def scenario_team_collaboration():
    """시나리오 2: 팀 협업 환경"""
    print("\n👥 시나리오 2: 팀 협업 환경")
    print("=" * 60)
    print("상황: 팀 내 여러 개발자가 같은 프로젝트 작업")
    print()
    
    # 개발자 A
    print("1️⃣ 개발자 A - 최초 설정")
    dev_a_pm = PortManager(
        project_name="team-project",
        global_mode=True  # 전역 모드로 팀 공유
    )
    dev_a_ports = dev_a_pm.allocate_services(['frontend', 'backend', 'database'])
    
    print("개발자 A 할당 포트:")
    for service, port_info in dev_a_ports.items():
        print(f"  {service:<12}: {port_info.port}")
    
    # 개발자 B
    print("\n2️⃣ 개발자 B - 기존 설정 공유")
    dev_b_pm = PortManager(
        project_name="team-project", 
        global_mode=True
    )
    dev_b_ports = dev_b_pm.get_allocated_ports()
    
    print("개발자 B 확인 포트 (공유됨):")
    for service, port_info in dev_b_ports.items():
        print(f"  {service:<12}: {port_info.port}")
    
    # 개발자 C - 독립 브랜치 작업
    print("\n3️⃣ 개발자 C - 독립 브랜치 작업")
    dev_c_pm = PortManager(project_name="team-project-feature-x")
    dev_c_ports = dev_c_pm.allocate_services(['frontend', 'backend', 'database'])
    
    print("개발자 C 할당 포트 (독립):")
    for service, port_info in dev_c_ports.items():
        print(f"  {service:<12}: {port_info.port}")
    
    print("\n✅ 팀 협업 시나리오 완료!")
    
    return dev_a_pm, dev_b_pm, dev_c_pm

def scenario_cicd_integration():
    """시나리오 3: CI/CD 파이프라인 통합"""
    print("\n🔄 시나리오 3: CI/CD 파이프라인 통합")
    print("=" * 60)
    print("상황: GitHub Actions에서 자동 배포")
    print()
    
    # 동적 프로젝트명 (GitHub 레포지토리명 사용)
    repository_name = "user/awesome-project"
    project_name = repository_name.replace("/", "-")
    
    print(f"1️⃣ GitHub 레포지토리: {repository_name}")
    print(f"   프로젝트명: {project_name}")
    
    # CI/CD 환경에서 포트 할당
    cicd_pm = PortManager(project_name=project_name)
    
    # 프로젝트 자동 감지 (package.json, requirements.txt 등)
    services = ['frontend', 'backend', 'database']  # 실제로는 auto_detect=True
    cicd_ports = cicd_pm.allocate_services(services)
    
    print("\n2️⃣ CI/CD 환경 포트 할당:")
    for service, port_info in cicd_ports.items():
        print(f"  {service:<12}: {port_info.port}")
    
    # GitHub Actions 환경변수 출력 형식
    print("\n3️⃣ GitHub Actions 환경변수:")
    for service, port_info in cicd_ports.items():
        env_name = f"{service.upper()}_PORT"
        print(f"  echo \"{env_name}={port_info.port}\" >> $GITHUB_ENV")
    
    # Docker Compose 생성
    cicd_pm.generate_all_configs()
    print("\n4️⃣ Docker Compose 파일 생성 완료")
    
    print("\n✅ CI/CD 통합 시나리오 완료!")
    
    return cicd_pm

def scenario_microservices():
    """시나리오 4: 마이크로서비스 아키텍처"""
    print("\n🏗️  시나리오 4: 마이크로서비스 아키텍처")
    print("=" * 60)
    print("상황: 여러 마이크로서비스를 하나의 프로젝트로 관리")
    print()
    
    micro_pm = PortManager(project_name="microservices-platform")
    
    # 마이크로서비스 정의
    microservices = [
        {'name': 'api-gateway', 'type': 'nginx'},
        {'name': 'user-service', 'type': 'backend'},
        {'name': 'auth-service', 'type': 'backend'},
        {'name': 'notification-service', 'type': 'backend'},
        {'name': 'data-service', 'type': 'backend'},
        {'name': 'frontend-web', 'type': 'frontend'},
        {'name': 'frontend-mobile-api', 'type': 'backend'},
        {'name': 'postgres-main', 'type': 'database'},
        {'name': 'postgres-analytics', 'type': 'database'},
        {'name': 'redis-cache', 'type': 'redis'},
        {'name': 'redis-sessions', 'type': 'redis'},
        {'name': 'elasticsearch', 'type': 'elasticsearch'},
        {'name': 'prometheus', 'type': 'monitoring'},
        {'name': 'grafana', 'type': 'monitoring'}
    ]
    
    print(f"1️⃣ {len(microservices)}개 마이크로서비스 포트 할당")
    
    micro_ports = micro_pm.allocate_services(microservices)
    
    # 서비스 타입별 그룹화하여 출력
    service_groups = {}
    for service_name, port_info in micro_ports.items():
        service_type = port_info.service_type
        if service_type not in service_groups:
            service_groups[service_type] = []
        service_groups[service_type].append((service_name, port_info.port))
    
    print("\n2️⃣ 서비스 타입별 포트 할당:")
    for service_type, services in service_groups.items():
        print(f"\n  📦 {service_type.upper()} Services:")
        for service_name, port in services:
            print(f"    {service_name:<25}: {port}")
    
    # 설정 파일 생성
    print("\n3️⃣ 마이크로서비스 설정 파일 생성")
    micro_pm.generate_all_configs()
    
    print("\n✅ 마이크로서비스 시나리오 완료!")
    
    return micro_pm

def scenario_legacy_migration():
    """시나리오 5: 레거시 프로젝트 마이그레이션"""
    print("\n🔄 시나리오 5: 레거시 프로젝트 마이그레이션")
    print("=" * 60)
    print("상황: 기존 하드코딩된 포트를 포트 매니저로 마이그레이션")
    print()
    
    # 기존 레거시 포트 설정
    legacy_ports = {
        'web-server': 8000,
        'api-server': 8001,
        'database': 5432,
        'cache': 6379,
        'monitoring': 9090
    }
    
    print("1️⃣ 기존 레거시 포트 설정:")
    for service, port in legacy_ports.items():
        print(f"  {service:<15}: {port}")
    
    # 포트 매니저로 마이그레이션
    print("\n2️⃣ 포트 매니저로 마이그레이션")
    legacy_pm = PortManager(project_name="legacy-migration")
    
    # 기존 포트를 선호 포트로 설정하여 최대한 유지
    services = [
        {'name': 'web-server', 'type': 'frontend'},
        {'name': 'api-server', 'type': 'backend'}, 
        {'name': 'database', 'type': 'database'},
        {'name': 'cache', 'type': 'redis'},
        {'name': 'monitoring', 'type': 'monitoring'}
    ]
    
    migrated_ports = legacy_pm.allocate_services(
        services=services,
        preferred_ports=legacy_ports
    )
    
    print("\n3️⃣ 마이그레이션 결과:")
    for service_name, port_info in migrated_ports.items():
        original = legacy_ports.get(service_name, '없음')
        status = "✅ 유지됨" if port_info.port == original else f"⚠️ 변경됨 ({original} → {port_info.port})"
        print(f"  {service_name:<15}: {port_info.port} {status}")
    
    # 충돌 검사
    conflicts = legacy_pm.check_conflicts()
    if conflicts:
        print(f"\n4️⃣ 포트 충돌 감지: {len(conflicts)}건")
        for port, info in conflicts.items():
            print(f"  포트 {port}: {info.description}")
    else:
        print("\n4️⃣ 포트 충돌 없음 ✅")
    
    # 새로운 설정 파일 생성
    legacy_pm.generate_all_configs()
    print("\n5️⃣ 새로운 설정 파일 생성 완료")
    
    print("\n✅ 레거시 마이그레이션 시나리오 완료!")
    
    return legacy_pm

def scenario_development_workflow():
    """시나리오 6: 개발 워크플로우 통합"""
    print("\n⚡ 시나리오 6: 개발 워크플로우 통합")
    print("=" * 60)
    print("상황: 개발자의 일상적인 워크플로우에 통합")
    print()
    
    # 1. 새 프로젝트 시작
    print("1️⃣ 새 프로젝트 시작")
    workflow_pm = PortManager(project_name="new-awesome-app")
    
    # 자동 감지로 서비스 파악 (시뮬레이션)
    print("   📁 프로젝트 디렉토리 스캔...")
    print("   📦 package.json 발견 → React 프로젝트")
    print("   🐍 requirements.txt 발견 → Python 백엔드")
    print("   🐳 docker-compose.yml 발견 → Docker 환경")
    
    services = ['frontend', 'backend', 'mongodb', 'redis']
    ports = workflow_pm.allocate_services(services, auto_detect=True)
    
    print("\n   🎯 자동 할당된 포트:")
    for service, port_info in ports.items():
        print(f"     {service:<12}: {port_info.port}")
    
    # 2. 개발 환경 설정
    print("\n2️⃣ 개발 환경 설정")
    workflow_pm.generate_all_configs()
    
    print("   📝 생성된 설정 파일:")
    print("     - docker-compose.yml")
    print("     - docker-compose.override.yml")
    print("     - .env")
    print("     - set_ports.sh")
    print("     - start.sh")
    
    # 3. 개발 시작
    print("\n3️⃣ 개발 시작")
    print("   🚀 서비스 시작 명령:")
    print("     ./start.sh")
    print("   또는")
    print("     docker-compose up -d")
    
    # 4. 상태 확인
    print("\n4️⃣ 개발 중 상태 확인")
    urls = workflow_pm.get_service_urls()
    print("   🌐 서비스 URL:")
    for service, url in urls.items():
        print(f"     {service:<12}: {url}")
    
    # 5. 정리
    print("\n5️⃣ 개발 완료 후 정리")
    print("   🧹 정리 명령:")
    print("     docker-compose down")
    print("     python3 -m universal_port_manager.cli cleanup")
    
    print("\n✅ 개발 워크플로우 시나리오 완료!")
    
    return workflow_pm

def generate_integration_examples():
    """통합 예제 코드 생성"""
    print("\n📝 통합 예제 코드 생성")
    print("=" * 60)
    
    examples = {
        "flask_integration.py": '''
# Flask 프로젝트 통합 예제
from universal_port_manager import PortManager

def create_app():
    # 포트 매니저로 포트 할당
    pm = PortManager(project_name="flask-app")
    ports = pm.allocate_services(['backend', 'redis', 'database'])
    
    app = Flask(__name__)
    
    # 할당된 포트 사용
    backend_port = ports['backend'].port
    redis_port = ports['redis'].port
    
    app.config['REDIS_URL'] = f"redis://localhost:{redis_port}"
    
    return app, backend_port

if __name__ == "__main__":
    app, port = create_app()
    app.run(host="0.0.0.0", port=port)
''',
        
        "django_settings.py": '''
# Django 설정 통합 예제
from universal_port_manager import PortManager
import os

# 포트 매니저 초기화
pm = PortManager(project_name="django-project")
ports = pm.allocate_services(['backend', 'database', 'redis'])

# Django 설정에 포트 적용
DATABASE_PORT = ports['database'].port
REDIS_PORT = ports['redis'].port

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'myproject',
        'HOST': 'localhost',
        'PORT': DATABASE_PORT,
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'redis://localhost:{REDIS_PORT}/1',
    }
}
''',
        
        "docker_integration.sh": '''#!/bin/bash
# Docker 통합 스크립트 예제

echo "🚀 포트 매니저를 사용한 Docker 배포"

# 포트 할당
python3 -c "
from universal_port_manager import PortManager
pm = PortManager(project_name='$1')
pm.allocate_services(['frontend', 'backend', 'database'])
pm.generate_all_configs()
"

# Docker Compose 실행
echo "📦 Docker 서비스 시작"
docker-compose up -d

echo "✅ 배포 완료!"
echo "📊 서비스 상태:"
docker-compose ps
'''
    }
    
    # 예제 파일들 저장
    examples_dir = Path(__file__).parent / "integration_examples"
    examples_dir.mkdir(exist_ok=True)
    
    for filename, content in examples.items():
        file_path = examples_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content.strip())
        print(f"   📄 {filename} 생성")
    
    print(f"\n✅ {len(examples)}개 통합 예제 파일 생성 완료!")
    print(f"   📁 위치: {examples_dir}")

def main():
    """모든 통합 시나리오 실행"""
    print("🎭 Universal Port Manager 통합 가이드")
    print("=" * 70)
    print("실제 개발 환경에서 사용할 수 있는 다양한 시나리오를 시연합니다.\n")
    
    try:
        # 시나리오들 실행
        scenario_multiple_projects()
        scenario_team_collaboration() 
        scenario_cicd_integration()
        scenario_microservices()
        scenario_legacy_migration()
        scenario_development_workflow()
        
        # 통합 예제 코드 생성
        generate_integration_examples()
        
        print("\n" + "=" * 70)
        print("🎉 모든 통합 시나리오 완료!")
        print("\n💡 주요 사용 패턴:")
        print("   1. 여러 프로젝트 동시 실행 → 자동 포트 충돌 회피")
        print("   2. 팀 협업 → 전역 모드로 포트 정보 공유")
        print("   3. CI/CD 통합 → 동적 포트 할당 및 환경변수 생성")
        print("   4. 마이크로서비스 → 대규모 서비스 포트 관리")
        print("   5. 레거시 마이그레이션 → 기존 포트 최대한 유지")
        print("   6. 개발 워크플로우 → 프로젝트 시작부터 배포까지")
        
        print("\n🔗 다음 단계:")
        print("   - examples/ 디렉토리의 통합 예제 참고")
        print("   - CLI 도구로 실제 프로젝트에 적용")
        print("   - README.md에서 더 자세한 사용법 확인")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()