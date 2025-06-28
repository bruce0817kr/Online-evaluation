// 관리자 비밀번호 업데이트 스크립트
db = db.getSiblingDB('online_evaluation');

// 간단한 비밀번호 해시 (테스트용)
// bcrypt로 admin123을 해시화한 값
const newPasswordHash = "$2b$12$LQv3c1yqBWVHxkd8eTe2aOKZdyEFfO3.Y2x/7lllmBU/vqNQlw3ja";

// 관리자 사용자 비밀번호 업데이트
const result = db.users.updateOne(
    {login_id: "admin"},
    {$set: {password_hash: newPasswordHash}}
);

print("비밀번호 업데이트 결과:", result.modifiedCount > 0 ? "성공" : "실패");

// 업데이트된 사용자 확인
const updatedUser = db.users.findOne({login_id: "admin"});
print("업데이트된 사용자:", JSON.stringify(updatedUser, null, 2));