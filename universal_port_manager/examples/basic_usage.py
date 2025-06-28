"""
Universal Port Manager - 기본 사용 예제
=====================================

가장 일반적인 사용 패턴들을 보여주는 예제 코드
"""

import sys
from pathlib import Path

# 모듈 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.port_manager import PortManager

def example_basic_allocation():
    """기본 포트 할당 예제"""
    print("🎯 기본 포트 할당 예제")
    print("=" * 50)
    
    # 포트 매니저 생성
    pm = PortManager(project_name="basic-example")
    
    # 서비스 목록에 포트 할당
    services = ['frontend', 'backend', 'mongodb', 'redis']
    ports = pm.allocate_services(services)
    
    print("할당된 포트:")
    for service_name, allocated_port in ports.items():
        print(f"  {service_name:<12}: {allocated_port.port} ({allocated_port.service_type})")
    
    print("\n✅ 포트 할당 완료!")
    return pm

def example_template_usage():
    """템플릿 사용 예제"""
    print("\n🏗️  템플릿 사용 예제")
    print("=" * 50)
    
    pm = PortManager(project_name="template-example")
    
    # 미리 정의된 템플릿 사용
    ports = pm.allocate_from_template('fullstack-react-fastapi')
    
    print("템플릿으로 할당된 포트:")
    for service_name, allocated_port in ports.items():
        print(f"  {service_name:<12}: {allocated_port.port} ({allocated_port.service_type})")
    
    return pm

def example_preferred_ports():
    """선호 포트 지정 예제"""
    print("\n🎛️  선호 포트 지정 예제")
    print("=" * 50)
    
    pm = PortManager(project_name="preferred-example")
    
    # 선호하는 포트 번호 지정
    preferred_ports = {
        'frontend': 3001,
        'backend': 8081,
        'mongodb': 27018
    }
    
    services = ['frontend', 'backend', 'mongodb']
    ports = pm.allocate_services(services, preferred_ports=preferred_ports)
    
    print("선호 포트로 할당된 결과:")
    for service_name, allocated_port in ports.items():
        preferred = preferred_ports.get(service_name, '없음')
        status = "✅" if allocated_port.port == preferred else "⚠️"
        print(f"  {service_name:<12}: {allocated_port.port} (선호: {preferred}) {status}")
    
    return pm

def example_conflict_detection():
    """포트 충돌 감지 예제"""
    print("\n🔍 포트 충돌 감지 예제")
    print("=" * 50)
    
    pm = PortManager(project_name="conflict-example")
    
    # 포트 할당
    ports = pm.allocate_services(['frontend', 'backend'])
    
    # 충돌 검사
    conflicts = pm.check_conflicts()
    
    if conflicts:
        print("⚠️  포트 충돌 감지:")
        for port, info in conflicts.items():
            print(f"  포트 {port}: {info.description}")
    else:
        print("✅ 포트 충돌 없음")
    
    return pm

def example_file_generation():
    """설정 파일 생성 예제"""
    print("\n📝 설정 파일 생성 예제")
    print("=" * 50)
    
    pm = PortManager(project_name="file-generation-example")
    
    # 포트 할당
    pm.allocate_services(['frontend', 'backend', 'mongodb'])
    
    # 모든 설정 파일 생성
    results = pm.generate_all_configs()
    
    print("생성된 파일:")
    print(f"  Docker Compose: {'✅' if results['docker_compose'] else '❌'}")
    print(f"  환경 파일: {len(results['env_files'])}개")
    for format_name, file_path in results['env_files'].items():
        print(f"    - {Path(file_path).name} ({format_name})")
    print(f"  시작 스크립트: {'✅' if results['start_script'] else '❌'}")
    
    return pm

def example_status_report():
    """상태 보고서 예제"""
    print("\n📊 상태 보고서 예제")
    print("=" * 50)
    
    pm = PortManager(project_name="status-example")
    pm.allocate_services(['frontend', 'backend', 'redis'])
    
    # 상태 보고서 생성
    report = pm.get_status_report()
    
    print(f"프로젝트: {report['project_name']}")
    print(f"서비스 수: {len(report['services'])}")
    print(f"충돌 수: {len(report['conflicts'])}")
    
    print("\n서비스별 상태:")
    for service_name, service_info in report['services'].items():
        status_icon = "✅" if service_info['status'] == 'available' else "❌"
        print(f"  {service_name:<12}: {service_info['port']} {status_icon}")
    
    return pm

def example_cleanup():
    """정리 작업 예제"""
    print("\n🧹 정리 작업 예제")
    print("=" * 50)
    
    pm = PortManager(project_name="cleanup-example")
    pm.allocate_services(['frontend', 'backend'])
    
    # 정리 작업 수행
    results = pm.cleanup()
    
    print("정리 결과:")
    print(f"  정리된 포트: {results['cleaned_ports']}개")
    print(f"  정리된 파일: {results['cleaned_files']}개")
    
    return pm

def main():
    """모든 예제 실행"""
    print("🚀 Universal Port Manager 예제 실행")
    print("=" * 60)
    
    try:
        # 기본 예제들 실행
        example_basic_allocation()
        example_template_usage()
        example_preferred_ports()
        example_conflict_detection()
        example_file_generation()
        example_status_report()
        example_cleanup()
        
        print("\n" + "=" * 60)
        print("🎉 모든 예제 실행 완료!")
        print("\n💡 생성된 파일들을 확인해보세요:")
        print("   - docker-compose.yml")
        print("   - .env")
        print("   - set_ports.sh")
        print("   - port_config.py")
        print("   - ports.json")
        print("   - start.sh")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()