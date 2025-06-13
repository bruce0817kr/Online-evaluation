// MongoDB 패스워드 해시 수정 스크립트
// 올바른 bcrypt 해시로 사용자 비밀번호를 업데이트합니다.

// 온라인 평가 데이터베이스 선택
db = db.getSiblingDB('online_evaluation');

print("🔧 패스워드 해시 수정 시작...");

// 수정할 사용자들과 올바른 해시
const userUpdates = [
    {
        login_id: "admin",
        password_hash: "$2b$12$aDr0uWYIttEbKZs/YEgEou7IpYar6QMrPw5oJjnQoLyT4Z5D/HT6K"
    },
    {
        login_id: "secretary01", 
        password_hash: "$2b$12$vLWDmfG5/Eo0sonS/lZhcujqhXVTBBTGAPuM9UFEDVfGoPzhhusJ."
    },
    {
        login_id: "secretary02",
        password_hash: "$2b$12$8jOy63VQaFnFEe26lEWPA.spOBDeaSzUpjsp5HlyfgSy4vdMfXwva"
    },
    {
        login_id: "evaluator01",
        password_hash: "$2b$12$83tpYH.2OCOym8sVa8AMFegy65gZgdBJnO9X5QJR7tO1fn0dTuz0i"
    },
    {
        login_id: "evaluator02",
        password_hash: "$2b$12$GevNpd7NM9.frSt3l957i.SZhTh8tFfIBmKgXDRHz.jJ5dbF.i5Pq"
    },
    {
        login_id: "evaluator03",
        password_hash: "$2b$12$5DcAQ0gw.nPeVN7vMFSlr.zuPFIovzTW/i89T1FROcLHY.DqssfUm"
    },
    {
        login_id: "evaluator04",
        password_hash: "$2b$12$BerZdJJzQiZVhpESBZPJj.xSrAi9Dv58./oSNynbT8HwmZZP8C/Iq"
    },
    {
        login_id: "evaluator05",
        password_hash: "$2b$12$B.fHr01PeSIu0YC6Jzq3s.G9RWwKgGxIHlOJUc9XQD10FiQWDAupy"
    }
];

let updatedCount = 0;

userUpdates.forEach(function(user) {
    print(`📝 ${user.login_id} 패스워드 해시 업데이트 중...`);
    
    const result = db.users.updateOne(
        { login_id: user.login_id },
        { 
            $set: { 
                password_hash: user.password_hash,
                updated_at: new Date()
            }
        }
    );
    
    if (result.modifiedCount > 0) {
        print(`✅ ${user.login_id} 업데이트 완료`);
        updatedCount++;
    } else {
        print(`❌ ${user.login_id} 업데이트 실패`);
    }
});

print(`\n✅ 총 ${updatedCount}명의 사용자 패스워드 해시가 업데이트되었습니다.`);

// 업데이트 검증
print("\n🔍 업데이트된 해시 길이 검증:");
db.users.find({}, {login_id: 1, password_hash: 1}).forEach(function(user) {
    print(`${user.login_id}: 해시 길이 ${user.password_hash.length}`);
});

print("\n🎉 패스워드 해시 수정 완료!");
