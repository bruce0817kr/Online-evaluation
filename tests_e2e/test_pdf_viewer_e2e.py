import pytest
import asyncio
from playwright.async_api import async_playwright, expect
import aiohttp
import os
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api" # 백엔드 API 주소
FRONTEND_URL = "http://localhost:3000" # 프론트엔드 주소
TEST_PDF_PATH = r"c:\Project\Online-evaluation\tests_e2e\dummy.pdf" # 테스트용 PDF 파일 경로

# 테스트용 PDF 파일 생성 (실제로는 미리 준비된 파일을 사용)
if not os.path.exists(TEST_PDF_PATH):
    with open(TEST_PDF_PATH, "w") as f:
        f.write("This is a dummy PDF content for testing.")

async def api_request(session, method, url, data=None, headers=None, is_form_data=False):
    async with session.request(method, url, data=data if not is_form_data else None, json=data if not is_form_data and method != 'get' else None, headers=headers) as response:
        response.raise_for_status() # 오류 발생 시 예외 발생
        if response.status == 204: # No Content
            return None
        return await response.json()

async def get_admin_token(session):
    login_data = {"username": "admin", "password": "admin123"}
    # FastAPI의 OAuth2PasswordRequestForm은 x-www-form-urlencoded 형식으로 데이터를 받음
    form = aiohttp.FormData()
    form.add_field('username', login_data['username'])
    form.add_field('password', login_data['password'])
    
    token_data = await api_request(session, "post", f"{BASE_URL}/auth/login", data=form, is_form_data=True)
    return token_data["access_token"]

async def create_secretary(session, admin_token, secretary_data):
    headers = {"Authorization": f"Bearer {admin_token}"}
    return await api_request(session, "post", f"{BASE_URL}/users", data=secretary_data, headers=headers)

async def create_evaluator(session, admin_token, evaluator_data):
    headers = {"Authorization": f"Bearer {admin_token}"}
    return await api_request(session, "post", f"{BASE_URL}/evaluators", data=evaluator_data, headers=headers)

async def create_project(session, admin_token, project_data):
    headers = {"Authorization": f"Bearer {admin_token}"}
    return await api_request(session, "post", f"{BASE_URL}/projects", data=project_data, headers=headers)

async def create_company(session, admin_token, company_data):
    headers = {"Authorization": f"Bearer {admin_token}"}
    return await api_request(session, "post", f"{BASE_URL}/companies", data=company_data, headers=headers)

async def upload_pdf(session, admin_token, company_id, file_path):
    headers = {"Authorization": f"Bearer {admin_token}"}
    data = aiohttp.FormData()
    data.add_field('company_id', company_id)
    data.add_field('file',
                   open(file_path, 'rb'),
                   filename=os.path.basename(file_path),
                   content_type='application/pdf')
    return await api_request(session, "post", f"{BASE_URL}/upload", data=data, headers=headers, is_form_data=True)


@pytest.mark.asyncio
async def test_pdf_opens_in_new_tab():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False) # 테스트 중 브라우저 확인을 위해 headless=False
        context = await browser.new_context()
        page = await context.new_page()
        
        admin_token = None
        project_id = None
        company_id = None
        file_id = None

        # --- API를 통한 사전 설정 ---
        async with aiohttp.ClientSession() as session:
            try:
                admin_token = await get_admin_token(session)

                # 1. 간사 생성 (필요시)
                # secretary_data = {"login_id": "testsecretary", "password": "password123", "user_name": "테스트간사", "email": "sec@example.com", "role": "secretary"}
                # await create_secretary(session, admin_token, secretary_data)

                # 2. 평가자 5명 생성 (필요시)
                # for i in range(5):
                #     evaluator_data = {"user_name": f"테스트평가자{i+1}", "phone": f"010-1234-567{i}", "email": f"eval{i+1}@example.com"}
                #     await create_evaluator(session, admin_token, evaluator_data)
                
                # 3. 테스트 프로젝트 생성
                deadline = (datetime.utcnow() + timedelta(days=30)).isoformat() + "Z"
                project_data = {"name": "E2E PDF 테스트 프로젝트", "description": "PDF 새창 열기 기능 테스트용", "deadline": deadline}
                project_response = await create_project(session, admin_token, project_data)
                project_id = project_response["id"]

                # 4. 테스트 회사 생성
                company_data = {
                    "name": "E2E 테스트 회사", 
                    "business_number": "123-45-67890", 
                    "address": "테스트시 테스트구 테스트동",
                    "contact_person": "김테스트", 
                    "phone": "02-123-4567", 
                    "email": "company@example.com",
                    "project_id": project_id
                }
                company_response = await create_company(session, admin_token, company_data)
                company_id = company_response["id"]

                # 5. PDF 파일 업로드
                upload_response = await upload_pdf(session, admin_token, company_id, TEST_PDF_PATH)
                file_id = upload_response["file_id"]
                
                print(f"Admin token: {admin_token}")
                print(f"Project ID: {project_id}")
                print(f"Company ID: {company_id}")
                print(f"File ID: {file_id}")


            except Exception as e:
                pytest.fail(f"API 사전 설정 중 오류 발생: {e}")

        # --- Playwright E2E 테스트 ---
        try:
            # 1. 관리자로 로그인
            await page.goto(f"{FRONTEND_URL}/login")
            await page.fill("input[name='login_id']", "admin")
            await page.fill("input[name='password']", "admin123")
            await page.click("button[type='submit']")
            await expect(page).to_have_url(f"{FRONTEND_URL}/") # 로그인 후 리디렉션 확인

            # 2. 업로드된 PDF가 있는 프로젝트 상세 페이지 또는 회사 상세 페이지로 이동
            # 이 부분은 실제 애플리케이션의 네비게이션 구조에 따라 달라짐
            # 예시: 프로젝트 목록 -> 프로젝트 상세 -> 회사 목록 -> 회사 상세 -> 파일 목록
            await page.goto(f"{FRONTEND_URL}/projects/{project_id}/companies/{company_id}") # 예시 URL, 실제 경로로 수정 필요
            
            # 파일 목록이 로드될 때까지 대기 (예시: 파일 이름이 포함된 요소)
            await expect(page.locator(f"text={os.path.basename(TEST_PDF_PATH)}")).to_be_visible(timeout=10000)

            # 3. PDF '보기' 버튼 클릭 (버튼의 selector는 실제 애플리케이션에 맞게 수정)
            # 파일 ID 또는 특정 식별자를 사용하여 버튼을 정확히 타겟팅해야 함
            # 예시: data-testid 속성 사용 또는 파일 이름과 연관된 버튼 찾기
            # view_button_selector = f"//tr[.//td[contains(text(), '{os.path.basename(TEST_PDF_PATH)}')]]//button[contains(text(), '보기') or contains(@aria-label, '보기') or .//span[contains(text(), '보기')]]"
            # view_button_selector = f"button[data-file-id='{file_id}'][aria-label*='View']" # 좀 더 구체적인 selector
            
            # 파일 이름으로 row를 찾고 그 안의 '보기' 버튼을 클릭
            file_row = page.locator("tr", has_text=os.path.basename(TEST_PDF_PATH))
            view_button = file_row.locator("button", has_text="보기") # 또는 아이콘 버튼의 경우 aria-label 사용
            
            # 새 탭이 열릴 것을 예상하고 클릭 액션 수행
            async with page.expect_popup() as popup_info:
                await view_button.click()
            
            new_page = await popup_info.value
            await new_page.wait_for_load_state()

            # 4. 새 탭이 열리는지 확인
            assert new_page is not None, "새 탭이 열리지 않았습니다."

            # 5. 새 탭의 URL이 올바른 PDF 경로인지 확인
            #    PDF 미리보기 API 엔드포인트(/api/files/{file_id}/preview 또는 /api/files/{file_id})를 확인
            #    또는 프론트엔드에서 PDF를 렌더링하는 특정 경로(/viewer/pdf/{file_id} 등)
            #    여기서는 /api/files/{file_id} 또는 /api/files/{file_id}/preview 를 가정
            expected_pdf_url_pattern_1 = f"{BASE_URL}/files/{file_id}"
            expected_pdf_url_pattern_2 = f"{FRONTEND_URL}/pdf-viewer/{file_id}" # 프론트엔드 라우팅 기반 뷰어
            
            current_url = new_page.url
            print(f"새 탭 URL: {current_url}")

            # URL이 blob URL로 시작하는지, 또는 직접적인 API 경로인지 확인
            is_blob_url = current_url.startswith("blob:")
            is_direct_api_url = expected_pdf_url_pattern_1 in current_url
            is_frontend_viewer_url = expected_pdf_url_pattern_2 in current_url
            
            assert is_blob_url or is_direct_api_url or is_frontend_viewer_url, \
                f"새 탭의 URL({current_url})이 예상한 PDF 경로({expected_pdf_url_pattern_1} 또는 {expected_pdf_url_pattern_2} 또는 blob:)가 아닙니다."

            # 6. (선택 사항) PDF 뷰어가 로드되었는지 간단히 확인
            #    예: PDF 뷰어의 특정 요소가 보이는지 (예: <embed type="application/pdf"> 또는 PDF.js 컨테이너)
            if is_blob_url or is_direct_api_url: # 직접 PDF를 여는 경우
                 await expect(new_page.locator('embed[type="application/pdf"], iframe[src*="blob:"], object[type="application/pdf"]')).to_be_visible(timeout=10000)
            elif is_frontend_viewer_url: # 프론트엔드 뷰어를 사용하는 경우
                # 프론트엔드 PDF 뷰어의 특정 요소 확인 (예: id="pdf-viewer-container")
                await expect(new_page.locator("#pdf-viewer-container")).to_be_visible(timeout=10000) # 예시 ID

            print("PDF가 새 탭에서 성공적으로 열리고 내용이 확인되었습니다.")

            # 7. 새 탭 닫기
            await new_page.close()

            # 8. 로그아웃 (필요시)
            # await page.click("text=로그아웃") # 실제 로그아웃 버튼 selector로 변경
            # await expect(page).to_have_url(f"{FRONTEND_URL}/login")

        except Exception as e:
            # 테스트 실패 시 스크린샷 저장
            screenshot_path = fr"c:\Project\Online-evaluation\tests_e2e\failure_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            await page.screenshot(path=screenshot_path)
            print(f"테스트 실패. 스크린샷 저장: {screenshot_path}")
            pytest.fail(f"Playwright E2E 테스트 중 오류 발생: {e}")
        finally:
            await browser.close()

# 로컬에서 직접 실행하기 위한 코드 (pytest 실행 시에는 필요 없음)
# if __name__ == "__main__":
#     async def main():
#         await test_pdf_opens_in_new_tab()
#     asyncio.run(main())

