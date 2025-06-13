#!/usr/bin/env python3
"""
프론트엔드 로그인 기능 브라우저 테스트
Selenium을 사용하여 실제 브라우저에서 로그인 기능을 테스트
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import json
from datetime import datetime

class FrontendLoginTester:
    def __init__(self):
        self.setup_driver()
        self.test_results = []
        
    def setup_driver(self):
        """Chrome 드라이버 설정"""
        chrome_options = Options()
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_window_size(1280, 720)
            print("✅ Chrome 드라이버 초기화 완료")
        except Exception as e:
            print(f"❌ Chrome 드라이버 초기화 실패: {e}")
            raise
    
    def check_console_errors(self):
        """브라우저 콘솔 오류 확인"""
        logs = self.driver.get_log('browser')
        errors = [log for log in logs if log['level'] == 'SEVERE']
        if errors:
            print("❌ 콘솔 오류 발견:")
            for error in errors:
                print(f"   - {error['message']}")
        return errors
    
    def check_network_requests(self):
        """네트워크 요청 확인 (Performance API 사용)"""
        script = """
        return performance.getEntriesByType('resource')
            .filter(entry => entry.name.includes('/api/'))
            .map(entry => ({
                name: entry.name,
                duration: entry.duration,
                responseStart: entry.responseStart,
                responseEnd: entry.responseEnd
            }));
        """
        return self.driver.execute_script(script)
    
    def test_page_load(self):
        """페이지 로드 테스트"""
        print("🌐 페이지 로드 테스트...")
        try:
            self.driver.get("http://localhost:3000")
            
            # 페이지 로드 대기
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # 로그인 폼이 로드되는지 확인
            login_form = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.TAG_NAME, "form"))
            )
            
            print("✅ 페이지 로드 성공")
            
            # 콘솔 오류 확인
            errors = self.check_console_errors()
            if not errors:
                print("✅ 콘솔 오류 없음")
            
            return True
            
        except Exception as e:
            print(f"❌ 페이지 로드 실패: {e}")
            return False
    
    def test_login_ui_elements(self):
        """로그인 UI 요소 확인"""
        print("🔍 로그인 UI 요소 확인...")
        
        try:
            # 사용자명 입력 필드
            username_field = self.driver.find_element(By.XPATH, "//input[@type='text']")
            print("✅ 사용자명 입력 필드 발견")
            
            # 비밀번호 입력 필드
            password_field = self.driver.find_element(By.XPATH, "//input[@type='password']")
            print("✅ 비밀번호 입력 필드 발견")
            
            # 로그인 버튼
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            print("✅ 로그인 버튼 발견")
            
            return True
            
        except Exception as e:
            print(f"❌ UI 요소 확인 실패: {e}")
            return False
    
    def test_single_login(self, username, password, test_name="Login Test"):
        """단일 로그인 테스트"""
        print(f"🔑 {test_name} 시작...")
        
        start_time = time.time()
        result = {
            'test_name': test_name,
            'username': username,
            'success': False,
            'error': None,
            'duration': 0,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # 페이지 새로고침
            self.driver.refresh()
            time.sleep(2)
            
            # 입력 필드 찾기
            username_field = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//input[@type='text']"))
            )
            password_field = self.driver.find_element(By.XPATH, "//input[@type='password']")
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            
            # 기존 값 지우기
            username_field.clear()
            password_field.clear()
            
            # 로그인 정보 입력
            username_field.send_keys(username)
            time.sleep(0.5)
            password_field.send_keys(password)
            time.sleep(0.5)
            
            # 로그인 버튼 클릭
            login_button.click()
            
            # 로그인 결과 대기 (성공 또는 오류 메시지)
            try:
                # 성공 시 대시보드 또는 다른 페이지 요소 확인
                WebDriverWait(self.driver, 10).until(
                    lambda driver: "대시보드" in driver.page_source or 
                                  "로그아웃" in driver.page_source or
                                  "평가" in driver.page_source or
                                  "관리" in driver.page_source
                )
                result['success'] = True
                print(f"✅ {test_name} 성공!")
                
            except:
                # 오류 메시지 확인
                try:
                    error_element = self.driver.find_element(By.XPATH, "//*[contains(text(), '실패') or contains(text(), '오류') or contains(text(), '잘못')]")
                    result['error'] = error_element.text
                    print(f"❌ {test_name} 실패: {result['error']}")
                except:
                    result['error'] = "알 수 없는 오류 또는 타임아웃"
                    print(f"❌ {test_name} 실패: 타임아웃 또는 알 수 없는 오류")
            
            # 콘솔 오류 확인
            console_errors = self.check_console_errors()
            if console_errors:
                result['console_errors'] = [error['message'] for error in console_errors]
            
            # 네트워크 요청 확인
            api_requests = self.check_network_requests()
            result['api_requests'] = api_requests
            
        except Exception as e:
            result['error'] = str(e)
            print(f"❌ {test_name} 예외 발생: {e}")
        
        result['duration'] = time.time() - start_time
        self.test_results.append(result)
        return result
    
    def run_comprehensive_test(self):
        """종합 테스트 실행"""
        print("🚀 프론트엔드 로그인 종합 테스트 시작")
        print("=" * 50)
        
        if not self.test_page_load():
            return False
        
        if not self.test_login_ui_elements():
            return False
        
        # 테스트 계정들
        test_accounts = [
            ("admin", "admin123", "관리자 로그인"),
            ("secretary01", "secretary123", "간사 로그인"),
            ("evaluator01", "evaluator123", "평가위원 로그인"),
            ("invalid_user", "wrong_pass", "잘못된 계정 로그인")
        ]
        
        for username, password, test_name in test_accounts:
            self.test_single_login(username, password, test_name)
            time.sleep(2)  # 테스트 간 간격
        
        self.analyze_results()
        self.save_results()
    
    def analyze_results(self):
        """결과 분석"""
        print("\n📊 테스트 결과 분석")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        successful_tests = len([r for r in self.test_results if r['success']])
        
        print(f"총 테스트: {total_tests}")
        print(f"성공: {successful_tests}")
        print(f"실패: {total_tests - successful_tests}")
        print(f"성공률: {(successful_tests/total_tests)*100:.1f}%")
        
        print("\n테스트별 결과:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test_name']}: {result['duration']:.2f}초")
            if result['error']:
                print(f"   오류: {result['error']}")
            if result.get('console_errors'):
                print(f"   콘솔 오류: {len(result['console_errors'])}개")
    
    def save_results(self):
        """결과 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"frontend_login_test_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        print(f"📁 결과가 {filename}에 저장되었습니다.")
    
    def cleanup(self):
        """정리"""
        if hasattr(self, 'driver'):
            self.driver.quit()
            print("🧹 브라우저 정리 완료")

def main():
    tester = None
    try:
        tester = FrontendLoginTester()
        tester.run_comprehensive_test()
    except Exception as e:
        print(f"❌ 테스트 실행 중 오류: {e}")
    finally:
        if tester:
            tester.cleanup()

if __name__ == "__main__":
    main()
