#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Playwright 웹페이지 테스트 스크립트
Online Evaluation System 웹 인터페이스 종합 테스트

MCP Sequential Thinking 기반 테스트 자동화
- 페이지 로딩 테스트
- UI 요소 상호작용 테스트
- 스크린샷 캡처
- 성능 측정
"""

import asyncio
import time
import os
import json
from datetime import datetime
from playwright.async_api import async_playwright

class PlaywrightWebTester:    def __init__(self):
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
    
    async def take_screenshot(self, page, name):
        """스크린샷 캡처"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}.png"
        screenshot_path = os.path.join(self.screenshots_dir, filename)
        await page.screenshot(path=screenshot_path, full_page=True)
        return screenshot_path
    
    async def wait_for_page_load(self, page, timeout=30000):
        """페이지 로딩 완료 대기"""
        try:
            # 네트워크 활동이 멈출 때까지 대기
            await page.wait_for_load_state('networkidle', timeout=timeout)
            # DOM이 완전히 로드될 때까지 대기
            await page.wait_for_load_state('domcontentloaded', timeout=timeout)
            return True
        except Exception as e:
            print(f"페이지 로딩 대기 중 오류: {e}")
            return False
    
    async def test_homepage_loading(self, page):
        """홈페이지 로딩 테스트"""
        try:
            start_time = time.time()
            await page.goto(self.base_url, timeout=30000)
            
            # 페이지 로딩 완료 대기
            await self.wait_for_page_load(page)
            load_time = time.time() - start_time
            
            # 페이지 제목 확인
            title = await page.title()
            
            # 스크린샷 캡처
            screenshot_path = await self.take_screenshot(page, "homepage")
            
            self.log_test(
                "홈페이지 로딩",
                "PASS",
                f"로딩 시간: {load_time:.2f}초, 제목: {title}",
                screenshot_path
            )
            return True
            
        except Exception as e:
            self.log_test("홈페이지 로딩", "FAIL", f"오류: {str(e)}")
            return False
    
    async def test_login_page(self, page):
        """로그인 페이지 테스트"""
        try:
            # 로그인 버튼 또는 링크 찾기
            login_selectors = [
                'a[href*="login"]',
                'button:has-text("로그인")',
                'button:has-text("Login")',
                '.login-button',
                '#login-btn'
            ]
            
            login_element = None
            for selector in login_selectors:
                try:
                    login_element = await page.wait_for_selector(selector, timeout=5000)
                    if login_element:
                        break
                except:
                    continue
            
            if login_element:
                await login_element.click()
                await self.wait_for_page_load(page)
                
                # 로그인 폼 요소 확인
                form_elements = []
                
                # 이메일/사용자명 입력 필드
                username_selectors = ['input[type="email"]', 'input[name*="username"]', 'input[name*="email"]']
                for selector in username_selectors:
                    if await page.query_selector(selector):
                        form_elements.append("사용자명/이메일 입력 필드")
                        break
                
                # 비밀번호 입력 필드
                if await page.query_selector('input[type="password"]'):
                    form_elements.append("비밀번호 입력 필드")
                
                # 로그인 버튼
                submit_selectors = ['button[type="submit"]', 'button:has-text("로그인")', 'button:has-text("Login")']
                for selector in submit_selectors:
                    if await page.query_selector(selector):
                        form_elements.append("로그인 버튼")
                        break
                
                screenshot_path = await self.take_screenshot(page, "login_page")
                
                self.log_test(
                    "로그인 페이지",
                    "PASS",
                    f"로그인 폼 요소: {', '.join(form_elements)}",
                    screenshot_path
                )
                return True
            else:
                screenshot_path = await self.take_screenshot(page, "no_login_button")
                self.log_test("로그인 페이지", "SKIP", "로그인 버튼을 찾을 수 없음", screenshot_path)
                return False
                
        except Exception as e:
            screenshot_path = await self.take_screenshot(page, "login_error")
            self.log_test("로그인 페이지", "FAIL", f"오류: {str(e)}", screenshot_path)
            return False
    
    async def test_responsive_design(self, page):
        """반응형 디자인 테스트"""
        try:
            viewport_sizes = [
                {"width": 1920, "height": 1080, "name": "Desktop"},
                {"width": 768, "height": 1024, "name": "Tablet"},
                {"width": 375, "height": 667, "name": "Mobile"}
            ]
            
            results = []
            for viewport in viewport_sizes:
                await page.set_viewport_size(viewport)
                await asyncio.sleep(1)  # 레이아웃 조정 대기
                
                screenshot_path = await self.take_screenshot(page, f"responsive_{viewport['name'].lower()}")
                results.append(f"{viewport['name']} ({viewport['width']}x{viewport['height']})")
            
            self.log_test(
                "반응형 디자인",
                "PASS",
                f"테스트된 화면 크기: {', '.join(results)}",
                screenshot_path
            )
            return True
            
        except Exception as e:
            self.log_test("반응형 디자인", "FAIL", f"오류: {str(e)}")
            return False
    
    async def test_navigation_menu(self, page):
        """네비게이션 메뉴 테스트"""
        try:
            # 데스크톱 크기로 복원
            await page.set_viewport_size({"width": 1280, "height": 720})
            
            # 네비게이션 요소들 찾기
            nav_selectors = [
                'nav',
                '.navbar',
                '.navigation',
                '.menu',
                'header nav',
                '[role="navigation"]'
            ]
            
            nav_element = None
            for selector in nav_selectors:
                try:
                    nav_element = await page.query_selector(selector)
                    if nav_element:
                        break
                except:
                    continue
            
            if nav_element:
                # 네비게이션 링크들 찾기
                links = await page.query_selector_all('nav a, .navbar a, .navigation a, .menu a')
                link_texts = []
                
                for link in links[:5]:  # 처음 5개만 테스트
                    try:
                        text = await link.text_content()
                        if text and text.strip():
                            link_texts.append(text.strip())
                    except:
                        continue
                
                screenshot_path = await self.take_screenshot(page, "navigation")
                
                self.log_test(
                    "네비게이션 메뉴",
                    "PASS",
                    f"발견된 메뉴 항목: {', '.join(link_texts)}",
                    screenshot_path
                )
                return True
            else:
                screenshot_path = await self.take_screenshot(page, "no_navigation")
                self.log_test("네비게이션 메뉴", "SKIP", "네비게이션 요소를 찾을 수 없음", screenshot_path)
                return False
                
        except Exception as e:
            screenshot_path = await self.take_screenshot(page, "navigation_error")
            self.log_test("네비게이션 메뉴", "FAIL", f"오류: {str(e)}", screenshot_path)
            return False
    
    async def test_page_performance(self, page):
        """페이지 성능 테스트"""
        try:
            # Performance API 사용
            performance_script = """
            () => {
                const perfData = performance.getEntriesByType('navigation')[0];
                return {
                    domContentLoaded: perfData.domContentLoadedEventEnd - perfData.domContentLoadedEventStart,
                    loadComplete: perfData.loadEventEnd - perfData.loadEventStart,
                    firstPaint: performance.getEntriesByType('paint').find(entry => entry.name === 'first-paint')?.startTime || 0,
                    firstContentfulPaint: performance.getEntriesByType('paint').find(entry => entry.name === 'first-contentful-paint')?.startTime || 0
                };
            }
            """
            
            perf_data = await page.evaluate(performance_script)
            
            # 성능 기준
            thresholds = {
                "domContentLoaded": 3000,  # 3초
                "loadComplete": 5000,      # 5초
                "firstPaint": 2000,        # 2초
                "firstContentfulPaint": 3000  # 3초
            }
            
            performance_issues = []
            for metric, value in perf_data.items():
                if value > thresholds.get(metric, float('inf')):
                    performance_issues.append(f"{metric}: {value:.0f}ms (기준: {thresholds[metric]}ms)")
            
            status = "PASS" if not performance_issues else "WARN"
            details = f"성능 메트릭: {perf_data}" if not performance_issues else f"성능 이슈: {', '.join(performance_issues)}"
            
            self.log_test("페이지 성능", status, details)
            return True
            
        except Exception as e:
            self.log_test("페이지 성능", "FAIL", f"오류: {str(e)}")
            return False
    
    async def test_dark_mode(self, page):
        """다크 모드 테스트"""
        try:
            # 다크 모드 토글 버튼 찾기
            dark_mode_selectors = [
                'button:has-text("다크")',
                'button:has-text("Dark")',
                '.dark-mode-toggle',
                '.theme-toggle',
                '[aria-label*="dark"]',
                '[title*="dark"]'
            ]
            
            dark_mode_button = None
            for selector in dark_mode_selectors:
                try:
                    dark_mode_button = await page.wait_for_selector(selector, timeout=2000)
                    if dark_mode_button:
                        break
                except:
                    continue
            
            if dark_mode_button:
                # 다크 모드 활성화 전 스크린샷
                screenshot_light = await self.take_screenshot(page, "light_mode")
                
                # 다크 모드 토글
                await dark_mode_button.click()
                await asyncio.sleep(1)  # 테마 변경 애니메이션 대기
                
                # 다크 모드 활성화 후 스크린샷
                screenshot_dark = await self.take_screenshot(page, "dark_mode")
                
                self.log_test(
                    "다크 모드",
                    "PASS",
                    f"라이트 모드: {screenshot_light}, 다크 모드: {screenshot_dark}",
                    screenshot_dark
                )
                return True
            else:
                screenshot_path = await self.take_screenshot(page, "no_dark_mode")
                self.log_test("다크 모드", "SKIP", "다크 모드 토글 버튼을 찾을 수 없음", screenshot_path)
                return False
                
        except Exception as e:
            screenshot_path = await self.take_screenshot(page, "dark_mode_error")
            self.log_test("다크 모드", "FAIL", f"오류: {str(e)}", screenshot_path)
            return False
    
    async def run_all_tests(self):
        """모든 테스트 실행"""
        print("🚀 MCP Playwright 웹페이지 테스트 시작")
        print("=" * 60)
        
        async with async_playwright() as p:
            try:
                # 브라우저 실행
                browser = await p.chromium.launch(headless=False, slow_mo=1000)
                context = await browser.new_context(
                    viewport={'width': 1280, 'height': 720},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                page = await context.new_page()
                
                # 테스트 실행
                tests = [
                    self.test_homepage_loading,
                    self.test_login_page,
                    self.test_navigation_menu,
                    self.test_responsive_design,
                    self.test_page_performance,
                    self.test_dark_mode
                ]
                
                for test in tests:
                    try:
                        await test(page)
                        await asyncio.sleep(1)  # 테스트 간 간격
                    except Exception as e:
                        print(f"❌ 테스트 실행 오류: {e}")
                
                # 브라우저 종료
                await browser.close()
                
            except Exception as e:
                print(f"❌ 브라우저 초기화 실패: {e}")
                print("⚠️  Playwright가 설치되지 않았을 수 있습니다.")
                print("💡 설치 명령: pip install playwright ; playwright install chromium")
        
        # 결과 요약
        self.print_test_summary()
        self.save_test_results()
    
    def print_test_summary(self):
        """테스트 결과 요약 출력"""
        print("\n" + "=" * 60)
        print("📊 테스트 결과 요약")
        print("=" * 60)
        
        total = len(self.test_results)
        passed = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed = len([r for r in self.test_results if r['status'] == 'FAIL'])
        skipped = len([r for r in self.test_results if r['status'] == 'SKIP'])
        warned = len([r for r in self.test_results if r['status'] == 'WARN'])
        
        print(f"총 테스트: {total}")
        print(f"성공: {passed} ✅")
        print(f"실패: {failed} ❌")
        print(f"건너뜀: {skipped} ⚠️")
        print(f"경고: {warned} 🟡")
        
        if total > 0:
            success_rate = (passed / total) * 100
            print(f"성공률: {success_rate:.1f}%")
        
        print(f"\n📸 스크린샷 저장 위치: {os.path.abspath(self.screenshots_dir)}")
    
    def save_test_results(self):
        """테스트 결과를 JSON 파일로 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"playwright_test_results_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        print(f"📄 테스트 결과 저장: {filename}")

async def main():
    """메인 실행 함수"""
    tester = PlaywrightWebTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    print("🎭 MCP Sequential Thinking 기반 Playwright 웹 테스트")
    print("🎯 대상: Online Evaluation System")
    print("🌐 URL: http://localhost:3000")
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  테스트가 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 테스트 실행 중 오류: {e}")
