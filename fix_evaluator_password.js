// MongoDB에서 evaluator01 비밀번호 수정

// bcrypt로 evaluator123을 해시한 값 (정확히 계산된 값)
const newPasswordHash = "$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi"; // evaluator123

// evaluator01 사용자 업데이트
const result = db.users.updateOne(
    { login_id: "evaluator01" },
    { 
        $set: { 
            password_hash: newPasswordHash,
            is_active: true 
        } 
    }
);

if (result.modifiedCount > 0) {
    print("✅ evaluator01 비밀번호 업데이트 성공");
} else {
    print("❌ evaluator01 비밀번호 업데이트 실패");
}

// 결과 확인
const user = db.users.findOne({ login_id: "evaluator01" });
if (user) {
    print("🔍 evaluator01 정보:");
    print("  - login_id: " + user.login_id);
    print("  - user_name: " + user.user_name);
    print("  - role: " + user.role);
    print("  - is_active: " + user.is_active);
    print("  - password_hash: " + user.password_hash.substring(0, 20) + "...");
} else {
    print("❌ evaluator01 사용자를 찾을 수 없음");
}