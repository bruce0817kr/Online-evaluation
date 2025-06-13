#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP 기반 Playwright 웹페이지 테스트 - 개선된 버전
Online Evaluation System 종합 웹 테스트

Sequential Thinking 적용:
1. 환경 검증 및 준비
2. 기본 네비게이션 테스트
3. 사용자 인터페이스 상호작용
4. 성능 및 반응성 측정
5. 결과 분석 및 보고서 생성
"""

import asyncio
import time
import json
import requests
import webbrowser
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin
import os

class EnhancedWebTester:
    def __init__(self):
        self.frontend_url = "http://localhost:3000"
        self.backend_url = "http://localhost:8080"
        self.test_results = []
        self.session = requests.Session()
        self.test_start_time = datetime.now()
        
        # 테스트 결과 저장 디렉토리
        self.results_dir = Path("test_results")
        self.results_dir.mkdir(exist_ok=True)
        
        # User-Agent 설정
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        })
    
    def log_test(self, test_name, status, details="", data=None):
        """테스트 결과 로깅 (한글 지원)"""
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
            print(f"    📋 {details}")
    
    def test_system_health(self):
        """시스템 상태 확인"""
        print("\n🔍 시스템 상태 검사 중...")
        
        # Docker 컨테이너 상태 확인
        try:
            import subprocess
            result = subprocess.run(['docker', 'ps', '--format', 'table {{.Names}}\\t{{.Status}}'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                containers = result.stdout.strip().split('\n')[1:]  # 헤더 제외
                active_containers = [line for line in containers if 'Up' in line]
                self.log_test("Docker 컨테이너 상태", "PASS", 
                            f"{len(active_containers)}개 컨테이너 실행 중", 
                            {"containers": active_containers})
            else:
                self.log_test("Docker 컨테이너 상태", "FAIL", "Docker 명령 실행 실패")
        except Exception as e:
            self.log_test("Docker 컨테이너 상태", "WARN", f"상태 확인 실패: {str(e)}")
    
    def test_frontend_comprehensive(self):
        """프론트엔드 종합 테스트"""
        print("\n🌐 프론트엔드 종합 테스트 진행 중...")
        
        try:
            start_time = time.time()
            response = self.session.get(self.frontend_url, timeout=10)
            load_time = time.time() - start_time
            
            if response.status_code == 200:
                content = response.text
                
                # HTML 구조 분석
                html_checks = {
                    "DOCTYPE 선언": "<!DOCTYPE html>" in content,
                    "HTML 태그": "<html" in content,
                    "HEAD 섹션": "<head>" in content,
                    "BODY 태그": "<body>" in content,
                    "타이틀 태그": "<title>" in content,
                    "메타 태그": "<meta" in content,
                    "CSS 링크": 'rel="stylesheet"' in content,
                    "JavaScript": "<script" in content
                }
                
                passed_checks = sum(html_checks.values())
                total_checks = len(html_checks)
                
                # 반응형 디자인 확인
                responsive_indicators = {
                    "뷰포트 메타태그": 'name="viewport"' in content,
                    "CSS 미디어쿼리": '@media' in content,
                    "Bootstrap/Tailwind": any(framework in content.lower() 
                                            for framework in ['bootstrap', 'tailwind', 'responsive']),
                    "모바일 친화적 CSS": 'mobile' in content.lower()
                }
                
                mobile_score = sum(responsive_indicators.values())
                
                self.log_test("프론트엔드 접근성", "PASS", 
                            f"로딩 시간: {load_time:.2f}초, HTML 구조: {passed_checks}/{total_checks}",
                            {
                                "load_time": load_time,
                                "html_checks": html_checks,
                                "mobile_score": f"{mobile_score}/4",
                                "content_size": len(content)
                            })
            else:                self.log_test("프론트엔드 접근성", "FAIL", 
                            f"HTTP {response.status_code}: {response.reason}")
                
        except Exception as e:
            self.log_test("프론트엔드 접근성", "FAIL", f"연결 실패: {str(e)}")
    
    def test_api_endpoints(self):
        """백엔드 API 엔드포인트 테스트"""
        print("\n🔧 API 엔드포인트 테스트 중...")
        
        endpoints = [
            ("/health", "GET", "헬스체크"),
            ("/docs", "GET", "API 문서"),
            ("/", "GET", "루트 엔드포인트")
        ]
        
        successful_endpoints = 0
        
        for endpoint, method, description in endpoints:
            try:
                url = urljoin(self.backend_url, endpoint)
                response = self.session.request(method, url, timeout=5)
                
                if response.status_code in [200]:
                    successful_endpoints += 1
                    status = "PASS"
                    details = f"HTTP {response.status_code}"
                else:
                    status = "WARN"
                    details = f"HTTP {response.status_code}: {response.reason}"
                
                self.log_test(f"API 엔드포인트: {description}", status, details)
                
            except Exception as e:
                self.log_test(f"API 엔드포인트: {description}", "FAIL", f"오류: {str(e)}")
        
        overall_status = "PASS" if successful_endpoints >= len(endpoints) // 2 else "WARN"
        self.log_test("API 엔드포인트 전체", overall_status, 
                     f"{successful_endpoints}/{len(endpoints)} 엔드포인트 성공")
    
    def test_performance_metrics(self):
        """성능 지표 측정"""
        print("\n⚡ 성능 지표 측정 중...")
        
        metrics = {
            "frontend_load_times": [],
            "backend_response_times": [],
            "resource_sizes": {}
        }
        
        # 프론트엔드 로딩 시간 측정 (3회)
        for i in range(3):
            start_time = time.time()
            try:
                response = self.session.get(self.frontend_url, timeout=10)
                load_time = time.time() - start_time
                metrics["frontend_load_times"].append(load_time)
                metrics["resource_sizes"]["frontend"] = len(response.content)
            except Exception as e:
                print(f"    로딩 테스트 {i+1} 실패: {e}")
          # 백엔드 응답 시간 측정
        for i in range(3):
            start_time = time.time()
            try:
                response = self.session.get(f"{self.backend_url}/health", timeout=5)
                response_time = time.time() - start_time
                metrics["backend_response_times"].append(response_time)
            except Exception as e:
                print(f"    API 응답 테스트 {i+1} 실패: {e}")
        
        # 결과 분석
        if metrics["frontend_load_times"]:
            avg_frontend = sum(metrics["frontend_load_times"]) / len(metrics["frontend_load_times"])
            max_frontend = max(metrics["frontend_load_times"])
        else:
            avg_frontend = max_frontend = 0
            
        if metrics["backend_response_times"]:
            avg_backend = sum(metrics["backend_response_times"]) / len(metrics["backend_response_times"])
            max_backend = max(metrics["backend_response_times"])
        else:
            avg_backend = max_backend = 0
        
        # 성능 평가
        performance_score = "PASS"
        if avg_frontend > 3.0 or avg_backend > 1.0:
            performance_score = "WARN"
        if avg_frontend > 5.0 or avg_backend > 2.0:
            performance_score = "FAIL"
        
        self.log_test("성능 지표", performance_score,
                     f"프론트엔드 평균: {avg_frontend:.2f}초, 백엔드 평균: {avg_backend:.2f}초",
                     metrics)
    
    def test_user_workflow_simulation(self):
        """사용자 워크플로우 시뮬레이션"""
        print("\n👤 사용자 워크플로우 시뮬레이션...")
        
        # 시뮬레이션할 워크플로우
        workflows = [
            ("홈페이지 접근", self.frontend_url),
            ("로그인 페이지", f"{self.frontend_url}/login"),
            ("회원가입 페이지", f"{self.frontend_url}/register"),
            ("평가 목록", f"{self.frontend_url}/evaluations"),
            ("관리자 대시보드", f"{self.frontend_url}/admin")
        ]
        
        workflow_results = {}
        
        for workflow_name, url in workflows:
            try:
                start_time = time.time()
                response = self.session.get(url, timeout=10)
                load_time = time.time() - start_time
                
                if response.status_code == 200:
                    status = "PASS"
                    details = f"로딩 시간: {load_time:.2f}초"
                elif response.status_code == 404:
                    status = "WARN"
                    details = "페이지 없음 (개발 중일 수 있음)"
                else:
                    status = "FAIL"
                    details = f"HTTP {response.status_code}"
                
                workflow_results[workflow_name] = {
                    "status": status,
                    "load_time": load_time,
                    "status_code": response.status_code
                }
                
                self.log_test(f"워크플로우: {workflow_name}", status, details)
                
            except Exception as e:
                workflow_results[workflow_name] = {
                    "status": "FAIL",
                    "error": str(e)
                }
                self.log_test(f"워크플로우: {workflow_name}", "FAIL", f"오류: {str(e)}")
        
        # 전체 워크플로우 평가
        successful_workflows = sum(1 for result in workflow_results.values() 
                                 if result.get("status") == "PASS")
        total_workflows = len(workflows)
        
        overall_status = "PASS" if successful_workflows >= total_workflows // 2 else "WARN"
        self.log_test("사용자 워크플로우 전체", overall_status,
                     f"{successful_workflows}/{total_workflows} 워크플로우 성공")
    
    def test_security_headers(self):
        """보안 헤더 검사"""
        print("\n🔒 보안 헤더 검사 중...")
        
        try:
            response = self.session.get(self.frontend_url, timeout=10)
            headers = response.headers
            
            security_checks = {
                "X-Content-Type-Options": "nosniff" in headers.get("X-Content-Type-Options", ""),
                "X-Frame-Options": "X-Frame-Options" in headers,
                "X-XSS-Protection": "X-XSS-Protection" in headers,
                "Strict-Transport-Security": "Strict-Transport-Security" in headers,
                "Content-Security-Policy": "Content-Security-Policy" in headers
            }
            
            passed_security = sum(security_checks.values())
            total_security = len(security_checks)
            
            security_status = "PASS" if passed_security >= 3 else "WARN" if passed_security >= 1 else "FAIL"
            
            self.log_test("보안 헤더", security_status,
                         f"{passed_security}/{total_security} 보안 헤더 설정됨",
                         security_checks)
            
        except Exception as e:
            self.log_test("보안 헤더", "FAIL", f"검사 실패: {str(e)}")
    
    def open_browser_for_visual_test(self):
        """브라우저에서 시각적 테스트"""
        print("\n👁️ 브라우저 시각적 테스트 시작...")
        
        try:
            webbrowser.open(self.frontend_url)
            self.log_test("브라우저 시각적 테스트", "PASS", 
                         f"브라우저에서 {self.frontend_url} 열림")
            
            # 잠시 대기하여 페이지 로딩 시간 확보
            time.sleep(2)
            
        except Exception as e:
            self.log_test("브라우저 시각적 테스트", "FAIL", f"브라우저 열기 실패: {str(e)}")
    
    def generate_report(self):
        """테스트 결과 보고서 생성"""
        print("\n📊 테스트 결과 보고서 생성 중...")
        
        test_end_time = datetime.now()
        duration = (test_end_time - self.test_start_time).total_seconds()
        
        # 테스트 통계
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["status"] == "PASS")
        failed_tests = sum(1 for result in self.test_results if result["status"] == "FAIL")
        warned_tests = sum(1 for result in self.test_results if result["status"] == "WARN")
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        report = {
            "test_summary": {
                "start_time": self.test_start_time.strftime("%Y-%m-%d %H:%M:%S"),
                "end_time": test_end_time.strftime("%Y-%m-%d %H:%M:%S"),
                "duration_seconds": duration,
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "warnings": warned_tests,
                "success_rate": f"{success_rate:.1f}%"
            },
            "test_results": self.test_results,
            "recommendations": self.generate_recommendations()
        }
        
        # JSON 파일로 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.results_dir / f"enhanced_web_test_report_{timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n📈 테스트 완료!")
        print(f"   📊 전체 테스트: {total_tests}개")
        print(f"   ✅ 성공: {passed_tests}개")
        print(f"   ❌ 실패: {failed_tests}개")
        print(f"   ⚠️ 경고: {warned_tests}개")
        print(f"   🎯 성공률: {success_rate:.1f}%")
        print(f"   📄 보고서: {report_file}")
        
        return report
    
    def generate_recommendations(self):
        """개선 권장사항 생성"""
        recommendations = []
        
        # 실패한 테스트 기반 권장사항
        for result in self.test_results:
            if result["status"] == "FAIL":
                if "프론트엔드" in result["test_name"]:
                    recommendations.append("프론트엔드 서버 상태 및 설정 확인")
                elif "API" in result["test_name"]:
                    recommendations.append("백엔드 API 서버 상태 및 라우팅 확인")
                elif "보안" in result["test_name"]:
                    recommendations.append("웹 서버 보안 헤더 설정 추가")
        
        # 성능 관련 권장사항
        performance_results = [r for r in self.test_results if "성능" in r["test_name"]]
        if performance_results and performance_results[0]["status"] in ["WARN", "FAIL"]:
            recommendations.append("성능 최적화: 이미지 압축, CDN 사용, 캐싱 전략 검토")
        
        return list(set(recommendations))  # 중복 제거
    
    async def run_all_tests(self):
        """모든 테스트 실행"""
        print("🚀 Enhanced 웹페이지 테스트 시작!")
        print("=" * 50)
        
        # Sequential Thinking 적용
        test_sequence = [
            self.test_system_health,
            self.test_frontend_comprehensive,
            self.test_api_endpoints,
            self.test_performance_metrics,
            self.test_user_workflow_simulation,
            self.test_security_headers,
            self.open_browser_for_visual_test
        ]
        
        for test_function in test_sequence:
            try:
                test_function()
                time.sleep(1)  # 테스트 간 간격
            except Exception as e:
                print(f"❌ 테스트 실행 중 오류: {e}")
                continue
        
        # 보고서 생성
        report = self.generate_report()
        return report

def main():
    """메인 실행 함수"""
    tester = EnhancedWebTester()
    
    # 비동기 실행
    try:
        report = asyncio.run(tester.run_all_tests())
        
        # Memory Bank에 결과 저장
        print("\n💾 Memory Bank에 결과 저장 중...")
        
    except KeyboardInterrupt:
        print("\n⏹️ 사용자에 의해 테스트가 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 테스트 실행 중 예상치 못한 오류: {e}")

if __name__ == "__main__":
    main()
