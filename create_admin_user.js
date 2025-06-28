// 관리자 사용자 생성 스크립트
db = db.getSiblingDB('online_evaluation');

// 기존 admin 사용자 확인
const existingAdmin = db.users.findOne({login_id: "admin"});

if (!existingAdmin) {
    // bcrypt 해시화된 admin123 비밀번호
    // bcrypt 라운드 12로 해시화: admin123
    const hashedPassword = "$2b$12$K8Y5mQs8eOVLOdP2vQHrZOVvGX8X5JaVrUBXZcUmJUGt4tOyJMzym";
    
    const adminUser = {
        id: "admin-" + new Date().getTime(),
        login_id: "admin",
        password_hash: hashedPassword,
        user_name: "시스템 관리자",
        email: "admin@evaluation.com",
        phone: "010-1234-5678",
        role: "admin",
        created_at: new Date(),
        is_active: true,
        last_login: null
    };
    
    const result = db.users.insertOne(adminUser);
    print("관리자 사용자 생성됨:", result.insertedId);
    print("로그인 정보 - ID: admin, 비밀번호: admin123");
} else {
    print("관리자 사용자가 이미 존재합니다.");
}

// 사용자 수 확인
print("전체 사용자 수:", db.users.find().count());