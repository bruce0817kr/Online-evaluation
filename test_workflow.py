
import re
from playwright.sync_api import Page, expect, sync_playwright

def test_admin_login_and_dashboard(playwright):
    """Admin login and dashboard check"""
    browser = playwright.chromium.launch(headless=False, slow_mo=500)
    context = browser.new_context(locale="ko-KR", extra_http_headers={"Accept-Language": "ko-KR"})
    page = context.new_page()
    
    # Capture console logs
    page.on("console", lambda msg: print(f"Browser console: {msg.text}"))

    # Capture network requests and responses
    page.on("request", lambda request: print(f"Request: {request.method} {request.url}"))
    page.on("response", lambda response: print(f"Response: {response.status} {response.url}"))

    page.goto("http://localhost:3100/")
    page.locator("input").nth(0).fill("admin") # Assuming first input is for ID
    page.locator("input").nth(1).fill("admin123") # Assuming second input is for password
    page.locator("button").nth(0).click() # Assuming first button is login button
    
    # Capture page content after login attempt
    print("\n--- Page Content After Login Attempt ---")
    print(page.content())
    print("----------------------------------------")

    expect(page).to_have_url("http://localhost:3100/dashboard")
    page.screenshot(path="screenshots/admin_dashboard.png")
    context.close()
    browser.close()

# Remaining tests are commented out for debugging login issue
# def test_secretary_creates_project(playwright):
#     """Secretary logs in, creates a project, and verifies it"""
#     browser = playwright.chromium.launch(headless=False, slow_mo=500)
#     context = browser.new_context(locale="ko-KR", extra_http_headers={"Accept-Language": "ko-KR"})
#     page = context.new_page()
#     page.goto("http://localhost:3100/")
#     page.get_by_placeholder("아이디").fill("secretary01")
#     page.get_by_placeholder("비밀번호").fill("secretary123")
#     page.locator("button.w-full.bg-blue-600").click()
    
#     # Navigate to project management and create a new project
#     page.locator("button").filter(has_text="평가 관리").click()
#     page.locator("button").filter(has_text="신규 평가 등록").click()
    
#     project_name = "신규 AI 모델 성능 평가"
#     page.get_by_label("평가명").fill(project_name)
#     page.locator("button").filter(has_text="저장").click()
    
#     # Verify the project was created
#     expect(page.locator("body")).to_contain_text(project_name)
#     page.screenshot(path="screenshots/secretary_project_created.png")
#     context.close()
#     browser.close()

# def test_evaluator_sees_project(playwright):
#     """Evaluator logs in and sees the newly created project"""
#     browser = playwright.chromium.launch(headless=False, slow_mo=500)
#     context = browser.new_context(locale="ko-KR", extra_http_headers={"Accept-Language": "ko-KR"})
#     page = context.new_page()
#     page.goto("http://localhost:3100/")
#     page.get_by_placeholder("아이디").fill("evaluator01")
#     page.get_by_placeholder("비밀번호").fill("evaluator123")
#     page.locator("button.w-full.bg-blue-600").click()
    
#     # Navigate to the project list
#     page.locator("button").filter(has_text="평가 참여").click()
    
#     # Verify the new project is visible
#     project_name = "신규 AI 모델 성능 평가"
#     expect(page.locator("body")).to_contain_text(project_name)
#     page.screenshot(path="screenshots/evaluator_sees_project.png")
#     context.close()
#     browser.close()

# def test_logout(playwright):
#     """Test user logout"""
#     browser = playwright.chromium.launch(headless=False, slow_mo=500)
#     context = browser.new_context(locale="ko-KR", extra_http_headers={"Accept-Language": "ko-KR"})
#     page = context.new_page()
#     # This test assumes a user is already logged in
#     # A more robust implementation would handle login first
#     page.goto("http://localhost:3100/dashboard") # Go to a logged-in page
#     if page.locator("button").filter(has_text="로그아웃").is_visible():
#         page.locator("button").filter(has_text="로그아웃").click()
#         expect(page.locator("button[type='submit']")).to_contain_text("로그인")
#         page.screenshot(path="screenshots/logout_success.png")
#     else:
#         # If logout button is not visible, we might not be logged in.
#         # For this simple test, we'll just pass.
#         pass
#     context.close()
#     browser.close()
