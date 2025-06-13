#!/usr/bin/env python3
"""
새로 구현된 평가 제출 및 결과 API 엔드포인트 테스트
/api/evaluations/submit, /api/evaluations/results, /api/evaluations/user, /api/evaluations/statistics
"""

import requests
import json
import time
from datetime import datetime

class NewEvaluationAPITester:
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

    def test_submit_evaluation(self):
        """평가 제출 API 테스트"""
        try:
            submission_data = {
                "evaluation_id": "test_eval_001",
                "user_id": self.current_user.get("id", "test_user"),
                "responses": {
                    "question_1": {"score": 85, "comment": "Good implementation"},
                    "question_2": {"score": 90, "comment": "Excellent design"},
                    "question_3": {"score": 78, "comment": "Could be improved"}
                },
                "total_score": 84.3,
                "completion_time": 1800  # 30 minutes
            }
            
            response = requests.post(
                f"{self.base_url}/api/evaluations/submit",
                headers=self.get_headers(),
                json=submission_data
            )
            
            success = response.status_code in [200, 201]
            if success:
                data = response.json()
                self.log_test("POST /api/evaluations/submit", True, f"Submission ID: {data.get('submission_id', 'N/A')}")
                return True, data.get('submission_id')
            else:
                self.log_test("POST /api/evaluations/submit", False, f"Status: {response.status_code}, Body: {response.text}")
                return False, None
        except Exception as e:
            self.log_test("POST /api/evaluations/submit", False, str(e))
            return False, None

    def test_get_evaluation_results(self, evaluation_id="test_eval_001"):
        """평가 결과 조회 API 테스트"""
        try:
            response = requests.get(
                f"{self.base_url}/api/evaluations/results/{evaluation_id}",
                headers=self.get_headers()
            )
            
            success = response.status_code == 200
            if success:
                data = response.json()
                self.log_test(f"GET /api/evaluations/results/{evaluation_id}", True, f"Results found: {bool(data)}")
                return True, data
            else:
                self.log_test(f"GET /api/evaluations/results/{evaluation_id}", False, f"Status: {response.status_code}, Body: {response.text}")
                return False, None
        except Exception as e:
            self.log_test(f"GET /api/evaluations/results/{evaluation_id}", False, str(e))
            return False, None

    def test_get_user_evaluations(self, user_id=None):
        """사용자 평가 목록 조회 API 테스트"""
        try:
            if not user_id:
                user_id = self.current_user.get("id", "test_user")
            
            response = requests.get(
                f"{self.base_url}/api/evaluations/user/{user_id}",
                headers=self.get_headers()
            )
            
            success = response.status_code == 200
            if success:
                data = response.json()
                evaluations_count = len(data) if isinstance(data, list) else 0
                self.log_test(f"GET /api/evaluations/user/{user_id}", True, f"Found {evaluations_count} evaluations")
                return True, data
            else:
                self.log_test(f"GET /api/evaluations/user/{user_id}", False, f"Status: {response.status_code}, Body: {response.text}")
                return False, None
        except Exception as e:
            self.log_test(f"GET /api/evaluations/user/{user_id}", False, str(e))
            return False, None

    def test_get_evaluation_statistics(self):
        """평가 통계 조회 API 테스트"""
        try:
            response = requests.get(
                f"{self.base_url}/api/evaluations/statistics",
                headers=self.get_headers()
            )
            
            success = response.status_code == 200
            if success:
                data = response.json()
                self.log_test("GET /api/evaluations/statistics", True, f"Statistics: {json.dumps(data, indent=2)}")
                return True, data
            else:
                self.log_test("GET /api/evaluations/statistics", False, f"Status: {response.status_code}, Body: {response.text}")
                return False, None
        except Exception as e:
            self.log_test("GET /api/evaluations/statistics", False, str(e))
            return False, None

    def test_submit_invalid_evaluation(self):
        """잘못된 데이터로 평가 제출 테스트 (에러 처리 확인)"""
        try:
            invalid_data = {
                "evaluation_id": "",  # 빈 evaluation_id
                "user_id": "",        # 빈 user_id
                "responses": {},      # 빈 responses
            }
            
            response = requests.post(
                f"{self.base_url}/api/evaluations/submit",
                headers=self.get_headers(),
                json=invalid_data
            )
            
            # 에러 응답을 기대 (400 또는 422)
            success = response.status_code in [400, 422]
            if success:
                self.log_test("POST /api/evaluations/submit (invalid data)", True, f"Properly returned error: {response.status_code}")
                return True
            else:
                self.log_test("POST /api/evaluations/submit (invalid data)", False, f"Expected error but got: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("POST /api/evaluations/submit (invalid data)", False, str(e))
            return False

    def test_get_nonexistent_evaluation_results(self):
        """존재하지 않는 평가 결과 조회 테스트"""
        try:
            response = requests.get(
                f"{self.base_url}/api/evaluations/results/nonexistent_id",
                headers=self.get_headers()
            )
            
            # 404 에러를 기대
            success = response.status_code == 404
            if success:
                self.log_test("GET /api/evaluations/results/nonexistent_id", True, "Properly returned 404")
                return True
            else:
                self.log_test("GET /api/evaluations/results/nonexistent_id", False, f"Expected 404 but got: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("GET /api/evaluations/results/nonexistent_id", False, str(e))
            return False

    def run_comprehensive_test(self):
        """종합 테스트 실행"""
        print("🔍 새로운 평가 API 엔드포인트 종합 테스트 시작")
        print("=" * 70)
        
        # 1. 서버 상태 확인
        if not self.test_health():
            print("❌ 서버 상태 확인 실패. 테스트를 중단합니다.")
            return False
        
        # 2. 관리자로 로그인
        if not self.login("admin", "admin123"):
            print("❌ 관리자 로그인 실패. 테스트를 중단합니다.")
            return False
        
        print("\n📋 새로운 평가 API 엔드포인트 테스트")
        print("-" * 50)
        
        # 3. 평가 제출 테스트
        success, submission_id = self.test_submit_evaluation()
        
        # 4. 평가 결과 조회 테스트
        self.test_get_evaluation_results()
        
        # 5. 사용자 평가 목록 조회 테스트
        self.test_get_user_evaluations()
        
        # 6. 평가 통계 조회 테스트
        self.test_get_evaluation_statistics()
        
        print("\n🔍 에러 처리 테스트")
        print("-" * 30)
        
        # 7. 잘못된 데이터로 평가 제출 테스트
        self.test_submit_invalid_evaluation()
        
        # 8. 존재하지 않는 평가 결과 조회 테스트
        self.test_get_nonexistent_evaluation_results()
        
        # 테스트 결과 요약
        print("\n📊 테스트 결과 요약")
        print("=" * 70)
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
    tester = NewEvaluationAPITester()
    success = tester.run_comprehensive_test()
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
