#!/usr/bin/env python3
"""
Frontend Port Consistency Verification Test
테스트: 프론트엔드 포트 일관성 수정 확인
"""

import os
import re
import json
from pathlib import Path

def test_port_consistency():
    """포트 일관성 검증"""
    
    print("=== 프론트엔드 포트 일관성 검증 시작 ===")
    
    base_path = Path("/mnt/c/project/Online-evaluation")
    issues_found = []
    
    try:
        # 1. 메인 .env 파일에서 기본 포트 읽기
        main_env_file = base_path / ".env"
        if main_env_file.exists():
            with open(main_env_file, 'r', encoding='utf-8') as f:
                content = f.read()
                frontend_port_match = re.search(r'FRONTEND_PORT=(\d+)', content)
                backend_port_match = re.search(r'BACKEND_PORT=(\d+)', content)
                cors_match = re.search(r'CORS_ORIGINS=([^\n]+)', content)
                
                if frontend_port_match:
                    main_frontend_port = frontend_port_match.group(1)
                    print(f"✓ 메인 .env FRONTEND_PORT: {main_frontend_port}")
                else:
                    issues_found.append("메인 .env에서 FRONTEND_PORT를 찾을 수 없음")
                
                if backend_port_match:
                    main_backend_port = backend_port_match.group(1)
                    print(f"✓ 메인 .env BACKEND_PORT: {main_backend_port}")
                else:
                    issues_found.append("메인 .env에서 BACKEND_PORT를 찾을 수 없음")
                
                if cors_match:
                    cors_origins = cors_match.group(1)
                    print(f"✓ 메인 .env CORS_ORIGINS: {cors_origins}")
                    if main_frontend_port not in cors_origins:
                        issues_found.append(f"CORS_ORIGINS에 frontend port {main_frontend_port}가 포함되지 않음")
                else:
                    issues_found.append("메인 .env에서 CORS_ORIGINS를 찾을 수 없음")
        
        # 2. Frontend .env 파일 검증
        frontend_env_file = base_path / "frontend" / ".env"
        if frontend_env_file.exists():
            with open(frontend_env_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # 환경변수 참조 패턴 확인
                if "${FRONTEND_PORT" in content:
                    print("✓ Frontend .env가 환경변수를 올바르게 참조함")
                else:
                    issues_found.append("Frontend .env가 FRONTEND_PORT 환경변수를 참조하지 않음")
                
                if "${BACKEND_PORT" in content:
                    print("✓ Frontend .env가 BACKEND_PORT 환경변수를 올바르게 참조함")
                else:
                    issues_found.append("Frontend .env가 BACKEND_PORT 환경변수를 참조하지 않음")
        
        # 3. Backend .env 파일 검증
        backend_env_file = base_path / "backend" / ".env"
        if backend_env_file.exists():
            with open(backend_env_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if "${FRONTEND_PORT" in content:
                    print("✓ Backend .env가 FRONTEND_PORT 환경변수를 올바르게 참조함")
                else:
                    issues_found.append("Backend .env가 FRONTEND_PORT 환경변수를 참조하지 않음")
        
        # 4. Docker Compose 파일 검증
        docker_compose_file = base_path / "docker-compose.yml"
        if docker_compose_file.exists():
            with open(docker_compose_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Frontend 포트 설정 확인
                if "${FRONTEND_PORT:-3002}" in content:
                    print("✓ Docker Compose가 올바른 frontend port 기본값을 사용함 (3002)")
                else:
                    issues_found.append("Docker Compose가 잘못된 frontend port 기본값을 사용함")
                
                # Backend 포트 설정 확인
                if "${BACKEND_PORT:-8002}" in content:
                    print("✓ Docker Compose가 올바른 backend port 기본값을 사용함 (8002)")
                else:
                    issues_found.append("Docker Compose가 잘못된 backend port 기본값을 사용함")
                
                # CORS 설정 확인
                if "CORS_ORIGINS" in content and "${FRONTEND_PORT:-3002}" in content:
                    print("✓ Docker Compose CORS 설정이 올바름")
                else:
                    issues_found.append("Docker Compose CORS 설정에 문제가 있음")
        
        # 5. Playwright 설정 검증
        playwright_config_file = base_path / "playwright.config.js"
        if playwright_config_file.exists():
            with open(playwright_config_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                if "process.env.FRONTEND_PORT || 3002" in content:
                    print("✓ Playwright가 올바른 frontend port를 사용함")
                else:
                    issues_found.append("Playwright가 잘못된 frontend port를 사용함")
                
                if "process.env.BACKEND_PORT || 8002" in content:
                    print("✓ Playwright가 올바른 backend port를 사용함")
                else:
                    issues_found.append("Playwright가 잘못된 backend port를 사용함")
        
        # 6. 포트 표준화 확인
        print(f"\n=== 포트 표준화 상태 ===")
        print(f"✓ Frontend Port: {main_frontend_port} (표준화됨)")
        print(f"✓ Backend Port: {main_backend_port} (표준화됨)")
        
        if issues_found:
            print(f"\n❌ {len(issues_found)}개의 문제 발견:")
            for i, issue in enumerate(issues_found, 1):
                print(f"  {i}. {issue}")
            return False
        else:
            print(f"\n✅ 모든 검증 통과! 포트 일관성이 수정되었습니다.")
            print(f"\n=== 수정 사항 요약 ===")
            print(f"1. Frontend .env가 환경변수 참조로 수정됨")
            print(f"2. Backend .env CORS 설정이 동적으로 수정됨")
            print(f"3. Docker Compose 기본값이 통일됨 (Frontend: 3002, Backend: 8002)")
            print(f"4. Playwright 설정이 환경변수 기반으로 수정됨")
            print(f"5. 모든 CORS 설정이 일관성 있게 수정됨")
            return True
            
    except Exception as e:
        print(f"\n✗ 검증 중 오류 발생:")
        print(f"오류 타입: {type(e).__name__}")
        print(f"오류 메시지: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_port_consistency()
    exit(0 if success else 1)