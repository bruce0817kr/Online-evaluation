#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Playwright 웹페이지 테스트 스크립트
Online Evaluation System 로그인 기능 테스트

환경변수 수정 후 로그인 안정성 검증
"""

import asyncio
import time
import os
import json
from datetime import datetime
from playwright.async_api import async_playwright

class LoginTester:
    def __init__(self):
        self.base_url = "http://localhost:3000"
        self.backend_url = "http://localhost:8000"
        self.test_results = []
        self.screenshots_dir = "screenshots"
        self.create_screenshots_dir()
    
    def create_screenshots_dir(self):
        """스크린샷 저장 디렉토리 생성"""
        if not os.path.exists(self.screenshots_dir):
            os.makedirs(self.screenshots_dir)
    
    def log_test(self, test_name, status, details="", screenshot_path=""):
        """테스트 결과 로깅"""
        result = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "test_name": test_name,
            "status": status,
            "details": details,
            "screenshot": screenshot_path
        }
        self.test_results.append(result)
        
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"[{status_icon}] {test_name}: {status}")
        if details:
            print(f"    {details}")
        if screenshot_path:
            print(f"    📸 Screenshot: {screenshot_path}")

    async def test_login_functionality(self, page):
        """로그인 기능 테스트"""
        try:
            # 로그인 페이지로 이동
            await page.goto(self.base_url)
            await page.wait_for_load_state('networkidle')
            
            # 로그인 탭 클릭
            await page.click('text=로그인')
            await page.wait_for_timeout(1000)
            
            # 스크린샷 촬영
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            login_page_screenshot = f"{self.screenshots_dir}/login_page_{timestamp}.png"
            await page.screenshot(path=login_page_screenshot)
            
            # 로그인 폼 입력
            await page.fill('input[name="user_id"]', 'test_user')
            await page.fill('input[name="password"]', 'test_password')
            
            # 로그인 버튼 클릭 전 네트워크 로그 시작
            responses = []
            
            def handle_response(response):
                if '/api/login' in response.url:
                    responses.append({
                        'url': response.url,
                        'status': response.status,
                        'headers': dict(response.headers)
                    })
            
            page.on('response', handle_response)
            
            # 로그인 시도
            await page.click('button[type="submit"]')
            
            # 응답 대기
            await page.wait_for_timeout(3000)
            
            # 결과 스크린샷
            result_screenshot = f"{self.screenshots_dir}/login_result_{timestamp}.png"
            await page.screenshot(path=result_screenshot)
            
            # 콘솔 로그 확인
            console_logs = []
            page.on('console', lambda msg: console_logs.append(f"{msg.type}: {msg.text}"))
            
            # 결과 분석
            current_url = page.url
            if '/dashboard' in current_url or '로그인 성공' in await page.content():
                self.log_test("로그인 성공 테스트", "PASS", 
                            f"URL: {current_url}", result_screenshot)
            else:
                # 에러 메시지 확인
                error_element = await page.query_selector('.error-message, .alert-danger')
                error_text = await error_element.inner_text() if error_element else "알 수 없는 오류"
                
                self.log_test("로그인 실패 분석", "WARN", 
                            f"Error: {error_text}, Responses: {responses}", result_screenshot)
            
            return responses, console_logs
            
        except Exception as e:
            error_screenshot = f"{self.screenshots_dir}/login_error_{timestamp}.png"
            await page.screenshot(path=error_screenshot)
            self.log_test("로그인 테스트 오류", "FAIL", str(e), error_screenshot)
            return [], []

    async def test_secretary_signup(self, page):
        """간사 회원가입 테스트"""
        try:
            # 간사 회원가입 페이지로 이동
            await page.goto(f"{self.base_url}/secretary-signup")
            await page.wait_for_load_state('networkidle')
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            signup_page_screenshot = f"{self.screenshots_dir}/secretary_signup_{timestamp}.png"
            await page.screenshot(path=signup_page_screenshot)
            
            # 폼 입력
            test_data = {
                'name': '테스트간사',
                'user_id': f'test_secretary_{timestamp}',
                'password': 'test123!',
                'phone': '010-1234-5678',
                'institution': '테스트기관',
                'department': '테스트부서',
                'position': '간사'
            }
            
            for field, value in test_data.items():
                await page.fill(f'input[name="{field}"]', value)
            
            # 네트워크 응답 모니터링
            responses = []
            page.on('response', lambda response: 
                    responses.append({
                        'url': response.url,
                        'status': response.status
                    }) if '/api/secretary-signup' in response.url else None)
            
            # 신청서 제출
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(3000)
            
            # 결과 스크린샷
            result_screenshot = f"{self.screenshots_dir}/signup_result_{timestamp}.png"
            await page.screenshot(path=result_screenshot)
            
            # 결과 분석
            page_content = await page.content()
            if '신청이 완료' in page_content or '성공' in page_content:
                self.log_test("간사 회원가입 테스트", "PASS", 
                            f"Data: {test_data}", result_screenshot)
            else:
                self.log_test("간사 회원가입 실패", "WARN", 
                            f"Responses: {responses}", result_screenshot)
            
            return responses
            
        except Exception as e:
            error_screenshot = f"{self.screenshots_dir}/signup_error_{timestamp}.png"
            await page.screenshot(path=error_screenshot)
            self.log_test("간사 회원가입 오류", "FAIL", str(e), error_screenshot)
            return []

    async def test_environment_variables(self, page):
        """환경변수 확인 테스트"""
        try:
            await page.goto(self.base_url)
            
            # 개발자 도구에서 환경변수 확인
            backend_url = await page.evaluate('''
                () => {
                    return window.location.origin.includes('3000') ? 
                           (process?.env?.REACT_APP_BACKEND_URL || 'not found') : 'not applicable';
                }
            ''')
            
            self.log_test("환경변수 확인", "INFO", f"Backend URL: {backend_url}")
            
            # 실제 API 호출 URL 확인을 위해 네트워크 요청 모니터링
            api_calls = []
            page.on('request', lambda request: 
                   api_calls.append(request.url) if 'localhost:' in request.url else None)
            
            # 로그인 시도하여 실제 API 호출 확인
            await page.click('text=로그인')
            await page.fill('input[name="user_id"]', 'test')
            await page.fill('input[name="password"]', 'test')
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(2000)
            
            backend_calls = [url for url in api_calls if ':8000' in url]
            wrong_calls = [url for url in api_calls if ':8080' in url]
            
            if backend_calls:
                self.log_test("API 호출 확인", "PASS", f"올바른 포트(8000) 사용: {len(backend_calls)}개")
            if wrong_calls:
                self.log_test("잘못된 API 호출", "FAIL", f"잘못된 포트(8080) 사용: {wrong_calls}")
            
            return api_calls
            
        except Exception as e:
            self.log_test("환경변수 테스트 오류", "FAIL", str(e))
            return []

    async def run_all_tests(self):
        """모든 테스트 실행"""
        print("🚀 로그인 기능 안정성 테스트 시작")
        print(f"📍 프론트엔드: {self.base_url}")
        print(f"📍 백엔드: {self.backend_url}")
        print("-" * 60)
        
        async with async_playwright() as p:
            # 브라우저 시작 (헤드리스 모드 끄기 - 디버깅용)
            browser = await p.chromium.launch(headless=False, slow_mo=1000)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                # 1. 환경변수 확인
                await self.test_environment_variables(page)
                
                # 2. 로그인 기능 테스트
                login_responses, console_logs = await self.test_login_functionality(page)
                
                # 3. 간사 회원가입 테스트
                signup_responses = await self.test_secretary_signup(page)
                
                # 브라우저 열어둔 채로 5초 대기 (수동 확인용)
                print("\n⏱️  브라우저를 5초간 열어둡니다. 수동으로 확인해보세요...")
                await asyncio.sleep(5)
                
            finally:
                await browser.close()
        
        # 결과 리포트 생성
        self.generate_report()

    def generate_report(self):
        """테스트 결과 리포트 생성"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"login_test_report_{timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        
        # 콘솔 요약
        total_tests = len(self.test_results)
        passed = len([t for t in self.test_results if t['status'] == 'PASS'])
        failed = len([t for t in self.test_results if t['status'] == 'FAIL'])
        warnings = len([t for t in self.test_results if t['status'] == 'WARN'])
        
        print("\n" + "=" * 60)
        print("📊 테스트 결과 요약")
        print("=" * 60)
        print(f"전체 테스트: {total_tests}")
        print(f"✅ 성공: {passed}")
        print(f"❌ 실패: {failed}")
        print(f"⚠️  경고: {warnings}")
        print(f"📄 상세 리포트: {report_file}")
        print("=" * 60)

async def main():
    """메인 실행 함수"""
    tester = LoginTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  테스트가 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 테스트 실행 중 오류: {e}")
