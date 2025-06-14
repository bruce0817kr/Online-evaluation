
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
