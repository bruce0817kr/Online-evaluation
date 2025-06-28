// 정확한 비밀번호 해시로 업데이트
db = db.getSiblingDB('online_evaluation');

// 새로 생성한 정확한 해시
const correctPasswordHash = "$2b$12$WTeAuzCykM8vuaJVx70Hh.rtNq/J96XgQy.1.1yF/mjZvIxngU0hO";

// 관리자 사용자 비밀번호 업데이트
const result = db.users.updateOne(
    {login_id: "admin"},
    {$set: {password_hash: correctPasswordHash}}
);

print("비밀번호 업데이트 결과:", result.modifiedCount > 0 ? "성공" : "실패");
print("새 해시:", correctPasswordHash);