#!/bin/bash

# 테스트 사용자 생성 스크립트
echo "🔧 테스트 사용자 계정 생성 중..."

# MongoDB 컨테이너에서 계정 생성
docker exec online-evaluation-mongodb-prod mongosh -u admin -p password123 --authenticationDatabase admin --eval "
use online_evaluation;

// 기존 테스트 계정 삭제 (있다면)
db.users.deleteMany({login_id: {$in: ['secretary', 'evaluator']}});

// secretary 계정 생성
db.users.insertOne({
  login_id: 'secretary',
  password: '\$2a\$10\$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', // password
  user_name: '테스트 간사',
  email: 'secretary@test.com',
  role: 'secretary',
  is_active: true,
  created_at: new Date(),
  last_login: null
});

// evaluator 계정 생성  
db.users.insertOne({
  login_id: 'evaluator',
  password: '\$2a\$10\$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', // password
  user_name: '테스트 평가위원',
  email: 'evaluator@test.com', 
  role: 'evaluator',
  is_active: true,
  created_at: new Date(),
  last_login: null
});

print('✅ 테스트 사용자 생성 완료');
"

echo "✅ 테스트 계정 생성 완료"