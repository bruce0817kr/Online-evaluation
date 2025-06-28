/**
 * E2E 테스트를 위한 사용자 계정 생성 스크립트
 */

const { MongoClient } = require('mongodb');
const bcrypt = require('bcryptjs');

const MONGO_URL = process.env.MONGO_URL || 'mongodb://localhost:27036/online_evaluation';

async function createTestAccounts() {
  const client = new MongoClient(MONGO_URL);
  
  try {
    await client.connect();
    console.log('MongoDB 연결 성공');
    
    const db = client.db('online_evaluation');
    const users = db.collection('users');
    
    // 테스트 계정 정보
    const testAccounts = [
      {
        login_id: 'secretary',
        password: 'secretary123',
        user_name: '테스트 간사',
        email: 'secretary@test.com',
        role: 'secretary',
        is_active: true,
        created_at: new Date()
      },
      {
        login_id: 'evaluator',
        password: 'evaluator123',
        user_name: '테스트 평가위원',
        email: 'evaluator@test.com',
        role: 'evaluator',
        is_active: true,
        created_at: new Date()
      }
    ];
    
    // 계정 생성
    for (const account of testAccounts) {
      // 기존 계정 확인
      const existing = await users.findOne({ login_id: account.login_id });
      
      if (existing) {
        console.log(`${account.login_id} 계정이 이미 존재합니다.`);
        continue;
      }
      
      // 비밀번호 해시
      const hashedPassword = await bcrypt.hash(account.password, 10);
      account.password = hashedPassword;
      
      // 계정 생성
      await users.insertOne(account);
      console.log(`✅ ${account.login_id} (${account.role}) 계정 생성 완료`);
    }
    
    console.log('\n모든 테스트 계정 생성 완료!');
    
  } catch (error) {
    console.error('오류 발생:', error);
  } finally {
    await client.close();
  }
}

// 스크립트 실행
createTestAccounts();