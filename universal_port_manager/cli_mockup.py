#!/usr/bin/env python3
"""
Universal Port Manager CLI - Mockup Version
===========================================

의존성 없이 CLI 구조를 테스트할 수 있는 목업 버전
실제 기능은 동작하지 않지만 CLI 구조와 인자 파싱을 확인할 수 있음
"""

import click
import json
from typing import List, Dict
from pathlib import Path

@click.group()
@click.option('--project', '-p', default=None, help='프로젝트 이름')
@click.option('--global-mode/--local-mode', default=True, help='전역/로컬 모드')
@click.option('--verbose', '-v', is_flag=True, help='상세 출력')
@click.pass_context
def cli(ctx, project, global_mode, verbose):
    """
    Universal Port Manager CLI (Mockup Version)
    
    여러 프로젝트 간 포트 충돌 방지 및 자동 할당 도구
    """
    ctx.ensure_object(dict)
    ctx.obj['project'] = project or Path.cwd().name
    ctx.obj['global_mode'] = global_mode
    ctx.obj['verbose'] = verbose
    
    if verbose:
        click.echo(f"🔧 Debug Mode: project={ctx.obj['project']}, global_mode={global_mode}")

@cli.command()
@click.option('--range', 'port_range', default='3000-9999', help='스캔할 포트 범위 (예: 3000-9999)')
@click.option('--format', 'output_format', type=click.Choice(['table', 'json', 'yaml']), default='table')
@click.pass_context
def scan(ctx, port_range, output_format):
    """시스템 포트 스캔 (Mockup)"""
    click.echo(f"📡 [MOCKUP] 포트 스캔 시뮬레이션 ({port_range})")
    click.echo(f"   형식: {output_format}")
    click.echo(f"   프로젝트: {ctx.obj['project']}")
    
    # 목업 데이터
    mock_ports = {
        3000: {"status": "available", "process": None},
        3001: {"status": "occupied", "process": "node"},
        8080: {"status": "available", "process": None},
        27017: {"status": "occupied", "process": "mongod"}
    }
    
    if output_format == 'json':
        click.echo(json.dumps(mock_ports, indent=2))
    else:
        click.echo("\n📊 포트 상태 (목업 데이터):")
        for port, info in mock_ports.items():
            status = "🟢 사용가능" if info["status"] == "available" else "🔴 사용중"
            process = f" ({info['process']})" if info["process"] else ""
            click.echo(f"  {port}: {status}{process}")

@cli.command()
@click.argument('services', nargs=-1, required=True)
@click.option('--template', '-t', help='사용할 서비스 템플릿')
@click.option('--preferred-ports', help='선호 포트 (JSON 형식)')
@click.option('--auto-detect/--no-auto-detect', default=True, help='프로젝트 자동 감지')
@click.pass_context
def allocate(ctx, services, template, preferred_ports, auto_detect):
    """서비스에 포트 할당 (Mockup)"""
    project_name = ctx.obj['project']
    
    click.echo(f"🎯 [MOCKUP] 프로젝트 '{project_name}'의 포트 할당 시뮬레이션")
    click.echo(f"   서비스: {', '.join(services)}")
    click.echo(f"   템플릿: {template or 'None'}")
    click.echo(f"   선호 포트: {preferred_ports or 'None'}")
    click.echo(f"   자동 감지: {auto_detect}")
    
    # 목업 포트 할당
    mock_allocations = {}
    base_port = 3000
    
    for i, service in enumerate(services):
        allocated_port = base_port + i * 100
        mock_allocations[service] = allocated_port
        click.echo(f"  🔌 {service:<15}: {allocated_port}")
    
    click.echo("\n✅ [MOCKUP] 포트 할당 시뮬레이션 완료!")

@cli.command()
@click.option('--include-override/--no-override', default=True, help='override 파일 포함')
@click.option('--template', '-t', help='서비스 템플릿')
@click.pass_context
def generate(ctx, include_override, template):
    """Docker Compose 및 환경 파일 생성 (Mockup)"""
    project_name = ctx.obj['project']
    
    click.echo(f"📝 [MOCKUP] '{project_name}' 설정 파일 생성 시뮬레이션")
    click.echo("   생성될 파일들:")
    click.echo("   📦 docker-compose.yml")
    if include_override:
        click.echo("   📦 docker-compose.override.yml")
    click.echo("   🔧 .env")
    click.echo("   🚀 start.sh")
    click.echo("\n✅ [MOCKUP] 설정 파일 생성 시뮬레이션 완료!")

@cli.command()
@click.option('--build', is_flag=True, help='이미지 빌드')
@click.pass_context
def start(ctx, build):
    """서비스 시작 (Mockup)"""
    project_name = ctx.obj['project']
    
    click.echo(f"🚀 [MOCKUP] '{project_name}' 서비스 시작 시뮬레이션")
    if build:
        click.echo("   🔨 이미지 빌드 시뮬레이션")
    click.echo("   🐳 Docker Compose 시작 시뮬레이션")
    click.echo("\n✅ [MOCKUP] 서비스 시작 시뮬레이션 완료!")

@cli.command()
@click.pass_context
def stop(ctx):
    """서비스 중지 (Mockup)"""
    project_name = ctx.obj['project']
    
    click.echo(f"⏹️ [MOCKUP] '{project_name}' 서비스 중지 시뮬레이션")
    click.echo("✅ [MOCKUP] 서비스 중지 시뮬레이션 완료!")

@cli.command()
@click.argument('services', nargs=-1)
@click.pass_context
def release(ctx, services):
    """포트 해제 (Mockup)"""
    project_name = ctx.obj['project']
    
    if services:
        click.echo(f"🔓 [MOCKUP] 특정 서비스 포트 해제 시뮬레이션: {', '.join(services)}")
    else:
        click.echo(f"🔓 [MOCKUP] '{project_name}' 전체 포트 해제 시뮬레이션")
    
    click.echo("✅ [MOCKUP] 포트 해제 시뮬레이션 완료!")

@cli.command()
@click.option('--format', 'output_format', type=click.Choice(['table', 'json', 'yaml']), default='table')
@click.pass_context
def status(ctx, output_format):
    """프로젝트 상태 조회 (Mockup)"""
    project_name = ctx.obj['project']
    
    click.echo(f"📊 [MOCKUP] 프로젝트 '{project_name}' 상태 시뮬레이션")
    
    mock_status = {
        "project_name": project_name,
        "services": {
            "frontend": {"port": 3000, "status": "running"},
            "backend": {"port": 8080, "status": "running"},
            "mongodb": {"port": 27017, "status": "running"}
        },
        "conflicts": 0
    }
    
    if output_format == 'json':
        click.echo(json.dumps(mock_status, indent=2))
    else:
        click.echo("\n🔌 할당된 포트 (목업 데이터):")
        for service, info in mock_status["services"].items():
            status_icon = "🟢" if info["status"] == "running" else "🔴"
            click.echo(f"  {service:<15}: {info['port']} {status_icon}")

@cli.command()
@click.option('--type', 'list_type', type=click.Choice(['services', 'templates', 'projects']), default='services')
@click.pass_context
def list(ctx, list_type):
    """서비스, 템플릿, 프로젝트 목록 조회 (Mockup)"""
    
    click.echo(f"📋 [MOCKUP] {list_type} 목록 시뮬레이션:")
    
    if list_type == 'services':
        mock_services = [
            "frontend (web) - React/Vue.js 프론트엔드",
            "backend (api) - Express/FastAPI 백엔드", 
            "mongodb (database) - MongoDB 데이터베이스",
            "redis (cache) - Redis 캐시 서버"
        ]
        for service in mock_services:
            click.echo(f"  {service}")
    
    elif list_type == 'templates':
        mock_templates = [
            "fullstack - 프론트엔드 + 백엔드 + 데이터베이스",
            "api-only - 백엔드 API 서버만",
            "microservices - 마이크로서비스 아키텍처"
        ]
        for template in mock_templates:
            click.echo(f"  {template}")
    
    elif list_type == 'projects':
        mock_projects = [
            "online-evaluation - 3개 서비스",
            "my-app - 2개 서비스",
            "test-project - 1개 서비스"
        ]
        for project in mock_projects:
            click.echo(f"  {project}")

@cli.command()
@click.pass_context
def cleanup(ctx):
    """정리 작업 수행 (Mockup)"""
    project_name = ctx.obj['project']
    
    click.echo(f"🧹 [MOCKUP] '{project_name}' 정리 작업 시뮬레이션")
    click.echo("   정리된 항목:")
    click.echo("   - 포트: 3개")
    click.echo("   - 파일: 2개")
    click.echo("✅ [MOCKUP] 정리 시뮬레이션 완료!")

@cli.command()
@click.argument('project_path', type=click.Path(exists=True))
@click.pass_context
def detect(ctx, project_path):
    """프로젝트에서 서비스 자동 감지 (Mockup)"""
    click.echo(f"🔍 [MOCKUP] '{project_path}' 서비스 감지 시뮬레이션")
    
    mock_detected = [
        "frontend (React 앱 감지됨)",
        "backend (FastAPI 서버 감지됨)",
        "mongodb (docker-compose.yml에서 감지됨)"
    ]
    
    click.echo(f"   감지된 서비스 ({len(mock_detected)}개):")
    for service in mock_detected:
        click.echo(f"  {service}")

if __name__ == '__main__':
    cli()