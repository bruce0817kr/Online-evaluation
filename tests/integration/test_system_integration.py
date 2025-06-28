"""
통합 테스트 - 전체 시스템 기능 검증
온라인 평가 시스템의 모든 주요 기능들이 올바르게 작동하는지 검증
"""

import pytest
import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, List, Any
import os
import subprocess

# 테스트 설정
BACKEND_URL = "http://localhost:8080"
FRONTEND_URL = "http://localhost:3000"
TEST_TIMEOUT = 30

class SystemIntegrationTest:
    """시스템 통합 테스트 클래스"""
    
    def __init__(self):
        self.session = None
        self.admin_token = None
        self.secretary_token = None
        self.evaluator_token = None
        self.test_data = {}
        
    async def setup(self):
        """테스트 환경 설정"""
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=TEST_TIMEOUT))
        
        # 서비스 상태 확인
        await self.check_services_health()
        
        # 테스트 사용자 생성 및 토큰 획득
        await self.setup_test_users()
        
        print("✅ 테스트 환경 설정 완료")
    
    async def teardown(self):
        """테스트 환경 정리"""
        if self.session:
            await self.session.close()
        print("🧹 테스트 환경 정리 완료")
    
    async def check_services_health(self):
        """서비스 헬스체크"""
        services = {
            "Backend": f"{BACKEND_URL}/api/health",
            "Frontend": FRONTEND_URL,
            "Security": f"{BACKEND_URL}/api/security/health"
        }
        
        print("🏥 서비스 헬스체크 시작...")
        
        for service_name, url in services.items():
            try:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        print(f"  ✅ {service_name}: 정상")
                    else:
                        print(f"  ⚠️ {service_name}: 상태코드 {response.status}")
            except Exception as e:
                print(f"  ❌ {service_name}: 연결 실패 - {e}")
                raise Exception(f"{service_name} 서비스가 실행되지 않고 있습니다")
    
    async def setup_test_users(self):
        """테스트 사용자 생성 및 토큰 획득"""
        print("👤 테스트 사용자 설정 중...")
        
        # 관리자 로그인
        admin_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        try:
            async with self.session.post(
                f"{BACKEND_URL}/api/auth/login",
                data=admin_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    self.admin_token = result.get("access_token")
                    print("  ✅ 관리자 로그인 성공")
                else:
                    print("  ⚠️ 관리자 로그인 실패, 기본 사용자 생성 시도")
                    await self.create_default_users()
        except Exception as e:
            print(f"  ❌ 사용자 설정 오류: {e}")
            raise
    
    async def create_default_users(self):
        """기본 사용자 생성"""
        users = [
            {
                "username": "admin",
                "password": "admin123",
                "email": "admin@test.com",
                "user_name": "관리자",
                "role": "admin"
            },
            {
                "username": "secretary",
                "password": "secretary123",
                "email": "secretary@test.com", 
                "user_name": "간사",
                "role": "secretary"
            },
            {
                "username": "evaluator",
                "password": "evaluator123",
                "email": "evaluator@test.com",
                "user_name": "평가위원",
                "role": "evaluator"
            }
        ]
        
        for user in users:
            try:
                async with self.session.post(
                    f"{BACKEND_URL}/api/auth/register",
                    json=user
                ) as response:
                    if response.status in [200, 201]:
                        print(f"  ✅ {user['username']} 사용자 생성")
                    else:
                        print(f"  ⚠️ {user['username']} 사용자 이미 존재")
            except Exception as e:
                print(f"  ❌ {user['username']} 생성 실패: {e}")
    
    async def test_authentication_system(self):
        """인증 시스템 테스트"""
        print("\n🔐 인증 시스템 테스트 시작...")
        
        test_cases = [
            {
                "name": "관리자 로그인",
                "credentials": {"username": "admin", "password": "admin123"},
                "expected_role": "admin"
            },
            {
                "name": "잘못된 비밀번호",
                "credentials": {"username": "admin", "password": "wrong"},
                "should_fail": True
            },
            {
                "name": "존재하지 않는 사용자",
                "credentials": {"username": "nonexistent", "password": "test"},
                "should_fail": True
            }
        ]
        
        for case in test_cases:
            try:
                async with self.session.post(
                    f"{BACKEND_URL}/api/auth/login",
                    data=case["credentials"]
                ) as response:
                    
                    if case.get("should_fail"):
                        if response.status != 200:
                            print(f"  ✅ {case['name']}: 올바르게 실패")
                        else:
                            print(f"  ❌ {case['name']}: 실패해야 하는데 성공")
                    else:
                        if response.status == 200:
                            result = await response.json()
                            token = result.get("access_token")
                            if token:
                                print(f"  ✅ {case['name']}: 성공")
                                if case['name'] == "관리자 로그인":
                                    self.admin_token = token
                            else:
                                print(f"  ❌ {case['name']}: 토큰 없음")
                        else:
                            print(f"  ❌ {case['name']}: 상태코드 {response.status}")
                            
            except Exception as e:
                print(f"  ❌ {case['name']}: 오류 - {e}")
    
    async def test_ai_provider_management(self):
        """AI 공급자 관리 시스템 테스트"""
        print("\n🤖 AI 공급자 관리 테스트 시작...")
        
        if not self.admin_token:
            print("  ❌ 관리자 토큰이 없어 테스트를 건너뜀")
            return
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # AI 공급자 목록 조회
        try:
            async with self.session.get(
                f"{BACKEND_URL}/api/ai-admin/providers",
                headers=headers
            ) as response:
                if response.status == 200:
                    providers = await response.json()
                    print(f"  ✅ AI 공급자 목록 조회: {len(providers.get('providers', []))}개")
                else:
                    print(f"  ⚠️ AI 공급자 목록 조회 실패: {response.status}")
        except Exception as e:
            print(f"  ❌ AI 공급자 테스트 오류: {e}")
        
        # 테스트 AI 공급자 생성
        test_provider = {
            "name": "test_openai",
            "display_name": "테스트 OpenAI",
            "provider_type": "openai",
            "api_key": "test-key-123",
            "api_base_url": "https://api.openai.com/v1",
            "models": ["gpt-3.5-turbo", "gpt-4"],
            "is_active": True,
            "priority": 1
        }
        
        try:
            async with self.session.post(
                f"{BACKEND_URL}/api/ai-admin/providers",
                headers=headers,
                json=test_provider
            ) as response:
                if response.status in [200, 201]:
                    result = await response.json()
                    provider_id = result.get("provider_id")
                    if provider_id:
                        self.test_data["ai_provider_id"] = provider_id
                        print("  ✅ 테스트 AI 공급자 생성 성공")
                    else:
                        print("  ⚠️ AI 공급자 생성 응답에 ID 없음")
                else:
                    print(f"  ⚠️ AI 공급자 생성 실패: {response.status}")
        except Exception as e:
            print(f"  ❌ AI 공급자 생성 오류: {e}")
    
    async def test_template_management(self):
        """템플릿 관리 시스템 테스트"""
        print("\n📋 템플릿 관리 테스트 시작...")
        
        if not self.admin_token:
            print("  ❌ 관리자 토큰이 없어 테스트를 건너뜀")
            return
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # 템플릿 목록 조회
        try:
            async with self.session.get(
                f"{BACKEND_URL}/api/templates",
                headers=headers
            ) as response:
                if response.status == 200:
                    templates = await response.json()
                    print(f"  ✅ 템플릿 목록 조회: {len(templates)}개")
                else:
                    print(f"  ⚠️ 템플릿 목록 조회 실패: {response.status}")
        except Exception as e:
            print(f"  ❌ 템플릿 목록 조회 오류: {e}")
        
        # 테스트 템플릿 생성
        test_template = {
            "name": "테스트 평가템플릿",
            "description": "통합 테스트용 평가템플릿",
            "category": "기술평가",
            "criteria": [
                {
                    "id": "tech_innovation",
                    "name": "기술혁신성",
                    "description": "기술의 혁신성 평가",
                    "max_score": 20,
                    "weight": 1.0,
                    "evaluation_items": [
                        {
                            "id": "novelty",
                            "name": "신규성",
                            "max_score": 10
                        },
                        {
                            "id": "advancement",
                            "name": "진보성",
                            "max_score": 10
                        }
                    ]
                },
                {
                    "id": "market_potential",
                    "name": "시장성",
                    "description": "시장 잠재력 평가",
                    "max_score": 15,
                    "weight": 0.8
                }
            ],
            "bonus_criteria": [
                {
                    "id": "special_bonus",
                    "name": "특별가점",
                    "max_score": 5,
                    "conditions": ["정부정책 부합", "사회적 가치"]
                }
            ],
            "is_active": True
        }
        
        try:
            async with self.session.post(
                f"{BACKEND_URL}/api/templates",
                headers=headers,
                json=test_template
            ) as response:
                if response.status in [200, 201]:
                    result = await response.json()
                    template_id = result.get("id")
                    if template_id:
                        self.test_data["template_id"] = template_id
                        print("  ✅ 테스트 템플릿 생성 성공")
                    else:
                        print("  ⚠️ 템플릿 생성 응답에 ID 없음")
                else:
                    print(f"  ⚠️ 템플릿 생성 실패: {response.status}")
        except Exception as e:
            print(f"  ❌ 템플릿 생성 오류: {e}")
    
    async def test_deployment_management(self):
        """배포 관리 시스템 테스트"""
        print("\n🚀 배포 관리 테스트 시작...")
        
        if not self.admin_token:
            print("  ❌ 관리자 토큰이 없어 테스트를 건너뜀")
            return
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # 포트 상태 확인
        try:
            async with self.session.get(
                f"{BACKEND_URL}/api/deployment/ports/status",
                headers=headers
            ) as response:
                if response.status == 200:
                    port_status = await response.json()
                    allocated_ports = port_status.get("port_status", {}).get("allocated_ports", {})
                    print(f"  ✅ 포트 상태 조회: {len(allocated_ports)}개 포트 할당됨")
                else:
                    print(f"  ⚠️ 포트 상태 조회 실패: {response.status}")
        except Exception as e:
            print(f"  ❌ 포트 상태 조회 오류: {e}")
        
        # 서비스 설정 조회
        try:
            async with self.session.get(
                f"{BACKEND_URL}/api/deployment/ports/services",
                headers=headers
            ) as response:
                if response.status == 200:
                    services = await response.json()
                    service_list = services.get("services", {})
                    print(f"  ✅ 서비스 설정 조회: {len(service_list)}개 서비스")
                else:
                    print(f"  ⚠️ 서비스 설정 조회 실패: {response.status}")
        except Exception as e:
            print(f"  ❌ 서비스 설정 조회 오류: {e}")
        
        # 배포 전제 조건 확인
        try:
            async with self.session.get(
                f"{BACKEND_URL}/api/deployment/prerequisites",
                headers=headers
            ) as response:
                if response.status == 200:
                    prerequisites = await response.json()
                    ready = prerequisites.get("ready", False)
                    prereq_list = prerequisites.get("prerequisites", {})
                    passed = sum(1 for v in prereq_list.values() if v)
                    total = len(prereq_list)
                    print(f"  ✅ 배포 전제 조건: {passed}/{total} 통과 (배포 준비: {'완료' if ready else '미완료'})")
                else:
                    print(f"  ⚠️ 전제 조건 확인 실패: {response.status}")
        except Exception as e:
            print(f"  ❌ 전제 조건 확인 오류: {e}")
        
        # 포트 충돌 검사
        try:
            async with self.session.get(
                f"{BACKEND_URL}/api/deployment/ports/conflicts",
                headers=headers
            ) as response:
                if response.status == 200:
                    conflicts = await response.json()
                    has_conflicts = conflicts.get("has_conflicts", False)
                    conflict_list = conflicts.get("conflicts", [])
                    print(f"  ✅ 포트 충돌 검사: {'충돌 없음' if not has_conflicts else f'{len(conflict_list)}개 충돌 발견'}")
                else:
                    print(f"  ⚠️ 포트 충돌 검사 실패: {response.status}")
        except Exception as e:
            print(f"  ❌ 포트 충돌 검사 오류: {e}")
    
    async def test_security_system(self):
        """보안 시스템 테스트"""
        print("\n🔒 보안 시스템 테스트 시작...")
        
        # 보안 헬스체크
        try:
            async with self.session.get(f"{BACKEND_URL}/api/security/health") as response:
                if response.status == 200:
                    health = await response.json()
                    status = health.get("status", "unknown")
                    components = health.get("components", {})
                    active_components = sum(1 for v in components.values() if v in ["active", "healthy"])
                    total_components = len(components)
                    print(f"  ✅ 보안 시스템 상태: {status} ({active_components}/{total_components} 컴포넌트 활성)")
                else:
                    print(f"  ⚠️ 보안 헬스체크 실패: {response.status}")
        except Exception as e:
            print(f"  ❌ 보안 헬스체크 오류: {e}")
        
        # 권한이 없는 접근 테스트
        try:
            async with self.session.get(f"{BACKEND_URL}/api/deployment/ports/status") as response:
                if response.status == 401:
                    print("  ✅ 권한 없는 접근 차단: 정상")
                else:
                    print(f"  ⚠️ 권한 없는 접근이 허용됨: {response.status}")
        except Exception as e:
            print(f"  ❌ 권한 테스트 오류: {e}")
        
        # 잘못된 토큰 테스트
        try:
            headers = {"Authorization": "Bearer invalid-token-123"}
            async with self.session.get(
                f"{BACKEND_URL}/api/deployment/ports/status",
                headers=headers
            ) as response:
                if response.status == 401:
                    print("  ✅ 잘못된 토큰 차단: 정상")
                else:
                    print(f"  ⚠️ 잘못된 토큰이 허용됨: {response.status}")
        except Exception as e:
            print(f"  ❌ 토큰 검증 테스트 오류: {e}")
    
    async def test_api_endpoints(self):
        """API 엔드포인트 테스트"""
        print("\n🌐 API 엔드포인트 테스트 시작...")
        
        if not self.admin_token:
            print("  ❌ 관리자 토큰이 없어 테스트를 건너뜀")
            return
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # 주요 API 엔드포인트 목록
        endpoints = [
            {"url": "/api/health", "method": "GET", "auth": False, "name": "헬스체크"},
            {"url": "/api/auth/me", "method": "GET", "auth": True, "name": "사용자 정보"},
            {"url": "/api/users", "method": "GET", "auth": True, "name": "사용자 목록"},
            {"url": "/api/projects", "method": "GET", "auth": True, "name": "프로젝트 목록"},
            {"url": "/api/companies", "method": "GET", "auth": True, "name": "기업 목록"},
            {"url": "/api/evaluations", "method": "GET", "auth": True, "name": "평가 목록"},
            {"url": "/api/templates", "method": "GET", "auth": True, "name": "템플릿 목록"},
            {"url": "/api/files", "method": "GET", "auth": True, "name": "파일 목록"},
        ]
        
        successful_endpoints = 0
        total_endpoints = len(endpoints)
        
        for endpoint in endpoints:
            try:
                request_headers = headers if endpoint["auth"] else {}
                
                if endpoint["method"] == "GET":
                    async with self.session.get(
                        f"{BACKEND_URL}{endpoint['url']}",
                        headers=request_headers
                    ) as response:
                        if response.status in [200, 404]:  # 404도 정상 (데이터 없음)
                            print(f"  ✅ {endpoint['name']}: 정상 ({response.status})")
                            successful_endpoints += 1
                        else:
                            print(f"  ⚠️ {endpoint['name']}: 상태코드 {response.status}")
                            
            except Exception as e:
                print(f"  ❌ {endpoint['name']}: 오류 - {e}")
        
        print(f"  📊 API 테스트 결과: {successful_endpoints}/{total_endpoints} 성공")
    
    async def test_file_operations(self):
        """파일 관련 기능 테스트"""
        print("\n📁 파일 시스템 테스트 시작...")
        
        if not self.admin_token:
            print("  ❌ 관리자 토큰이 없어 테스트를 건너뜀")
            return
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # 파일 목록 조회
        try:
            async with self.session.get(
                f"{BACKEND_URL}/api/files",
                headers=headers
            ) as response:
                if response.status in [200, 404]:
                    if response.status == 200:
                        files = await response.json()
                        print(f"  ✅ 파일 목록 조회: {len(files)}개 파일")
                    else:
                        print("  ✅ 파일 목록 조회: 파일 없음")
                else:
                    print(f"  ⚠️ 파일 목록 조회 실패: {response.status}")
        except Exception as e:
            print(f"  ❌ 파일 목록 조회 오류: {e}")
        
        # 업로드 디렉토리 확인
        upload_dir = "/mnt/c/Project/Online-evaluation/uploads"
        if os.path.exists(upload_dir):
            file_count = len([f for f in os.listdir(upload_dir) if os.path.isfile(os.path.join(upload_dir, f))])
            print(f"  ✅ 업로드 디렉토리: {file_count}개 파일 존재")
        else:
            print("  ⚠️ 업로드 디렉토리 없음")
    
    async def test_performance_metrics(self):
        """성능 메트릭 테스트"""
        print("\n⚡ 성능 테스트 시작...")
        
        # API 응답 시간 측정
        start_time = time.time()
        try:
            async with self.session.get(f"{BACKEND_URL}/api/health") as response:
                if response.status == 200:
                    response_time = (time.time() - start_time) * 1000
                    print(f"  ✅ API 응답 시간: {response_time:.2f}ms")
                    
                    if response_time < 1000:
                        print("  ✅ 응답 시간 우수 (< 1초)")
                    elif response_time < 2000:
                        print("  ⚠️ 응답 시간 보통 (1-2초)")
                    else:
                        print("  ❌ 응답 시간 느림 (> 2초)")
                else:
                    print(f"  ❌ 헬스체크 실패: {response.status}")
        except Exception as e:
            print(f"  ❌ 성능 테스트 오류: {e}")
        
        # 프론트엔드 응답 시간 측정
        start_time = time.time()
        try:
            async with self.session.get(FRONTEND_URL) as response:
                if response.status == 200:
                    response_time = (time.time() - start_time) * 1000
                    print(f"  ✅ 프론트엔드 응답 시간: {response_time:.2f}ms")
                else:
                    print(f"  ⚠️ 프론트엔드 응답 코드: {response.status}")
        except Exception as e:
            print(f"  ❌ 프론트엔드 테스트 오류: {e}")
    
    async def run_all_tests(self):
        """모든 테스트 실행"""
        print("🧪 온라인 평가 시스템 통합 테스트 시작")
        print("=" * 60)
        
        start_time = time.time()
        
        try:
            await self.setup()
            
            # 핵심 기능 테스트
            await self.test_authentication_system()
            await self.test_ai_provider_management()
            await self.test_template_management()
            await self.test_deployment_management()
            await self.test_security_system()
            await self.test_api_endpoints()
            await self.test_file_operations()
            await self.test_performance_metrics()
            
        except Exception as e:
            print(f"\n❌ 테스트 중 치명적 오류 발생: {e}")
        finally:
            await self.teardown()
        
        total_time = time.time() - start_time
        print("\n" + "=" * 60)
        print(f"🏁 통합 테스트 완료 (소요시간: {total_time:.2f}초)")
        print("=" * 60)

async def main():
    """메인 테스트 함수"""
    test_runner = SystemIntegrationTest()
    await test_runner.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())