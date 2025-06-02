import requests
import json
import sys

print('PDF 인증 문제 테스트 시작...')

# 1. 관리자 로그인 테스트
try:
    login_response = requests.post('http://localhost:8080/api/auth/login', 
        data={'username': 'admin', 'password': 'admin123'})
    print(f'로그인 상태: {login_response.status_code}')
    
    if login_response.status_code != 200:
        print(f'로그인 실패: {login_response.text}')
        sys.exit(1)
    
    token = login_response.json()['access_token']
    print('로그인 성공, 토큰 획득')
    
    # 2. 기업 목록 조회로 파일 ID 찾기
    companies_response = requests.get('http://localhost:8080/api/companies', 
        headers={'Authorization': f'Bearer {token}'})
    print(f'기업 목록 조회 상태: {companies_response.status_code}')
    
    if companies_response.status_code == 200:
        companies = companies_response.json()
        file_id = None
        
        # 업로드된 파일이 있는 기업 찾기
        for company in companies:
            if 'files' in company and company['files']:
                file_id = company['files'][0]['id']
                print(f'테스트할 파일 ID: {file_id}')
                break
        
        if file_id:
            # 3. 파일 미리보기 테스트
            preview_response = requests.get(f'http://localhost:8080/api/files/{file_id}/preview',
                headers={'Authorization': f'Bearer {token}'})
            print(f'파일 미리보기 상태: {preview_response.status_code}')
            
            if preview_response.status_code == 200:
                print('PDF 미리보기 성공')
                result = preview_response.json()
                print(f'응답 타입: {result.get("type", "unknown")}')
            else:
                print(f'미리보기 실패: {preview_response.text}')
                
            # 4. 파일 다운로드 테스트
            download_response = requests.get(f'http://localhost:8080/api/files/{file_id}',
                headers={'Authorization': f'Bearer {token}'})
            print(f'파일 다운로드 상태: {download_response.status_code}')
            
            if download_response.status_code == 200:
                print('PDF 다운로드 성공')
            else:
                print(f'다운로드 실패: {download_response.text}')
        else:
            print('테스트할 파일이 없습니다. 기업에 파일을 업로드해주세요.')
    else:
        print(f'기업 목록 조회 실패: {companies_response.text}')

except Exception as e:
    print(f'테스트 중 오류 발생: {e}')