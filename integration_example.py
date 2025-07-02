#!/usr/bin/env python3
"""
온라인 평가 시스템 - Universal Port Manager 통합 예제
==================================================

이 스크립트는 online-evaluation 프로젝트가 Universal Port Manager를 
어떻게 활용하는지 보여주는 실제 예제입니다.
"""

import sys
from pathlib import Path
import json
import subprocess

# Universal Port Manager 모듈 경로 추가
sys.path.insert(0, str(Path(__file__).parent / "universal_port_manager"))

from universal_port_manager import PortManager

def main():
    """온라인 평가 시스템과 Universal Port Manager 통합 데모"""
    
    print("🚀 온라인 평가 시스템 - Universal Port Manager 통합 예제")
    print("=" * 70)
    print()
    
    # 1. 프로젝트별 포트 매니저 생성
    print("1️⃣ 온라인 평가 시스템 포트 매니저 초기화")
    print("-" * 50)
    
    pm = PortManager(project_name="online-evaluation")
    
    # 2. 필요한 서비스 정의 (실제 프로젝트 구조에 맞춤)
    services = [
        {'name': 'frontend', 'type': 'react'},
        {'name': 'backend', 'type': 'fastapi'},
        {'name': 'mongodb', 'type': 'mongodb'},
        {'name': 'redis', 'type': 'redis'},
        {'name': 'nginx', 'type': 'nginx'},  # production용
        {'name': 'prometheus', 'type': 'prometheus'},  # 모니터링
        {'name': 'grafana', 'type': 'grafana'},  # 모니터링
        {'name': 'elasticsearch', 'type': 'elasticsearch'},  # 로깅
        {'name': 'kibana', 'type': 'elasticsearch'},  # 로깅
    ]
    
    print("📦 필요한 서비스:")
    for service in services:
        print(f"   - {service['name']} ({service['type']})")
    
    # 3. 포트 할당
    print("\n2️⃣ 포트 할당 실행")
    print("-" * 50)
    
    # 기존 선호 포트 정의 (기존 설정 유지 시도)
    preferred_ports = {
        'frontend': 3000,
        'backend': 8080,
        'mongodb': 27017,
        'redis': 6379,
        'nginx': 80,
        'prometheus': 9090,
        'grafana': 3001,
        'elasticsearch': 9200,
        'kibana': 5601
    }
    
    allocated_ports = pm.allocate_services(
        services=services,
        preferred_ports=preferred_ports
    )
    
    print("🎯 할당된 포트:")
    for service_name, port_info in allocated_ports.items():
        original = preferred_ports.get(service_name, '없음')
        status = "✅ 유지" if port_info.port == original else f"⚠️ 변경 ({original} → {port_info.port})"
        print(f"   {service_name:<15}: {port_info.port:>5} {status}")
    
    # 4. 충돌 검사
    print("\n3️⃣ 포트 충돌 검사")
    print("-" * 50)
    
    conflicts = pm.check_conflicts()
    if conflicts:
        print(f"⚠️ 포트 충돌 {len(conflicts)}건 감지:")
        for port, info in conflicts.items():
            print(f"   포트 {port}: {info.description}")
    else:
        print("✅ 포트 충돌 없음")
    
    # 5. 설정 파일 생성
    print("\n4️⃣ 설정 파일 생성")
    print("-" * 50)
    
    results = pm.generate_all_configs()
    
    print("📝 생성된 파일:")
    print(f"   Docker Compose: {'✅' if results['docker_compose'] else '❌'}")
    print(f"   환경 파일: {len(results['env_files'])}개")
    for format_name, file_path in results['env_files'].items():
        print(f"     - {Path(file_path).name} ({format_name})")
    print(f"   시작 스크립트: {'✅' if results['start_script'] else '❌'}")
    
    # 6. 서비스 URL 정보
    print("\n5️⃣ 서비스 접속 정보")
    print("-" * 50)
    
    urls = pm.get_service_urls()
    print("🌐 서비스 URL:")
    for service, url in urls.items():
        print(f"   {service:<15}: {url}")
    
    # 7. newsscout와의 호환성 테스트
    print("\n6️⃣ 다른 프로젝트와 호환성 테스트")
    print("-" * 50)
    
    # newsscout 프로젝트 시뮬레이션
    newsscout_pm = PortManager(project_name="newsscout")
    newsscout_services = ['frontend', 'backend', 'postgresql', 'redis']
    newsscout_ports = newsscout_pm.allocate_services(newsscout_services)
    
    print("📊 newsscout 프로젝트 포트 할당:")
    for service, port_info in newsscout_ports.items():
        print(f"   {service:<15}: {port_info.port}")
    
    # 두 프로젝트 간 충돌 확인
    online_eval_ports = set(port_info.port for port_info in allocated_ports.values())
    newsscout_port_values = set(port_info.port for port_info in newsscout_ports.values())
    
    conflicts = online_eval_ports & newsscout_port_values
    if conflicts:
        print(f"⚠️ 두 프로젝트 간 포트 충돌: {conflicts}")
    else:
        print("✅ 두 프로젝트 동시 실행 가능!")
    
    # 8. 상태 보고서
    print("\n7️⃣ 상태 보고서")
    print("-" * 50)
    
    report = pm.get_status_report()
    print(f"📋 프로젝트: {report['project_name']}")
    print(f"   서비스 수: {len(report['services'])}")
    print(f"   사용 포트: {len([s for s in report['services'].values() if s['status'] == 'allocated'])}")
    print(f"   충돌 수: {len(report['conflicts'])}")
    
    # 9. 실제 사용 명령어 안내
    print("\n8️⃣ 실제 사용 명령어")
    print("-" * 50)
    
    print("🔧 CLI 명령어:")
    print("   # 포트 할당")
    print("   python3 -m universal_port_manager.cli allocate frontend backend mongodb redis --project online-evaluation")
    print()
    print("   # 설정 파일 생성") 
    print("   python3 -m universal_port_manager.cli generate --project online-evaluation")
    print()
    print("   # 서비스 시작")
    print("   python3 -m universal_port_manager.cli start --project online-evaluation")
    print()
    print("   # 상태 확인")
    print("   python3 -m universal_port_manager.cli status --project online-evaluation")
    
    print("\n🐳 Docker 명령어:")
    print("   # 배포 스크립트 실행")
    print("   deploy_with_port_manager.bat")
    print()
    print("   # 수동 실행")
    print("   docker-compose up -d")
    
    # 10. 요약
    print("\n" + "=" * 70)
    print("🎉 통합 예제 완료!")
    print()
    print("💡 주요 이점:")
    print("   ✅ 자동 포트 충돌 감지 및 회피")
    print("   ✅ 여러 프로젝트 동시 실행 지원")
    print("   ✅ 설정 파일 자동 생성")
    print("   ✅ 개발-운영 환경 일관성")
    print("   ✅ CLI와 배치 스크립트 지원")
    
    print("\n🔗 다음 단계:")
    print("   1. deploy_with_port_manager.bat 실행으로 실제 배포 테스트")
    print("   2. newsscout 프로젝트와 동시 실행 테스트")
    print("   3. 팀 내 다른 개발자와 포트 설정 공유")
    print("   4. CI/CD 파이프라인에 통합")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()