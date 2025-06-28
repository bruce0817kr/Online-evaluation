// MongoDB 테스트 사용자 생성 스크립트
// 온라인 평가 시스템용 admin, secretary, evaluator 사용자들을 생성합니다.

// 온라인 평가 데이터베이스 선택
db = db.getSiblingDB('online_evaluation');

print("🔧 테스트 사용자 생성 시작...");

// UUID 생성 함수
function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

// 테스트 사용자 데이터
const testUsers = [
    // 관리자 계정
    {
        id: generateUUID(),
        login_id: "admin",
        password_hash: "$2b$12$rPUnaLzNMgg1paiw0VsLhOnIeaJQN8Cn5Lk49pNImgjcxQih0ii1Ka",
        user_name: "시스템 관리자",
        email: "admin@evaluation.com",
        phone: "010-1234-5678",
        role: "admin",
        created_at: new Date(),
        is_active: true,
        last_login: null
    },
    // 비서 계정 1
    {
        id: generateUUID(),
        login_id: "secretary01",
        password_hash: "$2b$12$70HnUyMjXogdTfdjc2GSpO3nHZ1mEusrShAJvp0xotibRjjlHfMQqq",
        user_name: "김비서",
        email: "secretary1@evaluation.com",
        phone: "010-2345-6789", 
        role: "secretary",
        created_at: new Date(),
        is_active: true,
        last_login: null
    },
    // 비서 계정 2
    {
        id: generateUUID(),
        login_id: "secretary02",
        password_hash: "$2b$12$70HnUyMjXogdTfdjc2GSpO3nHZ1mEusrShAJvp0xotibRjjlHfMQqq",
        user_name: "이비서",
        email: "secretary2@evaluation.com",
        phone: "010-3456-7890",
        role: "secretary", 
        created_at: new Date(),
        is_active: true,
        last_login: null
    },
    // 평가자 계정들
    {
        id: generateUUID(),
        login_id: "evaluator01",
        password_hash: "$2b$12$oUbTyfClbX1hMozwtJuSKeO.B.ddc/VfIDL5bYfWXaVpMUU4alAIYe",
        user_name: "박평가",
        email: "evaluator1@evaluation.com",
        phone: "010-4567-8901",
        role: "evaluator",
        created_at: new Date(),
        is_active: true,
        last_login: null
    },
    {
        id: generateUUID(),
        login_id: "evaluator02",
        password_hash: "$2b$12$oUbTyfClbX1hMozwtJuSKeO.B.ddc/VfIDL5bYfWXaVpMUU4alAIYe",
        user_name: "최평가",
        email: "evaluator2@evaluation.com",
        phone: "010-5678-9012",
        role: "evaluator",
        created_at: new Date(),
        is_active: true,
        last_login: null
    },
    {
        id: generateUUID(),
        login_id: "evaluator03",
        password_hash: "$2b$12$oUbTyfClbX1hMozwtJuSKeO.B.ddc/VfIDL5bYfWXaVpMUU4alAIYe",
        user_name: "정평가",
        email: "evaluator3@evaluation.com",
        phone: "010-6789-0123",
        role: "evaluator",
        created_at: new Date(),
        is_active: true,
        last_login: null
    },
    {
        id: generateUUID(),
        login_id: "evaluator04", 
        password_hash: "$2b$12$oUbTyfClbX1hMozwtJuSKeO.B.ddc/VfIDL5bYfWXaVpMUU4alAIYe",
        user_name: "강평가",
        email: "evaluator4@evaluation.com",
        phone: "010-7890-1234",
        role: "evaluator",
        created_at: new Date(),
        is_active: true,
        last_login: null
    },
    {
        id: generateUUID(),
        login_id: "evaluator05",
        password_hash: "$2b$12$oUbTyfClbX1hMozwtJuSKeO.B.ddc/VfIDL5bYfWXaVpMUU4alAIYe",
        user_name: "신평가", 
        email: "evaluator5@evaluation.com",
        phone: "010-8901-2345",
        role: "evaluator",
        created_at: new Date(),
        is_active: true,
        last_login: null
    }
];

// 기존 사용자 수 확인
const existingCount = db.users.countDocuments({});
print(`📊 기존 사용자 수: ${existingCount}명`);

let createdCount = 0;
let skippedCount = 0;

// 사용자 생성
testUsers.forEach(userData => {
    // 중복 검사 (login_id 기준)
    const existingUser = db.users.findOne({"login_id": userData.login_id});
    
    if (existingUser) {
        print(`⚠️  사용자 '${userData.login_id}'는 이미 존재합니다. 건너뛰기...`);
        skippedCount++;
        return;
    }
    
    // 사용자 삽입
    try {
        const result = db.users.insertOne(userData);
        if (result.insertedId) {
            print(`✅ 사용자 생성: ${userData.login_id} (${userData.user_name}) - ${userData.role}`);
            createdCount++;
        } else {
            print(`❌ 사용자 생성 실패: ${userData.login_id}`);
        }
    } catch (error) {
        print(`❌ 사용자 생성 오류 (${userData.login_id}): ${error.message}`);
    }
});

// 최종 사용자 수 확인
const finalCount = db.users.countDocuments({});
print(`\n📊 최종 사용자 수: ${finalCount}명`);
print(`🆕 생성된 사용자 수: ${createdCount}명`);
print(`⚠️  건너뛴 사용자 수: ${skippedCount}명`);

// 역할별 사용자 수 확인
print("\n📋 역할별 사용자 현황:");
const roles = ['admin', 'secretary', 'evaluator'];
roles.forEach(role => {
    const count = db.users.countDocuments({"role": role});
    print(`  - ${role}: ${count}명`);
});

// 테스트용 로그인 정보 출력
print("\n🔑 테스트 계정 정보:");
print("=================================");
print("관리자 계정:");
print("  ID: admin, PW: admin123");
print("\n비서 계정:");
print("  ID: secretary01, PW: secretary123");
print("  ID: secretary02, PW: secretary123");
print("\n평가자 계정:");
print("  ID: evaluator01, PW: evaluator123");
print("  ID: evaluator02, PW: evaluator123");
print("  ID: evaluator03, PW: evaluator123");
print("  ID: evaluator04, PW: evaluator123");
print("  ID: evaluator05, PW: evaluator123");
print("=================================");

print("\n✅ 테스트 사용자 생성 완료!");
