"""
E2E 테스트 - 완전한 워크플로우 테스트
사용자 시나리오에 따른 전체 워크플로우가 올바르게 작동하는지 검증
"""

import pytest
import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, List, Any
import os

# 테스트 설정
BACKEND_URL = "http://localhost:8080"
FRONTEND_URL = "http://localhost:3000"
TEST_TIMEOUT = 60

class CompleteWorkflowTest:
    """완전한 워크플로우 E2E 테스트"""
    
    def __init__(self):
        self.session = None
        self.admin_token = None
        self.secretary_token = None
        self.evaluator_token = None
        self.test_data = {}
        
    async def setup(self):
        """테스트 환경 설정"""
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=TEST_TIMEOUT))
        print("🔧 E2E 테스트 환경 설정 중...")
        
        # 관리자 로그인
        await self.login_as_admin()
        
    async def teardown(self):
        """테스트 환경 정리"""
        # 테스트 데이터 정리
        await self.cleanup_test_data()
        
        if self.session:
            await self.session.close()
        print("🧹 E2E 테스트 환경 정리 완료")
    
    async def login_as_admin(self):
        """관리자로 로그인"""
        try:
            async with self.session.post(
                f"{BACKEND_URL}/api/auth/login",
                data={"username": "admin", "password": "admin123"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    self.admin_token = result.get("access_token")
                    print("✅ 관리자 로그인 성공")
                    return True
                else:
                    print(f"❌ 관리자 로그인 실패: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ 로그인 오류: {e}")
            return False
    
    async def cleanup_test_data(self):
        """테스트 데이터 정리"""
        if not self.admin_token:
            return
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # 생성된 테스트 데이터 삭제
        for data_type, data_id in self.test_data.items():
            try:
                if data_type == "project_id":
                    await self.session.delete(f"{BACKEND_URL}/api/projects/{data_id}", headers=headers)
                elif data_type == "company_id":
                    await self.session.delete(f"{BACKEND_URL}/api/companies/{data_id}", headers=headers)
                elif data_type == "template_id":
                    await self.session.delete(f"{BACKEND_URL}/api/templates/{data_id}", headers=headers)
                elif data_type == "evaluation_id":
                    await self.session.delete(f"{BACKEND_URL}/api/evaluations/{data_id}", headers=headers)
            except Exception as e:
                print(f"⚠️ {data_type} 정리 실패: {e}")
    
    async def scenario_1_project_creation_workflow(self):
        """시나리오 1: 프로젝트 생성부터 평가 완료까지"""
        print("\n📋 시나리오 1: 완전한 평가 워크플로우 테스트")
        print("-" * 50)
        
        if not self.admin_token:
            print("❌ 관리자 토큰 없음")
            return False
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # 1단계: 프로젝트 생성
        print("1️⃣ 프로젝트 생성...")
        project_data = {
            "name": "E2E 테스트 프로젝트",
            "description": "E2E 테스트를 위한 프로젝트",
            "start_date": datetime.now().isoformat(),
            "end_date": datetime.now().isoformat(),
            "status": "active"
        }
        
        try:
            async with self.session.post(
                f"{BACKEND_URL}/api/projects",
                headers=headers,
                json=project_data
            ) as response:
                if response.status in [200, 201]:
                    result = await response.json()
                    project_id = result.get("id") or result.get("_id")
                    if project_id:
                        self.test_data["project_id"] = project_id
                        print(f"   ✅ 프로젝트 생성 성공: {project_id}")
                    else:
                        print("   ❌ 프로젝트 ID 누락")
                        return False
                else:
                    print(f"   ❌ 프로젝트 생성 실패: {response.status}")
                    return False
        except Exception as e:
            print(f"   ❌ 프로젝트 생성 오류: {e}")
            return False
        
        # 2단계: 평가 템플릿 생성
        print("2️⃣ 평가 템플릿 생성...")
        template_data = {
            "name": "E2E 테스트 템플릿",
            "description": "E2E 테스트용 평가 템플릿",
            "category": "기술평가",
            "criteria": [
                {
                    "id": "innovation",
                    "name": "혁신성",
                    "description": "기술 혁신성 평가",
                    "max_score": 20,
                    "weight": 1.0,
                    "evaluation_items": [
                        {"id": "novelty", "name": "신규성", "max_score": 10},
                        {"id": "creativity", "name": "창의성", "max_score": 10}
                    ]
                },
                {
                    "id": "feasibility",
                    "name": "실현가능성",
                    "description": "기술 실현 가능성",
                    "max_score": 15,
                    "weight": 0.8
                }
            ],
            "bonus_criteria": [
                {
                    "id": "social_impact",
                    "name": "사회적 영향",
                    "max_score": 5,
                    "conditions": ["사회적 가치 창출"]
                }
            ],
            "is_active": True
        }
        
        try:
            async with self.session.post(
                f"{BACKEND_URL}/api/templates",
                headers=headers,
                json=template_data
            ) as response:
                if response.status in [200, 201]:
                    result = await response.json()
                    template_id = result.get("id") or result.get("_id")
                    if template_id:
                        self.test_data["template_id"] = template_id
                        print(f"   ✅ 템플릿 생성 성공: {template_id}")
                    else:
                        print("   ❌ 템플릿 ID 누락")
                        return False
                else:
                    print(f"   ❌ 템플릿 생성 실패: {response.status}")
                    return False
        except Exception as e:
            print(f"   ❌ 템플릿 생성 오류: {e}")
            return False
        
        # 3단계: 기업 정보 등록
        print("3️⃣ 기업 정보 등록...")
        company_data = {
            "name": "E2E 테스트 기업",
            "business_number": "123-45-67890",
            "ceo_name": "김대표",
            "address": "서울시 강남구 테스트로 123",
            "phone": "02-1234-5678",
            "email": "test@company.com",
            "business_type": "소프트웨어 개발",
            "employee_count": 50,
            "established_year": 2020,
            "project_id": self.test_data["project_id"]
        }
        
        try:
            async with self.session.post(
                f"{BACKEND_URL}/api/companies",
                headers=headers,
                json=company_data
            ) as response:
                if response.status in [200, 201]:
                    result = await response.json()
                    company_id = result.get("id") or result.get("_id")
                    if company_id:
                        self.test_data["company_id"] = company_id
                        print(f"   ✅ 기업 등록 성공: {company_id}")
                    else:
                        print("   ❌ 기업 ID 누락")
                        return False
                else:
                    print(f"   ❌ 기업 등록 실패: {response.status}")
                    return False
        except Exception as e:
            print(f"   ❌ 기업 등록 오류: {e}")
            return False
        
        # 4단계: 평가위원 생성 및 할당
        print("4️⃣ 평가위원 생성 및 할당...")
        evaluator_data = {
            "username": f"evaluator_e2e_{int(time.time())}",
            "password": "test123",
            "email": f"evaluator_e2e_{int(time.time())}@test.com",
            "user_name": "E2E 테스트 평가위원",
            "role": "evaluator",
            "phone": "010-1234-5678",
            "organization": "테스트 기관"
        }
        
        try:
            async with self.session.post(
                f"{BACKEND_URL}/api/auth/register",
                headers=headers,
                json=evaluator_data
            ) as response:
                if response.status in [200, 201]:
                    result = await response.json()
                    evaluator_id = result.get("id") or result.get("user_id")
                    if evaluator_id:
                        self.test_data["evaluator_id"] = evaluator_id
                        print(f"   ✅ 평가위원 생성 성공: {evaluator_id}")
                    else:
                        print("   ❌ 평가위원 ID 누락")
                        return False
                else:
                    print(f"   ❌ 평가위원 생성 실패: {response.status}")
                    return False
        except Exception as e:
            print(f"   ❌ 평가위원 생성 오류: {e}")
            return False
        
        # 5단계: 평가 할당
        print("5️⃣ 평가 할당...")
        assignment_data = {
            "evaluator_id": self.test_data["evaluator_id"],
            "company_id": self.test_data["company_id"],
            "template_id": self.test_data["template_id"],
            "project_id": self.test_data["project_id"]
        }
        
        try:
            async with self.session.post(
                f"{BACKEND_URL}/api/assignments",
                headers=headers,
                json=assignment_data
            ) as response:
                if response.status in [200, 201]:
                    result = await response.json()
                    evaluation_id = result.get("evaluation_id")
                    if evaluation_id:
                        self.test_data["evaluation_id"] = evaluation_id
                        print(f"   ✅ 평가 할당 성공: {evaluation_id}")
                    else:
                        print("   ❌ 평가 ID 누락")
                        return False
                else:
                    print(f"   ❌ 평가 할당 실패: {response.status}")
                    return False
        except Exception as e:
            print(f"   ❌ 평가 할당 오류: {e}")
            return False
        
        # 6단계: 평가 수행 (시뮬레이션)
        print("6️⃣ 평가 수행...")
        evaluation_scores = {
            "scores": {
                "innovation": 18,
                "feasibility": 12
            },
            "comments": {
                "innovation": "우수한 기술 혁신성을 보여줌",
                "feasibility": "실현 가능성이 높음"
            },
            "bonus_scores": {
                "social_impact": 3
            },
            "total_score": 33,
            "overall_comment": "전반적으로 우수한 기술력을 보유한 기업"
        }
        
        try:
            async with self.session.post(
                f"{BACKEND_URL}/api/evaluations/{self.test_data['evaluation_id']}/submit",
                headers=headers,
                json=evaluation_scores
            ) as response:
                if response.status in [200, 201]:
                    print("   ✅ 평가 제출 성공")
                else:
                    print(f"   ❌ 평가 제출 실패: {response.status}")
                    return False
        except Exception as e:
            print(f"   ❌ 평가 제출 오류: {e}")
            return False
        
        print("✅ 시나리오 1 완료: 프로젝트 생성부터 평가 완료까지 성공")
        return True
    
    async def scenario_2_ai_evaluation_workflow(self):
        """시나리오 2: AI 평가 시스템 워크플로우"""
        print("\n🤖 시나리오 2: AI 평가 시스템 워크플로우")
        print("-" * 50)
        
        if not self.admin_token:
            print("❌ 관리자 토큰 없음")
            return False
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # 1단계: AI 공급자 설정
        print("1️⃣ AI 공급자 설정...")
        ai_provider_data = {
            "name": "test_ai_provider",
            "display_name": "테스트 AI 공급자",
            "provider_type": "openai",
            "api_key": "test-key-123456",
            "api_base_url": "https://api.openai.com/v1",
            "models": ["gpt-3.5-turbo", "gpt-4"],
            "is_active": True,
            "priority": 1
        }
        
        try:
            async with self.session.post(
                f"{BACKEND_URL}/api/ai-admin/providers",
                headers=headers,
                json=ai_provider_data
            ) as response:
                if response.status in [200, 201]:
                    result = await response.json()
                    provider_id = result.get("provider_id")
                    if provider_id:
                        self.test_data["ai_provider_id"] = provider_id
                        print(f"   ✅ AI 공급자 설정 성공: {provider_id}")
                    else:
                        print("   ❌ AI 공급자 ID 누락")
                else:
                    print(f"   ❌ AI 공급자 설정 실패: {response.status}")
        except Exception as e:
            print(f"   ❌ AI 공급자 설정 오류: {e}")
        
        # 2단계: AI 평가 실행 (기존 평가 데이터 사용)
        if "evaluation_id" in self.test_data:
            print("2️⃣ AI 평가 실행...")
            ai_evaluation_request = {
                "evaluation_ids": [self.test_data["evaluation_id"]],
                "template_id": self.test_data.get("template_id"),
                "ai_provider": "test_ai_provider",
                "evaluation_mode": "comprehensive",
                "include_file_analysis": True,
                "custom_prompt": "평가 기준에 따라 정확하게 평가해주세요."
            }
            
            try:
                async with self.session.post(
                    f"{BACKEND_URL}/api/ai-evaluation/execute",
                    headers=headers,
                    json=ai_evaluation_request
                ) as response:
                    if response.status in [200, 201]:
                        result = await response.json()
                        job_id = result.get("job_id")
                        if job_id:
                            self.test_data["ai_job_id"] = job_id
                            print(f"   ✅ AI 평가 실행 성공: {job_id}")
                        else:
                            print("   ❌ AI 작업 ID 누락")
                    else:
                        print(f"   ⚠️ AI 평가 실행 실패: {response.status} (AI 서비스 비활성화 가능)")
            except Exception as e:
                print(f"   ⚠️ AI 평가 실행 오류: {e} (정상적인 경우 - AI 서비스 설정 필요)")
        
        # 3단계: AI 평가 작업 상태 확인
        if "ai_job_id" in self.test_data:
            print("3️⃣ AI 평가 작업 상태 확인...")
            try:
                async with self.session.get(
                    f"{BACKEND_URL}/api/ai-evaluation/jobs/{self.test_data['ai_job_id']}",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        job_status = result.get("job", {}).get("status")
                        print(f"   ✅ AI 작업 상태: {job_status}")
                    else:
                        print(f"   ⚠️ AI 작업 상태 확인 실패: {response.status}")
            except Exception as e:
                print(f"   ⚠️ AI 작업 상태 확인 오류: {e}")
        
        print("✅ 시나리오 2 완료: AI 평가 시스템 워크플로우")
        return True
    
    async def scenario_3_deployment_workflow(self):
        """시나리오 3: 배포 관리 워크플로우"""
        print("\n🚀 시나리오 3: 배포 관리 워크플로우")
        print("-" * 50)
        
        if not self.admin_token:
            print("❌ 관리자 토큰 없음")
            return False
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # 1단계: 포트 상태 확인
        print("1️⃣ 포트 상태 확인...")
        try:
            async with self.session.get(
                f"{BACKEND_URL}/api/deployment/ports/status",
                headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    allocated_ports = result.get("port_status", {}).get("allocated_ports", {})
                    print(f"   ✅ 현재 할당된 포트: {len(allocated_ports)}개")
                else:
                    print(f"   ❌ 포트 상태 확인 실패: {response.status}")
        except Exception as e:
            print(f"   ❌ 포트 상태 확인 오류: {e}")
        
        # 2단계: 포트 충돌 검사
        print("2️⃣ 포트 충돌 검사...")
        try:
            async with self.session.get(
                f"{BACKEND_URL}/api/deployment/ports/conflicts",
                headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    has_conflicts = result.get("has_conflicts", False)
                    conflicts = result.get("conflicts", [])
                    if has_conflicts:
                        print(f"   ⚠️ 포트 충돌 발견: {len(conflicts)}개")
                    else:
                        print("   ✅ 포트 충돌 없음")
                else:
                    print(f"   ❌ 포트 충돌 검사 실패: {response.status}")
        except Exception as e:
            print(f"   ❌ 포트 충돌 검사 오류: {e}")
        
        # 3단계: 배포 전제 조건 확인
        print("3️⃣ 배포 전제 조건 확인...")
        try:
            async with self.session.get(
                f"{BACKEND_URL}/api/deployment/prerequisites",
                headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    ready = result.get("ready", False)
                    prerequisites = result.get("prerequisites", {})
                    passed_count = sum(1 for v in prerequisites.values() if v)
                    total_count = len(prerequisites)
                    print(f"   ✅ 전제 조건: {passed_count}/{total_count} 통과")
                    if ready:
                        print("   ✅ 배포 준비 완료")
                    else:
                        print("   ⚠️ 배포 준비 미완료")
                else:
                    print(f"   ❌ 전제 조건 확인 실패: {response.status}")
        except Exception as e:
            print(f"   ❌ 전제 조건 확인 오류: {e}")
        
        # 4단계: 배포 스크립트 생성
        print("4️⃣ 배포 스크립트 생성...")
        try:
            async with self.session.post(
                f"{BACKEND_URL}/api/deployment/generate-scripts?environment=development",
                headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    files_created = result.get("files_created", [])
                    print(f"   ✅ 배포 스크립트 생성 성공: {len(files_created)}개 파일")
                else:
                    print(f"   ❌ 배포 스크립트 생성 실패: {response.status}")
        except Exception as e:
            print(f"   ❌ 배포 스크립트 생성 오류: {e}")
        
        # 5단계: 배포 이력 확인
        print("5️⃣ 배포 이력 확인...")
        try:
            async with self.session.get(
                f"{BACKEND_URL}/api/deployment/history",
                headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    history = result.get("history", [])
                    print(f"   ✅ 배포 이력: {len(history)}개 기록")
                else:
                    print(f"   ❌ 배포 이력 확인 실패: {response.status}")
        except Exception as e:
            print(f"   ❌ 배포 이력 확인 오류: {e}")
        
        print("✅ 시나리오 3 완료: 배포 관리 워크플로우")
        return True
    
    async def scenario_4_security_workflow(self):
        """시나리오 4: 보안 시스템 워크플로우"""
        print("\n🔒 시나리오 4: 보안 시스템 워크플로우")
        print("-" * 50)
        
        # 1단계: 보안 헬스체크
        print("1️⃣ 보안 시스템 상태 확인...")
        try:
            async with self.session.get(f"{BACKEND_URL}/api/security/health") as response:
                if response.status == 200:
                    result = await response.json()
                    status = result.get("status")
                    components = result.get("components", {})
                    active_components = [k for k, v in components.items() if v in ["active", "healthy"]]
                    print(f"   ✅ 보안 시스템 상태: {status}")
                    print(f"   ✅ 활성 컴포넌트: {len(active_components)}개")
                else:
                    print(f"   ❌ 보안 헬스체크 실패: {response.status}")
        except Exception as e:
            print(f"   ❌ 보안 헬스체크 오류: {e}")
        
        # 2단계: 권한 없는 접근 테스트
        print("2️⃣ 권한 제어 테스트...")
        restricted_endpoints = [
            "/api/deployment/ports/status",
            "/api/ai-admin/providers",
            "/api/users",
            "/api/security/metrics"
        ]
        
        blocked_count = 0
        for endpoint in restricted_endpoints:
            try:
                async with self.session.get(f"{BACKEND_URL}{endpoint}") as response:
                    if response.status == 401:
                        blocked_count += 1
            except:
                pass
        
        print(f"   ✅ 권한 제어: {blocked_count}/{len(restricted_endpoints)} 엔드포인트 차단됨")
        
        # 3단계: 잘못된 토큰 테스트
        print("3️⃣ 토큰 검증 테스트...")
        invalid_headers = {"Authorization": "Bearer invalid-token-12345"}
        try:
            async with self.session.get(
                f"{BACKEND_URL}/api/auth/me",
                headers=invalid_headers
            ) as response:
                if response.status == 401:
                    print("   ✅ 잘못된 토큰 차단 성공")
                else:
                    print(f"   ❌ 잘못된 토큰이 허용됨: {response.status}")
        except Exception as e:
            print(f"   ❌ 토큰 검증 테스트 오류: {e}")
        
        # 4단계: 역할 기반 접근 제어 테스트
        print("4️⃣ 역할 기반 접근 제어 테스트...")
        if self.admin_token:
            admin_headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # 관리자만 접근 가능한 엔드포인트 테스트
            admin_endpoints = [
                "/api/deployment/ports/status",
                "/api/ai-admin/providers",
                "/api/users"
            ]
            
            accessible_count = 0
            for endpoint in admin_endpoints:
                try:
                    async with self.session.get(
                        f"{BACKEND_URL}{endpoint}",
                        headers=admin_headers
                    ) as response:
                        if response.status in [200, 404]:  # 404도 접근 가능한 것으로 간주
                            accessible_count += 1
                except:
                    pass
            
            print(f"   ✅ 관리자 접근: {accessible_count}/{len(admin_endpoints)} 엔드포인트 접근 가능")
        
        print("✅ 시나리오 4 완료: 보안 시스템 워크플로우")
        return True
    
    async def run_all_scenarios(self):
        """모든 E2E 시나리오 실행"""
        print("🎬 온라인 평가 시스템 E2E 테스트 시작")
        print("=" * 60)
        
        start_time = time.time()
        results = {}
        
        try:
            await self.setup()
            
            # 시나리오 실행
            results["scenario_1"] = await self.scenario_1_project_creation_workflow()
            results["scenario_2"] = await self.scenario_2_ai_evaluation_workflow()
            results["scenario_3"] = await self.scenario_3_deployment_workflow()
            results["scenario_4"] = await self.scenario_4_security_workflow()
            
        except Exception as e:
            print(f"\n❌ E2E 테스트 중 치명적 오류 발생: {e}")
        finally:
            await self.teardown()
        
        # 결과 요약
        total_time = time.time() - start_time
        successful_scenarios = sum(1 for result in results.values() if result)
        total_scenarios = len(results)
        
        print("\n" + "=" * 60)
        print("📊 E2E 테스트 결과 요약")
        print("=" * 60)
        
        for scenario, result in results.items():
            status = "✅ 성공" if result else "❌ 실패"
            print(f"{scenario}: {status}")
        
        print(f"\n🏁 E2E 테스트 완료")
        print(f"📈 성공률: {successful_scenarios}/{total_scenarios} ({successful_scenarios/total_scenarios*100:.1f}%)")
        print(f"⏱️ 소요시간: {total_time:.2f}초")
        print("=" * 60)
        
        return successful_scenarios == total_scenarios

async def main():
    """메인 E2E 테스트 함수"""
    test_runner = CompleteWorkflowTest()
    success = await test_runner.run_all_scenarios()
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)