/**
 * 최종 자동화 테스트 - Rate Limit 대응
 */

const http = require('http');
const fs = require('fs');
const path = require('path');

const CONFIG = {
  baseUrl: 'http://localhost:3019',
  apiUrl: 'http://localhost:8019',
  reportDir: path.join(__dirname, 'test-reports', new Date().toISOString().split('T')[0]),
  requestDelay: 2000 // Rate limit 방지용 지연
};

const USERS = [
  { username: 'admin', password: 'admin123', role: 'admin', name: '시스템 관리자' },
  { username: 'secretary', password: 'password', role: 'secretary', name: '간사' },
  { username: 'evaluator', password: 'password', role: 'evaluator', name: '평가위원' }
];

const testResults = {
  timestamp: new Date().toISOString(),
  results: [],
  summary: { total: 0, passed: 0, failed: 0 }
};

function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function makeRequest(options, data = null) {
  return new Promise((resolve, reject) => {
    const url = new URL(options.url);
    const reqOptions = {
      hostname: url.hostname,
      port: url.port,
      path: url.pathname,
      method: options.method || 'GET',
      headers: options.headers || {}
    };

    const req = http.request(reqOptions, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => resolve({ status: res.statusCode, body }));
    });

    req.on('error', reject);
    if (data) req.write(data);
    req.end();
  });
}

async function testUser(user) {
  console.log(`\n🔐 ${user.name} 테스트 시작...`);
  
  try {
    // 지연 추가
    await delay(CONFIG.requestDelay);
    
    // 로그인 테스트
    const loginResponse = await makeRequest({
      url: `${CONFIG.apiUrl}/api/auth/login`,
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    }, `username=${user.username}&password=${user.password}`);

    if (loginResponse.status === 200) {
      const data = JSON.parse(loginResponse.body);
      console.log(`✅ ${user.name} 로그인 성공`);
      
      // API 테스트
      const token = data.access_token;
      await delay(500);
      
      const profileResponse = await makeRequest({
        url: `${CONFIG.apiUrl}/api/auth/me`,
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (profileResponse.status === 200) {
        console.log(`✅ ${user.name} 프로필 조회 성공`);
        testResults.results.push({
          user: user.name,
          login: 'success',
          profile: 'success',
          role: user.role
        });
        testResults.summary.passed += 2;
      } else {
        throw new Error('프로필 조회 실패');
      }
    } else {
      throw new Error(`로그인 실패: ${loginResponse.status}`);
    }
  } catch (error) {
    console.log(`❌ ${user.name} 테스트 실패: ${error.message}`);
    testResults.results.push({
      user: user.name,
      login: 'failed',
      error: error.message,
      role: user.role
    });
    testResults.summary.failed++;
  }
  
  testResults.summary.total++;
}

async function runFinalTest() {
  console.log('🚀 최종 자동화 테스트 실행\n');
  
  if (!fs.existsSync(CONFIG.reportDir)) {
    fs.mkdirSync(CONFIG.reportDir, { recursive: true });
  }

  for (const user of USERS) {
    await testUser(user);
  }

  // 리포트 생성
  console.log('\n' + '='.repeat(60));
  console.log('📊 최종 테스트 결과');
  console.log('='.repeat(60));
  
  const successRate = (testResults.summary.passed / (testResults.summary.passed + testResults.summary.failed) * 100).toFixed(1);
  
  console.log(`✅ 성공: ${testResults.summary.passed}개`);
  console.log(`❌ 실패: ${testResults.summary.failed}개`);
  console.log(`📈 성공률: ${successRate}%\n`);

  testResults.results.forEach(result => {
    console.log(`👤 ${result.user} (${result.role}): ${result.login === 'success' ? '✅' : '❌'}`);
  });

  const reportPath = path.join(CONFIG.reportDir, 'final_test_report.json');
  fs.writeFileSync(reportPath, JSON.stringify(testResults, null, 2));
  console.log(`\n📄 리포트 저장: ${reportPath}`);
}

runFinalTest().catch(console.error);