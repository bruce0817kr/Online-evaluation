#!/usr/bin/env python3
"""
통합 로그인 워크플로우 E2E 테스트
전체 로그인 프로세스의 완전한 검증
"""

import requests
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import time
import json

class LoginWorkflowTester:
    def __init__(self):
        self.backend_url = "http://localhost:8080"
        self.frontend_url = "http://localhost:3001"
        self.api_url = f"{self.backend_url}/api"
        self.test_results = []

    def log_test(self, test_name, success, details=""):
        """테스트 결과 로깅"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.test_results.append(result)
        
        status = "✅ 성공" if success else "❌ 실패"
        print(f"{status} {test_name}: {details}")

    def test_infrastructure(self):
        """인프라 상태 테스트"""
        print("🏗️ 인프라 상태 테스트")
        print("-" * 40)
        
        # 백엔드 헬스체크
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                mongodb_status = data.get("services", {}).get("mongodb", "unknown")
                redis_status = data.get("services", {}).get("redis", "unknown")
                
                self.log_test("백엔드 헬스체크", True, f"MongoDB: {mongodb_status}, Redis: {redis_status}")
            else:
                self.log_test("백엔드 헬스체크", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("백엔드 헬스체크", False, str(e))
        
        # 프론트엔드 접근성
        try:
            response = requests.get(self.frontend_url, timeout=10)
            success = response.status_code == 200
            self.log_test("프론트엔드 접근성", success, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("프론트엔드 접근성", False, str(e))

    async def test_database_users(self):
        """데이터베이스 사용자 확인"""
        print("\n🗄️ 데이터베이스 사용자 확인")
        print("-" * 40)
        
        try:
            # MongoDB 연결
            mongo_url = "mongodb://admin:password123@localhost:27017/online_evaluation?authSource=admin"
            client = AsyncIOMotorClient(mongo_url)
            db = client['online_evaluation']
            
            # 사용자 수 확인
            user_count = await db.users.count_documents({})
            self.log_test("사용자 데이터베이스 연결", True, f"{user_count}명의 사용자 발견")
            
            # 테스트 계정들 확인
            test_accounts = ['admin', 'secretary01', 'evaluator01']
            for account in test_accounts:
                user = await db.users.find_one({"login_id": account})
                if user:
                    self.log_test(f"테스트 계정 {account}", True, f"역할: {user.get('role')}")
                else:
                    self.log_test(f"테스트 계정 {account}", False, "계정을 찾을 수 없음")
            
            client.close()
            
        except Exception as e:
            self.log_test("데이터베이스 사용자 확인", False, str(e))

    def test_api_authentication(self):
        """API 인증 테스트"""
        print("\n🔐 API 인증 테스트")
        print("-" * 40)
        
        test_accounts = [
            {"username": "admin", "password": "admin123", "expected_role": "admin"},
            {"username": "secretary01", "password": "secretary123", "expected_role": "secretary"},
            {"username": "evaluator01", "password": "evaluator123", "expected_role": "evaluator"}
        ]
        
        for account in test_accounts:
            try:
                # 로그인 시도
                response = requests.post(
                    f"{self.api_url}/auth/login",
                    data=f"username={account['username']}&password={account['password']}",
                    headers={'Content-Type': 'application/x-www-form-urlencoded'},
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    token = data.get('access_token')
                    user = data.get('user', {})
                    actual_role = user.get('role')
                    
                    if token and actual_role == account['expected_role']:
                        self.log_test(f"로그인 {account['username']}", True, f"역할: {actual_role}")
                        
                        # 토큰 검증 (/auth/me)
                        me_response = requests.get(
                            f"{self.api_url}/auth/me",
                            headers={'Authorization': f'Bearer {token}'},
                            timeout=10
                        )
                        
                        if me_response.status_code == 200:
                            self.log_test(f"토큰 검증 {account['username']}", True, "유효한 토큰")
                        else:
                            self.log_test(f"토큰 검증 {account['username']}", False, f"HTTP {me_response.status_code}")
                    else:
                        self.log_test(f"로그인 {account['username']}", False, f"예상 역할: {account['expected_role']}, 실제: {actual_role}")
                else:
                    self.log_test(f"로그인 {account['username']}", False, f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test(f"로그인 {account['username']}", False, str(e))

    def test_cors_headers(self):
        """CORS 헤더 테스트"""
        print("\n🌐 CORS 설정 테스트")
        print("-" * 40)
        
        try:
            # OPTIONS 요청으로 CORS 확인
            response = requests.options(
                f"{self.api_url}/auth/login",
                headers={
                    'Origin': self.frontend_url,
                    'Access-Control-Request-Method': 'POST',
                    'Access-Control-Request-Headers': 'Content-Type'
                },
                timeout=10
            )
            
            cors_origin = response.headers.get('Access-Control-Allow-Origin')
            cors_methods = response.headers.get('Access-Control-Allow-Methods')
            
            if cors_origin == self.frontend_url:
                self.log_test("CORS Origin 설정", True, cors_origin)
            else:
                self.log_test("CORS Origin 설정", False, f"예상: {self.frontend_url}, 실제: {cors_origin}")
            
            if 'POST' in str(cors_methods):
                self.log_test("CORS Methods 설정", True, cors_methods)
            else:
                self.log_test("CORS Methods 설정", False, cors_methods)
                
        except Exception as e:
            self.log_test("CORS 설정 확인", False, str(e))

    def test_frontend_backend_integration(self):
        """프론트엔드-백엔드 통합 테스트"""
        print("\n🔗 프론트엔드-백엔드 통합 테스트")
        print("-" * 40)
        
        try:
            # 프론트엔드와 동일한 방식으로 로그인 요청
            form_data = {
                'username': 'admin',
                'password': 'admin123'
            }
            
            response = requests.post(
                f"{self.api_url}/auth/login",
                data=form_data,
                headers={
                    'Origin': self.frontend_url,
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # 응답 구조 검증
                required_fields = ['access_token', 'token_type', 'user']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    user = data['user']
                    user_fields = ['id', 'login_id', 'user_name', 'role', 'email']
                    missing_user_fields = [field for field in user_fields if field not in user]
                    
                    if not missing_user_fields:
                        self.log_test("통합 로그인 응답 구조", True, "모든 필수 필드 존재")
                    else:
                        self.log_test("통합 로그인 응답 구조", False, f"사용자 필드 누락: {missing_user_fields}")
                else:
                    self.log_test("통합 로그인 응답 구조", False, f"필수 필드 누락: {missing_fields}")
            else:
                self.log_test("통합 로그인 요청", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("프론트엔드-백엔드 통합", False, str(e))

    def test_session_management(self):
        """세션 관리 테스트"""
        print("\n🎫 세션 관리 테스트")
        print("-" * 40)
        
        try:
            # 로그인으로 토큰 획득
            response = requests.post(
                f"{self.api_url}/auth/login",
                data="username=admin&password=admin123",
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=10
            )
            
            if response.status_code == 200:
                token = response.json().get('access_token')
                
                # 보호된 엔드포인트 접근 테스트
                protected_endpoints = [
                    "/auth/me",
                    "/users"
                ]
                
                for endpoint in protected_endpoints:
                    # 토큰과 함께 요청
                    auth_response = requests.get(
                        f"{self.api_url}{endpoint}",
                        headers={'Authorization': f'Bearer {token}'},
                        timeout=10
                    )
                    
                    # 토큰 없이 요청
                    no_auth_response = requests.get(
                        f"{self.api_url}{endpoint}",
                        timeout=10
                    )
                    
                    if auth_response.status_code in [200, 403] and no_auth_response.status_code == 401:
                        self.log_test(f"보호된 엔드포인트 {endpoint}", True, "토큰 인증 정상")
                    else:
                        self.log_test(f"보호된 엔드포인트 {endpoint}", False, 
                                    f"토큰 있음: {auth_response.status_code}, 토큰 없음: {no_auth_response.status_code}")
            else:
                self.log_test("세션 관리 테스트", False, "로그인 토큰 획득 실패")
                
        except Exception as e:
            self.log_test("세션 관리", False, str(e))

    def generate_report(self):
        """최종 리포트 생성"""
        print("\n" + "=" * 60)
        print("📋 통합 로그인 워크플로우 테스트 결과")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 전체 테스트: {total_tests}개")
        print(f"✅ 성공: {passed_tests}개")
        print(f"❌ 실패: {failed_tests}개")
        print(f"📈 성공률: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print(f"\n🔍 실패한 테스트:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   ❌ {result['test']}: {result['details']}")
        
        # JSON 리포트 저장
        report_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "summary": {
                "total": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "success_rate": success_rate
            },
            "tests": self.test_results
        }
        
        with open('login_workflow_test_report.json', 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 상세 리포트 저장: login_workflow_test_report.json")
        
        # 최종 결론
        if success_rate >= 90:
            print(f"\n🎉🎉🎉 로그인 시스템이 완벽하게 작동합니다! 🎉🎉🎉")
            return True
        elif success_rate >= 70:
            print(f"\n⚠️ 로그인 시스템이 대부분 작동하지만 일부 개선이 필요합니다.")
            return False
        else:
            print(f"\n❌ 로그인 시스템에 중대한 문제가 있습니다. 추가 조치가 필요합니다.")
            return False

    async def run_all_tests(self):
        """모든 테스트 실행"""
        print("🚀 통합 로그인 워크플로우 테스트 시작")
        print("=" * 60)
        
        # 순차적으로 모든 테스트 실행
        self.test_infrastructure()
        await self.test_database_users()
        self.test_api_authentication()
        self.test_cors_headers()
        self.test_frontend_backend_integration()
        self.test_session_management()
        
        # 최종 리포트 생성
        return self.generate_report()

async def main():
    """메인 테스트 실행"""
    tester = LoginWorkflowTester()
    success = await tester.run_all_tests()
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)
