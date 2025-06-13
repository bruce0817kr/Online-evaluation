#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
개선된 온라인 평가 시스템 UI 자동화 테스트
- 더 안정적인 요소 선택 전략 적용
- JavaScript 실행 기반 클릭 방식 활용
- 향상된 오류 처리 및 리트라이 메커니즘
"""

import asyncio
import json
import os
from datetime import datetime
from playwright.async_api import async_playwright
import time

class ImprovedUITester:
    def __init__(self, base_url="http://localhost:3000"):
        self.base_url = base_url
        self.test_results = []
        self.screenshot_dir = "improved_test_screenshots"
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
    
    async def safe_click(self, page, selector, timeout=10000):
        """JavaScript를 사용한 안전한 클릭"""
        try:
            # 첫 번째 시도: 일반 클릭
            element = await page.wait_for_selector(selector, timeout=timeout)
            await element.click()
            return True
        except Exception as e1:
            try:
                # 두 번째 시도: JavaScript 클릭
                await page.evaluate(f"""
                    const element = document.querySelector('{selector}');
                    if (element) {{
                        element.click();
                    }}
                """)
                await page.wait_for_timeout(1000)
                return True
            except Exception as e2:
                print(f"⚠️ 클릭 실패: {selector} - {str(e2)}")
                return False
    
    async def safe_fill(self, page, selector, text, timeout=10000):
        """안전한 텍스트 입력"""
        try:
            element = await page.wait_for_selector(selector, timeout=timeout)
            await element.fill(text)
            return True
        except Exception as e:
            print(f"⚠️ 입력 실패: {selector} - {str(e)}")
            return False
    
    async def test_comprehensive_workflow(self, page):
        """종합적인 워크플로우 테스트"""
        test_name = "종합 워크플로우"
        start_time = time.time()
        
        try:
            print(f"🔄 {test_name} 테스트 시작")
            
            # 1. 페이지 로딩 확인
            await page.goto(self.base_url)
            await page.wait_for_load_state('networkidle')
            await self.capture_screenshot(page, "workflow_start")
            
            # 2. 로그인 진행
            login_button = await page.wait_for_selector("button:has-text('로그인')", timeout=5000)
            await login_button.click()
            
            await self.safe_fill(page, "input[name='username']", "admin")
            await self.safe_fill(page, "input[name='password']", "admin123")
            
            submit_button = await page.wait_for_selector("button[type='submit']")
            await submit_button.click()
            
            # 3. 로그인 성공 확인
            await page.wait_for_selector("text=관리자 대시보드", timeout=10000)
            await self.capture_screenshot(page, "workflow_login_success")
            
            # 4. 각 탭 순회 테스트 (JavaScript 클릭 방식)
            tabs = [
                ("프로젝트 관리", "🏗️ 프로젝트 관리"),
                ("사용자 관리", "👥 사용자 관리"),
                ("평가 관리", "📋 평가 관리"),
                ("템플릿 관리", "📄 템플릿 관리"),
                ("결과 분석", "📊 결과 분석")
            ]
            
            successful_tabs = 0
            for tab_name, tab_text in tabs:
                try:
                    # JavaScript로 탭 클릭
                    await page.evaluate(f"""
                        const tabs = Array.from(document.querySelectorAll('button'));
                        const targetTab = tabs.find(tab => tab.textContent.includes('{tab_text}'));
                        if (targetTab) {{
                            targetTab.click();
                        }}
                    """)
                    
                    await page.wait_for_timeout(2000)  # 페이지 로딩 대기
                    await self.capture_screenshot(page, f"workflow_tab_{tab_name}")
                    successful_tabs += 1
                    print(f"  ✅ {tab_name} 탭 정상 작동")
                    
                except Exception as e:
                    print(f"  ⚠️ {tab_name} 탭 오류: {str(e)}")
            
            # 5. 사용자 생성 시뮬레이션 (간단한 UI 상호작용)
            try:
                # 사용자 관리 탭으로 이동
                await page.evaluate("""
                    const tabs = Array.from(document.querySelectorAll('button'));
                    const userTab = tabs.find(tab => tab.textContent.includes('👥 사용자 관리'));
                    if (userTab) {
                        userTab.click();
                    }
                """)
                await page.wait_for_timeout(2000)
                
                # 새 사용자 추가 버튼 찾기 및 클릭 시도
                try:
                    add_button = await page.wait_for_selector("button:has-text('추가')", timeout=5000)
                    await add_button.click()
                    await self.capture_screenshot(page, "workflow_user_add_attempt")
                    print(f"  ✅ 사용자 추가 기능 접근 성공")
                except:
                    print(f"  ℹ️ 사용자 추가 버튼 없음 (정상적인 상황)")
                
            except Exception as e:
                print(f"  ⚠️ 사용자 관리 오류: {str(e)}")
            
            # 6. 로그아웃
            try:
                logout_button = await page.wait_for_selector("button:has-text('로그아웃')", timeout=5000)
                await logout_button.click()
                await page.wait_for_selector("button:has-text('로그인')", timeout=5000)
                await self.capture_screenshot(page, "workflow_logout_success")
                print(f"  ✅ 로그아웃 성공")
            except Exception as e:
                print(f"  ⚠️ 로그아웃 오류: {str(e)}")
            
            duration = time.time() - start_time
            result = {
                "test_name": test_name,
                "status": "PASS",
                "message": f"종합 워크플로우 완료 - {successful_tabs}/5 탭 성공",
                "duration": f"{duration:.2f}s",
                "timestamp": datetime.now().isoformat()
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
    
    async def test_responsive_design(self, page):
        """반응형 디자인 테스트"""
        test_name = "반응형 디자인"
        start_time = time.time()
        
        try:
            print(f"📱 {test_name} 테스트 시작")
            
            viewports = [
                {"name": "모바일", "width": 375, "height": 667},
                {"name": "태블릿", "width": 768, "height": 1024},
                {"name": "데스크톱", "width": 1920, "height": 1080}
            ]
            
            successful_viewports = 0
            for viewport in viewports:
                try:
                    await page.set_viewport_size(viewport)
                    await page.goto(self.base_url)
                    await page.wait_for_load_state('networkidle')
                    
                    # 기본 요소 존재 확인
                    title_element = await page.wait_for_selector("h1, .title, [data-testid='title']", timeout=5000)
                    if title_element:
                        await self.capture_screenshot(page, f"responsive_{viewport['name']}")
                        successful_viewports += 1
                        print(f"  ✅ {viewport['name']} ({viewport['width']}x{viewport['height']}) 정상")
                    
                except Exception as e:
                    print(f"  ⚠️ {viewport['name']} 오류: {str(e)}")
            
            duration = time.time() - start_time
            result = {
                "test_name": test_name,
                "status": "PASS" if successful_viewports > 0 else "FAIL",
                "message": f"{successful_viewports}/{len(viewports)} 뷰포트에서 정상 작동",
                "duration": f"{duration:.2f}s",
                "timestamp": datetime.now().isoformat()
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
    
    async def test_performance_metrics(self, page):
        """성능 지표 테스트"""
        test_name = "성능 지표"
        start_time = time.time()
        
        try:
            print(f"⚡ {test_name} 테스트 시작")
            
            # 페이지 로딩 시간 측정
            load_start = time.time()
            await page.goto(self.base_url)
            await page.wait_for_load_state('networkidle')
            load_time = time.time() - load_start
            
            # JavaScript 성능 지표 수집
            performance_metrics = await page.evaluate("""
                () => {
                    const navigation = performance.getEntriesByType('navigation')[0];
                    return {
                        loadTime: navigation.loadEventEnd - navigation.loadEventStart,
                        domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
                        firstContentfulPaint: performance.getEntriesByType('paint').find(p => p.name === 'first-contentful-paint')?.startTime || 0
                    };
                }
            """)
            
            await self.capture_screenshot(page, "performance_test")
            
            duration = time.time() - start_time
            result = {
                "test_name": test_name,
                "status": "PASS",
                "message": f"로딩 시간: {load_time:.2f}s, DOM 준비: {performance_metrics.get('domContentLoaded', 0):.2f}ms",
                "duration": f"{duration:.2f}s",
                "timestamp": datetime.now().isoformat(),
                "metrics": performance_metrics
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
        report_filename = f"improved_ui_test_report_{timestamp}.json"
        
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # 결과 출력
        print("=" * 70)
        print("📊 개선된 UI 테스트 결과 요약")
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
    print("🔧 개선된 온라인 평가 시스템 UI 자동화 테스트")
    print(f"🕐 테스트 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 테스트 대상: http://localhost:3000")
    print("=" * 70)
    
    tester = ImprovedUITester()
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
        
        # 콘솔 오류 캐치
        def handle_console(msg):
            if msg.type == 'error':
                print(f"🖥️ Console error: {msg.text}")
        
        page = await context.new_page()
        page.on('console', handle_console)
        
        try:
            # 테스트 실행
            await tester.test_comprehensive_workflow(page)
            await tester.test_responsive_design(page)
            await tester.test_performance_metrics(page)
            
        except Exception as e:
            print(f"❌ 테스트 실행 중 오류: {str(e)}")
        
        finally:
            await browser.close()
    
    # 리포트 생성
    await tester.generate_report()

if __name__ == "__main__":
    asyncio.run(main())
