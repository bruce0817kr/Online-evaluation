#!/usr/bin/env python3
"""
프론트엔드 로그인 E2E 테스트
브라우저 자동화를 통한 실제 로그인 테스트
"""

import requests
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def test_frontend_login():
    """프론트엔드 로그인 E2E 테스트"""
    print("🌐 프론트엔드 로그인 E2E 테스트 시작")
    print("=" * 50)
    
    # Chrome 옵션 설정
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 헤드리스 모드
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    driver = None
    
    try:
        print("🔧 Chrome 드라이버 시작 중...")
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(30)
        
        print("📱 프론트엔드 접속 중...")
        driver.get("http://localhost:3001")
        
        # 페이지 로딩 대기
        time.sleep(3)
        
        print("🔍 로그인 폼 요소 찾기...")
        
        # 로그인 폼 대기
        wait = WebDriverWait(driver, 10)
        
        # 아이디 입력 필드 찾기
        username_field = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']"))
        )
        
        # 비밀번호 입력 필드 찾기
        password_field = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
        
        # 로그인 버튼 찾기
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        
        print("✅ 로그인 폼 요소 발견")
        
        print("📝 로그인 정보 입력 중...")
        
        # 로그인 정보 입력
        username_field.clear()
        username_field.send_keys("admin")
        
        password_field.clear()
        password_field.send_keys("admin123")
        
        print("🔘 로그인 버튼 클릭...")
        login_button.click()
        
        # 로그인 처리 대기
        time.sleep(5)
        
        # 현재 URL 확인
        current_url = driver.current_url
        print(f"📍 현재 URL: {current_url}")
        
        # 페이지 제목 확인
        page_title = driver.title
        print(f"📄 페이지 제목: {page_title}")
        
        # 로그인 성공 확인
        # 로그인 후 대시보드나 다른 페이지로 이동했는지 확인
        if "login" not in current_url.lower():
            print("✅ 로그인 성공! (로그인 페이지에서 벗어남)")
            
            # 추가 성공 지표 확인
            try:
                # 로그아웃 버튼이나 사용자 메뉴 찾기
                logout_element = driver.find_element(By.XPATH, "//*[contains(text(), '로그아웃') or contains(text(), '관리자') or contains(text(), 'admin')]")
                print(f"✅ 로그인 성공 확인: {logout_element.text}")
                return True
                
            except:
                print("⚠️ 로그인은 성공한 것 같지만 사용자 요소를 찾을 수 없음")
                return True
        else:
            print("❌ 로그인 실패 (여전히 로그인 페이지에 있음)")
            
            # 에러 메시지 확인
            try:
                error_element = driver.find_element(By.CSS_SELECTOR, ".error, .alert, [class*='error'], [class*='alert']")
                print(f"❌ 에러 메시지: {error_element.text}")
            except:
                print("❌ 에러 메시지를 찾을 수 없음")
            
            return False
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        
        # 스크린샷 저장 (디버깅용)
        try:
            if driver:
                driver.save_screenshot("login_error.png")
                print("📸 스크린샷 저장: login_error.png")
        except:
            pass
        
        return False
        
    finally:
        if driver:
            driver.quit()
            print("🔒 브라우저 종료")

def test_api_direct():
    """API 직접 호출 테스트 (비교용)"""
    print("\n🔌 API 직접 호출 테스트")
    print("-" * 30)
    
    try:
        response = requests.post(
            "http://localhost:8080/api/auth/login",
            data="username=admin&password=admin123",
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API 직접 호출 성공")
            print(f"   사용자: {data.get('user', {}).get('user_name', 'N/A')}")
            return True
        else:
            print(f"❌ API 직접 호출 실패: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ API 호출 오류: {e}")
        return False

def main():
    """메인 테스트 실행"""
    print("🚀 프론트엔드 통합 로그인 테스트")
    print("=" * 60)
    
    # 1. API 직접 테스트
    api_success = test_api_direct()
    
    # 2. 프론트엔드 E2E 테스트
    frontend_success = test_frontend_login()
    
    # 3. 결과 요약
    print("\n" + "=" * 60)
    print("🏁 테스트 결과 요약")
    print("=" * 60)
    print(f"🔌 API 직접 호출: {'✅ 성공' if api_success else '❌ 실패'}")
    print(f"🌐 프론트엔드 E2E: {'✅ 성공' if frontend_success else '❌ 실패'}")
    
    if api_success and frontend_success:
        print("\n🎉🎉🎉 모든 테스트 통과! 로그인 시스템이 완전히 작동합니다! 🎉🎉🎉")
    elif api_success and not frontend_success:
        print("\n⚠️ 백엔드는 정상이지만 프론트엔드에 문제가 있습니다.")
    elif not api_success and frontend_success:
        print("\n⚠️ 프론트엔드는 정상이지만 백엔드에 문제가 있습니다.")
    else:
        print("\n❌ 전체 시스템에 문제가 있습니다.")

if __name__ == "__main__":
    main()
