#!/usr/bin/env python3
"""
인증 상태 체크 수정사항 검증 테스트
checkAuthStatus 함수가 서버 응답 데이터를 올바르게 사용하는지 확인
"""

import requests
import json
import time
from datetime import datetime

class AuthStatusFixVerificationTest:
    def __init__(self):
        self.base_url = "http://localhost:8080"
        self.frontend_url = "http://localhost:3000"
        self.test_results = []
        
    def log_test(self, test_name, success, message, details=None):
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        self.test_results.append(result)
        
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {message}")
        if details:
            for key, value in details.items():
                print(f"   {key}: {value}")
        print()
    
    def verify_auth_fix_implementation(self):
        """App.js의 checkAuthStatus 함수 수정사항 확인"""
        print("🔍 App.js checkAuthStatus 함수 수정사항 확인...")
        
        app_js_path = "c:/Project/Online-evaluation/frontend/src/App.js"
        
        try:
            with open(app_js_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 수정된 코드가 포함되어 있는지 확인
            fixes_found = {
                "server_response_usage": "const userData = response.data;" in content,
                "set_user_with_server_data": "setUser(userData);" in content,
                "fresh_data_comment": "Use fresh data from server instead of cached localStorage data" in content,
                "auth_me_endpoint": "axios.get(`${API}/auth/me`" in content
            }
            
            all_fixes_present = all(fixes_found.values())
            
            self.log_test(
                "App.js checkAuthStatus 수정 확인",
                all_fixes_present,
                "서버 응답 데이터 사용 수정사항 확인됨" if all_fixes_present else "일부 수정사항이 누락됨",
                {
                    "file": app_js_path,
                    "fixes_found": fixes_found,
                    "all_fixes_present": all_fixes_present
                }
            )
            return all_fixes_present
                
        except Exception as e:
            self.log_test(
                "App.js 파일 확인 오류",
                False,
                f"파일 읽기 실패: {str(e)}"
            )
            return False
    
    def test_login_flow(self):
        """로그인 플로우 테스트"""
        print("🔐 로그인 플로우 테스트 시작...")
        
        # 1. 로그인 요청
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/auth/login",
                data=login_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            if response.status_code == 200:
                data = response.json()
                token = data.get('access_token')
                user_data = data.get('user')
                
                self.log_test(
                    "로그인 성공",
                    True,
                    "관리자 로그인 성공",
                    {
                        "token_received": bool(token),
                        "user_data_received": bool(user_data),
                        "user_name": user_data.get('user_name') if user_data else None,
                        "user_role": user_data.get('role') if user_data else None
                    }
                )
                return token, user_data
            else:
                self.log_test(
                    "로그인 실패",
                    False,
                    f"상태 코드: {response.status_code}",
                    {"response": response.text}
                )
                return None, None
                
        except Exception as e:
            self.log_test(
                "로그인 오류",
                False,
                f"예외 발생: {str(e)}"
            )
            return None, None
    
    def test_auth_me_endpoint(self, token):
        """'/auth/me' 엔드포인트 테스트"""
        print("👤 /auth/me 엔드포인트 테스트...")
        
        if not token:
            self.log_test(
                "/auth/me 테스트 건너뜀",
                False,
                "토큰이 없어서 테스트를 건너뜁니다"
            )
            return None
            
        try:
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(f"{self.base_url}/api/auth/me", headers=headers)
            
            if response.status_code == 200:
                user_data = response.json()
                
                # 필수 필드 확인
                required_fields = ['id', 'login_id', 'user_name', 'role', 'email']
                missing_fields = [field for field in required_fields if field not in user_data]
                
                self.log_test(
                    "/auth/me 응답 확인",
                    len(missing_fields) == 0,
                    "사용자 데이터 응답 확인",
                    {
                        "user_id": user_data.get('id'),
                        "login_id": user_data.get('login_id'),
                        "user_name": user_data.get('user_name'),
                        "role": user_data.get('role'),
                        "email": user_data.get('email'),
                        "missing_fields": missing_fields,
                        "last_login": user_data.get('last_login')
                    }
                )
                return user_data
            else:
                self.log_test(
                    "/auth/me 실패",
                    False,
                    f"상태 코드: {response.status_code}",
                    {"response": response.text}
                )
                return None
                
        except Exception as e:
            self.log_test(
                "/auth/me 오류",
                False,
                f"예외 발생: {str(e)}"
            )
            return None
    
    def test_frontend_health(self):
        """프론트엔드 헬스 체크"""
        print("🌐 프론트엔드 헬스 체크...")
        
        try:
            response = requests.get(self.frontend_url, timeout=10)
            
            if response.status_code == 200:
                self.log_test(
                    "프론트엔드 접근",
                    True,
                    "프론트엔드 서버 정상 응답",
                    {
                        "status_code": response.status_code,
                        "content_length": len(response.content)
                    }
                )
                return True
            else:
                self.log_test(
                    "프론트엔드 접근 실패",
                    False,
                    f"상태 코드: {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "프론트엔드 오류",
                False,
                f"예외 발생: {str(e)}"
            )
            return False
    
    def test_backend_health(self):
        """백엔드 헬스 체크"""
        print("⚙️ 백엔드 헬스 체크...")
        
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            
            if response.status_code == 200:
                health_data = response.json()
                self.log_test(
                    "백엔드 헬스 체크",
                    True,
                    "백엔드 서버 정상 응답",
                    {
                        "status": health_data.get('status'),
                        "database": health_data.get('database'),
                        "timestamp": health_data.get('timestamp')
                    }
                )
                return True
            else:
                self.log_test(
                    "백엔드 헬스 체크 실패",
                    False,
                    f"상태 코드: {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "백엔드 헬스 체크 오류",
                False,
                f"예외 발생: {str(e)}"
            )
            return False
    
    def run_all_tests(self):
        """모든 테스트 실행"""
        print("=" * 60)
        print("🧪 인증 상태 체크 수정사항 검증 테스트 시작")
        print("=" * 60)
        print()
        
        # 코드 수정사항 확인
        self.verify_auth_fix_implementation()
        
        # 백엔드 헬스 체크
        backend_healthy = self.test_backend_health()
        
        # 프론트엔드 헬스 체크  
        frontend_healthy = self.test_frontend_health()
        
        if backend_healthy:
            # 로그인 테스트
            token, login_user_data = self.test_login_flow()
            
            if token:
                # /auth/me 엔드포인트 테스트
                auth_me_user_data = self.test_auth_me_endpoint(token)
                
                # 데이터 일관성 확인
                if login_user_data and auth_me_user_data:
                    user_id_match = login_user_data.get('id') == auth_me_user_data.get('id')
                    user_name_match = login_user_data.get('user_name') == auth_me_user_data.get('user_name')
                    role_match = login_user_data.get('role') == auth_me_user_data.get('role')
                    
                    self.log_test(
                        "데이터 일관성 확인",
                        user_id_match and user_name_match and role_match,
                        "로그인과 /auth/me 응답 데이터 일관성 확인",
                        {
                            "user_id_match": user_id_match,
                            "user_name_match": user_name_match,
                            "role_match": role_match,
                            "login_user_id": login_user_data.get('id'),
                            "auth_me_user_id": auth_me_user_data.get('id')
                        }
                    )
        
        # 결과 요약
        self.print_summary()
        
        # 결과를 파일로 저장
        self.save_results()
    
    def print_summary(self):
        """테스트 결과 요약 출력"""
        print("\n" + "=" * 60)
        print("📊 테스트 결과 요약")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests
        
        print(f"총 테스트: {total_tests}")
        print(f"성공: {passed_tests} ✅")
        print(f"실패: {failed_tests} ❌")
        print(f"성공률: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n실패한 테스트:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  ❌ {result['test']}: {result['message']}")
        
        print("\n" + "=" * 60)
    
    def save_results(self):
        """테스트 결과를 파일로 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"auth_status_fix_verification_results_{timestamp}.json"
        filepath = f"c:/Project/Online-evaluation/{filename}"
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, indent=2, ensure_ascii=False)
            
            print(f"📁 테스트 결과가 저장되었습니다: {filename}")
            
        except Exception as e:
            print(f"❌ 결과 저장 실패: {str(e)}")

if __name__ == "__main__":
    tester = AuthStatusFixVerificationTest()
    tester.run_all_tests()
