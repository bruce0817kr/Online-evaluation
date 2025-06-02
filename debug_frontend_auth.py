import requests
import json
import sys

print('프론트엔드 PDF 인증 문제 디버깅...')

# 1. 관리자 로그인으로 토큰 획득
try:
    login_response = requests.post('http://localhost:8080/api/auth/login', 
        data={'username': 'admin', 'password': 'admin123'})
    print(f'로그인 상태: {login_response.status_code}')
    
    if login_response.status_code != 200:
        print(f'로그인 실패: {login_response.text}')
        sys.exit(1)
    
    token = login_response.json()['access_token']
    print(f'토큰 획득: {token[:20]}...')
    
    # 2. 토큰 검증 테스트
    me_response = requests.get('http://localhost:8080/api/auth/me', 
        headers={'Authorization': f'Bearer {token}'})
    print(f'토큰 검증 상태: {me_response.status_code}')
    
    if me_response.status_code == 200:
        print('토큰 검증 성공')
    else:
        print(f'토큰 검증 실패: {me_response.text}')
    
    # 3. 기업 목록으로 파일 ID 찾기
    companies_response = requests.get('http://localhost:8080/api/companies', 
        headers={'Authorization': f'Bearer {token}'})
    print(f'기업 목록 조회 상태: {companies_response.status_code}')
    
    if companies_response.status_code != 200:
        print(f'기업 목록 조회 실패: {companies_response.text}')
        sys.exit(1)
    
    # companies = companies_response.json()
    # if not companies:
    #     print('등록된 기업이 없습니다.')
    #     sys.exit(1)
    
    # # 첫 번째 기업의 첫 번째 파일로 테스트
    # company = companies[0]
    # if 'files' not in company or not company['files']:
    #     print('기업에 업로드된 파일이 없습니다.')
    #     sys.exit(1)
    
    # file_id = company['files'][0]['id']
    file_id = "0a328b1b-8914-4f10-862a-145099609589"  # 테스트용 파일 ID 직접 명시
    print(f'테스트할 파일 ID: {file_id}')
    
    # 4. PDF 미리보기 요청 (프론트엔드와 동일한 방식)
    print('\n=== PDF 미리보기 요청 테스트 ===')
    preview_response = requests.get(f'http://localhost:8080/api/files/{file_id}/preview', 
        headers={'Authorization': f'Bearer {token}'})
    print(f'PDF 미리보기 상태: {preview_response.status_code}')
    
    if preview_response.status_code == 200:
        result = preview_response.json()
        print(f'응답 타입: {result.get("type", "unknown")}')
        print(f'컨텐츠 길이: {len(result.get("content", ""))}')
        print('PDF 미리보기 성공!')
    else:
        print(f'PDF 미리보기 실패: {preview_response.text}')
        print(f'응답 헤더: {dict(preview_response.headers)}')
    
    # 5. CORS 헤더 확인
    print('\n=== CORS 헤더 확인 ===')
    options_response = requests.options(f'http://localhost:8080/api/files/{file_id}/preview')
    print(f'OPTIONS 요청 상태: {options_response.status_code}')
    print(f'CORS 헤더: {dict(options_response.headers)}')
    
    # 6. 다른 인증이 필요한 엔드포인트 테스트
    print('\n=== 다른 인증 엔드포인트 테스트 ===')
    projects_response = requests.get('http://localhost:8080/api/projects', 
        headers={'Authorization': f'Bearer {token}'})
    print(f'프로젝트 목록 상태: {projects_response.status_code}')
    
except Exception as e:
    print(f'오류 발생: {e}')
    import traceback
    traceback.print_exc()