// mongosh 전용 관리자 계정 생성 스크립트
const adminUser = {
  id: 'admin-0001',
  login_id: 'admin',
  password_hash: '$2b$12$3j8IH7Fbs7Il8NzyEh8IyO2uWvaFYz2r6XVzoplG9ACakJIhvUVp6',
  user_name: '관리자',
  email: 'admin@test.com',
  phone: '010-0000-0000',
  role: 'admin',
  created_at: new Date(),
  is_active: true
};

const exists = db.users.findOne({ login_id: 'admin' });
if (!exists) {
  db.users.insertOne(adminUser);
  print('테스트용 관리자 계정 생성 완료');
} else {
  print('관리자 계정 이미 존재');
}
