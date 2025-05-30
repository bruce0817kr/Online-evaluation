
import requests
import sys
import time
from datetime import datetime

class OnlineEvaluationSystemTester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.current_user = None

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        
        if headers is None:
            headers = {'Content-Type': 'application/json'}
            if self.token:
                headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, data=data, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json()
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    print(f"Response: {response.text}")
                except:
                    pass
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_system_init(self):
        """Test system initialization"""
        success, response = self.run_test(
            "System Initialization",
            "POST",
            "api/init",
            200,
            data=None
        )
        if success:
            print(f"System initialization response: {response}")
        return success

    def test_login(self, username, password):
        """Test login and get token"""
        form_data = {
            "username": username,
            "password": password
        }
        
        # Create form data
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
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.current_user = response['user']
            print(f"Logged in as {username} with role: {response['user']['role']}")
            return True
        return False

    def test_get_me(self):
        """Test getting current user info"""
        success, response = self.run_test(
            "Get Current User",
            "GET",
            "api/auth/me",
            200
        )
        if success:
            print(f"Current user: {response['user_name']} (Role: {response['role']})")
        return success

    def test_get_projects(self):
        """Test getting projects"""
        success, response = self.run_test(
            "Get Projects",
            "GET",
            "api/projects",
            200
        )
        if success:
            print(f"Retrieved {len(response)} projects")
        return success

    def test_get_companies(self):
        """Test getting companies"""
        success, response = self.run_test(
            "Get Companies",
            "GET",
            "api/companies",
            200
        )
        if success:
            print(f"Retrieved {len(response)} companies")
        return success

    def test_evaluator_dashboard(self):
        """Test evaluator dashboard"""
        if self.current_user and self.current_user['role'] == 'evaluator':
            success, response = self.run_test(
                "Get Evaluator Dashboard",
                "GET",
                "api/dashboard/evaluator",
                200
            )
            if success:
                print(f"Retrieved evaluator dashboard with {len(response)} assignments")
            return success
        else:
            print("Skipping evaluator dashboard test - not logged in as evaluator")
            return True

def main():
    # Get backend URL from environment variable or use default
    backend_url = "https://c9538c52-9ad8-41a7-9b0c-0f121f66378a.preview.emergentagent.com"
    
    print(f"Testing backend at: {backend_url}")
    
    # Setup tester
    tester = OnlineEvaluationSystemTester(backend_url)
    
    # Test system initialization
    if not tester.test_system_init():
        print("⚠️ System initialization failed, but continuing tests...")
    
    # Test admin login
    if not tester.test_login("admin", "admin123"):
        print("❌ Admin login failed, stopping tests")
        return 1
    
    # Test getting current user
    if not tester.test_get_me():
        print("❌ Getting current user failed")
    
    # Test getting projects
    if not tester.test_get_projects():
        print("❌ Getting projects failed")
    
    # Test getting companies
    if not tester.test_get_companies():
        print("❌ Getting companies failed")
    
    # Logout (clear token)
    tester.token = None
    tester.current_user = None
    
    # Test secretary login
    if not tester.test_login("secretary01", "secretary123"):
        print("❌ Secretary login failed")
    else:
        # Test getting current user
        if not tester.test_get_me():
            print("❌ Getting current user failed for secretary")
        
        # Test getting projects
        if not tester.test_get_projects():
            print("❌ Getting projects failed for secretary")
        
        # Test getting companies
        if not tester.test_get_companies():
            print("❌ Getting companies failed for secretary")
    
    # Logout (clear token)
    tester.token = None
    tester.current_user = None
    
    # Test evaluator login
    if not tester.test_login("evaluator01", "evaluator123"):
        print("❌ Evaluator login failed")
    else:
        # Test getting current user
        if not tester.test_get_me():
            print("❌ Getting current user failed for evaluator")
        
        # Test evaluator dashboard
        if not tester.test_evaluator_dashboard():
            print("❌ Getting evaluator dashboard failed")
    
    # Print results
    print(f"\n📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())
