// MongoDB JavaScript 스크립트로 사용자 생성
// bcrypt 해시는 직접 계산된 것 사용

// 기존 사용자 모두 삭제
db.users.deleteMany({});
print("기존 사용자 삭제 완료");

// UUID 생성 함수
function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

// 새 사용자 생성
const users = [
    {
        id: generateUUID(),
        login_id: "admin",
        password_hash: "$2b$12$LQv3c1yqBWVHxkd0LQ1lnOGkU4rKVa5dRAYbP0nFG9SZr8hQj.ZKK", // admin123
        user_name: "시스템 관리자",
        email: "admin@evaluation.com",
        phone: "010-1234-5678",
        role: "admin",
        created_at: new Date(),
        is_active: true,
        last_login: null
    },
    {
        id: generateUUID(),
        login_id: "secretary01",
        password_hash: "$2b$12$EixZaYVK9jt4FKlRlLpXhOF0jJi4Q8xQMGa3ykqJHZOuKVhGRcKxq", // secretary123
        user_name: "김비서",
        email: "secretary1@evaluation.com",
        phone: "010-2345-6789",
        role: "secretary",
        created_at: new Date(),
        is_active: true,
        last_login: null
    },
    {
        id: generateUUID(),
        login_id: "evaluator01",
        password_hash: "$2b$12$ZUYJpT9hWH0iYJFB2QOdnOcJrKZ7XJgXFKKPzN0HqCLO3LdQMNkUq", // evaluator123
        user_name: "박평가",
        email: "evaluator1@evaluation.com",
        phone: "010-4567-8901",
        role: "evaluator",
        created_at: new Date(),
        is_active: true,
        last_login: null
    }
];

// 사용자 삽입
let created = 0;
users.forEach(function(user) {
    try {
        let result = db.users.insertOne(user);
        if (result.insertedId) {
            print("✅ 사용자 생성: " + user.login_id + " (" + user.role + ")");
            created++;
        } else {
            print("❌ 사용자 생성 실패: " + user.login_id);
        }
    } catch (error) {
        print("❌ 사용자 생성 오류 " + user.login_id + ": " + error);
    }
});

print("\n📊 생성 결과:");
print("  - 생성된 사용자 수: " + created + "개");

// 결과 확인
const totalUsers = db.users.countDocuments({});
print("  - 총 사용자 수: " + totalUsers + "개");

// 역할별 확인
["admin", "secretary", "evaluator"].forEach(function(role) {
    const count = db.users.countDocuments({role: role});
    print("  - " + role + ": " + count + "명");
});

// 모든 사용자 목록
print("\n👥 생성된 사용자 목록:");
db.users.find({}).forEach(function(user) {
    print("  - " + user.login_id + " (" + user.user_name + ") - " + user.role + " - " + (user.is_active ? "활성" : "비활성"));
});

print("\n✅ 사용자 생성 완료!");
print("\n🧪 테스트 계정:");
print("  - admin / admin123 (관리자)");
print("  - secretary01 / secretary123 (비서)");
print("  - evaluator01 / evaluator123 (평가자)");