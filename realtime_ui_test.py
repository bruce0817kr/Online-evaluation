"""
온라인 평가 시스템 실시간 UI 자동화 테스트
Author: GitHub Copilot  
Date: 2025-06-05
Purpose: Docker 환경에서 실행 중인 시스템의 실시간 UI 테스트
"""

import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
import time
import os
import sys

class RealTimeUITester:
    def __init__(self):
        self.base_url = "http://localhost:3000"
        self.backend_url = "http://localhost:8080"
        self.test_results = []
        self.screenshot_dir = "realtime_test_screenshots"
        
        # 테스트 계정 정보
        self.test_accounts = {
            "admin": {"username": "admin", "password": "admin123"},
            "secretary": {"username": "secretary01", "password": "secretary123"},
            "evaluator": {"username": "evaluator01", "password": "evaluator123"}
        }
        
        # 스크린샷 디렉토리 생성
        os.makedirs(self.screenshot_dir, exist_ok=True)
        
        # 테스트 통계
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0

    async def log_test_result(self, test_name: str, success: bool, message: str, duration: float = 0):
        """테스트 결과 로깅"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
        else:
            self.failed_tests += 1
            
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
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot_path = os.path.join(self.screenshot_dir, f"{name}_{timestamp}.png")
            await page.screenshot(path=screenshot_path, full_page=True)
            print(f"📸 스크린샷 저장: {screenshot_path}")
        except Exception as e:
            print(f"⚠️ 스크린샷 저장 실패: {e}")

    async def wait_for_element_safe(self, page: Page, selector: str, timeout: int = 10000):
        """안전한 요소 대기"""
        try:
            await page.wait_for_selector(selector, timeout=timeout)
            return True
        except Exception as e:
            print(f"⚠️ 요소 대기 실패 ({selector}): {e}")
            return False

    async def test_initial_page_load(self, page: Page):
        """시나리오 1: 초기 페이지 로딩 및 시스템 상태 확인"""
        start_time = time.time()
        
        try:
            print("\n🔍 시나리오 1: 초기 페이지 로딩 테스트")
            
            # 페이지 접속
            await page.goto(self.base_url, wait_until="networkidle")
            
            # 페이지 제목 확인
            title = await page.title()
            
            # 로딩 상태 확인 (로딩 스피너가 사라질 때까지 대기)
            try:
                await page.wait_for_selector(".animate-spin", state="detached", timeout=15000)
            except:
                print("⚠️ 로딩 스피너를 찾을 수 없거나 이미 사라짐")
            
            # 주요 UI 요소 확인
            main_title = await page.is_visible("h1")
            login_form = await page.is_visible("form")
            
            duration = time.time() - start_time
            
            if main_title and login_form:
                await self.log_test_result("초기 페이지 로딩", True, f"모든 요소 정상 로딩 (제목: {title})", duration)
                await self.take_screenshot(page, "initial_load_success")
                return True
            else:
                await self.log_test_result("초기 페이지 로딩", False, "필수 UI 요소 누락", duration)
                await self.take_screenshot(page, "initial_load_fail")
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            await self.log_test_result("초기 페이지 로딩", False, f"예외 발생: {str(e)}", duration)
            await self.take_screenshot(page, "initial_load_error")
            return False

    async def test_admin_login_workflow(self, page: Page):
        """시나리오 2: 관리자 로그인 및 대시보드 접근"""
        start_time = time.time()
        
        try:
            print("\n👨‍💼 시나리오 2: 관리자 로그인 워크플로우")
            
            # 로그인 폼 대기
            if not await self.wait_for_element_safe(page, "input[name='login_id'], input[type='text']"):
                await self.log_test_result("관리자 로그인", False, "로그인 폼을 찾을 수 없음", time.time() - start_time)
                return False

            # 사용자명/비밀번호 입력
            username_input = await page.query_selector("input[name='login_id']") or await page.query_selector("input[type='text']")
            password_input = await page.query_selector("input[name='password']") or await page.query_selector("input[type='password']")
            
            if username_input and password_input:
                await username_input.fill("admin")
                await password_input.fill("admin123")
                
                # 로그인 버튼 클릭
                await page.click("button[type='submit']")
                
                # 로그인 처리 대기 (네트워크 요청 완료까지)
                await page.wait_for_timeout(3000)
                
                # 성공 여부 확인: 로그인 폼이 사라지고 네비게이션이 나타남
                is_nav_visible = await page.is_visible("nav")
                is_logout_button_visible = await page.is_visible("button:has-text('로그아웃')")
                current_url = page.url
                
                duration = time.time() - start_time
                
                if is_nav_visible or is_logout_button_visible:
                    await self.log_test_result("관리자 로그인", True, "로그인 성공, 대시보드 접근됨", duration)
                    await self.take_screenshot(page, "admin_login_success")
                    return True
                else:
                    # 오류 메시지 확인
                    error_element = await page.query_selector(".text-red-700, .bg-red-50")
                    error_text = await error_element.inner_text() if error_element else "알 수 없는 오류"
                    
                    await self.log_test_result("관리자 로그인", False, f"로그인 실패: {error_text}", duration)
                    await self.take_screenshot(page, "admin_login_fail")
                    return False
            else:
                await self.log_test_result("관리자 로그인", False, "입력 필드를 찾을 수 없음", time.time() - start_time)
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            await self.log_test_result("관리자 로그인", False, f"예외 발생: {str(e)}", duration)
            await self.take_screenshot(page, "admin_login_error")
            return False

    async def test_navigation_tabs(self, page: Page):
        """시나리오 3: 대시보드 탭 네비게이션 테스트"""
        start_time = time.time()
        
        try:
            print("\n🧭 시나리오 3: 대시보드 네비게이션 테스트")
            
            # 네비게이션 탭들 확인
            tabs_to_test = [
                ("프로젝트 관리", "projects"),
                ("사용자 관리", "users"), 
                ("평가 관리", "evaluations"),
                ("템플릿 관리", "templates"),
                ("분석", "analytics")
            ]
            
            successful_tabs = 0
            
            for tab_name, tab_id in tabs_to_test:
                try:
                    # 탭 클릭
                    tab_selector = f"button:has-text('{tab_name}')"
                    if await page.is_visible(tab_selector):
                        await page.click(tab_selector)
                        await page.wait_for_timeout(1000)  # 탭 전환 대기
                        
                        # 해당 탭의 콘텐츠가 로드되었는지 확인
                        content_loaded = await page.is_visible(".space-y-6, .bg-white")
                        
                        if content_loaded:
                            successful_tabs += 1
                            print(f"  ✅ {tab_name} 탭 정상 작동")
                            await self.take_screenshot(page, f"tab_{tab_id}")
                        else:
                            print(f"  ❌ {tab_name} 탭 콘텐츠 로드 실패")
                    else:
                        print(f"  ⚠️ {tab_name} 탭 버튼을 찾을 수 없음")
                        
                except Exception as tab_error:
                    print(f"  ❌ {tab_name} 탭 테스트 중 오류: {tab_error}")
            
            duration = time.time() - start_time
            success_rate = successful_tabs / len(tabs_to_test)
            
            if success_rate >= 0.8:  # 80% 이상 성공
                await self.log_test_result("네비게이션 탭", True, f"{successful_tabs}/{len(tabs_to_test)} 탭 정상 작동", duration)
                return True
            else:
                await self.log_test_result("네비게이션 탭", False, f"일부 탭 실패 ({successful_tabs}/{len(tabs_to_test)})", duration)
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            await self.log_test_result("네비게이션 탭", False, f"예외 발생: {str(e)}", duration)
            return False

    async def test_user_management_features(self, page: Page):
        """시나리오 4: 사용자 관리 기능 테스트"""
        start_time = time.time()
        
        try:
            print("\n👥 시나리오 4: 사용자 관리 기능 테스트")
            
            # 사용자 관리 탭으로 이동
            users_tab = "button:has-text('사용자 관리'), button:has-text('⚙️ 관리자')"
            if await page.is_visible(users_tab):
                await page.click(users_tab)
                await page.wait_for_timeout(2000)
                
                # 사용자 목록 테이블 확인
                user_table = await page.is_visible("table, .space-y-6")
                create_button = await page.is_visible("button:has-text('새 사용자 생성'), button:has-text('사용자 추가')")
                
                if user_table:
                    # 새 사용자 생성 버튼 클릭 (있는 경우)
                    if create_button:
                        await page.click("button:has-text('새 사용자 생성'), button:has-text('사용자 추가')")
                        await page.wait_for_timeout(1000)
                        
                        # 모달이나 폼이 나타나는지 확인
                        modal_visible = await page.is_visible(".modal, .fixed, form")
                        
                        if modal_visible:
                            # 모달 닫기 (ESC 키 또는 취소 버튼)
                            await page.keyboard.press("Escape")
                            await page.wait_for_timeout(500)
                        
                        duration = time.time() - start_time
                        await self.log_test_result("사용자 관리", True, "사용자 관리 기능 접근 성공", duration)
                        await self.take_screenshot(page, "user_management_success")
                        return True
                    else:
                        duration = time.time() - start_time
                        await self.log_test_result("사용자 관리", True, "사용자 목록 표시됨 (생성 버튼 없음)", duration)
                        return True
                else:
                    duration = time.time() - start_time
                    await self.log_test_result("사용자 관리", False, "사용자 목록을 찾을 수 없음", duration)
                    await self.take_screenshot(page, "user_management_fail")
                    return False
            else:
                duration = time.time() - start_time
                await self.log_test_result("사용자 관리", False, "사용자 관리 탭을 찾을 수 없음", duration)
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            await self.log_test_result("사용자 관리", False, f"예외 발생: {str(e)}", duration)
            return False

    async def test_logout_workflow(self, page: Page):
        """시나리오 5: 로그아웃 워크플로우"""
        start_time = time.time()
        
        try:
            print("\n🔐 시나리오 5: 로그아웃 워크플로우")
            
            # 로그아웃 버튼 찾기 및 클릭
            logout_button = "button:has-text('로그아웃')"
            if await page.is_visible(logout_button):
                await page.click(logout_button)
                await page.wait_for_timeout(2000)
                
                # 로그인 페이지로 돌아갔는지 확인
                login_form_visible = await page.is_visible("form")
                title_visible = await page.is_visible("h1:has-text('온라인 평가 시스템')")
                
                duration = time.time() - start_time
                
                if login_form_visible and title_visible:
                    await self.log_test_result("로그아웃", True, "성공적으로 로그아웃됨", duration)
                    await self.take_screenshot(page, "logout_success")
                    return True
                else:
                    await self.log_test_result("로그아웃", False, "로그인 페이지로 이동하지 않음", duration)
                    await self.take_screenshot(page, "logout_fail")
                    return False
            else:
                duration = time.time() - start_time
                await self.log_test_result("로그아웃", False, "로그아웃 버튼을 찾을 수 없음", duration)
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            await self.log_test_result("로그아웃", False, f"예외 발생: {str(e)}", duration)
            return False

    async def test_error_handling(self, page: Page):
        """시나리오 6: 오류 처리 테스트 (잘못된 로그인)"""
        start_time = time.time()
        
        try:
            print("\n🚫 시나리오 6: 오류 처리 테스트")
            
            # 잘못된 계정으로 로그인 시도
            if await self.wait_for_element_safe(page, "input[type='text']"):
                await page.fill("input[type='text']", "wrong_user")
                await page.fill("input[type='password']", "wrong_password")
                await page.click("button[type='submit']")
                
                await page.wait_for_timeout(3000)
                
                # 오류 메시지 확인
                error_visible = await page.is_visible(".text-red-700, .bg-red-50, .text-red-600")
                still_on_login = await page.is_visible("form")
                
                duration = time.time() - start_time
                
                if error_visible and still_on_login:
                    await self.log_test_result("오류 처리", True, "잘못된 로그인에 대한 적절한 오류 표시", duration)
                    await self.take_screenshot(page, "error_handling_success")
                    return True
                else:
                    await self.log_test_result("오류 처리", False, "오류 메시지가 표시되지 않음", duration)
                    await self.take_screenshot(page, "error_handling_fail")
                    return False
            else:
                await self.log_test_result("오류 처리", False, "로그인 폼을 찾을 수 없음", time.time() - start_time)
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            await self.log_test_result("오류 처리", False, f"예외 발생: {str(e)}", duration)
            return False

    async def run_all_tests(self):
        """모든 테스트 실행"""
        print("=" * 80)
        print("🧪 온라인 평가 시스템 실시간 UI 자동화 테스트")
        print(f"🕐 테스트 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌐 테스트 대상: {self.base_url}")
        print("=" * 80)
        
        async with async_playwright() as p:
            # 브라우저 실행 (테스트 중 확인을 위해 headless=False)
            browser = await p.chromium.launch(
                headless=False,  # 실제 브라우저 창 표시
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            
            try:
                context = await browser.new_context(
                    viewport={'width': 1280, 'height': 720},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                
                page = await context.new_page()
                
                # 콘솔 오류 캐치
                page.on("console", lambda msg: print(f"🖥️ Console {msg.type}: {msg.text}") if msg.type in ["error", "warning"] else None)
                
                # 테스트 시나리오 순차 실행
                test_success = True
                
                test_success &= await self.test_initial_page_load(page)
                test_success &= await self.test_error_handling(page)
                test_success &= await self.test_admin_login_workflow(page)
                
                if test_success:  # 로그인이 성공한 경우에만 진행
                    test_success &= await self.test_navigation_tabs(page)
                    test_success &= await self.test_user_management_features(page)
                    test_success &= await self.test_logout_workflow(page)
                
                await self.generate_test_report()
                
            finally:
                await browser.close()

    async def generate_test_report(self):
        """테스트 리포트 생성"""
        print("\n" + "=" * 80)
        print("📊 테스트 결과 요약")
        print("=" * 80)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"총 테스트: {self.total_tests}")
        print(f"성공: {self.passed_tests}")
        print(f"실패: {self.failed_tests}")
        print(f"성공률: {success_rate:.1f}%")
        
        # JSON 리포트 저장
        report_data = {
            "test_summary": {
                "total_tests": self.total_tests,
                "passed_tests": self.passed_tests,
                "failed_tests": self.failed_tests,
                "success_rate": success_rate,
                "test_timestamp": datetime.now().isoformat()
            },
            "test_results": self.test_results,
            "environment": {
                "frontend_url": self.base_url,
                "backend_url": self.backend_url,
                "test_accounts": list(self.test_accounts.keys())
            }
        }
        
        report_path = f"realtime_ui_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 상세 리포트 저장: {report_path}")
        print(f"📸 스크린샷 저장 위치: {self.screenshot_dir}/")
        
        # 추천사항
        if success_rate >= 90:
            print("\n🎉 테스트 결과: 우수 - 시스템이 안정적으로 작동하고 있습니다!")
        elif success_rate >= 70:
            print("\n⚠️ 테스트 결과: 양호 - 일부 개선이 필요할 수 있습니다.")
        else:
            print("\n🚨 테스트 결과: 주의 - 시스템에 문제가 있을 수 있습니다.")

async def main():
    """메인 실행 함수"""
    tester = RealTimeUITester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
