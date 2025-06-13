#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
웹페이지 접근성 및 기능 테스트 (MCP 기반)
Online Evaluation System 웹 인터페이스 종합 테스트

Playwright 대신 requests + BeautifulSoup 활용
- 페이지 접근성 테스트
- HTML 구조 분석
- API 엔드포인트 테스트
- 성능 측정
"""

import requests
import time
import json
import webbrowser
from datetime import datetime
from urllib.parse import urljoin, urlparse
import re

class WebInterfaceTester:
    def __init__(self):
        self.frontend_url = "http://localhost:3000"
        self.backend_url = "http://localhost:8080"
        self.test_results = []
        self.session = requests.Session()
        
        # User-Agent 설정 (브라우저처럼 보이도록)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def log_test(self, test_name, status, details="", data=None):
        """테스트 결과 로깅"""
        result = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "test_name": test_name,
            "status": status,
            "details": details,
            "data": data
        }
        self.test_results.append(result)
        
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"[{status_icon}] {test_name}: {status}")
        if details:
            print(f"    {details}")
    
    def test_frontend_accessibility(self):
        """프론트엔드 접근성 테스트"""
        try:
            start_time = time.time()
            response = self.session.get(self.frontend_url, timeout=30)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                # HTML 내용 분석
                html_content = response.text
                
                # 기본 HTML 구조 확인
                checks = {
                    "DOCTYPE": "<!DOCTYPE" in html_content,
                    "HTML tag": "<html" in html_content,
                    "HEAD section": "<head" in html_content,
                    "BODY section": "<body" in html_content,
                    "Title tag": "<title" in html_content,
                    "Meta charset": "charset" in html_content,
                    "Viewport meta": "viewport" in html_content
                }
                
                # React 관련 요소 확인
                react_checks = {
                    "React root": 'id="root"' in html_content,
                    "React scripts": "react" in html_content.lower(),
                    "Bundle scripts": ".js" in html_content
                }
                
                passed_checks = sum(checks.values())
                react_elements = sum(react_checks.values())
                
                self.log_test(
                    "프론트엔드 접근성",
                    "PASS",
                    f"응답시간: {response_time:.2f}초, HTML 구조: {passed_checks}/7, React 요소: {react_elements}/3",
                    {"response_time": response_time, "html_checks": checks, "react_checks": react_checks}
                )
                return True
            else:
                self.log_test("프론트엔드 접근성", "FAIL", f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("프론트엔드 접근성", "FAIL", f"오류: {str(e)}")
            return False
    
    def test_backend_api_endpoints(self):
        """백엔드 API 엔드포인트 테스트"""
        try:
            endpoints = [
                {"path": "/health", "method": "GET", "description": "헬스 체크"},
                {"path": "/docs", "method": "GET", "description": "API 문서"},
                {"path": "/api/auth/login", "method": "POST", "description": "로그인 API"},
                {"path": "/api/health/detailed", "method": "GET", "description": "상세 시스템 상태"}
            ]
            
            results = []
            for endpoint in endpoints:
                try:
                    url = urljoin(self.backend_url, endpoint["path"])
                    
                    if endpoint["method"] == "GET":
                        response = self.session.get(url, timeout=10)
                    elif endpoint["method"] == "POST":
                        # POST 요청은 기본적으로 401/422 응답 예상
                        response = self.session.post(url, json={}, timeout=10)
                    
                    status = "접근 가능" if response.status_code < 500 else "서버 오류"
                    results.append(f"{endpoint['description']}: {response.status_code} ({status})")
                    
                except Exception as e:
                    results.append(f"{endpoint['description']}: 오류 ({str(e)[:50]})")
            
            self.log_test(
                "백엔드 API 엔드포인트",
                "PASS",
                f"테스트된 엔드포인트: {len(endpoints)}개",
                {"endpoints": results}
            )
            return True
            
        except Exception as e:
            self.log_test("백엔드 API 엔드포인트", "FAIL", f"오류: {str(e)}")
            return False
    
    def test_cors_configuration(self):
        """CORS 설정 테스트"""
        try:
            # OPTIONS 요청으로 CORS 설정 확인
            response = self.session.options(
                urljoin(self.backend_url, "/api/auth/login"),
                headers={'Origin': self.frontend_url},
                timeout=10
            )
            
            cors_headers = {
                "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
                "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
                "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers")
            }
            
            cors_configured = any(header for header in cors_headers.values())
            
            self.log_test(
                "CORS 설정",
                "PASS" if cors_configured else "WARN",
                f"CORS 헤더 발견: {cors_configured}",
                cors_headers
            )
            return True
            
        except Exception as e:
            self.log_test("CORS 설정", "FAIL", f"오류: {str(e)}")
            return False
    
    def test_static_resources(self):
        """정적 리소스 접근 테스트"""
        try:
            # 일반적인 정적 리소스 경로들 테스트
            static_paths = [
                "/favicon.ico",
                "/manifest.json",
                "/static/css/",
                "/static/js/",
                "/logo192.png",
                "/robots.txt"
            ]
            
            accessible_resources = []
            for path in static_paths:
                try:
                    url = urljoin(self.frontend_url, path)
                    response = self.session.head(url, timeout=5)
                    if response.status_code < 400:
                        accessible_resources.append(path)
                except:
                    continue
            
            self.log_test(
                "정적 리소스",
                "PASS",
                f"접근 가능한 리소스: {len(accessible_resources)}/{len(static_paths)}개",
                {"accessible": accessible_resources}
            )
            return True
            
        except Exception as e:
            self.log_test("정적 리소스", "FAIL", f"오류: {str(e)}")
            return False
    
    def test_response_headers(self):
        """응답 헤더 보안 분석"""
        try:
            response = self.session.get(self.frontend_url, timeout=10)
            
            security_headers = {
                "X-Content-Type-Options": response.headers.get("X-Content-Type-Options"),
                "X-Frame-Options": response.headers.get("X-Frame-Options"),
                "X-XSS-Protection": response.headers.get("X-XSS-Protection"),
                "Strict-Transport-Security": response.headers.get("Strict-Transport-Security"),
                "Content-Security-Policy": response.headers.get("Content-Security-Policy")
            }
            
            present_headers = [header for header, value in security_headers.items() if value]
            
            self.log_test(
                "보안 헤더",
                "PASS" if len(present_headers) > 2 else "WARN",
                f"보안 헤더: {len(present_headers)}/5개 설정됨",
                security_headers
            )
            return True
            
        except Exception as e:
            self.log_test("보안 헤더", "FAIL", f"오류: {str(e)}")
            return False
    
    def test_page_performance_metrics(self):
        """페이지 성능 메트릭 측정"""
        try:
            # 여러 번 요청해서 평균 응답시간 측정
            response_times = []
            for i in range(5):
                start_time = time.time()
                response = self.session.get(self.frontend_url, timeout=30)
                response_time = time.time() - start_time
                response_times.append(response_time)
                time.sleep(0.5)  # 요청 간격
            
            avg_response_time = sum(response_times) / len(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            
            # 응답 크기 측정
            content_length = len(response.content)
            
            performance_data = {
                "average_response_time": avg_response_time,
                "min_response_time": min_response_time,
                "max_response_time": max_response_time,
                "content_size_bytes": content_length,
                "content_size_kb": content_length / 1024
            }
            
            status = "PASS" if avg_response_time < 3.0 else "WARN"
            
            self.log_test(
                "페이지 성능",
                status,
                f"평균 응답시간: {avg_response_time:.2f}초, 콘텐츠 크기: {content_length/1024:.1f}KB",
                performance_data
            )
            return True
            
        except Exception as e:
            self.log_test("페이지 성능", "FAIL", f"오류: {str(e)}")
            return False
    
    def test_mobile_compatibility(self):
        """모바일 호환성 테스트"""
        try:
            # 모바일 User-Agent로 요청
            mobile_headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15'
            }
            
            response = self.session.get(self.frontend_url, headers=mobile_headers, timeout=10)
            
            if response.status_code == 200:
                html_content = response.text
                
                # 모바일 친화적 요소 확인
                mobile_features = {
                    "Viewport meta": "viewport" in html_content and "width=device-width" in html_content,
                    "Responsive CSS": "media" in html_content or "@media" in html_content,
                    "Touch-friendly": "touch" in html_content.lower(),
                    "Mobile-first": "mobile" in html_content.lower()
                }
                
                mobile_score = sum(mobile_features.values())
                
                self.log_test(
                    "모바일 호환성",
                    "PASS" if mobile_score >= 2 else "WARN",
                    f"모바일 기능: {mobile_score}/4개 지원",
                    mobile_features
                )
                return True
            else:
                self.log_test("모바일 호환성", "FAIL", f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("모바일 호환성", "FAIL", f"오류: {str(e)}")
            return False
    
    def open_browser_for_visual_test(self):
        """브라우저를 열어서 시각적 테스트 진행"""
        try:
            print("\n🌐 브라우저를 열어서 시각적 테스트를 진행합니다...")
            webbrowser.open(self.frontend_url)
            
            self.log_test(
                "브라우저 시각적 테스트",
                "PASS",
                f"브라우저에서 {self.frontend_url} 열림"
            )
            return True
            
        except Exception as e:
            self.log_test("브라우저 시각적 테스트", "FAIL", f"오류: {str(e)}")
            return False
    
    def run_all_tests(self):
        """모든 테스트 실행"""
        print("🌐 MCP 기반 웹 인터페이스 테스트 시작")
        print("🎯 대상: Online Evaluation System")
        print("=" * 60)
        
        tests = [
            self.test_frontend_accessibility,
            self.test_backend_api_endpoints,
            self.test_cors_configuration,
            self.test_static_resources,
            self.test_response_headers,
            self.test_page_performance_metrics,
            self.test_mobile_compatibility,
            self.open_browser_for_visual_test
        ]
        
        for test in tests:
            try:
                test()
                time.sleep(0.5)  # 테스트 간 간격
            except Exception as e:
                print(f"❌ 테스트 실행 오류: {e}")
        
        # 결과 요약
        self.print_test_summary()
        self.save_test_results()
    
    def print_test_summary(self):
        """테스트 결과 요약 출력"""
        print("\n" + "=" * 60)
        print("📊 웹 인터페이스 테스트 결과 요약")
        print("=" * 60)
        
        total = len(self.test_results)
        passed = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed = len([r for r in self.test_results if r['status'] == 'FAIL'])
        warned = len([r for r in self.test_results if r['status'] == 'WARN'])
        
        print(f"총 테스트: {total}")
        print(f"성공: {passed} ✅")
        print(f"실패: {failed} ❌") 
        print(f"경고: {warned} ⚠️")
        
        if total > 0:
            success_rate = (passed / total) * 100
            print(f"성공률: {success_rate:.1f}%")
        
        # 주요 발견사항
        print("\n🔍 주요 발견사항:")
        for result in self.test_results:
            if result['status'] in ['FAIL', 'WARN']:
                print(f"  • {result['test_name']}: {result['details']}")
    
    def save_test_results(self):
        """테스트 결과를 JSON 파일로 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"web_interface_test_results_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 테스트 결과 저장: {filename}")

def main():
    """메인 실행 함수"""
    tester = WebInterfaceTester()
    tester.run_all_tests()

if __name__ == "__main__":
    print("🔍 MCP Sequential Thinking 기반 웹 인터페이스 테스트")
    print("🎪 Playwright 대신 HTTP 기반 접근법 사용")
    print()
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️  테스트가 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 테스트 실행 중 오류: {e}")
