"""
개선된 포트 매니저 CLI 인터페이스
===============================

의존성 문제 해결 및 모듈화된 아키텍처와 완벽 호환
사용자 친화적인 인터페이스와 강화된 에러 처리
"""

import click
import json
import sys
from typing import List, Dict, Optional
from pathlib import Path
import logging

# 선택적 의존성 처리
YAML_AVAILABLE = True
try:
    import yaml
except ImportError:
    YAML_AVAILABLE = False
    yaml = None

# 개선된 모듈 임포트 (안전한 임포트)
try:
    from .core.port_manager import PortManager
    from .core.port_manager_fallback import PortManagerFallback
    from .dependency_manager import DependencyManager
    CORE_MODULES_AVAILABLE = True
except ImportError:
    try:
        from core.port_manager import PortManager
        from core.port_manager_fallback import PortManagerFallback
        from dependency_manager import DependencyManager
        CORE_MODULES_AVAILABLE = True
    except ImportError:
        CORE_MODULES_AVAILABLE = False
        PortManager = None
        PortManagerFallback = None
        DependencyManager = None

logger = logging.getLogger(__name__)

class CLIHelper:
    """CLI 도우미 클래스"""
    
    @staticmethod
    def setup_logging(verbose: bool):
        """로깅 설정"""
        if verbose:
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        else:
            logging.basicConfig(level=logging.WARNING)
    
    @staticmethod
    def check_system_requirements() -> Dict[str, bool]:
        """시스템 요구사항 확인"""
        requirements = {
            'core_modules': CORE_MODULES_AVAILABLE,
            'yaml_support': YAML_AVAILABLE,
            'click_support': True
        }
        
        # Docker 확인
        try:
            import subprocess
            result = subprocess.run(['docker', '--version'], 
                                  capture_output=True, text=True)
            requirements['docker'] = result.returncode == 0
        except FileNotFoundError:
            requirements['docker'] = False
        
        # Docker Compose 확인
        try:
            result = subprocess.run(['docker-compose', '--version'], 
                                  capture_output=True, text=True)
            requirements['docker_compose'] = result.returncode == 0
        except FileNotFoundError:
            requirements['docker_compose'] = False
        
        return requirements

def safe_port_manager_operation(func):
    """포트 매니저 작업을 안전하게 실행하는 데코레이터"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            click.echo(f"❌ 작업 실패: {e}", err=True)
            if logging.getLogger().level <= logging.DEBUG:
                import traceback
                click.echo(traceback.format_exc(), err=True)
            return False
    return wrapper

@click.group(invoke_without_command=True)
@click.option('--project', '-p', default=None, help='프로젝트 이름')
@click.option('--global-mode/--local-mode', default=True, help='전역/로컬 모드')
@click.option('--verbose', '-v', is_flag=True, help='상세 출력')
@click.option('--check-system', is_flag=True, help='시스템 요구사항 확인')
@click.pass_context
def cli(ctx, project, global_mode, verbose, check_system):
    """
    🚀 Universal Port Manager CLI (개선된 버전)
    
    여러 프로젝트 간 포트 충돌 방지 및 자동 할당 도구
    의존성 문제 해결 및 안정성 향상
    """
    ctx.ensure_object(dict)
    ctx.obj['project'] = project or Path.cwd().name
    ctx.obj['global_mode'] = global_mode
    ctx.obj['verbose'] = verbose
    
    CLIHelper.setup_logging(verbose)
    
    if check_system:
        requirements = CLIHelper.check_system_requirements()
        click.echo("🔧 시스템 요구사항 확인:")
        click.echo("=" * 40)
        
        status_icons = {True: "✅", False: "❌"}
        for requirement, available in requirements.items():
            icon = status_icons[available]
            requirement_name = requirement.replace('_', ' ').title()
            click.echo(f"  {icon} {requirement_name}: {'사용 가능' if available else '사용 불가'}")
        return
    
    # 명령어가 지정되지 않은 경우 도움말 표시
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        click.echo("\n💡 빠른 시작:")
        click.echo("  universal-port-manager scan                    # 포트 스캔")
        click.echo("  universal-port-manager allocate frontend backend  # 포트 할당")
        click.echo("  universal-port-manager generate                # 설정 파일 생성")
        click.echo("  universal-port-manager start                   # 서비스 시작")

@cli.command()
@click.option('--range', 'port_range', default='3000-9999', help='스캔할 포트 범위 (예: 3000-9999)')
@click.option('--format', 'output_format', type=click.Choice(['table', 'json', 'yaml']), default='table')
@click.option('--conflicts-only', is_flag=True, help='충돌하는 포트만 표시')
@click.pass_context
@safe_port_manager_operation
def scan(ctx, port_range, output_format, conflicts_only):
    """🔍 시스템 포트 스캔"""
    
    project_name = ctx.obj['project']
    global_mode = ctx.obj['global_mode']
    
    # 범위 파싱
    try:
        start_port, end_port = map(int, port_range.split('-'))
    except ValueError:
        click.echo(f"❌ 잘못된 포트 범위 형식: {port_range}", err=True)
        click.echo("예시: 3000-9999", err=True)
        return
    
    if not CORE_MODULES_AVAILABLE:
        # 대체 스캔 시스템 사용
        fallback = PortManagerFallback()
        port_info = fallback.scan_ports((start_port, end_port))
        click.echo(f"📡 기본 포트 스캔 중 ({start_port}-{end_port})...")
    else:
        pm = PortManager(project_name=project_name, global_mode=global_mode, 
                        scan_range=(start_port, end_port))
        click.echo(f"📡 포트 스캔 중 ({start_port}-{end_port})...")
        port_info = pm.scan_system()
    
    if conflicts_only:
        port_info = {port: info for port, info in port_info.items() 
                    if getattr(info, 'status', 'occupied') != 'available'}
    
    if not port_info:
        click.echo("✅ 충돌하는 포트가 없습니다!" if conflicts_only else "✅ 사용 중인 포트가 없습니다!")
        return
    
    if output_format == 'table':
        _display_port_table(port_info)
    elif output_format == 'json':
        data = {}
        for port, info in port_info.items():
            data[port] = {
                'status': getattr(info, 'status', 'occupied'),
                'description': getattr(info, 'description', 'Port in use')
            }
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
    elif output_format == 'yaml' and YAML_AVAILABLE:
        data = {}
        for port, info in port_info.items():
            data[port] = {
                'status': getattr(info, 'status', 'occupied'),
                'description': getattr(info, 'description', 'Port in use')
            }
        click.echo(yaml.dump(data, allow_unicode=True))
    else:
        click.echo("❌ YAML 출력을 위해서는 PyYAML이 필요합니다.", err=True)

def _display_port_table(port_info: Dict):
    """포트 정보를 테이블 형식으로 출력"""
    click.echo("\n📊 포트 사용 현황")
    click.echo("=" * 60)
    click.echo(f"{'포트':<8} {'상태':<15} {'설명':<35}")
    click.echo("-" * 60)
    
    for port, info in sorted(port_info.items()):
        status = getattr(info, 'status', 'occupied')
        description = getattr(info, 'description', 'Port in use')
        
        status_color = {
            'available': 'green',
            'occupied': 'red',
            'OCCUPIED': 'red',
            'occupied_system': 'red', 
            'occupied_docker': 'yellow',
            'reserved': 'blue'
        }.get(status, 'white')
        
        click.echo(
            f"{port:<8} "
            f"{click.style(status, fg=status_color):<24} "
            f"{description:<35}"
        )

@cli.command()
@click.argument('services', nargs=-1, required=True)
@click.option('--template', '-t', help='사용할 서비스 템플릿')
@click.option('--preferred-ports', help='선호 포트 (JSON 형식, 예: {"frontend":3001,"backend":8001})')
@click.option('--auto-detect/--no-auto-detect', default=True, help='프로젝트 자동 감지')
@click.option('--dry-run', is_flag=True, help='실제 할당 없이 미리보기')
@click.pass_context
@safe_port_manager_operation
def allocate(ctx, services, template, preferred_ports, auto_detect, dry_run):
    """🎯 서비스에 포트 할당"""
    
    project_name = ctx.obj['project']
    global_mode = ctx.obj['global_mode']
    
    if not CORE_MODULES_AVAILABLE:
        click.echo("⚠️ 고급 포트 할당 기능을 사용할 수 없습니다.")
        click.echo("기본 대체 할당 시스템을 사용합니다.")
        
        fallback = PortManagerFallback()
        preferred_ports_dict = {}
        if preferred_ports:
            try:
                preferred_ports_dict = json.loads(preferred_ports)
            except json.JSONDecodeError:
                click.echo(f"❌ 선호 포트 JSON 형식 오류: {preferred_ports}", err=True)
                return
        
        allocated = fallback.allocate_ports(
            [{'name': s} for s in services], 
            preferred_ports_dict, 
            project_name
        )
    else:
        pm = PortManager(project_name=project_name, global_mode=global_mode)
        
        click.echo(f"🎯 프로젝트 '{project_name}'의 포트 할당 시작")
        
        # 선호 포트 파싱
        preferred_ports_dict = {}
        if preferred_ports:
            try:
                preferred_ports_dict = json.loads(preferred_ports)
            except json.JSONDecodeError:
                click.echo(f"❌ 선호 포트 JSON 형식 오류: {preferred_ports}", err=True)
                return
        
        # 템플릿 사용
        if template:
            try:
                allocated = pm.allocate_from_template(template)
            except ValueError as e:
                click.echo(f"❌ 템플릿 오류: {e}", err=True)
                return
        else:
            # 서비스 목록 사용
            service_list = list(services)
            allocated = pm.allocate_services(
                services=service_list,
                preferred_ports=preferred_ports_dict,
                auto_detect=auto_detect
            )
    
    if allocated:
        click.echo(f"\n✅ 포트 할당 {'미리보기' if dry_run else '완료'}!")
        click.echo("=" * 50)
        for service_name, allocated_port in allocated.items():
            service_type = getattr(allocated_port, 'service_type', 'unknown')
            port = getattr(allocated_port, 'port', allocated_port)
            click.echo(f"  🔌 {service_name:<15}: {port} ({service_type})")
        
        # 충돌 검사 (고급 기능이 있을 때만)
        if CORE_MODULES_AVAILABLE and not dry_run:
            conflicts = pm.check_conflicts()
            if conflicts:
                click.echo(f"\n⚠️  포트 충돌 감지: {len(conflicts)}건")
                for port, info in conflicts.items():
                    description = getattr(info, 'description', 'Port conflict')
                    click.echo(f"  - {port}: {description}")
    else:
        click.echo("❌ 포트 할당 실패")

@cli.command()
@click.option('--include-override/--no-override', default=True, help='override 파일 포함')
@click.option('--formats', multiple=True, default=['docker', 'bash'], 
              help='생성할 형식 (docker, bash, python, json)')
@click.pass_context
@safe_port_manager_operation
def generate(ctx, include_override, formats):
    """📝 Docker Compose 및 환경 파일 생성"""
    
    project_name = ctx.obj['project']
    global_mode = ctx.obj['global_mode']
    
    if not CORE_MODULES_AVAILABLE:
        click.echo("❌ 설정 파일 생성 기능을 사용할 수 없습니다.", err=True)
        return
    
    pm = PortManager(project_name=project_name, global_mode=global_mode)
    
    click.echo(f"📝 '{project_name}' 설정 파일 생성 중...")
    
    # 할당된 포트가 있는지 확인
    allocated_ports = pm.get_allocated_ports()
    if not allocated_ports:
        click.echo("⚠️ 할당된 포트가 없습니다. 먼저 'allocate' 명령을 실행하세요.", err=True)
        return
    
    results = pm.generate_all_configs()
    
    click.echo("\n✅ 설정 파일 생성 완료!")
    click.echo("=" * 40)
    
    if results.get('docker_compose'):
        click.echo("  📦 docker-compose.yml")
        if include_override:
            click.echo("  📦 docker-compose.override.yml")
    
    env_files = results.get('env_files', {})
    for format_name, file_path in env_files.items():
        if format_name in formats:
            click.echo(f"  🔧 {Path(file_path).name} ({format_name})")
    
    if results.get('start_script'):
        click.echo("  🚀 start.sh")

@cli.command()
@click.option('--build', is_flag=True, help='이미지 빌드')
@click.option('--logs', is_flag=True, help='시작 후 로그 표시')
@click.pass_context
@safe_port_manager_operation
def start(ctx, build, logs):
    """🚀 서비스 시작"""
    
    project_name = ctx.obj['project']
    global_mode = ctx.obj['global_mode']
    
    if not CORE_MODULES_AVAILABLE:
        click.echo("❌ 서비스 시작 기능을 사용할 수 없습니다.", err=True)
        return
    
    pm = PortManager(project_name=project_name, global_mode=global_mode)
    
    click.echo(f"🚀 '{project_name}' 서비스 시작 중...")
    
    if pm.start_services(build=build):
        click.echo("✅ 서비스 시작 성공!")
        
        # 서비스 URL 표시
        urls = pm.get_service_urls()
        if urls:
            click.echo("\n🌐 서비스 URL:")
            for service_name, url in urls.items():
                click.echo(f"  {service_name}: {url}")
        
        # 로그 표시 옵션
        if logs:
            click.echo("\n📄 컨테이너 로그:")
            import subprocess
            try:
                subprocess.run(['docker-compose', 'logs', '--tail=20'], 
                             cwd=Path.cwd())
            except Exception as e:
                click.echo(f"⚠️ 로그 표시 실패: {e}")
    else:
        click.echo("❌ 서비스 시작 실패")

@cli.command()
@click.option('--remove-volumes', is_flag=True, help='볼륨도 함께 제거')
@click.pass_context
@safe_port_manager_operation
def stop(ctx, remove_volumes):
    """⏹️ 서비스 중지"""
    
    project_name = ctx.obj['project']
    global_mode = ctx.obj['global_mode']
    
    if not CORE_MODULES_AVAILABLE:
        click.echo("❌ 서비스 중지 기능을 사용할 수 없습니다.", err=True)
        return
    
    pm = PortManager(project_name=project_name, global_mode=global_mode)
    
    click.echo(f"⏹️ '{project_name}' 서비스 중지 중...")
    
    if remove_volumes:
        # 볼륨도 함께 제거
        import subprocess
        try:
            subprocess.run(['docker-compose', 'down', '-v'], 
                         cwd=Path.cwd(), capture_output=True)
        except Exception:
            pass
    
    if pm.stop_services():
        click.echo("✅ 서비스 중지 완료")
    else:
        click.echo("❌ 서비스 중지 실패")

@cli.command()
@click.option('--format', 'output_format', type=click.Choice(['table', 'json', 'yaml']), default='table')
@click.option('--show-urls', is_flag=True, help='서비스 URL 표시')
@click.pass_context
@safe_port_manager_operation
def status(ctx, output_format, show_urls):
    """📊 프로젝트 상태 조회"""
    
    project_name = ctx.obj['project']
    global_mode = ctx.obj['global_mode']
    
    if not CORE_MODULES_AVAILABLE:
        click.echo("❌ 상태 조회 기능을 사용할 수 없습니다.", err=True)
        return
    
    pm = PortManager(project_name=project_name, global_mode=global_mode)
    
    report = pm.get_status_report()
    
    if output_format == 'table':
        _display_status_table(report, show_urls)
    elif output_format == 'json':
        click.echo(json.dumps(report, indent=2, ensure_ascii=False))
    elif output_format == 'yaml' and YAML_AVAILABLE:
        click.echo(yaml.dump(report, allow_unicode=True))
    else:
        click.echo("❌ YAML 출력을 위해서는 PyYAML이 필요합니다.", err=True)

def _display_status_table(report: Dict, show_urls: bool = False):
    """상태 보고서를 테이블 형식으로 출력"""
    click.echo(f"\n📊 프로젝트 상태: {report['project_name']}")
    click.echo("=" * 70)
    
    # 시스템 상태 표시
    system_status = report.get('system_status', {})
    if system_status:
        click.echo("\n🔧 시스템 상태:")
        features = system_status.get('available_features', {})
        for feature, available in features.items():
            status = "✅" if available else "❌"
            feature_name = feature.replace('_', ' ').title()
            click.echo(f"  {status} {feature_name}")
    
    if report['services']:
        click.echo("\n🔌 할당된 포트:")
        header = f"{'서비스':<15} {'포트':<8} {'타입':<12} {'상태':<10}"
        if show_urls:
            header += f" {'URL':<30}"
        click.echo(header)
        click.echo("-" * (50 if not show_urls else 80))
        
        for service_name, service_info in report['services'].items():
            status_color = 'green' if service_info['status'] == 'available' else 'red'
            
            line = (
                f"{service_name:<15} "
                f"{service_info['port']:<8} "
                f"{service_info['type']:<12} "
                f"{click.style(service_info['status'], fg=status_color):<18}"
            )
            
            if show_urls and service_info.get('url'):
                line += f" {service_info['url']:<30}"
            
            click.echo(line)
    else:
        click.echo("\n🔌 할당된 포트가 없습니다.")
    
    if report.get('conflicts'):
        click.echo(f"\n⚠️ 포트 충돌: {len(report['conflicts'])}건")
        for port, conflict_info in report['conflicts'].items():
            click.echo(f"  - {port}: {conflict_info.get('description', 'Port conflict')}")

@cli.command()
@click.option('--deep-clean', is_flag=True, help='완전 정리 (백업 파일도 제거)')
@click.pass_context
@safe_port_manager_operation
def cleanup(ctx, deep_clean):
    """🧹 정리 작업 수행"""
    
    project_name = ctx.obj['project']
    global_mode = ctx.obj['global_mode']
    
    if not CORE_MODULES_AVAILABLE:
        click.echo("❌ 정리 기능을 사용할 수 없습니다.", err=True)
        return
    
    pm = PortManager(project_name=project_name, global_mode=global_mode)
    
    click.echo("🧹 정리 작업 수행 중...")
    
    results = pm.cleanup()
    
    if deep_clean:
        # 추가 정리 작업
        config_dir = Path.cwd() / '.port-manager'
        if config_dir.exists():
            import shutil
            try:
                shutil.rmtree(config_dir)
                results['cleaned_directories'] = 1
                click.echo("  📁 설정 디렉토리 제거")
            except Exception as e:
                click.echo(f"⚠️ 설정 디렉토리 제거 실패: {e}")
    
    click.echo("✅ 정리 완료!")
    click.echo(f"  - 포트: {results.get('cleaned_ports', 0)}개")
    click.echo(f"  - 파일: {results.get('cleaned_files', 0)}개")
    if deep_clean and results.get('cleaned_directories'):
        click.echo(f"  - 디렉토리: {results['cleaned_directories']}개")

@cli.command()
@click.option('--group', default='minimal', type=click.Choice(['minimal', 'advanced', 'docker', 'full']),
              help='확인할 의존성 그룹')
@click.option('--fix', is_flag=True, help='누락된 의존성 자동 설치 시도')
@click.option('--report', is_flag=True, help='상세 의존성 보고서 출력')
@click.pass_context
def doctor(ctx, group, fix, report):
    """🩺 시스템 진단 및 문제 해결 가이드"""
    
    click.echo("🩺 시스템 진단 중...")
    click.echo("=" * 50)
    
    # 의존성 관리자를 사용한 고급 진단
    if CORE_MODULES_AVAILABLE and DependencyManager:
        try:
            dm = DependencyManager()
            
            if report:
                # 상세 보고서
                dependency_report = dm.create_dependency_report()
                click.echo("\n📊 상세 의존성 보고서:")
                click.echo("=" * 30)
                
                for group_name, group_status in dependency_report['groups'].items():
                    completeness = group_status['completeness'] * 100
                    status_icon = "✅" if group_status['is_functional'] else "❌"
                    click.echo(f"\n{status_icon} {group_name}: {completeness:.0f}% 완성")
                    click.echo(f"   {group_status['description']}")
                    
                    if group_status['missing_required']:
                        click.echo(f"   누락된 필수: {', '.join(group_status['missing_required'])}")
                    if group_status['missing_optional']:
                        click.echo(f"   누락된 선택적: {', '.join(group_status['missing_optional'])}")
                
                # 권장사항
                if dependency_report['recommendations']:
                    click.echo(f"\n💡 권장사항:")
                    for rec in dependency_report['recommendations']:
                        priority_icon = "🔴" if rec['priority'] == 'critical' else "🟡"
                        click.echo(f"   {priority_icon} {rec['message']}")
                        click.echo(f"      실행: {rec['action']}")
            
            elif fix:
                # 자동 수정 시도
                click.echo(f"\n🔧 '{group}' 그룹 의존성 자동 설치 중...")
                results = dm.install_missing_dependencies(group, auto_install=True)
                
                if results['successful']:
                    click.echo(f"✅ 성공적으로 설치: {', '.join(results['successful'])}")
                
                if results['failed']:
                    click.echo(f"\n❌ 설치 실패:")
                    for failure in results['failed']:
                        if isinstance(failure, dict):
                            click.echo(f"   {failure['package']}: {failure['error']}")
                        else:
                            click.echo(f"   {failure}")
                
                if results['skipped']:
                    click.echo(f"\n⏭️ 건너뛴 패키지: {len(results['skipped'])}개")
            
            else:
                # 기본 진단 및 가이드
                guide = dm.get_installation_guide(group)
                click.echo(guide)
                
        except Exception as e:
            click.echo(f"⚠️ 고급 진단 실패: {e}")
            click.echo("기본 진단으로 전환...")
            # 기본 진단으로 fallback
            _basic_system_diagnosis()
    else:
        # 기본 진단 시스템
        _basic_system_diagnosis()
    
    # 빠른 설정 가이드
    click.echo(f"\n🚀 빠른 설정 가이드:")
    click.echo(f"  1. 포트 할당: python3 -m universal_port_manager allocate frontend backend")
    click.echo(f"  2. 설정 생성: python3 -m universal_port_manager generate")  
    click.echo(f"  3. 서비스 시작: python3 -m universal_port_manager start")

def _basic_system_diagnosis():
    """기본 시스템 진단 (의존성 관리자 없이)"""
    requirements = CLIHelper.check_system_requirements()
    
    issues = []
    recommendations = []
    
    if not requirements['core_modules']:
        issues.append("핵심 모듈을 불러올 수 없음")
        recommendations.append("모듈 설치 확인: pip install -r requirements-minimal.txt")
    
    if not requirements['yaml_support']:
        issues.append("YAML 지원 없음")
        recommendations.append("PyYAML 설치: pip install PyYAML")
    
    if not requirements['docker']:
        issues.append("Docker 없음")
        recommendations.append("Docker 설치: https://docs.docker.com/get-docker/")
    
    if not requirements['docker_compose']:
        issues.append("Docker Compose 없음")
        recommendations.append("Docker Compose 설치: https://docs.docker.com/compose/install/")
    
    # 진단 결과 출력
    if issues:
        click.echo(f"\n❌ 발견된 문제: {len(issues)}개")
        for i, issue in enumerate(issues, 1):
            click.echo(f"  {i}. {issue}")
        
        click.echo(f"\n💡 권장 해결방법:")
        for i, rec in enumerate(recommendations, 1):
            click.echo(f"  {i}. {rec}")
    else:
        click.echo("\n✅ 모든 시스템 요구사항이 충족되었습니다!")

if __name__ == '__main__':
    cli()