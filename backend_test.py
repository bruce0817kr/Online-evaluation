
import requests
import sys
import time
import json
from datetime import datetime, timedelta

class OnlineEvaluationSystemTester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.current_user = None
        self.test_data = {
            "project_id": None,
            "company_id": None,
            "template_id": None,
            "evaluator_id": None,
            "sheet_id": None,
            "generated_evaluator": {
                "login_id": None,
                "password": None,
                "id": None
            }
        }

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, json_data=None):
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
                if json_data:
                    response = requests.post(url, json=json_data, headers=headers)
                else:
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
        return success, response

    def test_get_companies(self, project_id=None):
        """Test getting companies"""
        endpoint = "api/companies"
        if project_id:
            endpoint += f"?project_id={project_id}"
            
        success, response = self.run_test(
            "Get Companies",
            "GET",
            endpoint,
            200
        )
        if success:
            print(f"Retrieved {len(response)} companies")
        return success, response

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
                if len(response) > 0:
                    self.test_data["sheet_id"] = response[0]["sheet"]["id"]
                    print(f"Found evaluation sheet ID: {self.test_data['sheet_id']}")
            return success
        else:
            print("Skipping evaluator dashboard test - not logged in as evaluator")
            return True

    def test_admin_dashboard(self):
        """Test admin dashboard"""
        if self.current_user and self.current_user['role'] in ['admin', 'secretary']:
            success, response = self.run_test(
                "Get Admin Dashboard",
                "GET",
                "api/dashboard/admin",
                200
            )
            if success:
                print(f"Retrieved admin dashboard with stats: {response['stats']}")
            return success
        else:
            print("Skipping admin dashboard test - not logged in as admin/secretary")
            return True

    def test_create_evaluator(self, name, phone, email):
        """Test creating an evaluator with automatic credential generation"""
        if self.current_user and self.current_user['role'] in ['admin', 'secretary']:
            json_data = {
                "user_name": name,
                "phone": phone,
                "email": email
            }
            
            success, response = self.run_test(
                "Create Evaluator",
                "POST",
                "api/evaluators",
                200,
                json_data=json_data
            )
            
            if success:
                print(f"Created evaluator: {response['user_name']}")
                print(f"Generated login ID: {response.get('generated_login_id')}")
                print(f"Generated password: {response.get('generated_password')}")
                
                self.test_data["generated_evaluator"]["login_id"] = response.get('generated_login_id')
                self.test_data["generated_evaluator"]["password"] = response.get('generated_password')
                self.test_data["generated_evaluator"]["id"] = response.get('id')
                
            return success
        else:
            print("Skipping create evaluator test - not logged in as admin/secretary")
            return False

    def test_get_evaluators(self):
        """Test getting evaluators"""
        if self.current_user and self.current_user['role'] in ['admin', 'secretary']:
            success, response = self.run_test(
                "Get Evaluators",
                "GET",
                "api/evaluators",
                200
            )
            
            if success:
                print(f"Retrieved {len(response)} evaluators")
            return success, response
        else:
            print("Skipping get evaluators test - not logged in as admin/secretary")
            return False, []

    def test_create_project(self, name, description):
        """Test creating a project"""
        if self.current_user and self.current_user['role'] in ['admin', 'secretary']:
            # Set deadline to 30 days from now
            deadline = (datetime.utcnow() + timedelta(days=30)).isoformat()
            
            json_data = {
                "name": name,
                "description": description,
                "deadline": deadline
            }
            
            success, response = self.run_test(
                "Create Project",
                "POST",
                "api/projects",
                200,
                json_data=json_data
            )
            
            if success:
                print(f"Created project: {response['name']}")
                self.test_data["project_id"] = response["id"]
            return success
        else:
            print("Skipping create project test - not logged in as admin/secretary")
            return False

    def test_create_company(self, name, business_number, project_id=None):
        """Test creating a company"""
        if self.current_user and self.current_user['role'] in ['admin', 'secretary']:
            if not project_id:
                project_id = self.test_data["project_id"]
                
            if not project_id:
                print("Cannot create company - no project ID available")
                return False
                
            json_data = {
                "name": name,
                "business_number": business_number,
                "address": "서울시 강남구 테헤란로 123",
                "contact_person": "홍길동",
                "phone": "01012345678",
                "email": "company@test.com",
                "project_id": project_id
            }
            
            success, response = self.run_test(
                "Create Company",
                "POST",
                "api/companies",
                200,
                json_data=json_data
            )
            
            if success:
                print(f"Created company: {response['name']}")
                self.test_data["company_id"] = response["id"]
            return success
        else:
            print("Skipping create company test - not logged in as admin/secretary")
            return False

    def test_create_evaluation_template(self, name, description, project_id=None):
        """Test creating an evaluation template"""
        if self.current_user and self.current_user['role'] in ['admin', 'secretary']:
            if not project_id:
                project_id = self.test_data["project_id"]
                
            if not project_id:
                print("Cannot create template - no project ID available")
                return False
                
            json_data = {
                "name": name,
                "description": description,
                "items": [
                    {
                        "name": "기술성",
                        "description": "기술의 혁신성 및 완성도",
                        "max_score": 30,
                        "weight": 1.0
                    },
                    {
                        "name": "시장성",
                        "description": "시장 진입 가능성 및 성장 잠재력",
                        "max_score": 30,
                        "weight": 1.0
                    },
                    {
                        "name": "사업성",
                        "description": "사업 모델의 타당성 및 수익성",
                        "max_score": 40,
                        "weight": 1.0
                    }
                ]
            }
            
            success, response = self.run_test(
                "Create Evaluation Template",
                "POST",
                f"api/templates?project_id={project_id}",
                200,
                json_data=json_data
            )
            
            if success:
                print(f"Created evaluation template: {response['name']}")
                self.test_data["template_id"] = response["id"]
            return success
        else:
            print("Skipping create template test - not logged in as admin/secretary")
            return False

    def test_get_templates(self, project_id=None):
        """Test getting evaluation templates"""
        endpoint = "api/templates"
        if project_id:
            endpoint += f"?project_id={project_id}"
            
        success, response = self.run_test(
            "Get Evaluation Templates",
            "GET",
            endpoint,
            200
        )
        
        if success:
            print(f"Retrieved {len(response)} evaluation templates")
        return success, response

    def test_create_assignments(self, evaluator_ids=None, company_ids=None, template_id=None):
        """Test creating evaluation assignments"""
        if self.current_user and self.current_user['role'] in ['admin', 'secretary']:
            if not evaluator_ids:
                evaluator_ids = [self.test_data["generated_evaluator"]["id"]]
                if not evaluator_ids[0]:
                    # Try to get evaluators
                    _, evaluators = self.test_get_evaluators()
                    if evaluators and len(evaluators) > 0:
                        evaluator_ids = [evaluators[0]["id"]]
                    else:
                        print("Cannot create assignments - no evaluator IDs available")
                        return False
                        
            if not company_ids:
                company_ids = [self.test_data["company_id"]]
                if not company_ids[0]:
                    print("Cannot create assignments - no company IDs available")
                    return False
                    
            if not template_id:
                template_id = self.test_data["template_id"]
                if not template_id:
                    print("Cannot create assignments - no template ID available")
                    return False
                    
            # Set deadline to 15 days from now
            deadline = (datetime.utcnow() + timedelta(days=15)).isoformat()
                
            json_data = {
                "evaluator_ids": evaluator_ids,
                "company_ids": company_ids,
                "template_id": template_id,
                "deadline": deadline
            }
            
            success, response = self.run_test(
                "Create Evaluation Assignments",
                "POST",
                "api/assignments",
                200,
                json_data=json_data
            )
            
            if success:
                print(f"Created assignments: {response['message']}")
            return success
        else:
            print("Skipping create assignments test - not logged in as admin/secretary")
            return False

    def test_get_evaluation_sheet(self, sheet_id=None):
        """Test getting an evaluation sheet"""
        if not sheet_id:
            sheet_id = self.test_data["sheet_id"]
            
        if not sheet_id:
            print("Cannot get evaluation sheet - no sheet ID available")
            return False
            
        success, response = self.run_test(
            "Get Evaluation Sheet",
            "GET",
            f"api/evaluation/{sheet_id}",
            200
        )
        
        if success:
            print(f"Retrieved evaluation sheet for company: {response['company']['name']}")
        return success, response

    def test_save_evaluation(self, sheet_id=None, scores=None):
        """Test saving an evaluation as draft"""
        if not sheet_id:
            sheet_id = self.test_data["sheet_id"]
            
        if not sheet_id:
            print("Cannot save evaluation - no sheet ID available")
            return False
            
        # Get the sheet first to get the template items
        success, sheet_data = self.test_get_evaluation_sheet(sheet_id)
        if not success:
            return False
            
        if not scores:
            # Generate scores for each item
            scores = []
            for item in sheet_data["template"]["items"]:
                scores.append({
                    "item_id": item["id"],
                    "score": item["max_score"] // 2,  # Half of max score
                    "opinion": "테스트 의견입니다."
                })
                
        json_data = {
            "sheet_id": sheet_id,
            "scores": scores
        }
        
        success, response = self.run_test(
            "Save Evaluation as Draft",
            "POST",
            "api/evaluation/save",
            200,
            json_data=json_data
        )
        
        if success:
            print(f"Saved evaluation as draft: {response['message']}")
        return success

    def test_submit_evaluation(self, sheet_id=None, scores=None):
        """Test submitting an evaluation"""
        if not sheet_id:
            sheet_id = self.test_data["sheet_id"]
            
        if not sheet_id:
            print("Cannot submit evaluation - no sheet ID available")
            return False
            
        # Get the sheet first to get the template items
        success, sheet_data = self.test_get_evaluation_sheet(sheet_id)
        if not success:
            return False
            
        if not scores:
            # Generate scores for each item
            scores = []
            for item in sheet_data["template"]["items"]:
                scores.append({
                    "item_id": item["id"],
                    "score": item["max_score"] - 5,  # Almost max score
                    "opinion": "최종 제출 의견입니다."
                })
                
        json_data = {
            "sheet_id": sheet_id,
            "scores": scores
        }
        
        success, response = self.run_test(
            "Submit Evaluation",
            "POST",
            "api/evaluation/submit",
            200,
            json_data=json_data
        )
        
        if success:
            print(f"Submitted evaluation: {response['message']}")
        return success

def main():
    # Get backend URL from environment variable or use default
    backend_url = "https://c9538c52-9ad8-41a7-9b0c-0f121f66378a.preview.emergentagent.com"
    
    print(f"Testing backend at: {backend_url}")
    
    # Setup tester
    tester = OnlineEvaluationSystemTester(backend_url)
    
    # Test system initialization
    if not tester.test_system_init():
        print("⚠️ System initialization failed, but continuing tests...")
    
    print("\n===== 시나리오 1: 평가위원 생성 =====")
    # Test admin login
    if not tester.test_login("admin", "admin123"):
        print("❌ Admin login failed, stopping tests")
        return 1
    
    # Test getting current user
    if not tester.test_get_me():
        print("❌ Getting current user failed")
    
    # Test creating an evaluator
    timestamp = datetime.now().strftime("%H%M%S")
    if not tester.test_create_evaluator(f"김평가{timestamp}", f"01011112222", f"evaluator{timestamp}@test.com"):
        print("❌ Creating evaluator failed")
    
    # Test getting evaluators
    tester.test_get_evaluators()
    
    print("\n===== 시나리오 2: 전체 워크플로우 =====")
    # Test creating a project
    if not tester.test_create_project("2025년 중소기업 지원", "중소기업 기술 혁신 지원 사업"):
        print("❌ Creating project failed")
    
    # Test getting projects
    tester.test_get_projects()
    
    # Test creating a company
    if not tester.test_create_company("테스트 기업", "123-45-67890"):
        print("❌ Creating company failed")
    
    # Test getting companies
    tester.test_get_companies(tester.test_data["project_id"])
    
    # Test creating an evaluation template
    if not tester.test_create_evaluation_template("기본 평가표", "기술성, 시장성, 사업성 평가"):
        print("❌ Creating evaluation template failed")
    
    # Test getting templates
    tester.test_get_templates(tester.test_data["project_id"])
    
    # Test creating assignments
    if not tester.test_create_assignments():
        print("❌ Creating assignments failed")
    
    # Test admin dashboard
    if not tester.test_admin_dashboard():
        print("❌ Getting admin dashboard failed")
    
    print("\n===== 시나리오 3: 평가 시스템 =====")
    # Logout (clear token)
    tester.token = None
    tester.current_user = None
    
    # Test login with generated evaluator credentials
    if tester.test_data["generated_evaluator"]["login_id"] and tester.test_data["generated_evaluator"]["password"]:
        if not tester.test_login(tester.test_data["generated_evaluator"]["login_id"], tester.test_data["generated_evaluator"]["password"]):
            print("❌ Generated evaluator login failed")
        else:
            # Test evaluator dashboard
            if not tester.test_evaluator_dashboard():
                print("❌ Getting evaluator dashboard failed")
            
            # Test getting evaluation sheet
            if tester.test_data["sheet_id"]:
                tester.test_get_evaluation_sheet()
                
                # Test saving evaluation as draft
                if not tester.test_save_evaluation():
                    print("❌ Saving evaluation failed")
                
                # Test submitting evaluation
                if not tester.test_submit_evaluation():
                    print("❌ Submitting evaluation failed")
    else:
        print("⚠️ Skipping evaluator login test - no generated credentials")
        # Try with default evaluator
        if not tester.test_login("evaluator01", "evaluator123"):
            print("❌ Default evaluator login failed")
        else:
            # Test evaluator dashboard
            if not tester.test_evaluator_dashboard():
                print("❌ Getting evaluator dashboard failed")
            
            # Test getting evaluation sheet
            if tester.test_data["sheet_id"]:
                tester.test_get_evaluation_sheet()
                
                # Test saving evaluation as draft
                if not tester.test_save_evaluation():
                    print("❌ Saving evaluation failed")
                
                # Test submitting evaluation
                if not tester.test_submit_evaluation():
                    print("❌ Submitting evaluation failed")
    
    # Print results
    print(f"\n📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())
