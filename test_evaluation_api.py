#!/usr/bin/env python3
"""
평가 관리 API 테스트 스크립트
새로 구현된 /api/evaluations 엔드포인트를 테스트합니다.
"""

import requests
import json
import time
from datetime import datetime

class EvaluationAPITester:
    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url
        self.token = None
        self.current_user = None
        self.test_results = []

    def log_test(self, test_name, success, message=""):
        """테스트 결과 로깅"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status} {test_name}"
        if message:
            result += f" - {message}"
        print(result)
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })

    def test_health(self):
        """서버 상태 확인"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            success = response.status_code == 200
            self.log_test("Health Check", success, f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Health Check", False, str(e))
            return False

    def login(self, username, password):
        """로그인"""
        try:
            response = requests.post(
                f"{self.base_url}/api/auth/login",
                data={"username": username, "password": password},
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.current_user = data.get("user")
                self.log_test(f"Login as {username}", True, f"Role: {self.current_user.get('role')}")
                return True
            else:
                self.log_test(f"Login as {username}", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test(f"Login as {username}", False, str(e))
            return False

    def get_headers(self):
        """API 요청 헤더 생성"""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def test_get_evaluations(self):
        """평가 목록 조회 테스트"""
        try:
            response = requests.get(
                f"{self.base_url}/api/evaluations",
                headers=self.get_headers()
            )
            
            success = response.status_code == 200
            if success:
                data = response.json()
                self.log_test("GET /api/evaluations", True, f"Found {len(data)} evaluations")
                return True, data
            else:
                self.log_test("GET /api/evaluations", False, f"Status: {response.status_code}, Body: {response.text}")
                return False, None
        except Exception as e:
            self.log_test("GET /api/evaluations", False, str(e))
            return False, None

    def test_get_evaluation_with_filter(self, project_id=None, status=None):
        """필터 조건으로 평가 목록 조회 테스트"""
        try:
            params = {}
            if project_id:
                params["project_id"] = project_id
            if status:
                params["status"] = status
            
            response = requests.get(
                f"{self.base_url}/api/evaluations",
                headers=self.get_headers(),
                params=params
            )
            
            success = response.status_code == 200
            filter_desc = f"project_id={project_id}, status={status}" if params else "no filters"
            if success:
                data = response.json()
                self.log_test(f"GET /api/evaluations with filters ({filter_desc})", True, f"Found {len(data)} evaluations")
                return True, data
            else:
                self.log_test(f"GET /api/evaluations with filters ({filter_desc})", False, f"Status: {response.status_code}")
                return False, None
        except Exception as e:
            self.log_test(f"GET /api/evaluations with filters", False, str(e))
            return False, None

    def test_create_evaluation(self, evaluation_data):
        """평가 생성 테스트"""
        try:
            response = requests.post(
                f"{self.base_url}/api/evaluations",
                headers=self.get_headers(),
                json=evaluation_data
            )
            
            success = response.status_code == 200
            if success:
                data = response.json()
                evaluation_id = data.get("id")
                self.log_test("POST /api/evaluations", True, f"Created evaluation ID: {evaluation_id}")
                return True, evaluation_id
            else:
                self.log_test("POST /api/evaluations", False, f"Status: {response.status_code}, Body: {response.text}")
                return False, None
        except Exception as e:
            self.log_test("POST /api/evaluations", False, str(e))
            return False, None

    def test_get_evaluation_by_id(self, evaluation_id):
        """특정 평가 조회 테스트"""
        try:
            response = requests.get(
                f"{self.base_url}/api/evaluations/{evaluation_id}",
                headers=self.get_headers()
            )
            
            success = response.status_code == 200
            if success:
                data = response.json()
                self.log_test(f"GET /api/evaluations/{evaluation_id}", True, f"Status: {data.get('status')}")
                return True, data
            else:
                self.log_test(f"GET /api/evaluations/{evaluation_id}", False, f"Status: {response.status_code}")
                return False, None
        except Exception as e:
            self.log_test(f"GET /api/evaluations/{evaluation_id}", False, str(e))
            return False, None

    def test_update_evaluation(self, evaluation_id, update_data):
        """평가 수정 테스트"""
        try:
            response = requests.put(
                f"{self.base_url}/api/evaluations/{evaluation_id}",
                headers=self.get_headers(),
                json=update_data
            )
            
            success = response.status_code == 200
            if success:
                data = response.json()
                self.log_test(f"PUT /api/evaluations/{evaluation_id}", True, data.get("message"))
                return True
            else:
                self.log_test(f"PUT /api/evaluations/{evaluation_id}", False, f"Status: {response.status_code}, Body: {response.text}")
                return False
        except Exception as e:
            self.log_test(f"PUT /api/evaluations/{evaluation_id}", False, str(e))
            return False

    def test_delete_evaluation(self, evaluation_id):
        """평가 삭제 테스트"""
        try:
            response = requests.delete(
                f"{self.base_url}/api/evaluations/{evaluation_id}",
                headers=self.get_headers()
            )
            
            success = response.status_code == 200
            if success:
                data = response.json()
                self.log_test(f"DELETE /api/evaluations/{evaluation_id}", True, data.get("message"))
                return True
            else:
                self.log_test(f"DELETE /api/evaluations/{evaluation_id}", False, f"Status: {response.status_code}, Body: {response.text}")
                return False
        except Exception as e:
            self.log_test(f"DELETE /api/evaluations/{evaluation_id}", False, str(e))
            return False

    def run_comprehensive_test(self):
        """종합 테스트 실행"""
        print("🔍 평가 관리 API 종합 테스트 시작")
        print("=" * 60)
        
        # 1. 서버 상태 확인
        if not self.test_health():
            print("❌ 서버 상태 확인 실패. 테스트를 중단합니다.")
            return False
        
        # 2. 관리자로 로그인
        if not self.login("admin", "admin123"):
            print("❌ 관리자 로그인 실패. 테스트를 중단합니다.")
            return False
        
        print("\n📋 관리자 권한으로 평가 API 테스트")
        print("-" * 40)
        
        # 3. 평가 목록 조회 (관리자 - 모든 평가)
        success, evaluations = self.test_get_evaluations()
        
        # 4. 필터링된 평가 목록 조회
        self.test_get_evaluation_with_filter(status="draft")
        
        # 5. 새로운 평가 생성 (테스트용 더미 데이터)
        test_evaluation = {
            "evaluator_id": "test_evaluator_id",
            "company_id": "test_company_id", 
            "project_id": "test_project_id",
            "template_id": "test_template_id",
            "deadline": "2024-12-31T23:59:59"
        }
        
        created_success, evaluation_id = self.test_create_evaluation(test_evaluation)
        
        if created_success and evaluation_id:
            # 6. 생성된 평가 조회
            self.test_get_evaluation_by_id(evaluation_id)
            
            # 7. 평가 정보 수정
            update_data = {
                "status": "submitted",
                "total_score": 85.5,
                "weighted_score": 82.3
            }
            self.test_update_evaluation(evaluation_id, update_data)
            
            # 8. 수정된 평가 다시 조회
            self.test_get_evaluation_by_id(evaluation_id)
            
            # 9. 평가 삭제
            self.test_delete_evaluation(evaluation_id)
            
            # 10. 삭제된 평가 조회 시도 (404 예상)
            success, data = self.test_get_evaluation_by_id(evaluation_id)
            if not success:
                self.log_test("Verify evaluation deletion", True, "Evaluation not found as expected")

        # 테스트 결과 요약
        print("\n📊 테스트 결과 요약")
        print("=" * 60)
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"총 테스트: {total_tests}")
        print(f"성공: {passed_tests}")
        print(f"실패: {failed_tests}")
        print(f"성공률: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print("\n❌ 실패한 테스트:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        else:
            print("\n🎉 모든 테스트가 성공했습니다!")
        
        return failed_tests == 0

def main():
    tester = EvaluationAPITester()
    success = tester.run_comprehensive_test()
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
