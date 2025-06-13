#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
브라우저 콘솔 오류 및 네트워크 404 오류 감지 테스트
MCP Sequential Thinking 및 Graph Memory 적용
"""

import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright
from pathlib import Path

class ConsoleErrorDetector:
    def __init__(self):
        self.frontend_url = "http://localhost:3000"
        self.backend_url = "http://localhost:8080"
        self.console_errors = []
        self.network_errors = []
        self.test_results = []
        
        # 결과 저장 디렉토리
        self.results_dir = Path("test_results")
        self.results_dir.mkdir(exist_ok=True)
    
    async def capture_console_logs(self, page):
        """콘솔 로그 캡처"""
        def handle_console(msg):
            if msg.type in ['error', 'warning']:
                error_info = {
                    "timestamp": datetime.now().isoformat(),
                    "type": msg.type,
                    "text": msg.text,
                    "url": page.url,
                    "location": msg.location
                }
                self.console_errors.append(error_info)
                print(f"🚨 Console {msg.type.upper()}: {msg.text}")
        
        page.on("console", handle_console)
    
    async def capture_network_errors(self, page):
        """네트워크 오류 캡처"""
        def handle_response(response):
            if response.status >= 400:
                error_info = {
                    "timestamp": datetime.now().isoformat(),
                    "status": response.status,
                    "url": response.url,
                    "method": response.request.method,
                    "status_text": response.status_text
                }
                self.network_errors.append(error_info)
                print(f"🌐 Network Error: {response.status} {response.url}")
        
        def handle_request_failed(request):
            error_info = {
                "timestamp": datetime.now().isoformat(),
                "status": "FAILED",
                "url": request.url,
                "method": request.method,
                "failure": request.failure
            }
            self.network_errors.append(error_info)
            print(f"🔴 Request Failed: {request.url} - {request.failure}")
        
        page.on("response", handle_response)
        page.on("requestfailed", handle_request_failed)
    
    async def test_homepage_errors(self, page):
        """홈페이지 오류 테스트"""
        print("\n🏠 홈페이지 오류 감지 테스트...")
        
        try:
            # 페이지 로드
            await page.goto(self.frontend_url, wait_until="networkidle")
            await page.wait_for_timeout(2000)  # 2초 대기하여 모든 요청 완료
            
            # 페이지 제목 확인
            title = await page.title()
            print(f"   페이지 제목: {title}")
            
            # 스크린샷 저장
            screenshot_path = self.results_dir / f"homepage_errors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            await page.screenshot(path=str(screenshot_path))
            print(f"   📸 스크린샷 저장: {screenshot_path}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ 홈페이지 로드 실패: {str(e)}")
            return False
    
    async def test_navigation_errors(self, page):
        """네비게이션 오류 테스트"""
        print("\n🧭 네비게이션 오류 감지 테스트...")
        
        navigation_tests = [
            ("로그인 페이지", "#/login"),
            ("회원가입 페이지", "#/signup"),
            ("평가 목록", "#/evaluations"),
            ("관리자 대시보드", "#/admin")
        ]
        
        for test_name, path in navigation_tests:
            try:
                print(f"   🔍 테스트 중: {test_name}")
                
                # 네비게이션
                await page.goto(f"{self.frontend_url}/{path}", wait_until="networkidle")
                await page.wait_for_timeout(1000)
                
                # 현재 URL 확인
                current_url = page.url
                print(f"      현재 URL: {current_url}")
                
            except Exception as e:
                print(f"      ❌ {test_name} 네비게이션 실패: {str(e)}")
    
    async def test_api_calls_from_frontend(self, page):
        """프론트엔드에서 발생하는 API 호출 오류 테스트"""
        print("\n🔗 프론트엔드 API 호출 오류 감지...")
        
        try:
            # 홈페이지로 이동
            await page.goto(self.frontend_url, wait_until="networkidle")            # JavaScript를 통해 API 호출 시뮬레이션
            api_tests = [
                ("헬스체크", "fetch('http://localhost:8080/health')"),
                ("API 상태", "fetch('http://localhost:8080/api/status')")
            ]
            
            for test_name, js_code in api_tests:
                try:
                    print(f"   🧪 {test_name} API 호출 테스트...")
                    result = await page.evaluate(f"""
                        {js_code}
                        .then(r => ({{status: r.status, ok: r.ok, url: r.url}}))
                        .catch(e => ({{error: e.message}}))
                    """)
                    print(f"      결과: {result}")
                    
                except Exception as e:
                    print(f"      ❌ {test_name} API 테스트 실패: {str(e)}")
            
        except Exception as e:
            print(f"   ❌ API 호출 테스트 실패: {str(e)}")
    
    async def generate_report(self):
        """테스트 결과 보고서 생성"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_console_errors": len(self.console_errors),
                "total_network_errors": len(self.network_errors),
                "console_error_types": {},
                "network_error_codes": {}
            },
            "console_errors": self.console_errors,
            "network_errors": self.network_errors
        }
        
        # 콘솔 오류 유형별 통계
        for error in self.console_errors:
            error_type = error["type"]
            report["summary"]["console_error_types"][error_type] = \
                report["summary"]["console_error_types"].get(error_type, 0) + 1
        
        # 네트워크 오류 코드별 통계
        for error in self.network_errors:
            status = str(error["status"])
            report["summary"]["network_error_codes"][status] = \
                report["summary"]["network_error_codes"].get(status, 0) + 1
        
        # 보고서 저장
        report_path = self.results_dir / f"console_error_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return report, report_path
    
    async def run_all_tests(self):
        """모든 테스트 실행"""
        print("🔍 브라우저 콘솔 및 네트워크 오류 감지 테스트 시작")
        print("=" * 60)
        
        async with async_playwright() as p:
            # 브라우저 시작 (Chrome 사용)
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            
            # 오류 캡처 설정
            await self.capture_console_logs(page)
            await self.capture_network_errors(page)
            
            try:
                # 테스트 실행
                await self.test_homepage_errors(page)
                await self.test_navigation_errors(page)
                await self.test_api_calls_from_frontend(page)
                
                # 최종 대기 (모든 비동기 요청 완료 대기)
                await page.wait_for_timeout(3000)
                
            finally:
                await browser.close()
        
        # 결과 분석 및 보고서 생성
        report, report_path = await self.generate_report()
        
        print("\n" + "=" * 60)
        print("📊 테스트 결과 요약")
        print("=" * 60)
        print(f"콘솔 오류: {report['summary']['total_console_errors']}개")
        print(f"네트워크 오류: {report['summary']['total_network_errors']}개")
        
        if report['summary']['console_error_types']:
            print("\n🚨 콘솔 오류 유형:")
            for error_type, count in report['summary']['console_error_types'].items():
                print(f"   {error_type}: {count}개")
        
        if report['summary']['network_error_codes']:
            print("\n🌐 네트워크 오류 코드:")
            for status_code, count in report['summary']['network_error_codes'].items():
                print(f"   HTTP {status_code}: {count}개")
        
        if self.network_errors:
            print("\n🔍 네트워크 오류 상세:")
            for error in self.network_errors:
                print(f"   {error['status']} - {error['url']}")
        
        print(f"\n📄 상세 보고서: {report_path}")
        
        return report

async def main():
    detector = ConsoleErrorDetector()
    await detector.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
