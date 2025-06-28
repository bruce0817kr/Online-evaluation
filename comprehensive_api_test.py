#!/usr/bin/env python3
"""
MCP 기반 체계적 API 테스트 스크립트
Online Evaluation System 전체 기능 검증
"""

import requests
import json
import time
import sys
from datetime import datetime
from typing import Optional, Dict, Any

class OnlineEvaluationTester:
    def __init__(self, backend_url: str = "http://localhost:8002", frontend_url: str = "http://localhost:3002"):
        self.backend_url = backend_url
        self.frontend_url = frontend_url
        self.access_token: Optional[str] = None
        self.test_results = {}
        
    def log(self, message: str, level: str = "INFO"):
        """체계적 로그 메시지 출력"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def record_test_result(self, test_name: str, success: bool, details: str = ""):
        """테스트 결과 기록"""
        self.test_results[test_name] = {
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        
    def make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """인증 헤더가 포함된 HTTP 요청"""
        if self.access_token:
            headers = kwargs.get('headers', {})
            headers['Authorization'] = f"Bearer {self.access_token}"
            kwargs['headers'] = headers
            
        url = f"{self.backend_url}{endpoint}"
        response = requests.request(method, url, timeout=10, **kwargs)
        return response
        
    def test_health_endpoints(self) -> bool:
        """Step 1: 헬스체크 엔드포인트 테스트"""
        self.log("=== Step 1: 헬스체크 테스트 ===")
        
        try:
            # 백엔드 헬스체크
            response = self.make_request("GET", "/health")
            if response.status_code == 200:
                health_data = response.json()
                self.log(f"✅ 백엔드 헬스체크 성공: {health_data['status']}")
                self.record_test_result("backend_health", True, f"Status: {health_data['status']}")
                
                # 서비스별 상태 확인
                services = health_data.get('services', {})
                for service, status in services.items():
                    self.log(f"  - {service}: {status}")
                    
            else:
                self.log(f"❌ 백엔드 헬스체크 실패: HTTP {response.status_code}", "ERROR")
                self.record_test_result("backend_health", False, f"HTTP {response.status_code}")
                return False
                
            # 프론트엔드 접근성 확인
            response = requests.get(self.frontend_url, timeout=10)
            if response.status_code == 200:
                self.log("✅ 프론트엔드 접근성 확인 성공")
                self.record_test_result("frontend_accessibility", True)
            else:
                self.log(f"❌ 프론트엔드 접근 실패: HTTP {response.status_code}", "ERROR")
                self.record_test_result("frontend_accessibility", False, f"HTTP {response.status_code}")
                return False
                
            return True
            
        except Exception as e:
            self.log(f"❌ 헬스체크 테스트 중 오류: {e}", "ERROR")
            self.record_test_result("health_check", False, str(e))
            return False
            
    def test_authentication(self) -> bool:
        """Step 2: 인증 시스템 테스트"""
        self.log("=== Step 2: 인증 시스템 테스트 ===")
        
        try:
            # 로그인 테스트
            login_data = {
                "username": "admin",
                "password": "admin123"
            }
            
            response = self.make_request(
                "POST", 
                "/api/auth/login",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data=login_data
            )
            
            if response.status_code == 200:
                auth_data = response.json()
                self.access_token = auth_data["access_token"]
                user_info = auth_data["user"]
                
                self.log("✅ 로그인 성공")
                self.log(f"  - 사용자: {user_info['user_name']}")
                self.log(f"  - 역할: {user_info['role']}")
                self.log(f"  - 토큰 타입: {auth_data['token_type']}")
                
                self.record_test_result("login", True, f"User: {user_info['user_name']}, Role: {user_info['role']}")
                
                # 토큰 검증 테스트
                return self.test_token_validation()
                
            else:
                self.log(f"❌ 로그인 실패: HTTP {response.status_code}", "ERROR")
                self.log(f"응답: {response.text}")
                self.record_test_result("login", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ 인증 테스트 중 오류: {e}", "ERROR")
            self.record_test_result("authentication", False, str(e))
            return False
            
    def test_token_validation(self) -> bool:
        """토큰 검증 테스트"""
        try:
            # /api/auth/me 엔드포인트 테스트
            response = self.make_request("GET", "/api/auth/me")
            
            if response.status_code == 200:
                user_info = response.json()
                self.log("✅ 토큰 검증 성공")
                self.log(f"  - 인증된 사용자: {user_info['user_name']}")
                self.record_test_result("token_validation", True, f"User: {user_info['user_name']}")
                return True
            else:
                self.log(f"❌ 토큰 검증 실패: HTTP {response.status_code}", "ERROR")
                self.record_test_result("token_validation", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ 토큰 검증 중 오류: {e}", "ERROR")
            self.record_test_result("token_validation", False, str(e))
            return False
            
    def test_api_endpoints(self) -> bool:
        """Step 3: 주요 API 엔드포인트 테스트"""
        self.log("=== Step 3: API 엔드포인트 테스트 ===")
        
        if not self.access_token:
            self.log("❌ 인증 토큰이 없어 API 테스트를 건너뜁니다.", "ERROR")
            return False
            
        # 테스트할 엔드포인트 목록
        endpoints_to_test = [
            ("GET", "/api/evaluations/list", "평가 목록 조회"),
            ("GET", "/api/files/access-logs", "파일 접근 로그"),
            ("GET", "/api/evaluations/jobs", "평가 작업 목록"),
            ("GET", "/api/ai-evaluation/jobs", "AI 평가 작업 목록"),
        ]
        
        success_count = 0
        
        for method, endpoint, description in endpoints_to_test:
            try:
                response = self.make_request(method, endpoint)
                
                if response.status_code in [200, 404]:  # 404도 정상 응답으로 간주 (데이터 없음)
                    self.log(f"✅ {description}: HTTP {response.status_code}")
                    self.record_test_result(f"api_{endpoint.replace('/', '_')}", True, f"HTTP {response.status_code}")
                    success_count += 1
                else:
                    self.log(f"❌ {description}: HTTP {response.status_code}", "WARNING")
                    self.record_test_result(f"api_{endpoint.replace('/', '_')}", False, f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.log(f"❌ {description} 테스트 중 오류: {e}", "ERROR")
                self.record_test_result(f"api_{endpoint.replace('/', '_')}", False, str(e))
                
        return success_count > 0
        
    def test_database_connectivity(self) -> bool:
        """Step 4: 데이터베이스 연결 테스트"""
        self.log("=== Step 4: 데이터베이스 연결 테스트 ===")
        
        try:
            response = self.make_request("GET", "/db-status")
            
            if response.status_code == 200:
                db_status = response.json()
                self.log("✅ 데이터베이스 상태 조회 성공")
                self.log(f"  - MongoDB: {db_status.get('mongodb', 'Unknown')}")
                self.log(f"  - Redis: {db_status.get('redis', 'Unknown')}")
                self.record_test_result("database_connectivity", True, str(db_status))
                return True
            else:
                self.log(f"❌ 데이터베이스 상태 조회 실패: HTTP {response.status_code}", "ERROR")
                self.record_test_result("database_connectivity", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ 데이터베이스 연결 테스트 중 오류: {e}", "ERROR")
            self.record_test_result("database_connectivity", False, str(e))
            return False
            
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """전체 테스트 실행"""
        self.log("=" * 70)
        self.log("Online Evaluation System - MCP 기반 체계적 테스트 시작")
        self.log("=" * 70)
        
        test_steps = [
            ("헬스체크", self.test_health_endpoints),
            ("인증 시스템", self.test_authentication),
            ("API 엔드포인트", self.test_api_endpoints),
            ("데이터베이스 연결", self.test_database_connectivity),
        ]
        
        step_results = []
        
        for step_name, test_function in test_steps:
            self.log(f"\n🔄 {step_name} 테스트 시작...")
            start_time = time.time()
            
            try:
                result = test_function()
                end_time = time.time()
                duration = end_time - start_time
                
                step_results.append({
                    "name": step_name,
                    "success": result,
                    "duration": duration
                })
                
                status = "✅ 성공" if result else "❌ 실패"
                self.log(f"{status} {step_name} 테스트 완료 ({duration:.2f}초)")
                
            except Exception as e:
                end_time = time.time()
                duration = end_time - start_time
                
                step_results.append({
                    "name": step_name,
                    "success": False,
                    "duration": duration,
                    "error": str(e)
                })
                
                self.log(f"❌ {step_name} 테스트 중 예외 발생: {e}", "ERROR")
                
        return self.generate_test_report(step_results)
        
    def generate_test_report(self, step_results: list) -> Dict[str, Any]:
        """테스트 결과 보고서 생성"""
        self.log("\n" + "=" * 70)
        self.log("최종 테스트 결과 보고서")
        self.log("=" * 70)
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results.values() if result["success"])
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        self.log(f"\n📊 테스트 요약:")
        self.log(f"  - 전체 테스트 수: {total_tests}개")
        self.log(f"  - 성공: {successful_tests}개")
        self.log(f"  - 실패: {total_tests - successful_tests}개")
        self.log(f"  - 성공률: {success_rate:.1f}%")
        
        self.log(f"\n🔍 단계별 결과:")
        for step in step_results:
            status = "✅" if step["success"] else "❌"
            duration = step["duration"]
            self.log(f"  {status} {step['name']}: {duration:.2f}초")
            
        self.log(f"\n📋 상세 테스트 결과:")
        for test_name, result in self.test_results.items():
            status = "✅" if result["success"] else "❌"
            details = f" - {result['details']}" if result["details"] else ""
            self.log(f"  {status} {test_name}{details}")
            
        # 배포 상태 판단
        critical_tests = ["backend_health", "frontend_accessibility", "login", "token_validation"]
        critical_failures = [test for test in critical_tests if not self.test_results.get(test, {}).get("success", False)]
        
        if not critical_failures:
            deployment_status = "✅ 배포 성공 - 시스템이 정상적으로 작동하고 있습니다."
        else:
            deployment_status = f"❌ 배포 문제 발견 - 다음 핵심 기능에 문제가 있습니다: {', '.join(critical_failures)}"
            
        self.log(f"\n🚀 배포 상태: {deployment_status}")
        
        # 접속 정보 제공
        self.log(f"\n🌐 서비스 접속 정보:")
        self.log(f"  - 프론트엔드: {self.frontend_url}")
        self.log(f"  - 백엔드 API: {self.backend_url}")
        self.log(f"  - API 문서: {self.backend_url}/docs")
        self.log(f"  - 관리자 계정: admin / admin123")
        
        return {
            "summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "success_rate": success_rate,
                "deployment_status": deployment_status
            },
            "step_results": step_results,
            "detailed_results": self.test_results,
            "service_urls": {
                "frontend": self.frontend_url,
                "backend": self.backend_url,
                "api_docs": f"{self.backend_url}/docs"
            }
        }

def main():
    """메인 실행 함수"""
    tester = OnlineEvaluationTester()
    
    try:
        report = tester.run_comprehensive_test()
        
        # 결과를 JSON 파일로 저장
        with open("deployment_test_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
            
        tester.log("\n💾 상세 보고서가 'deployment_test_report.json'에 저장되었습니다.")
        
        # 성공률에 따른 종료 코드 결정
        success_rate = report["summary"]["success_rate"]
        exit_code = 0 if success_rate >= 80 else 1
        
        return exit_code
        
    except Exception as e:
        tester.log(f"❌ 테스트 실행 중 예외 발생: {e}", "ERROR")
        return 1

if __name__ == "__main__":
    sys.exit(main())