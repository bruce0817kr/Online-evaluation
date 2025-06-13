"""
온라인 평가 시스템 - 최종 시스템 테스트 및 검증
생성된 테스트 데이터를 사용하여 전체 시스템 기능을 검증합니다.
"""

import requests
import json
import sys
from datetime import datetime

# API 기본 설정
BASE_URL = "http://localhost:8080"
HEADERS = {"Content-Type": "application/json"}

class SystemTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.headers = HEADERS
        self.token = None
        self.test_results = []
        
    def log_test(self, test_name, success, details=""):
        """테스트 결과 로깅"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    def test_server_health(self):
        """서버 상태 확인"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            success = response.status_code == 200
                        details = f"Status: {response.status_code}, Response: {response.text}"
            self.log_test("서버 헬스체크", success, details)
            return success
        except Exception as e:
            self.log_test("서버 헬스체크", False, str(e))
            return False
    
    def test_login(self, login_id, password):
        """로그인 테스트"""
        try:
            # OAuth2PasswordRequestForm 형식으로 form-data 전송
            data = {"username": login_id, "password": password}
            response = requests.post(f"{self.base_url}/auth/login", 
                                   data=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                self.token = result.get("access_token")
                if self.token:
                    self.headers["Authorization"] = f"Bearer {self.token}"
                    self.log_test(f"로그인 테스트 ({login_id})", True, 
                                f"Role: {result.get('user', {}).get('role')}")
                    return True
            
            self.log_test(f"로그인 테스트 ({login_id})", False, 
                        f"Status: {response.status_code}, Response: {response.text}")
            return False
        except Exception as e:
            self.log_test(f"로그인 테스트 ({login_id})", False, str(e))
            return False
        
    def test_get_endpoint(self, endpoint, test_name):
        """GET 엔드포인트 테스트"""
        try:
            response = requests.get(f"{self.base_url}{endpoint}", 
                                  headers=self.headers, timeout=10)
            
            success = response.status_code == 200
            if success:
                data = response.json()
                count = len(data) if isinstance(data, list) else 1
                details = f"데이터 개수: {count}개"
            else:
                details = f"Status: {response.status_code}"
            
            self.log_test(test_name, success, details)
            return success, response.json() if success else None
        except Exception as e:
            self.log_test(test_name, False, str(e))
            return False, None
    
    def test_project_endpoints(self):
        """프로젝트 관련 엔드포인트 테스트"""
        print("\n=== 프로젝트 API 테스트 ===")
        
        # 프로젝트 목록 조회
        success, projects = self.test_get_endpoint("/projects/", "프로젝트 목록 조회")
        
        if success and projects:
            # 첫 번째 프로젝트의 상세 정보 조회
            project_id = projects[0].get("id")
            if project_id:
                self.test_get_endpoint(f"/projects/{project_id}", 
                                     "프로젝트 상세 조회")
                self.test_get_endpoint(f"/projects/{project_id}/companies", 
                                     "프로젝트별 회사 목록")
        
        return success
    
    def test_company_endpoints(self):
        """회사 관련 엔드포인트 테스트"""
        print("\n=== 회사 API 테스트 ===")
        
        # 회사 목록 조회
        success, companies = self.test_get_endpoint("/companies/", "회사 목록 조회")
        
        if success and companies:
            # 첫 번째 회사의 상세 정보 조회
            company_id = companies[0].get("id")
            if company_id:
                self.test_get_endpoint(f"/companies/{company_id}", 
                                     "회사 상세 조회")
        
        return success
    
    def test_evaluation_endpoints(self):
        """평가 관련 엔드포인트 테스트"""
        print("\n=== 평가 API 테스트 ===")
        
        # 평가 템플릿 조회
        success1, templates = self.test_get_endpoint("/evaluation-templates/", 
                                                    "평가 템플릿 목록")
        
        # 평가 시트 조회
        success2, sheets = self.test_get_endpoint("/evaluation-sheets/", 
                                                 "평가 시트 목록")
        
        # 평가 점수 조회 (첫 번째 시트의 점수)
        if success2 and sheets:
            sheet_id = sheets[0].get("id")
            if sheet_id:
                self.test_get_endpoint(f"/evaluation-sheets/{sheet_id}/scores", 
                                     "평가 점수 조회")
        
        return success1 and success2
    
    def run_comprehensive_test(self):
        """종합 시스템 테스트 실행"""
        print("🚀 온라인 평가 시스템 종합 테스트 시작")
        print("=" * 50)
        
        # 1. 서버 상태 확인
        if not self.test_server_health():
            print("❌ 서버가 응답하지 않습니다. 테스트를 중단합니다.")
            return False
        
        # 2. 관리자 로그인 테스트
        print("\n=== 인증 테스트 ===")
        if not self.test_login("admin", "admin123"):
            print("❌ 관리자 로그인 실패. 테스트를 중단합니다.")
            return False
        
        # 3. 각 모듈별 API 테스트
        tests_passed = 0
        total_tests = 3
        
        if self.test_project_endpoints():
            tests_passed += 1
        
        if self.test_company_endpoints():
            tests_passed += 1
            
        if self.test_evaluation_endpoints():
            tests_passed += 1
        
        # 4. 평가자 로그인 테스트
        print("\n=== 평가자 로그인 테스트 ===")
        evaluator_login_success = self.test_login("evaluator01", "evaluator123")
        if evaluator_login_success:
            # 평가자 관점에서 평가 시트 조회
            self.test_get_endpoint("/evaluation-sheets/my", "내 평가 시트 목록")
        
        # 5. 결과 요약
        print("\n" + "=" * 50)
        print("📊 테스트 결과 요약")
        print("=" * 50)
        
        total_tests_run = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        
        print(f"총 테스트: {total_tests_run}개")
        print(f"성공: {passed_tests}개")
        print(f"실패: {total_tests_run - passed_tests}개")
        print(f"성공률: {(passed_tests/total_tests_run)*100:.1f}%")
        
        # 실패한 테스트 목록
        failed_tests = [r for r in self.test_results if not r["success"]]
        if failed_tests:
            print(f"\n❌ 실패한 테스트 ({len(failed_tests)}개):")
            for test in failed_tests:
                print(f"   - {test['test']}: {test['details']}")
        
        # 테스트 결과를 JSON 파일로 저장
        with open("system_test_results.json", "w", encoding="utf-8") as f:
            json.dump({
                "summary": {
                    "total_tests": total_tests_run,
                    "passed": passed_tests,
                    "failed": total_tests_run - passed_tests,
                    "success_rate": (passed_tests/total_tests_run)*100,
                    "timestamp": datetime.now().isoformat()
                },
                "details": self.test_results
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 상세 결과가 'system_test_results.json' 파일에 저장되었습니다.")
        
        # 전체 시스템 상태 판정
        success_rate = (passed_tests/total_tests_run)*100
        if success_rate >= 90:
            print("\n🎉 시스템이 성공적으로 작동하고 있습니다!")
            return True
        elif success_rate >= 70:
            print("\n⚠️ 시스템이 대부분 정상 작동하지만 일부 개선이 필요합니다.")
            return True
        else:
            print("\n❌ 시스템에 중대한 문제가 있습니다. 점검이 필요합니다.")
            return False

if __name__ == "__main__":
    tester = SystemTester()
    success = tester.run_comprehensive_test()
    sys.exit(0 if success else 1)
