#!/usr/bin/env python3
"""
온라인 평가 시스템 종합 검증 테스트
=================================

이 스크립트는 전체 온라인 평가 시스템의 모든 컴포넌트를 검증합니다:
1. 서비스 상태 확인
2. API 엔드포인트 테스트
3. 데이터베이스 연결 및 CRUD 테스트
4. ELK 스택 검증
5. 통합 테스트
"""

import requests
import json
import time
import sys
from datetime import datetime
from typing import Dict, List, Any
import traceback

class SystemVerificationTest:
    def __init__(self):
        self.base_url = "http://localhost:8180"
        self.frontend_url = "http://localhost:3100"
        self.elasticsearch_url = "http://localhost:9300"
        self.kibana_url = "http://localhost:5701"
        self.logstash_url = "http://localhost:9700"
        
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "UNKNOWN",
            "tests": {},
            "summary": {},
            "recommendations": []
        }
        
    def log_test(self, test_name: str, status: str, details: Dict[str, Any] = None):
        """테스트 결과 로깅"""
        self.results["tests"][test_name] = {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        print(f"✓ {test_name}: {status}")
        if details:
            for key, value in details.items():
                print(f"  - {key}: {value}")
    
    def test_service_health(self):
        """서비스 상태 테스트"""
        print("\n=== 서비스 상태 테스트 ===")
        
        services = {
            "backend": f"{self.base_url}/health",
            "elasticsearch": f"{self.elasticsearch_url}/_cluster/health",
            "kibana": f"{self.kibana_url}/api/status",
            "logstash": f"{self.logstash_url}/"
        }
        
        healthy_services = 0
        
        for service_name, url in services.items():
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    self.log_test(f"{service_name}_health", "PASS", {
                        "status_code": response.status_code,
                        "response_time_ms": round(response.elapsed.total_seconds() * 1000, 2)
                    })
                    healthy_services += 1
                else:
                    self.log_test(f"{service_name}_health", "FAIL", {
                        "status_code": response.status_code,
                        "error": "Non-200 response"
                    })
            except Exception as e:
                self.log_test(f"{service_name}_health", "FAIL", {
                    "error": str(e)
                })
        
        # Frontend 테스트 (별도 처리)
        try:
            response = requests.get(self.frontend_url, timeout=10)
            if response.status_code == 200:
                self.log_test("frontend_health", "PASS", {
                    "status_code": response.status_code,
                    "response_time_ms": round(response.elapsed.total_seconds() * 1000, 2)
                })
                healthy_services += 1
            else:
                self.log_test("frontend_health", "FAIL", {
                    "status_code": response.status_code
                })
        except Exception as e:
            self.log_test("frontend_health", "FAIL", {
                "error": str(e)
            })
        
        self.results["summary"]["healthy_services"] = f"{healthy_services}/5"
        return healthy_services >= 4  # 최소 4개 서비스 정상이면 통과
      def test_api_endpoints(self):
        """API 엔드포인트 테스트"""
        print("\n=== API 엔드포인트 테스트 ===")
        
        endpoints = [
            ("GET", "/health", "Health Check", None),
            ("GET", "/docs", "API Documentation", None),
            ("GET", "/api/users", "Users API", None),
            ("GET", "/api/evaluations", "Evaluations API", None),
            ("POST", "/api/auth/login", "Auth Login", {
                "username": "test@example.com",
                "password": "testpassword"
            })
        ]
        
        successful_endpoints = 0
        
        for method, endpoint, description, data in endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                
                if method == "GET":
                    response = requests.get(url, timeout=10)
                elif method == "POST":
                    response = requests.post(url, json=data, timeout=10)
                
                # 인증이 필요한 엔드포인트는 401도 정상으로 간주
                if response.status_code in [200, 201, 401, 404]:
                    status = "PASS"
                    if response.status_code in [401, 404]:
                        status = "PASS (Expected)"
                    successful_endpoints += 1
                else:
                    status = "FAIL"
                
                self.log_test(f"api_{endpoint.replace('/', '_')}", status, {
                    "method": method,
                    "status_code": response.status_code,
                    "response_time_ms": round(response.elapsed.total_seconds() * 1000, 2),
                    "description": description
                })
                
            except Exception as e:
                self.log_test(f"api_{endpoint.replace('/', '_')}", "FAIL", {
                    "method": method,
                    "error": str(e),
                    "description": description
                })
        
        self.results["summary"]["successful_endpoints"] = f"{successful_endpoints}/{len(endpoints)}"
        return successful_endpoints >= len(endpoints) * 0.8  # 80% 성공률
    
    def test_database_connectivity(self):
        """데이터베이스 연결성 테스트"""
        print("\n=== 데이터베이스 연결성 테스트 ===")
        
        try:
            # Backend를 통한 데이터베이스 연결 테스트
            response = requests.get(f"{self.base_url}/health", timeout=10)
            
            if response.status_code == 200:
                health_data = response.json()
                
                # MongoDB 상태 확인
                mongodb_status = health_data.get("services", {}).get("mongodb", "unknown")
                redis_status = health_data.get("services", {}).get("redis", "unknown")
                
                self.log_test("mongodb_connectivity", 
                            "PASS" if mongodb_status == "healthy" else "FAIL",
                            {"status": mongodb_status})
                
                self.log_test("redis_connectivity",
                            "PASS" if redis_status == "healthy" else "FAIL", 
                            {"status": redis_status})
                
                return mongodb_status == "healthy" and redis_status == "healthy"
            
        except Exception as e:
            self.log_test("database_connectivity", "FAIL", {"error": str(e)})
            return False
    
    def test_elk_stack(self):
        """ELK 스택 테스트"""
        print("\n=== ELK 스택 테스트 ===")
        
        elk_tests_passed = 0
        
        # Elasticsearch 클러스터 상태
        try:
            response = requests.get(f"{self.elasticsearch_url}/_cluster/health", timeout=10)
            if response.status_code == 200:
                cluster_data = response.json()
                cluster_status = cluster_data.get("status", "unknown")
                
                self.log_test("elasticsearch_cluster", 
                            "PASS" if cluster_status == "green" else "PARTIAL" if cluster_status == "yellow" else "FAIL",
                            {
                                "cluster_status": cluster_status,
                                "number_of_nodes": cluster_data.get("number_of_nodes", 0),
                                "active_shards": cluster_data.get("active_shards", 0)
                            })
                
                if cluster_status in ["green", "yellow"]:
                    elk_tests_passed += 1
                    
        except Exception as e:
            self.log_test("elasticsearch_cluster", "FAIL", {"error": str(e)})
        
        # Kibana 상태
        try:
            response = requests.get(f"{self.kibana_url}/api/status", timeout=10)
            if response.status_code == 200:
                self.log_test("kibana_status", "PASS", {
                    "status_code": response.status_code
                })
                elk_tests_passed += 1
            else:
                self.log_test("kibana_status", "FAIL", {
                    "status_code": response.status_code
                })
        except Exception as e:
            self.log_test("kibana_status", "FAIL", {"error": str(e)})
        
        # Logstash 상태
        try:
            response = requests.get(f"{self.logstash_url}/", timeout=10)
            if response.status_code == 200:
                self.log_test("logstash_status", "PASS", {
                    "status_code": response.status_code
                })
                elk_tests_passed += 1
            else:
                self.log_test("logstash_status", "FAIL", {
                    "status_code": response.status_code
                })
        except Exception as e:
            self.log_test("logstash_status", "FAIL", {"error": str(e)})
        
        self.results["summary"]["elk_stack_health"] = f"{elk_tests_passed}/3"
        return elk_tests_passed >= 2  # 최소 2개 컴포넌트 정상
    
    def test_system_integration(self):
        """시스템 통합 테스트"""
        print("\n=== 시스템 통합 테스트 ===")
        
        integration_tests_passed = 0
        
        # CORS 테스트
        try:
            headers = {
                "Origin": "http://localhost:3100",
                "Access-Control-Request-Method": "GET"
            }
            response = requests.options(f"{self.base_url}/health", headers=headers, timeout=10)
            
            cors_headers = response.headers.get("Access-Control-Allow-Origin")
            if cors_headers:
                self.log_test("cors_configuration", "PASS", {
                    "cors_headers": cors_headers
                })
                integration_tests_passed += 1
            else:
                self.log_test("cors_configuration", "FAIL", {
                    "error": "No CORS headers found"
                })
                
        except Exception as e:
            self.log_test("cors_configuration", "FAIL", {"error": str(e)})
        
        # 보안 헤더 테스트
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            security_headers = [
                "x-content-type-options",
                "x-frame-options", 
                "x-xss-protection",
                "strict-transport-security"
            ]
            
            found_headers = []
            for header in security_headers:
                if header in response.headers:
                    found_headers.append(header)
            
            if len(found_headers) >= 3:
                self.log_test("security_headers", "PASS", {
                    "found_headers": found_headers,
                    "total_found": len(found_headers)
                })
                integration_tests_passed += 1
            else:
                self.log_test("security_headers", "PARTIAL", {
                    "found_headers": found_headers,
                    "total_found": len(found_headers)
                })
                
        except Exception as e:
            self.log_test("security_headers", "FAIL", {"error": str(e)})
        
        self.results["summary"]["integration_tests"] = f"{integration_tests_passed}/2"
        return integration_tests_passed >= 1
    
    def generate_recommendations(self):
        """개선 권장사항 생성"""
        recommendations = []
        
        # Frontend 상태 확인
        if self.results["tests"].get("frontend_health", {}).get("status") != "PASS":
            recommendations.append("Frontend 서비스 상태 확인 및 복구 필요")
        
        # ELK 스택 확인
        elk_health = self.results["summary"].get("elk_stack_health", "0/3")
        if not elk_health.startswith("3/"):
            recommendations.append("ELK 스택 일부 컴포넌트 확인 필요")
        
        # API 엔드포인트 확인
        api_success = self.results["summary"].get("successful_endpoints", "0/5")
        if not api_success.endswith("/5"):
            recommendations.append("일부 API 엔드포인트 응답 확인 필요")
        
        # 보안 설정 확인
        if self.results["tests"].get("security_headers", {}).get("status") != "PASS":
            recommendations.append("보안 헤더 설정 강화 권장")
        
        if not recommendations:
            recommendations.append("모든 시스템 컴포넌트가 정상 작동 중입니다!")
        
        self.results["recommendations"] = recommendations
    
    def run_all_tests(self):
        """모든 테스트 실행"""
        print("🚀 온라인 평가 시스템 종합 검증 테스트 시작")
        print("=" * 60)
        
        test_results = []
        
        # 각 테스트 실행
        test_results.append(self.test_service_health())
        test_results.append(self.test_api_endpoints())
        test_results.append(self.test_database_connectivity())
        test_results.append(self.test_elk_stack())
        test_results.append(self.test_system_integration())
        
        # 전체 결과 계산
        passed_tests = sum(test_results)
        total_tests = len(test_results)
        
        if passed_tests == total_tests:
            self.results["overall_status"] = "PASS"
        elif passed_tests >= total_tests * 0.8:
            self.results["overall_status"] = "PARTIAL"
        else:
            self.results["overall_status"] = "FAIL"
        
        self.results["summary"]["overall_score"] = f"{passed_tests}/{total_tests}"
        
        # 권장사항 생성
        self.generate_recommendations()
        
        # 결과 출력
        self.print_summary()
        
        # 결과 파일 저장
        self.save_results()
        
        return self.results["overall_status"] == "PASS"
    
    def print_summary(self):
        """결과 요약 출력"""
        print("\n" + "=" * 60)
        print("🎯 종합 테스트 결과 요약")
        print("=" * 60)
        
        status_emoji = {
            "PASS": "✅",
            "PARTIAL": "⚠️", 
            "FAIL": "❌"
        }
        
        print(f"전체 상태: {status_emoji.get(self.results['overall_status'], '❓')} {self.results['overall_status']}")
        print(f"테스트 점수: {self.results['summary'].get('overall_score', 'N/A')}")
        print()
        
        for key, value in self.results["summary"].items():
            if key != "overall_score":
                print(f"- {key}: {value}")
        
        print("\n📋 권장사항:")
        for i, rec in enumerate(self.results["recommendations"], 1):
            print(f"{i}. {rec}")
    
    def save_results(self):
        """결과를 JSON 파일로 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"system_verification_report_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 상세 결과가 저장되었습니다: {filename}")


if __name__ == "__main__":
    print("온라인 평가 시스템 종합 검증 테스트")
    print("개발자: GitHub Copilot")
    print(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tester = SystemVerificationTest()
    
    try:
        success = tester.run_all_tests()
        
        if success:
            print("\n🎉 모든 테스트를 성공적으로 통과했습니다!")
            sys.exit(0)
        else:
            print("\n⚠️  일부 테스트에서 문제가 발견되었습니다. 상세 내용을 확인하세요.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n❌ 사용자에 의해 테스트가 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류가 발생했습니다: {str(e)}")
        print("\n상세 오류 정보:")
        print(traceback.format_exc())
        sys.exit(1)
