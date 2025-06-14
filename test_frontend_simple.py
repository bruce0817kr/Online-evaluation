#!/usr/bin/env python3
"""
간단한 프론트엔드 로그인 테스트
JavaScript injection을 통한 로그인 테스트
"""

import requests
import time

def test_frontend_api_connectivity():
    """프론트엔드가 백엔드 API에 접근할 수 있는지 확인"""
    print("🔗 프론트엔드-백엔드 연결성 테스트")
    print("-" * 40)
    
    try:
        # CORS 정책을 고려하여 OPTIONS 요청 먼저 확인
        print("📡 CORS preflight 확인...")
        options_response = requests.options(
            "http://localhost:8080/api/auth/login",
            headers={
                'Origin': 'http://localhost:3001',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type'
            },
            timeout=10
        )
        
        print(f"   OPTIONS 응답: {options_response.status_code}")
        print(f"   CORS 헤더: {options_response.headers.get('Access-Control-Allow-Origin', 'None')}")
        
        # 실제 로그인 요청 (프론트엔드와 동일한 방식)
        print("\n🔑 프론트엔드 방식 로그인 테스트...")
        
        # FormData 형태로 요청 (프론트엔드와 동일)
        form_data = {
            'username': 'admin',
            'password': 'admin123'
        }
        
        response = requests.post(
            "http://localhost:8080/api/auth/login",
            data=form_data,
            headers={
                'Origin': 'http://localhost:3001',
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            timeout=10
        )
        
        print(f"   응답 코드: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("   ✅ 로그인 성공!")
            print(f"   토큰: {data.get('access_token', 'N/A')[:20]}...")
            print(f"   사용자: {data.get('user', {}).get('user_name', 'N/A')}")
            return True
        else:
            print(f"   ❌ 로그인 실패: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 연결성 테스트 오류: {e}")
        return False

def check_frontend_status():
    """프론트엔드 서버 상태 확인"""
    print("\n🌐 프론트엔드 서버 상태 확인")
    print("-" * 40)
    
    try:
        response = requests.get("http://localhost:3001", timeout=10)
        
        if response.status_code == 200:
            print("✅ 프론트엔드 서버 정상 응답")
            
            # HTML 내용에서 React 앱 확인
            html_content = response.text
            if 'react' in html_content.lower() or 'root' in html_content:
                print("✅ React 앱 감지됨")
            else:
                print("⚠️ React 앱을 확인할 수 없음")
            
            return True
        else:
            print(f"❌ 프론트엔드 서버 응답 오류: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 프론트엔드 서버 오류: {e}")
        return False

def create_manual_test_guide():
    """수동 테스트 가이드 생성"""
    print("\n📖 수동 테스트 가이드")
    print("-" * 40)
    
    guide = """
🔍 프론트엔드 로그인 수동 테스트 방법:

1. 브라우저에서 http://localhost:3001 접속
2. 개발자 도구 열기 (F12)
3. Console 탭 선택
4. 다음 정보로 로그인 시도:
   - 아이디: admin
   - 비밀번호: admin123

5. Console에서 확인할 사항:
   - "🔑 로그인 시도 시작..." 메시지
   - "📤 로그인 요청 전송 중..." 메시지
   - "📥 로그인 응답 받음: 200" 메시지
   - "✅ 로그인 성공, 토큰 저장 중..." 메시지

6. 성공 지표:
   - 로그인 페이지에서 대시보드로 이동
   - 상단에 "관리자" 또는 사용자 정보 표시
   - "로그아웃" 버튼 표시

7. 실패 시 확인:
   - Console의 에러 메시지
   - Network 탭의 API 요청/응답
   - 빨간색 에러 알림
"""
    
    print(guide)
    
    # 테스트 스크립트 파일 생성
    test_script = """
// 브라우저 Console에서 실행할 로그인 테스트 스크립트
console.log("🧪 로그인 테스트 스크립트 시작");

// 1. 현재 페이지가 로그인 페이지인지 확인
if (window.location.pathname !== '/login' && !document.querySelector('input[type="password"]')) {
    console.log("⚠️ 로그인 페이지가 아닙니다. http://localhost:3001 로 이동하세요.");
} else {
    console.log("✅ 로그인 페이지 확인됨");
    
    // 2. 로그인 폼 요소 확인
    const usernameField = document.querySelector('input[type="text"]');
    const passwordField = document.querySelector('input[type="password"]');
    const loginButton = document.querySelector('button[type="submit"]');
    
    if (usernameField && passwordField && loginButton) {
        console.log("✅ 로그인 폼 요소 확인됨");
        
        // 3. 자동 로그인 시도
        usernameField.value = 'admin';
        passwordField.value = 'admin123';
        
        console.log("📝 로그인 정보 입력 완료");
        console.log("🔘 로그인 버튼을 클릭하세요 또는 자동 실행을 위해 loginButton.click() 실행");
        
        // 자동 클릭하려면 아래 주석 해제
        // loginButton.click();
        
    } else {
        console.log("❌ 로그인 폼 요소를 찾을 수 없습니다:");
        console.log("   Username field:", !!usernameField);
        console.log("   Password field:", !!passwordField);
        console.log("   Login button:", !!loginButton);
    }
}
"""
    
    with open('browser_login_test.js', 'w', encoding='utf-8') as f:
        f.write(test_script)
    
    print("💾 브라우저 테스트 스크립트 저장: browser_login_test.js")

def main():
    """메인 테스트 실행"""
    print("🚀 프론트엔드 로그인 검증 테스트")
    print("=" * 50)
    
    # 1. 프론트엔드 서버 상태 확인
    frontend_ok = check_frontend_status()
    
    # 2. API 연결성 테스트
    api_ok = test_frontend_api_connectivity()
    
    # 3. 수동 테스트 가이드 제공
    create_manual_test_guide()
    
    # 4. 결과 요약
    print("\n" + "=" * 50)
    print("🏁 테스트 결과 요약")
    print("=" * 50)
    print(f"🌐 프론트엔드 서버: {'✅ 정상' if frontend_ok else '❌ 문제'}")
    print(f"🔗 API 연결성: {'✅ 정상' if api_ok else '❌ 문제'}")
    
    if frontend_ok and api_ok:
        print("\n🎉 시스템이 정상적으로 작동합니다!")
        print("📖 브라우저에서 직접 로그인을 시도해보세요.")
        print("🔧 추가 디버깅이 필요하면 browser_login_test.js 스크립트를 사용하세요.")
    else:
        print(f"\n⚠️ 일부 구성요소에 문제가 있습니다. 추가 조사가 필요합니다.")

if __name__ == "__main__":
    main()
