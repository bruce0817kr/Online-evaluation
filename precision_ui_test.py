#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
정밀한 온라인 평가 시스템 UI 자동화 테스트
- 실제 DOM 구조 기반 요소 선택
- 동적 대기 및 다중 선택자 전략
- 상세한 디버깅 정보 제공
"""

import asyncio
import json
import os
from datetime import datetime
from playwright.async_api import async_playwright
import time

class PrecisionUITester:
    def __init__(self, base_url="http://localhost:3000"):
        self.base_url = base_url
        self.test_results = []
        self.screenshot_dir = "precision_test_screenshots"
        self.start_time = datetime.now()
        
    async def setup(self):
        """테스트 환경 설정"""
        if not os.path.exists(self.screenshot_dir):
            os.makedirs(self.screenshot_dir)
    
    async def capture_screenshot(self, page, name):
        """스크린샷 촬영"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.screenshot_dir}/{name}_{timestamp}.png"
        await page.screenshot(path=filename)
        print(f"📸 스크린샷: {filename}")
        return filename
    
    async def debug_page_structure(self, page):
        """페이지 구조 디버깅"""
        try:
            # 페이지 제목 확인
            title = await page.title()
            print(f"🔍 페이지 제목: {title}")
            
            # 모든 버튼 요소 찾기
            buttons = await page.evaluate("""
                () => {
                    const buttons = Array.from(document.querySelectorAll('button'));
                    return buttons.map(btn => ({
                        text: btn.textContent.trim(),
                        id: btn.id,
                        className: btn.className,
                        type: btn.type
                    }));
                }
            """)
            
            print(f"🔍 발견된 버튼들:")
            for i, btn in enumerate(buttons[:10]):  # 최대 10개만 표시
                print(f"  {i+1}. '{btn['text']}' (type: {btn['type']}, class: {btn['className'][:50]})")
            
            # 모든 입력 필드 찾기
            inputs = await page.evaluate("""
                () => {
                    const inputs = Array.from(document.querySelectorAll('input'));
                    return inputs.map(inp => ({
                        type: inp.type,
                        name: inp.name,
                        id: inp.id,
                        placeholder: inp.placeholder,
                        className: inp.className
                    }));
                }
            """)
            
            print(f"🔍 발견된 입력 필드들:")
            for i, inp in enumerate(inputs):
                print(f"  {i+1}. type: {inp['type']}, name: '{inp['name']}', placeholder: '{inp['placeholder']}'")
                
        except Exception as e:
            print(f"⚠️ 디버깅 오류: {str(e)}")
    
    async def test_login_workflow_precise(self, page):
        """정밀한 로그인 워크플로우 테스트"""
        test_name = "정밀한 로그인 워크플로우"
        start_time = time.time()
        
        try:
            print(f"🔐 {test_name} 테스트 시작")
            
            # 1. 페이지 로딩
            await page.goto(self.base_url)
            await page.wait_for_load_state('networkidle')
            await self.capture_screenshot(page, "login_page_loaded")
            
            # 2. 페이지 구조 분석
            await self.debug_page_structure(page)
            
            # 3. 로그인 버튼 찾기 (다양한 선택자 시도)
            login_selectors = [
                "button:has-text('로그인')",
                "button[type='button']:has-text('로그인')",
                "//button[contains(text(), '로그인')]",
                "button",  # 모든 버튼 중에서 찾기
            ]
            
            login_button = None
            for selector in login_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    for element in elements:
                        text = await element.text_content()
                        if "로그인" in text:
                            login_button = element
                            print(f"✅ 로그인 버튼 발견: '{text}' (선택자: {selector})")
                            break
                    if login_button:
                        break
                except:
                    continue
            
            if not login_button:
                print("❌ 로그인 버튼을 찾을 수 없습니다.")
                await self.capture_screenshot(page, "login_button_not_found")
                raise Exception("로그인 버튼 없음")
            
            # 4. 로그인 버튼 클릭
            await login_button.click()
            await page.wait_for_timeout(2000)
            await self.capture_screenshot(page, "login_modal_opened")
            
            # 5. 입력 필드 찾기 (다양한 방법 시도)
            username_selectors = [
                "input[name='username']",
                "input[placeholder*='아이디']",
                "input[placeholder*='사용자']",
                "input[type='text']",
                "//input[contains(@placeholder, '아이디') or contains(@placeholder, '사용자')]"
            ]
            
            password_selectors = [
                "input[name='password']",
                "input[type='password']",
                "input[placeholder*='비밀번호']",
                "//input[@type='password']"
            ]
            
            # 사용자명 입력
            username_input = None
            for selector in username_selectors:
                try:
                    username_input = await page.wait_for_selector(selector, timeout=3000)
                    if username_input:
                        print(f"✅ 사용자명 입력 필드 발견 (선택자: {selector})")
                        break
                except:
                    continue
            
            # 비밀번호 입력
            password_input = None
            for selector in password_selectors:
                try:
                    password_input = await page.wait_for_selector(selector, timeout=3000)
                    if password_input:
                        print(f"✅ 비밀번호 입력 필드 발견 (선택자: {selector})")
                        break
                except:
                    continue
            
            if username_input and password_input:
                # 6. 로그인 정보 입력
                await username_input.fill("admin")
                await password_input.fill("admin123")
                await self.capture_screenshot(page, "login_form_filled")
                
                # 7. 로그인 제출
                submit_selectors = [
                    "button[type='submit']",
                    "button:has-text('로그인')",
                    "//button[contains(text(), '로그인')]"
                ]
                
                submit_button = None
                for selector in submit_selectors:
                    try:
                        elements = await page.query_selector_all(selector)
                        for element in elements:
                            text = await element.text_content()
                            if "로그인" in text:
                                submit_button = element
                                break
                        if submit_button:
                            break
                    except:
                        continue
                
                if submit_button:
                    await submit_button.click()
                    
                    # 8. 로그인 결과 대기
                    try:
                        # 성공적인 로그인 후 나타날 수 있는 요소들
                        success_selectors = [
                            "text=관리자 대시보드",
                            "text=대시보드",
                            "button:has-text('로그아웃')",
                            "//button[contains(text(), '로그아웃')]",
                            ".dashboard",
                            "[data-testid='dashboard']"
                        ]
                        
                        success_element = None
                        for selector in success_selectors:
                            try:
                                success_element = await page.wait_for_selector(selector, timeout=5000)
                                if success_element:
                                    print(f"✅ 로그인 성공 확인 (요소: {selector})")
                                    break
                            except:
                                continue
                        
                        if success_element:
                            await self.capture_screenshot(page, "login_success_confirmed")
                            
                            duration = time.time() - start_time
                            result = {
                                "test_name": test_name,
                                "status": "PASS",
                                "message": "로그인 성공, 대시보드 접근 확인됨",
                                "duration": f"{duration:.2f}s",
                                "timestamp": datetime.now().isoformat()
                            }
                            
                            print(f"✅ PASS | {test_name} | {result['message']} | {result['duration']}")
                        else:
                            raise Exception("로그인 후 대시보드 요소를 찾을 수 없음")
                            
                    except Exception as e:
                        await self.capture_screenshot(page, "login_result_check_failed")
                        raise Exception(f"로그인 결과 확인 실패: {str(e)}")
                else:
                    raise Exception("로그인 제출 버튼을 찾을 수 없음")
            else:
                missing = []
                if not username_input:
                    missing.append("사용자명 입력 필드")
                if not password_input:
                    missing.append("비밀번호 입력 필드")
                raise Exception(f"입력 필드 누락: {', '.join(missing)}")
            
        except Exception as e:
            duration = time.time() - start_time
            result = {
                "test_name": test_name,
                "status": "FAIL",
                "message": f"예외 발생: {str(e)}",
                "duration": f"{duration:.2f}s",
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"❌ FAIL | {test_name} | {result['message']} | {result['duration']}")
            await self.capture_screenshot(page, "login_workflow_failed")
        
        self.test_results.append(result)
        return result
    
    async def test_navigation_discovery(self, page):
        """네비게이션 구조 발견 테스트"""
        test_name = "네비게이션 구조 발견"
        start_time = time.time()
        
        try:
            print(f"🧭 {test_name} 테스트 시작")
            
            # 페이지의 모든 네비게이션 요소 분석
            nav_info = await page.evaluate("""
                () => {
                    const nav_elements = [];
                    
                    // 네비게이션 바 찾기
                    const navbars = document.querySelectorAll('nav, .nav, .navbar, [role="navigation"]');
                    navbars.forEach((nav, index) => {
                        nav_elements.push({
                            type: 'navbar',
                            index: index,
                            className: nav.className,
                            innerHTML: nav.innerHTML.substring(0, 200)
                        });
                    });
                    
                    // 탭 요소 찾기
                    const tabs = document.querySelectorAll('[role="tab"], .tab, .tabs button, .nav-tabs button');
                    tabs.forEach((tab, index) => {
                        nav_elements.push({
                            type: 'tab',
                            index: index,
                            text: tab.textContent.trim(),
                            className: tab.className
                        });
                    });
                    
                    // 링크 요소 찾기
                    const links = document.querySelectorAll('a');
                    links.forEach((link, index) => {
                        if (link.textContent.trim() && index < 20) { // 최대 20개
                            nav_elements.push({
                                type: 'link',
                                index: index,
                                text: link.textContent.trim(),
                                href: link.href,
                                className: link.className
                            });
                        }
                    });
                    
                    return nav_elements;
                }
            """)
            
            print(f"🔍 발견된 네비게이션 요소들:")
            for element in nav_info:
                if element['type'] == 'tab':
                    print(f"  📑 탭: '{element['text']}'")
                elif element['type'] == 'link':
                    print(f"  🔗 링크: '{element['text']}'")
                elif element['type'] == 'navbar':
                    print(f"  🧭 네비게이션 바 발견 (클래스: {element['className']})")
            
            await self.capture_screenshot(page, "navigation_analysis")
            
            duration = time.time() - start_time
            result = {
                "test_name": test_name,
                "status": "PASS",
                "message": f"{len(nav_info)} 개의 네비게이션 요소 발견",
                "duration": f"{duration:.2f}s",
                "timestamp": datetime.now().isoformat(),
                "nav_elements": nav_info
            }
            
            print(f"✅ PASS | {test_name} | {result['message']} | {result['duration']}")
            
        except Exception as e:
            duration = time.time() - start_time
            result = {
                "test_name": test_name,
                "status": "FAIL",
                "message": f"예외 발생: {str(e)}",
                "duration": f"{duration:.2f}s",
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"❌ FAIL | {test_name} | {result['message']} | {result['duration']}")
        
        self.test_results.append(result)
        return result
    
    async def test_accessibility_check(self, page):
        """접근성 검사 테스트"""
        test_name = "접근성 검사"
        start_time = time.time()
        
        try:
            print(f"♿ {test_name} 테스트 시작")
            
            accessibility_info = await page.evaluate("""
                () => {
                    const issues = [];
                    
                    // 이미지에 alt 텍스트 확인
                    const images = document.querySelectorAll('img');
                    images.forEach((img, index) => {
                        if (!img.alt) {
                            issues.push(`이미지 ${index + 1}: alt 텍스트 누락`);
                        }
                    });
                    
                    // 폼 레이블 확인
                    const inputs = document.querySelectorAll('input[type="text"], input[type="password"], input[type="email"]');
                    inputs.forEach((input, index) => {
                        const hasLabel = document.querySelector(`label[for="${input.id}"]`) || 
                                        input.closest('label') ||
                                        input.getAttribute('aria-label') ||
                                        input.getAttribute('placeholder');
                        if (!hasLabel) {
                            issues.push(`입력 필드 ${index + 1}: 레이블 누락`);
                        }
                    });
                    
                    // 버튼 텍스트 확인
                    const buttons = document.querySelectorAll('button');
                    buttons.forEach((button, index) => {
                        if (!button.textContent.trim() && !button.getAttribute('aria-label')) {
                            issues.push(`버튼 ${index + 1}: 텍스트 또는 aria-label 누락`);
                        }
                    });
                    
                    return {
                        total_images: images.length,
                        total_inputs: inputs.length,
                        total_buttons: buttons.length,
                        issues: issues
                    };
                }
            """)
            
            await self.capture_screenshot(page, "accessibility_check")
            
            duration = time.time() - start_time
            result = {
                "test_name": test_name,
                "status": "PASS",
                "message": f"접근성 검사 완료 - {len(accessibility_info['issues'])}개 이슈 발견",
                "duration": f"{duration:.2f}s",
                "timestamp": datetime.now().isoformat(),
                "accessibility_info": accessibility_info
            }
            
            print(f"✅ PASS | {test_name} | {result['message']} | {result['duration']}")
            print(f"  📊 요소 수: 이미지 {accessibility_info['total_images']}, 입력 {accessibility_info['total_inputs']}, 버튼 {accessibility_info['total_buttons']}")
            
            if accessibility_info['issues']:
                print("  ⚠️ 접근성 이슈:")
                for issue in accessibility_info['issues'][:5]:  # 최대 5개만 표시
                    print(f"    - {issue}")
            
        except Exception as e:
            duration = time.time() - start_time
            result = {
                "test_name": test_name,
                "status": "FAIL",
                "message": f"예외 발생: {str(e)}",
                "duration": f"{duration:.2f}s",
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"❌ FAIL | {test_name} | {result['message']} | {result['duration']}")
        
        self.test_results.append(result)
        return result
    
    async def generate_report(self):
        """테스트 리포트 생성"""
        end_time = datetime.now()
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        report = {
            "test_session": {
                "start_time": self.start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration": str(end_time - self.start_time),
                "base_url": self.base_url
            },
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": total_tests - passed_tests,
                "success_rate": f"{success_rate:.1f}%"
            },
            "test_results": self.test_results
        }
        
        # JSON 리포트 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"precision_ui_test_report_{timestamp}.json"
        
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # 결과 출력
        print("=" * 70)
        print("📊 정밀한 UI 테스트 결과 요약")
        print("=" * 70)
        print(f"총 테스트: {total_tests}")
        print(f"성공: {passed_tests}")
        print(f"실패: {total_tests - passed_tests}")
        print(f"성공률: {success_rate:.1f}%")
        print(f"📄 상세 리포트: {report_filename}")
        print(f"📸 스크린샷: {self.screenshot_dir}/")
        
        if success_rate >= 80:
            print("🎉 테스트 결과: 우수 - 시스템이 안정적으로 작동하고 있습니다!")
        elif success_rate >= 60:
            print("⚠️ 테스트 결과: 보통 - 일부 개선이 필요합니다.")
        else:
            print("❌ 테스트 결과: 개선 필요 - 시스템에 문제가 있습니다.")
        
        return report

async def main():
    """메인 테스트 실행 함수"""
    print("=" * 70)
    print("🎯 정밀한 온라인 평가 시스템 UI 자동화 테스트")
    print(f"🕐 테스트 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 테스트 대상: http://localhost:3000")
    print("=" * 70)
    
    tester = PrecisionUITester()
    await tester.setup()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # UI 확인을 위해 브라우저 표시
            args=['--no-sandbox', '--disable-web-security']
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            ignore_https_errors=True
        )
        
        # 콘솔 메시지 캐치
        def handle_console(msg):
            if msg.type == 'error':
                print(f"🖥️ Console error: {msg.text}")
            elif msg.type == 'warning':
                print(f"⚠️ Console warning: {msg.text}")
        
        page = await context.new_page()
        page.on('console', handle_console)
        
        try:
            # 테스트 실행
            await tester.test_navigation_discovery(page)
            await tester.test_accessibility_check(page)
            await tester.test_login_workflow_precise(page)
            
        except Exception as e:
            print(f"❌ 테스트 실행 중 오류: {str(e)}")
        
        finally:
            await browser.close()
    
    # 리포트 생성
    await tester.generate_report()

if __name__ == "__main__":
    asyncio.run(main())
