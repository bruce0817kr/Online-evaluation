#!/usr/bin/env python3
"""
Task 158 - 최종 시스템 테스트 스크립트
로그인 문제 해결 후 전체 API 기능 검증
"""

import requests
import json
import time
from datetime import datetime

# API 기본 URL
BASE_URL = "http://localhost:8080"
API_URL = f"{BASE_URL}/api"

class SystemTester:
    def __init__(self):
        self.tokens = {}
        self.test_results = []
        
    def log_test(self, test_name, success, message=""):
        """테스트 결과 로깅"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
    
    def login_user(self, username, password, role):
        """사용자 로그인"""
        try:
            response = requests.post(
                f"{API_URL}/auth/login",
                data={"username": username, "password": password},
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.tokens[role] = data["access_token"]
                user_info = data["user"]
                self.log_test(f"{role.upper()} 로그인", True, 
                            f"{user_info['user_name']} ({user_info['login_id']})")
                return True
            else:
                self.log_test(f"{role.upper()} 로그인", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test(f"{role.upper()} 로그인", False, str(e))
            return False
    
    def test_protected_endpoint(self, endpoint, role, method="GET", data=None):
        """인증이 필요한 엔드포인트 테스트"""
        try:
            headers = {"Authorization": f"Bearer {self.tokens[role]}"}
            
            if method == "GET":
                response = requests.get(f"{API_URL}{endpoint}", headers=headers)
            elif method == "POST":
                headers["Content-Type"] = "application/json"
                response = requests.post(f"{API_URL}{endpoint}", 
                                       headers=headers, json=data)
            
            success = response.status_code < 400
            self.log_test(f"{role.upper()} {method} {endpoint}", success,
                        f"HTTP {response.status_code}")
            return success, response
            
        except Exception as e:
            self.log_test(f"{role.upper()} {method} {endpoint}", False, str(e))
            return False, None
    
    def test_health_endpoints(self):
        """헬스체크 엔드포인트 테스트"""
        print("\n🏥 헬스체크 엔드포인트 테스트")
        
        endpoints = [
            "/health",
            "/db-status",
            "/api/health/detailed",
            "/api/health/liveness", 
            "/api/health/readiness",
            "/api/health/metrics"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(f"{BASE_URL}{endpoint}")
                success = response.status_code == 200
                self.log_test(f"헬스체크 {endpoint}", success, 
                            f"HTTP {response.status_code}")
            except Exception as e:
                self.log_test(f"헬스체크 {endpoint}", False, str(e))
    
    def test_authentication(self):
        """인증 테스트"""
        print("\n🔐 사용자 인증 테스트")
        
        # 테스트할 사용자들
        test_users = [
            ("admin", "admin123", "admin"),
            ("secretary01", "secretary123", "secretary"),
            ("evaluator01", "evaluator123", "evaluator")
        ]
        
        for username, password, role in test_users:
            self.login_user(username, password, role)
        
        # 잘못된 인증 정보 테스트
        try:
            response = requests.post(
                f"{API_URL}/auth/login",
                data={"username": "wrong", "password": "wrong"},
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            success = response.status_code == 401
            self.log_test("잘못된 인증 정보", success, 
                        f"HTTP {response.status_code} (예상: 401)")
        except Exception as e:
            self.log_test("잘못된 인증 정보", False, str(e))
    
    def test_admin_endpoints(self):
        """관리자 엔드포인트 테스트"""
        print("\n👑 관리자 엔드포인트 테스트")
        
        if "admin" not in self.tokens:
            self.log_test("관리자 엔드포인트", False, "관리자 토큰이 없습니다")
            return
        
        endpoints = [
            "/admin/users",
            "/admin/secretary-requests"
        ]
        
        for endpoint in endpoints:
            self.test_protected_endpoint(endpoint, "admin")
    
    def test_secretary_endpoints(self):
        """간사 엔드포인트 테스트"""
        print("\n📋 간사 엔드포인트 테스트")
        
        if "secretary" not in self.tokens:
            self.log_test("간사 엔드포인트", False, "간사 토큰이 없습니다")
            return
        
        endpoints = [
            "/secretary/projects",
            "/secretary/companies",
            "/secretary/evaluations"
        ]
        
        for endpoint in endpoints:
            self.test_protected_endpoint(endpoint, "secretary")
    
    def test_evaluator_endpoints(self):
        """평가자 엔드포인트 테스트"""
        print("\n📝 평가자 엔드포인트 테스트")
        
        if "evaluator" not in self.tokens:
            self.log_test("평가자 엔드포인트", False, "평가자 토큰이 없습니다")
            return
        
        endpoints = [
            "/evaluator/projects",
            "/evaluator/companies", 
            "/evaluator/evaluations"
        ]
        
        for endpoint in endpoints:
            self.test_protected_endpoint(endpoint, "evaluator")
    
    def test_template_endpoints(self):
        """템플릿 엔드포인트 테스트"""
        print("\n📋 템플릿 엔드포인트 테스트")
        
        if "admin" not in self.tokens:
            self.log_test("템플릿 엔드포인트", False, "관리자 토큰이 없습니다")
            return
        
        # 템플릿 목록 조회
        self.test_protected_endpoint("/templates", "admin")
    
    def test_project_endpoints(self):
        """프로젝트 엔드포인트 테스트"""
        print("\n🎯 프로젝트 엔드포인트 테스트")
        
        if "admin" not in self.tokens:
            self.log_test("프로젝트 엔드포인트", False, "관리자 토큰이 없습니다")
            return
        
        # 프로젝트 목록 조회
        self.test_protected_endpoint("/projects", "admin")
    
    def test_current_user(self):
        """현재 사용자 정보 조회 테스트"""
        print("\n👤 현재 사용자 정보 테스트")
        
        for role in self.tokens:
            self.test_protected_endpoint("/auth/me", role)
    
    def print_summary(self):
        """테스트 결과 요약"""
        print("\n" + "="*60)
        print("📊 최종 시스템 테스트 결과 요약")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"총 테스트: {total_tests}")
        print(f"성공: {passed_tests} ✅")
        print(f"실패: {failed_tests} ❌")
        print(f"성공률: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print("\n❌ 실패한 테스트:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        print("\n" + "="*60)
        
        # 결과를 JSON 파일로 저장
        with open("final_system_test_results.json", "w", encoding="utf-8") as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        
        print("📄 상세 결과가 'final_system_test_results.json'에 저장되었습니다.")

def main():
    print("🚀 Task 158 - 최종 시스템 테스트 시작")
    print(f"🌐 테스트 대상: {BASE_URL}")
    print(f"⏰ 테스트 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tester = SystemTester()
    
    # 순차적으로 테스트 실행
    tester.test_health_endpoints()
    tester.test_authentication()
    tester.test_current_user()
    tester.test_admin_endpoints()
    tester.test_secretary_endpoints()
    tester.test_evaluator_endpoints()
    tester.test_template_endpoints()
    tester.test_project_endpoints()
    
    # 결과 요약
    tester.print_summary()
    
    print(f"\n⏰ 테스트 완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎉 최종 시스템 테스트가 완료되었습니다!")

if __name__ == "__main__":
    main()
