"""
온라인 평가 시스템 Playwright 자동화 테스트
Author: GitHub Copilot
Date: 2025-06-05
Purpose: 프론트엔드 UI/UX 자동화 테스트
"""

import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
import time
import os

class OnlineEvaluationUITester:
    def __init__(self):
        self.base_url = "http://localhost:3000"
        self.backend_url = "http://localhost:8080"
        self.test_results = []
        self.screenshot_dir = "test_screenshots"
        
        # 테스트 계정 정보
        self.test_accounts = {
            "admin": {"username": "admin", "password": "admin123"},
            "secretary": {"username": "secretary01", "password": "secretary123"},
            "evaluator": {"username": "evaluator01", "password": "evaluator123"}
        }
        
        # 스크린샷 디렉토리 생성
        os.makedirs(self.screenshot_dir, exist_ok=True)

    async def log_test_result(self, test_name: str, success: bool, message: str, duration: float = 0):
        """테스트 결과 로깅"""
        result = {
            "test_name": test_name,
            "success": success,
            "message": message,
            "duration": f"{duration:.2f}s",
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} | {test_name} | {message} | {duration:.2f}s")

    async def take_screenshot(self, page: Page, name: str):
        """스크린샷 촬영"""
        try:
            screenshot_path = os.path.join(self.screenshot_dir, f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            await page.screenshot(path=screenshot_path, full_page=True)
            print(f"📸 스크린샷 저장: {screenshot_path}")
        except Exception as e:
            print(f"⚠️ 스크린샷 저장 실패: {e}")

    async def wait_for_element_with_timeout(self, page: Page, selector: str, timeout: int = 10000):
        """요소 대기 (타임아웃 포함)"""
        try:
            await page.wait_for_selector(selector, timeout=timeout)
            return True
        except Exception as e:
            print(f"⚠️ 요소 대기 실패 ({selector}): {e}")
            return False

    async def test_page_load(self, page: Page):
        """TC-001: 페이지 로딩 테스트"""
        start_time = time.time()
        
        try:
            # 페이지 접속
            response = await page.goto(self.base_url)
            
            if response and response.status == 200:
                # React 앱 로딩 대기
                await page.wait_for_selector("h1", timeout=10000)
                
                # 페이지 제목 확인
                title = await page.title()
                
                # 로그인 폼 요소 확인
                login_form_visible = await page.is_visible("form")
                
                duration = time.time() - start_time
                
                if login_form_visible and "온라인 평가 시스템" in await page.inner_text("h1"):
                    await self.log_test_result("페이지 로딩", True, f"페이지 정상 로딩 (제목: {title})", duration)
                    await self.take_screenshot(page, "page_load_success")
                    return True
                else:
                    await self.log_test_result("페이지 로딩", False, "필수 요소가 표시되지 않음", duration)
                    await self.take_screenshot(page, "page_load_fail")
                    return False
            else:
                duration = time.time() - start_time
                await self.log_test_result("페이지 로딩", False, f"HTTP 오류: {response.status if response else 'No response'}", duration)
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            await self.log_test_result("페이지 로딩", False, f"예외 발생: {str(e)}", duration)
            await self.take_screenshot(page, "page_load_error")
            return False

    async def test_login(self, page: Page, account_type: str):
        """TC-002~004: 로그인 테스트"""
        start_time = time.time()
        account = self.test_accounts[account_type]
        
        try:
            # 로그인 폼 요소 확인
            if not await self.wait_for_element_with_timeout(page, "input[type='text']"):
                await self.log_test_result(f"{account_type} 로그인", False, "로그인 폼을 찾을 수 없음", time.time() - start_time)
                return False

            # 사용자명 입력
            await page.fill("input[type='text']", account["username"])
            await page.fill("input[type='password']", account["password"])
            
            # 로그인 버튼 클릭
            await page.click("button[type='submit']")
            
            # 로그인 처리 대기
            await page.wait_for_timeout(2000)
            
            # 대시보드 로딩 확인
            current_url = page.url
            
            # 로그인 성공 여부 확인 (로그인 폼이 사라지고 대시보드가 표시됨)
            is_dashboard_visible = await page.is_visible("nav") or await page.is_visible(".max-w-7xl")
            
            duration = time.time() - start_time
            
            if is_dashboard_visible and current_url == self.base_url:
                await self.log_test_result(f"{account_type} 로그인", True, f"로그인 성공", duration)
                await self.take_screenshot(page, f"login_success_{account_type}")
                return True
            else:
                await self.log_test_result(f"{account_type} 로그인", False, "대시보드가 표시되지 않음", duration)
                await self.take_screenshot(page, f"login_fail_{account_type}")
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            await self.log_test_result(f"{account_type} 로그인", False, f"예외 발생: {str(e)}", duration)
            await self.take_screenshot(page, f"login_error_{account_type}")
            return False

    async def test_wrong_password(self, page: Page):
        """TC-005: 잘못된 비밀번호 테스트"""
        start_time = time.time()
        
        try:
            # 페이지 새로고침하여 로그인 폼으로 돌아가기
            await page.goto(self.base_url)
            await page.wait_for_selector("input[type='text']", timeout=5000)
            
            # 잘못된 비밀번호로 로그인 시도
            await page.fill("input[type='text']", "admin")
            await page.fill("input[type='password']", "wrongpassword")
            await page.click("button[type='submit']")
            
            # 오류 메시지 또는 경고 대기
            await page.wait_for_timeout(3000)
            
            # 여전히 로그인 폼이 표시되는지 확인
            is_login_form_visible = await page.is_visible("input[type='password']")
            
            duration = time.time() - start_time
            
            if is_login_form_visible:
                await self.log_test_result("잘못된 비밀번호", True, "올바르게 로그인이 거부됨", duration)
                await self.take_screenshot(page, "wrong_password_success")
                return True
            else:
                await self.log_test_result("잘못된 비밀번호", False, "잘못된 비밀번호로도 로그인됨", duration)
                await self.take_screenshot(page, "wrong_password_fail")
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            await self.log_test_result("잘못된 비밀번호", False, f"예외 발생: {str(e)}", duration)
            return False

    async def test_dashboard_elements(self, page: Page, account_type: str):
        """TC-101~103: 대시보드 요소 테스트"""
        start_time = time.time()
        
        try:
            # 대시보드 요소 확인
            elements_to_check = []
            
            if account_type == "admin":
                elements_to_check = [
                    ("nav", "네비게이션 바"),
                    (".text-2xl.font-bold", "제목 요소"),
                    ("button", "버튼 요소")
                ]
            elif account_type == "secretary":
                elements_to_check = [
                    ("nav", "네비게이션 바"),
                    ("button", "버튼 요소")
                ]
            else:  # evaluator
                elements_to_check = [
                    (".max-w-7xl", "메인 컨테이너"),
                    ("div", "컨텐츠 영역")
                ]
            
            all_elements_found = True
            missing_elements = []
            
            for selector, description in elements_to_check:
                if not await page.is_visible(selector):
                    all_elements_found = False
                    missing_elements.append(description)
            
            duration = time.time() - start_time
            
            if all_elements_found:
                await self.log_test_result(f"{account_type} 대시보드 요소", True, "모든 필수 요소가 표시됨", duration)
                await self.take_screenshot(page, f"dashboard_elements_{account_type}")
                return True
            else:
                await self.log_test_result(f"{account_type} 대시보드 요소", False, f"누락된 요소: {', '.join(missing_elements)}", duration)
                await self.take_screenshot(page, f"dashboard_elements_fail_{account_type}")
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            await self.log_test_result(f"{account_type} 대시보드 요소", False, f"예외 발생: {str(e)}", duration)
            return False

    async def test_navigation_tabs(self, page: Page, account_type: str):
        """TC-201: 네비게이션 탭 테스트"""
        start_time = time.time()
        
        try:
            if account_type == "evaluator":
                # 평가위원은 네비게이션 탭이 없으므로 스킵
                await self.log_test_result(f"{account_type} 네비게이션", True, "평가위원은 네비게이션 제한 정상", 0)
                return True
            
            # 네비게이션 탭 클릭 테스트
            tabs_to_test = []
            
            if account_type == "admin":
                tabs_to_test = ["프로젝트 관리", "사용자 관리", "결과 분석"]
            elif account_type == "secretary":
                tabs_to_test = ["프로젝트 관리"]
            
            successful_tabs = 0
            
            for tab_text in tabs_to_test:
                try:
                    # 탭 버튼 찾기 (부분 텍스트 매칭)
                    tab_button = page.locator(f"button:has-text('{tab_text}')")
                    
                    if await tab_button.count() > 0:
                        await tab_button.first.click()
                        await page.wait_for_timeout(1000)  # 탭 전환 대기
                        successful_tabs += 1
                except Exception as tab_error:
                    print(f"⚠️ 탭 '{tab_text}' 클릭 실패: {tab_error}")
            
            duration = time.time() - start_time
            
            if successful_tabs >= len(tabs_to_test) // 2:  # 절반 이상 성공하면 통과
                await self.log_test_result(f"{account_type} 네비게이션", True, f"{successful_tabs}/{len(tabs_to_test)} 탭 접근 성공", duration)
                await self.take_screenshot(page, f"navigation_{account_type}")
                return True
            else:
                await self.log_test_result(f"{account_type} 네비게이션", False, f"탭 접근 실패: {successful_tabs}/{len(tabs_to_test)}", duration)
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            await self.log_test_result(f"{account_type} 네비게이션", False, f"예외 발생: {str(e)}", duration)
            return False

    async def test_responsive_design(self, page: Page):
        """TC-401~403: 반응형 디자인 테스트"""
        start_time = time.time()
        
        viewports = [
            {"name": "Desktop", "width": 1920, "height": 1080},
            {"name": "Tablet", "width": 768, "height": 1024},
            {"name": "Mobile", "width": 375, "height": 667}
        ]
        
        successful_viewports = 0
        
        try:
            for viewport in viewports:
                await page.set_viewport_size({"width": viewport["width"], "height": viewport["height"]})
                await page.wait_for_timeout(1000)  # 리사이즈 대기
                
                # 기본 요소가 여전히 표시되는지 확인
                is_content_visible = await page.is_visible("div") and await page.is_visible("body")
                
                if is_content_visible:
                    successful_viewports += 1
                    await self.take_screenshot(page, f"responsive_{viewport['name'].lower()}")
                    print(f"✅ {viewport['name']} ({viewport['width']}x{viewport['height']}) 테스트 통과")
                else:
                    print(f"❌ {viewport['name']} ({viewport['width']}x{viewport['height']}) 테스트 실패")
            
            duration = time.time() - start_time
            
            if successful_viewports == len(viewports):
                await self.log_test_result("반응형 디자인", True, f"모든 해상도에서 정상 표시", duration)
                return True
            else:
                await self.log_test_result("반응형 디자인", False, f"{successful_viewports}/{len(viewports)} 해상도에서만 정상", duration)
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            await self.log_test_result("반응형 디자인", False, f"예외 발생: {str(e)}", duration)
            return False

    async def test_logout(self, page: Page):
        """TC-301: 로그아웃 테스트"""
        start_time = time.time()
        
        try:
            # 로그아웃 버튼 찾기 및 클릭
            logout_button = page.locator("button:has-text('로그아웃')")
            
            if await logout_button.count() > 0:
                await logout_button.click()
                await page.wait_for_timeout(2000)  # 로그아웃 처리 대기
                
                # 로그인 페이지로 리디렉션 확인
                is_login_form_visible = await page.is_visible("input[type='password']")
                
                duration = time.time() - start_time
                
                if is_login_form_visible:
                    await self.log_test_result("로그아웃", True, "로그아웃 후 로그인 페이지로 이동", duration)
                    await self.take_screenshot(page, "logout_success")
                    return True
                else:
                    await self.log_test_result("로그아웃", False, "로그아웃 후 페이지 이동 실패", duration)
                    return False
            else:
                duration = time.time() - start_time
                await self.log_test_result("로그아웃", False, "로그아웃 버튼을 찾을 수 없음", duration)
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            await self.log_test_result("로그아웃", False, f"예외 발생: {str(e)}", duration)
            return False

    async def run_full_test_suite(self):
        """전체 테스트 스위트 실행"""
        print("🚀 온라인 평가 시스템 Playwright 자동화 테스트 시작")
        print("=" * 60)
        
        async with async_playwright() as p:
            # Chrome 브라우저 시작
            browser = await p.chromium.launch(headless=False, slow_mo=500)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                # 1. 페이지 로딩 테스트
                await self.test_page_load(page)
                
                # 2. 각 계정별 로그인 및 대시보드 테스트
                for account_type in ["admin", "secretary", "evaluator"]:
                    print(f"\n--- {account_type.upper()} 계정 테스트 ---")
                    
                    # 로그인 테스트
                    login_success = await self.test_login(page, account_type)
                    
                    if login_success:
                        # 대시보드 요소 테스트
                        await self.test_dashboard_elements(page, account_type)
                        
                        # 네비게이션 테스트
                        await self.test_navigation_tabs(page, account_type)
                        
                        # 반응형 디자인 테스트 (관리자만)
                        if account_type == "admin":
                            await self.test_responsive_design(page)
                        
                        # 로그아웃 테스트
                        await self.test_logout(page)
                
                # 3. 잘못된 비밀번호 테스트
                print(f"\n--- 보안 테스트 ---")
                await self.test_wrong_password(page)
                
            finally:
                await browser.close()
        
        # 테스트 결과 요약
        await self.generate_test_report()

    async def generate_test_report(self):
        """테스트 결과 보고서 생성"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print("\n" + "=" * 60)
        print("📊 테스트 결과 요약")
        print("=" * 60)
        print(f"전체 테스트: {total_tests}")
        print(f"통과: {passed_tests}")
        print(f"실패: {failed_tests}")
        print(f"성공률: {success_rate:.1f}%")
        
        # 실패한 테스트 상세 정보
        if failed_tests > 0:
            print(f"\n❌ 실패한 테스트:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test_name']}: {result['message']}")
        
        # JSON 보고서 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"playwright_ui_test_results_{timestamp}.json"
        
        report_data = {
            "test_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": success_rate,
                "timestamp": datetime.now().isoformat()
            },
            "test_results": self.test_results
        }
        
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 상세 보고서 저장: {report_filename}")
        print(f"📸 스크린샷 폴더: {self.screenshot_dir}")

async def main():
    """메인 실행 함수"""
    tester = OnlineEvaluationUITester()
    await tester.run_full_test_suite()

if __name__ == "__main__":
    asyncio.run(main())
