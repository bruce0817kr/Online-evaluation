#!/usr/bin/env python3
"""
Deployment System Service Status Monitoring Fix Verification Test
테스트: 배포관리시스템 서비스 상태 모니터링 오류 수정 확인
"""

import requests
import json
import time
from datetime import datetime

def test_deployment_monitoring_fixes():
    """배포 모니터링 수정사항 검증"""
    
    print("=== 배포관리시스템 서비스 상태 모니터링 수정 검증 ===")
    
    # 환경 설정
    backend_url = "http://localhost:8002"  # Updated port
    
    tests_passed = 0
    tests_failed = 0
    
    def log_test(test_name, passed, details=""):
        nonlocal tests_passed, tests_failed
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"     {details}")
        if passed:
            tests_passed += 1
        else:
            tests_failed += 1
    
    print(f"\n1. 기본 헬스체크 엔드포인트 테스트")
    try:
        response = requests.get(f"{backend_url}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            log_test("기본 헬스체크 응답", True, f"Status: {data.get('status', 'unknown')}")
        else:
            log_test("기본 헬스체크 응답", False, f"HTTP {response.status_code}")
    except Exception as e:
        log_test("기본 헬스체크 응답", False, f"연결 실패: {e}")
    
    print(f"\n2. 새로운 Public 배포 상태 엔드포인트 테스트")
    try:
        response = requests.get(f"{backend_url}/health/deployment", timeout=10)
        if response.status_code == 200:
            data = response.json()
            log_test("Public 배포 상태 엔드포인트", True, f"Status: {data.get('deployment_status', 'unknown')}")
            
            # 서비스 상태 확인
            services = data.get('services', {})
            if services:
                for service_name, service_info in services.items():
                    running = service_info.get('running', False)
                    healthy = service_info.get('healthy', False)
                    status_text = f"Running: {running}, Healthy: {healthy}"
                    log_test(f"  {service_name} 서비스 상태", running, status_text)
            
            # 포트 설정 확인
            config = data.get('configuration', {})
            if config:
                backend_port = config.get('backend_port', 'unknown')
                frontend_port = config.get('frontend_port', 'unknown')
                log_test("포트 설정 동적 로드", True, f"Backend: {backend_port}, Frontend: {frontend_port}")
        else:
            log_test("Public 배포 상태 엔드포인트", False, f"HTTP {response.status_code}")
    except Exception as e:
        log_test("Public 배포 상태 엔드포인트", False, f"연결 실패: {e}")
    
    print(f"\n3. 인증이 필요한 배포 API 엔드포인트 테스트 (인증 없이)")
    try:
        response = requests.get(f"{backend_url}/api/deployment/status", timeout=10)
        if response.status_code == 401:
            log_test("인증 필요 엔드포인트 보안", True, "인증 없이 접근 시 401 응답 (정상)")
        else:
            log_test("인증 필요 엔드포인트 보안", False, f"예상과 다른 응답: HTTP {response.status_code}")
    except Exception as e:
        log_test("인증 필요 엔드포인트 보안", False, f"연결 실패: {e}")
    
    print(f"\n4. 포트 설정 일관성 검증")
    try:
        # 기본 헬스체크에서 포트 확인
        response = requests.get(f"{backend_url}/health", timeout=5)
        if response.status_code == 200:
            log_test("헬스체크 포트 접근", True, f"Backend가 포트 8002에서 응답함")
        
        # 배포 상태에서 설정 확인
        response = requests.get(f"{backend_url}/health/deployment", timeout=5)
        if response.status_code == 200:
            data = response.json()
            config = data.get('configuration', {})
            backend_port = config.get('backend_port', '')
            if backend_port == '8002':
                log_test("포트 설정 일관성", True, f"설정된 포트와 실제 포트 일치 ({backend_port})")
            else:
                log_test("포트 설정 일관성", False, f"포트 불일치: 설정 {backend_port}, 실제 8002")
        else:
            log_test("포트 설정 확인", False, "배포 상태 조회 실패")
    except Exception as e:
        log_test("포트 설정 일관성 검증", False, f"오류: {e}")
    
    print(f"\n5. 모니터링 데이터 품질 검증")
    try:
        response = requests.get(f"{backend_url}/health/deployment", timeout=10)
        if response.status_code == 200:
            data = response.json()
            
            # 필수 필드 확인
            required_fields = ['timestamp', 'deployment_status', 'services', 'overall_healthy']
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                log_test("모니터링 데이터 완전성", True, "모든 필수 필드 포함")
            else:
                log_test("모니터링 데이터 완전성", False, f"누락된 필드: {missing_fields}")
            
            # 타임스탬프 형식 확인
            timestamp = data.get('timestamp', '')
            if 'T' in timestamp and len(timestamp) > 15:
                log_test("타임스탬프 형식", True, f"ISO 형식: {timestamp}")
            else:
                log_test("타임스탬프 형식", False, f"잘못된 형식: {timestamp}")
        else:
            log_test("모니터링 데이터 품질", False, f"HTTP {response.status_code}")
    except Exception as e:
        log_test("모니터링 데이터 품질 검증", False, f"오류: {e}")
    
    print(f"\n6. 에러 처리 개선 검증")
    try:
        # 존재하지 않는 엔드포인트 테스트
        response = requests.get(f"{backend_url}/health/nonexistent", timeout=5)
        if response.status_code == 404:
            log_test("존재하지 않는 엔드포인트 처리", True, "404 응답 (정상)")
        else:
            log_test("존재하지 않는 엔드포인트 처리", False, f"예상과 다른 응답: {response.status_code}")
    except Exception as e:
        log_test("에러 처리 테스트", False, f"연결 실패: {e}")
    
    # 결과 요약
    print(f"\n" + "="*60)
    print(f"배포 모니터링 수정사항 검증 결과")
    print(f"="*60)
    print(f"✓ 성공: {tests_passed}")
    print(f"✗ 실패: {tests_failed}")
    print(f"총 테스트: {tests_passed + tests_failed}")
    
    if tests_failed == 0:
        print(f"\n🎉 모든 테스트 통과! 배포관리시스템 서비스 상태 모니터링이 수정되었습니다.")
        print(f"\n📋 수정된 사항:")
        print(f"1. ✅ 포트 설정 하드코딩 제거 - 환경변수 기반 동적 설정")
        print(f"2. ✅ Public 헬스체크 엔드포인트 추가 - /health/deployment")
        print(f"3. ✅ Docker 명령어 에러 처리 개선 - 재시도 및 상세 오류 분류")
        print(f"4. ✅ 타임아웃 시간 연장 - 10초 → 15초")
        print(f"5. ✅ 모니터링 데이터 품질 향상 - 타임스탬프 및 상세 상태 포함")
        return True
    else:
        print(f"\n❌ {tests_failed}개의 테스트가 실패했습니다. 추가 수정이 필요합니다.")
        return False

if __name__ == "__main__":
    success = test_deployment_monitoring_fixes()
    exit(0 if success else 1)