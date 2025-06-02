import requests
import sys
import time
import json
import random
import string
from datetime import datetime

class OnlineEvaluationSystemTester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.current_user = None
        self.session = requests.Session()
        
    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, json_data=None, files=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        
        if headers is None:
            headers = {}
            
        if self.token and 'Authorization' not in headers:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n[TEST] {name}...")
        print(f"   URL: {url}")
        print(f"   Method: {method}")
        
        try:
            if method == 'GET':
                response = self.session.get(url, headers=headers)
            elif method == 'POST':
                if files:
                    response = self.session.post(url, data=data, files=files, headers=headers)
                elif json_data:
                    headers['Content-Type'] = 'application/json'
                    response = self.session.post(url, json=json_data, headers=headers)
                else:
                    response = self.session.post(url, data=data, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"[PASS] Status: {response.status_code}")
                try:
                    return success, response.json()
                except:
                    return success, response.text
            else:
                print(f"[FAIL] Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:500]}")
                return False, response.text

        except Exception as e:
            print(f"[ERROR] {str(e)}")
            return False, str(e)

    def test_health(self):
        """Test system health endpoint"""
        success, response = self.run_test(
            "System Health Check",
            "GET",
            "health",
            200
        )
        if success:
            print(f"   Health status: OK")
        return success

    def test_login(self, username, password):
        """Test login with form data"""
        form_data = {
            "username": username,
            "password": password
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        success, response = self.run_test(
            f"Login as {username}",
            "POST",
            "api/auth/login",
            200,
            data=form_data,
            headers=headers
        )
        
        if success and isinstance(response, dict) and 'access_token' in response:
            self.token = response['access_token']
            print(f"   [SUCCESS] Login successful, token obtained")
            return True
        else:
            print(f"   [FAIL] Login failed or no token in response")
            return False

    def test_get_me(self):
        """Test getting current user info"""
        if not self.token:
            print("   [SKIP] No token available, skipping")
            return False
            
        success, response = self.run_test(
            "Get Current User Info",
            "GET", 
            "api/auth/me",
            200
        )
        
        if success and isinstance(response, dict):
            self.current_user = response
            print(f"   User: {response.get('login_id', 'Unknown')}")
            print(f"   Role: {response.get('role', 'Unknown')}")
            return True
        return False

    def test_secretary_signup(self, name, phone, email, reason):
        """Test secretary signup"""
        json_data = {
            "name": name,
            "phone": phone,
            "email": email,
            "reason": reason
        }
        
        success, response = self.run_test(
            "Secretary Signup",
            "POST",
            "api/auth/secretary-signup",
            200,
            json_data=json_data
        )
        
        if success:
            print(f"   [SUCCESS] Secretary signup request submitted")
            return True
        return False

    def test_admin_secretary_requests(self):
        """Test getting secretary requests (admin only)"""
        if not self.token:
            print("   [SKIP] No token available, skipping")
            return False
            
        success, response = self.run_test(
            "Get Secretary Requests",
            "GET",
            "api/admin/secretary-requests", 
            200
        )
        
        if success:
            print(f"   [SUCCESS] Retrieved secretary requests")
            return True
        return False

    def test_get_users(self):
        """Test getting all users"""
        success, response = self.run_test(
            "Get All Users",
            "GET",
            "api/users",
            200
        )
        
        if success:
            print(f"   [SUCCESS] Retrieved users list")
            return True
        return False

    def test_get_projects(self):
        """Test getting projects"""
        if not self.token:
            print("   [SKIP] No token available, skipping")
            return False
            
        success, response = self.run_test(
            "Get Projects",
            "GET",
            "api/projects",
            200
        )
        
        if success:
            print(f"   [SUCCESS] Retrieved projects list")
            return True
        return False

    def test_dashboard_admin(self):
        """Test admin dashboard"""
        if not self.token:
            print("   [SKIP] No token available, skipping")
            return False
            
        success, response = self.run_test(
            "Admin Dashboard",
            "GET",
            "api/dashboard/admin",
            200
        )
        
        if success:
            print(f"   [SUCCESS] Retrieved admin dashboard")
            return True
        return False

    def print_summary(self):
        """Print test summary"""
        print(f"\n{'='*60}")
        print(f"테스트 결과 요약")
        print(f"{'='*60}")
        print(f"총 테스트: {self.tests_run}")
        print(f"성공: {self.tests_passed}")
        print(f"실패: {self.tests_run - self.tests_passed}")
        print(f"성공률: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "성공률: 0%")
        print(f"{'='*60}")

def main():
    # 올바른 백엔드 URL 사용
    backend_url = "http://localhost:8080"
    
    print(f"Testing backend at: {backend_url}")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Setup tester
    tester = OnlineEvaluationSystemTester(backend_url)
    
    # Test 1: Health check
    print(f"\n{'='*60}")
    print("1. 시스템 헬스 체크")
    print(f"{'='*60}")
    if not tester.test_health():
        print("[WARNING] System health check failed, stopping tests")
        return 1
    
    # Test 2: Admin login
    print(f"\n{'='*60}")
    print("2. 관리자 로그인 테스트")
    print(f"{'='*60}")
    if not tester.test_login("admin", "admin123"):
        print("[ERROR] Admin login failed, stopping tests")
        return 1
    
    # Test 3: Get current user
    print(f"\n{'='*60}")
    print("3. 현재 사용자 정보 조회")
    print(f"{'='*60}")
    tester.test_get_me()
    
    # Test 4: Admin functions
    print(f"\n{'='*60}")
    print("4. 관리자 기능 테스트")
    print(f"{'='*60}")
    tester.test_admin_secretary_requests()
    tester.test_get_users()
    tester.test_get_projects()
    tester.test_dashboard_admin()
    
    # Test 5: Secretary signup (without token)
    print(f"\n{'='*60}")
    print("5. 비서 회원가입 테스트")
    print(f"{'='*60}")
    # Temporarily remove token for signup test
    temp_token = tester.token
    tester.token = None
    tester.test_secretary_signup(
        "테스트비서",
        "010-1234-5678", 
        "secretary@test.com",
        "시스템 테스트를 위한 비서 계정 신청"
    )
    # Restore token
    tester.token = temp_token
    
    # Print final summary
    tester.print_summary()
    
    if tester.tests_passed == tester.tests_run:
        print("[SUCCESS] 모든 테스트가 성공했습니다!")
        return 0
    else:
        print("[WARNING] 일부 테스트가 실패했습니다.")
        return 1

if __name__ == "__main__":
    sys.exit(main())