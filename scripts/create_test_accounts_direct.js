// 테스트 계정 생성 스크립트 (MongoDB 컨테이너 내부 실행용)

// 데이터베이스 선택
db = db.getSiblingDB('online_evaluation');

// bcrypt 해시 생성 (secretary123, evaluator123)
// 이 해시들은 bcrypt로 미리 생성된 값입니다
const secretaryHash = '$2a$10$YourHashHere'; // secretary123
const evaluatorHash = '$2a$10$YourHashHere'; // evaluator123

// 테스트 계정 생성
const testAccounts = [
  {
    login_id: 'secretary',
    password: '$2a$10$kJNJcVBqK2tqoQ.gE9CbbuQAoKCXc1.1L3UqvZ6tgKwxrJgDnJEZy', // secretary123
    user_name: '테스트 간사',
    email: 'secretary@test.com',
    role: 'secretary',
    is_active: true,
    created_at: new Date(),
    last_login: null
  },
  {
    login_id: 'evaluator',
    password: '$2a$10$J9b8VqGfzR6sL0mYBKrJMuFtAJxK3bGYLJxrKVoMhHiRPLKx5cQfK', // evaluator123
    user_name: '테스트 평가위원',
    email: 'evaluator@test.com',
    role: 'evaluator',
    is_active: true,
    created_at: new Date(),
    last_login: null
  }
];

// 계정 생성
testAccounts.forEach(account => {
  const existing = db.users.findOne({ login_id: account.login_id });
  if (!existing) {
    db.users.insertOne(account);
    print(`✅ ${account.login_id} (${account.role}) 계정 생성 완료`);
  } else {
    print(`${account.login_id} 계정이 이미 존재합니다.`);
  }
});

print('\n모든 테스트 계정 생성 완료!');