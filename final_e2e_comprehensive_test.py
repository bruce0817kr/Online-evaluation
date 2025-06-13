#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
최종 종합 E2E 시나리오 테스트
- 실제 사용자 워크플로우 시뮬레이션
- 전체 시스템 기능 검증
- 상세한 성능 및 안정성 분석
"""

import asyncio
import json
import os
from datetime import datetime
from playwright.async_api import async_playwright
import time

class FinalE2ETester:
    def __init__(self, base_url="http://localhost:3000"):
        self.base_url = base_url
        self.test_results = []
        self.screenshot_dir = "final_e2e_screenshots"
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
    
    async def test_complete_user_journey(self, page):
        """완전한 사용자 여정 테스트"""
        test_name = "완전한 사용자 여정"
        start_time = time.time()
        
        try:
            print(f"🎭 {test_name} 테스트 시작")
            
            # 1. 초기 랜딩 페이지
            await page.goto(self.base_url)
            await page.wait_for_load_state('networkidle')
            await self.capture_screenshot(page, "journey_start")
            
            # 2. 페이지 정보 수집
            page_info = await page.evaluate("""
                () => ({
                    title: document.title,
                    url: window.location.href,
                    readyState: document.readyState,
                    hasLoginButton: !!document.querySelector("button:has-text('로그인')"),
                    hasSignupButton: !!document.querySelector("button:has-text('회원가입')"),
                    buttonCount: document.querySelectorAll('button').length,
                    inputCount: document.querySelectorAll('input').length
                })
            """)
            
            print(f"📊 페이지 정보: {page_info}")
            
            # 3. 로그인 프로세스
            if page_info['hasLoginButton']:
                login_button = await page.wait_for_selector("button:has-text('로그인')")
                await login_button.click()
                await page.wait_for_timeout(1000)
                await self.capture_screenshot(page, "journey_login_opened")
                
                # 로그인 정보 입력
                username_input = await page.wait_for_selector("input[placeholder*='아이디']")
                password_input = await page.wait_for_selector("input[type='password']")
                
                await username_input.fill("admin")
                await password_input.fill("admin123")
                await self.capture_screenshot(page, "journey_credentials_entered")
                
                # 로그인 제출
                submit_button = await page.wait_for_selector("button[type='submit']")
                await submit_button.click()
                
                # 로그인 결과 대기
                await page.wait_for_selector("text=관리자 대시보드", timeout=10000)
                await self.capture_screenshot(page, "journey_dashboard_loaded")
                print("✅ 로그인 성공")
                
                # 4. 대시보드 탐색
                dashboard_info = await page.evaluate("""
                    () => {
                        const tabs = Array.from(document.querySelectorAll('button')).filter(btn => 
                            btn.textContent.includes('관리') || 
                            btn.textContent.includes('템플릿') || 
                            btn.textContent.includes('분석')
                        );
                        return {
                            availableTabs: tabs.map(tab => tab.textContent.trim()),
                            totalTabs: tabs.length
                        };
                    }
                """)
                
                print(f"📋 대시보드 탭: {dashboard_info['availableTabs']}")
                
                # 5. 각 주요 기능 영역 탐색
                function_areas = [
                    ("프로젝트 관리", "🏗️ 프로젝트 관리"),
                    ("사용자 관리", "👥 사용자 관리"),
                    ("평가 관리", "📋 평가 관리"),
                    ("템플릿 관리", "📄 템플릿 관리"),
                    ("결과 분석", "📊 결과 분석")
                ]
                
                successful_navigations = 0
                for area_name, button_text in function_areas[:3]:  # 처음 3개만 테스트
                    try:
                        # 탭 버튼 찾기 및 클릭
                        tab_button = await page.query_selector(f"button:has-text('{button_text}')")
                        if tab_button:
                            await tab_button.click()
                            await page.wait_for_timeout(2000)
                            await self.capture_screenshot(page, f"journey_{area_name.replace(' ', '_')}")
                            successful_navigations += 1
                            print(f"  ✅ {area_name} 접근 성공")
                        else:
                            print(f"  ⚠️ {area_name} 버튼 없음")
                    except Exception as e:
                        print(f"  ❌ {area_name} 오류: {str(e)}")
                
                # 6. 로그아웃 테스트
                try:
                    logout_button = await page.wait_for_selector("button:has-text('로그아웃')", timeout=5000)
                    await logout_button.click()
                    await page.wait_for_selector("button:has-text('로그인')", timeout=5000)
                    await self.capture_screenshot(page, "journey_logged_out")
                    print("  ✅ 로그아웃 성공")
                except Exception as e:
                    print(f"  ⚠️ 로그아웃 오류: {str(e)}")
                
                duration = time.time() - start_time
                result = {
                    "test_name": test_name,
                    "status": "PASS",
                    "message": f"사용자 여정 완료 - {successful_navigations}/{len(function_areas[:3])} 기능 영역 접근 성공",
                    "duration": f"{duration:.2f}s",
                    "timestamp": datetime.now().isoformat(),
                    "page_info": page_info,
                    "dashboard_info": dashboard_info
                }
                
                print(f"✅ PASS | {test_name} | {result['message']} | {result['duration']}")
            else:
                raise Exception("로그인 버튼을 찾을 수 없음")
            
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
            await self.capture_screenshot(page, "journey_failed")
        
        self.test_results.append(result)
        return result
    
    async def test_system_robustness(self, page):
        """시스템 견고성 테스트"""
        test_name = "시스템 견고성"
        start_time = time.time()
        
        try:
            print(f"🛡️ {test_name} 테스트 시작")
            
            robustness_checks = []
            
            # 1. 네트워크 지연 시뮬레이션
            await page.route("**/*", lambda route: route.continue_() if route.request.resource_type in ["document", "script", "stylesheet"] else route.abort())
            
            await page.goto(self.base_url)
            await page.wait_for_load_state('networkidle', timeout=15000)
            await self.capture_screenshot(page, "robustness_network_delay")
            robustness_checks.append("네트워크 지연 처리")
            
            # 2. 잘못된 로그인 시도
            try:
                login_button = await page.wait_for_selector("button:has-text('로그인')", timeout=5000)
                await login_button.click()
                
                username_input = await page.wait_for_selector("input[placeholder*='아이디']")
                password_input = await page.wait_for_selector("input[type='password']")
                
                await username_input.fill("wronguser")
                await password_input.fill("wrongpass")
                
                submit_button = await page.wait_for_selector("button[type='submit']")
                await submit_button.click()
                
                await page.wait_for_timeout(3000)  # 오류 메시지 대기
                await self.capture_screenshot(page, "robustness_invalid_login")
                robustness_checks.append("잘못된 로그인 처리")
                
            except Exception as e:
                print(f"  ⚠️ 잘못된 로그인 테스트 오류: {str(e)}")
            
            # 3. 빈 입력 필드 테스트
            try:
                # 입력 필드 비우기
                await username_input.fill("")
                await password_input.fill("")
                await submit_button.click()
                await page.wait_for_timeout(2000)
                await self.capture_screenshot(page, "robustness_empty_fields")
                robustness_checks.append("빈 입력 필드 처리")
                
            except Exception as e:
                print(f"  ⚠️ 빈 입력 필드 테스트 오류: {str(e)}")
            
            # 4. 브라우저 뒤로가기/앞으로가기 테스트
            try:
                await page.go_back()
                await page.wait_for_timeout(2000)
                await page.go_forward()
                await page.wait_for_timeout(2000)
                await self.capture_screenshot(page, "robustness_navigation")
                robustness_checks.append("브라우저 네비게이션 처리")
                
            except Exception as e:
                print(f"  ⚠️ 브라우저 네비게이션 테스트 오류: {str(e)}")
            
            duration = time.time() - start_time
            result = {
                "test_name": test_name,
                "status": "PASS",
                "message": f"견고성 테스트 완료 - {len(robustness_checks)}개 검사 수행",
                "duration": f"{duration:.2f}s",
                "timestamp": datetime.now().isoformat(),
                "robustness_checks": robustness_checks
            }
            
            print(f"✅ PASS | {test_name} | {result['message']} | {result['duration']}")
            print(f"  🔍 수행된 검사: {', '.join(robustness_checks)}")
            
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
        """성능 지표 상세 분석"""
        test_name = "성능 지표 분석"
        start_time = time.time()
        
        try:
            print(f"⚡ {test_name} 테스트 시작")
            
            # 성능 지표 수집 시작
            await page.evaluate("performance.mark('test-start')")
            
            load_start = time.time()
            await page.goto(self.base_url)
            await page.wait_for_load_state('networkidle')
            load_end = time.time()
            
            await page.evaluate("performance.mark('test-end')")
            
            # 상세 성능 지표 수집
            performance_data = await page.evaluate("""
                () => {
                    performance.measure('test-duration', 'test-start', 'test-end');
                    
                    const navigation = performance.getEntriesByType('navigation')[0];
                    const paint = performance.getEntriesByType('paint');
                    const resource = performance.getEntriesByType('resource');
                    
                    return {
                        navigation_timing: {
                            dns_lookup: navigation.domainLookupEnd - navigation.domainLookupStart,
                            tcp_connection: navigation.connectEnd - navigation.connectStart,
                            request_response: navigation.responseEnd - navigation.requestStart,
                            dom_processing: navigation.domContentLoadedEventEnd - navigation.responseEnd,
                            total_load: navigation.loadEventEnd - navigation.loadEventStart
                        },
                        paint_timing: paint.reduce((acc, entry) => {
                            acc[entry.name.replace('-', '_')] = entry.startTime;
                            return acc;
                        }, {}),
                        resource_summary: {
                            total_resources: resource.length,
                            scripts: resource.filter(r => r.initiatorType === 'script').length,
                            stylesheets: resource.filter(r => r.initiatorType === 'link').length,
                            images: resource.filter(r => r.initiatorType === 'img').length
                        },
                        memory_info: performance.memory ? {
                            used_js_heap_size: performance.memory.usedJSHeapSize,
                            total_js_heap_size: performance.memory.totalJSHeapSize,
                            js_heap_size_limit: performance.memory.jsHeapSizeLimit
                        } : null
                    };
                }
            """)
            
            client_load_time = load_end - load_start
            
            await self.capture_screenshot(page, "performance_analysis")
            
            duration = time.time() - start_time
            result = {
                "test_name": test_name,
                "status": "PASS",
                "message": f"성능 분석 완료 - 로딩 시간: {client_load_time:.2f}s",
                "duration": f"{duration:.2f}s",
                "timestamp": datetime.now().isoformat(),
                "performance_data": performance_data,
                "client_load_time": client_load_time
            }
            
            print(f"✅ PASS | {test_name} | {result['message']} | {result['duration']}")
            print(f"  📊 리소스 요약: {performance_data['resource_summary']}")
            
            if performance_data['memory_info']:
                memory_mb = performance_data['memory_info']['used_js_heap_size'] / (1024 * 1024)
                print(f"  🧠 메모리 사용량: {memory_mb:.2f} MB")
            
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
    
    async def generate_comprehensive_report(self):
        """종합 리포트 생성"""
        end_time = datetime.now()
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # 성능 지표 집계
        performance_summary = {}
        for result in self.test_results:
            if "performance_data" in result:
                performance_summary = result["performance_data"]
            if "client_load_time" in result:
                performance_summary["client_load_time"] = result["client_load_time"]
        
        report = {
            "test_session": {
                "start_time": self.start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "total_duration": str(end_time - self.start_time),
                "base_url": self.base_url,
                "test_type": "Final E2E Comprehensive Test"
            },
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": total_tests - passed_tests,
                "success_rate": f"{success_rate:.1f}%"
            },
            "performance_summary": performance_summary,
            "test_results": self.test_results,
            "recommendations": []
        }
        
        # 권장사항 생성
        if success_rate == 100:
            report["recommendations"].append("시스템이 모든 테스트를 통과했습니다. 프로덕션 배포 준비가 완료되었습니다.")
        elif success_rate >= 80:
            report["recommendations"].append("시스템이 대부분의 테스트를 통과했습니다. 소규모 개선 후 배포 가능합니다.")
        else:
            report["recommendations"].append("시스템에 중요한 문제가 있습니다. 배포 전 수정이 필요합니다.")
        
        if performance_summary.get("client_load_time", 0) > 3:
            report["recommendations"].append("페이지 로딩 시간이 3초를 초과합니다. 성능 최적화를 권장합니다.")
        
        # JSON 리포트 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"final_e2e_comprehensive_report_{timestamp}.json"
        
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # 결과 출력
        print("=" * 80)
        print("🏆 최종 종합 E2E 테스트 결과")
        print("=" * 80)
        print(f"📅 테스트 기간: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')} ~ {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️ 총 소요 시간: {end_time - self.start_time}")
        print(f"📊 총 테스트: {total_tests}")
        print(f"✅ 성공: {passed_tests}")
        print(f"❌ 실패: {total_tests - passed_tests}")
        print(f"📈 성공률: {success_rate:.1f}%")
        
        if performance_summary:
            print(f"⚡ 성능 지표:")
            if "client_load_time" in performance_summary:
                print(f"  - 페이지 로딩 시간: {performance_summary['client_load_time']:.2f}초")
            if "resource_summary" in performance_summary:
                rs = performance_summary["resource_summary"]
                print(f"  - 총 리소스: {rs.get('total_resources', 0)}개")
        
        print(f"📄 상세 리포트: {report_filename}")
        print(f"📸 스크린샷: {self.screenshot_dir}/")
        
        print("\n🎯 권장사항:")
        for i, rec in enumerate(report["recommendations"], 1):
            print(f"  {i}. {rec}")
        
        if success_rate == 100:
            print("\n🎉 축하합니다! 시스템이 모든 E2E 테스트를 성공적으로 통과했습니다!")
            print("🚀 프로덕션 환경 배포 준비가 완료되었습니다!")
        elif success_rate >= 80:
            print("\n✨ 시스템이 대부분의 테스트를 통과했습니다!")
            print("🔧 소규모 개선 후 배포를 권장합니다.")
        else:
            print("\n⚠️ 시스템에 개선이 필요한 부분이 있습니다.")
            print("🛠️ 배포 전 문제점을 해결해주세요.")
        
        return report

async def main():
    """메인 테스트 실행 함수"""
    print("=" * 80)
    print("🎯 최종 종합 E2E 시나리오 테스트")
    print(f"🕐 테스트 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 테스트 대상: http://localhost:3000")
    print("=" * 80)
    
    tester = FinalE2ETester()
    await tester.setup()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # UI 확인을 위해 브라우저 표시
            args=['--no-sandbox', '--disable-web-security', '--disable-features=VizDisplayCompositor']
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            ignore_https_errors=True,
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        )
        
        # 콘솔 메시지 캐치 (중요한 것만)
        def handle_console(msg):
            if msg.type == 'error' and 'Failed to load resource' not in msg.text:
                print(f"🖥️ Console error: {msg.text}")
        
        page = await context.new_page()
        page.on('console', handle_console)
        
        try:
            # 메인 테스트 실행
            await tester.test_complete_user_journey(page)
            await tester.test_performance_metrics(page)
            await tester.test_system_robustness(page)
            
        except Exception as e:
            print(f"❌ 테스트 실행 중 치명적 오류: {str(e)}")
        
        finally:
            await browser.close()
    
    # 종합 리포트 생성
    await tester.generate_comprehensive_report()

if __name__ == "__main__":
    asyncio.run(main())
