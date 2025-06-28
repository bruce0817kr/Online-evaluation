/**
 * 간단한 사용자 역할별 테스트 (Puppeteer 미설치 환경용)
 */

const http = require('http');
const https = require('https');
const fs = require('fs');
const path = require('path');

const TEST_CONFIG = {
  baseUrl: 'http://localhost:3019',
  apiUrl: 'http://localhost:8019',
  reportDir: path.join(__dirname, 'test-reports', new Date().toISOString().split('T')[0])
};

// 테스트 사용자 정보
const USERS = [
  {
    username: 'admin',
    password: 'admin123',
    role: 'admin',
    testName: '관리자'
  },
  {
    username: 'secretary',
    password: 'secretary123',
    role: 'secretary',
    testName: '간사'
  }
];

// 리포트 저장용
const testReport = {
  startTime: new Date(),
  results: []
};

// 리포트 디렉토리 생성
function ensureReportDir() {
  if (!fs.existsSync(TEST_CONFIG.reportDir)) {
    fs.mkdirSync(TEST_CONFIG.reportDir, { recursive: true });
  }
}

// HTTP 요청 헬퍼
function makeRequest(options, data = null) {
  return new Promise((resolve, reject) => {
    const protocol = options.url.startsWith('https') ? https : http;
    const url = new URL(options.url);
    
    const reqOptions = {
      hostname: url.hostname,
      port: url.port,
      path: url.pathname + url.search,
      method: options.method || 'GET',
      headers: options.headers || {}
    };
    
    const req = protocol.request(reqOptions, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => {
        resolve({
          status: res.statusCode,
          headers: res.headers,
          body: body
        });
      });
    });
    
    req.on('error', reject);
    
    if (data) {
      req.write(data);
    }
    
    req.end();
  });
}

// 로그인 테스트
async function testLogin(user) {
  console.log(`\n🔐 ${user.testName} 로그인 테스트...`);
  
  try {
    const response = await makeRequest({
      url: `${TEST_CONFIG.apiUrl}/api/auth/login`,
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    }, `username=${user.username}&password=${user.password}`);
    
    if (response.status === 200) {
      const data = JSON.parse(response.body);
      if (data.access_token) {
        console.log(`✅ ${user.testName} 로그인 성공`);
        testReport.results.push({
          user: user.testName,
          test: '로그인',
          status: 'passed',
          token: data.access_token
        });
        return data.access_token;
      }
    }
    
    throw new Error(`로그인 실패: ${response.status}`);
  } catch (error) {
    console.error(`❌ ${user.testName} 로그인 실패:`, error.message);
    testReport.results.push({
      user: user.testName,
      test: '로그인',
      status: 'failed',
      error: error.message
    });
    return null;
  }
}

// API 엔드포인트 테스트
async function testApiEndpoints(user, token) {
  console.log(`\n📡 ${user.testName} API 엔드포인트 테스트...`);
  
  const endpoints = {
    admin: [
      { name: '사용자 목록', path: '/api/users' },
      { name: '프로젝트 목록', path: '/api/projects' },
      { name: '템플릿 목록', path: '/api/templates' },
      { name: 'AI 공급자 목록', path: '/api/admin/ai/providers' },
      { name: 'AI 모델 목록', path: '/api/ai-models/models' },
      { name: '배포 상태', path: '/api/deployment/status' }
    ],
    secretary: [
      { name: '프로젝트 목록', path: '/api/projects' },
      { name: '템플릿 목록', path: '/api/templates' },
      { name: '평가표 출력', path: '/api/evaluations/print' },
      { name: '평가 목록', path: '/api/evaluations' }
    ]
  };
  
  const userEndpoints = endpoints[user.role] || [];
  
  for (const endpoint of userEndpoints) {
    try {
      const response = await makeRequest({
        url: `${TEST_CONFIG.apiUrl}${endpoint.path}`,
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.status < 400) {
        console.log(`✅ ${endpoint.name}: ${response.status} OK`);
        testReport.results.push({
          user: user.testName,
          test: `API - ${endpoint.name}`,
          status: 'passed',
          statusCode: response.status
        });
      } else {
        throw new Error(`Status ${response.status}`);
      }
    } catch (error) {
      console.error(`❌ ${endpoint.name}: 실패 - ${error.message}`);
      testReport.results.push({
        user: user.testName,
        test: `API - ${endpoint.name}`,
        status: 'failed',
        error: error.message
      });
    }
  }
}

// 권한 테스트
async function testPermissions(user, token) {
  console.log(`\n🔒 ${user.testName} 권한 테스트...`);
  
  const restrictedEndpoints = {
    secretary: [
      { name: '사용자 관리 (거부되어야 함)', path: '/api/users', method: 'POST' },
      { name: 'AI 공급자 관리 (거부되어야 함)', path: '/api/admin/ai/providers' }
    ]
  };
  
  const tests = restrictedEndpoints[user.role] || [];
  
  for (const test of tests) {
    try {
      const response = await makeRequest({
        url: `${TEST_CONFIG.apiUrl}${test.path}`,
        method: test.method || 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.status === 403 || response.status === 401) {
        console.log(`✅ ${test.name}: 정상적으로 거부됨 (${response.status})`);
        testReport.results.push({
          user: user.testName,
          test: `권한 - ${test.name}`,
          status: 'passed',
          note: '접근 거부 확인'
        });
      } else {
        throw new Error(`예상치 못한 접근 허용: ${response.status}`);
      }
    } catch (error) {
      if (error.message.includes('예상치 못한')) {
        console.error(`❌ ${test.name}: ${error.message}`);
        testReport.results.push({
          user: user.testName,
          test: `권한 - ${test.name}`,
          status: 'failed',
          error: error.message
        });
      }
    }
  }
}

// 메인 테스트 함수
async function runTests() {
  console.log('🚀 온라인 평가 시스템 사용자 역할별 API 테스트\n');
  console.log(`📍 API URL: ${TEST_CONFIG.apiUrl}`);
  console.log(`📄 리포트 저장 경로: ${TEST_CONFIG.reportDir}\n`);
  
  ensureReportDir();
  
  for (const user of USERS) {
    console.log(`\n${'='.repeat(50)}`);
    console.log(`👤 ${user.testName} (${user.username}) 테스트`);
    console.log(`${'='.repeat(50)}`);
    
    // 1. 로그인 테스트
    const token = await testLogin(user);
    
    if (token) {
      // 2. API 엔드포인트 테스트
      await testApiEndpoints(user, token);
      
      // 3. 권한 테스트
      await testPermissions(user, token);
    }
  }
  
  // 리포트 생성
  generateReport();
}

// 리포트 생성
function generateReport() {
  testReport.endTime = new Date();
  const duration = (testReport.endTime - testReport.startTime) / 1000;
  
  const passed = testReport.results.filter(r => r.status === 'passed').length;
  const failed = testReport.results.filter(r => r.status === 'failed').length;
  
  console.log('\n' + '='.repeat(70));
  console.log('📊 테스트 결과 요약');
  console.log('='.repeat(70));
  console.log(`\n⏱️  실행 시간: ${duration.toFixed(2)}초`);
  console.log(`✅ 성공: ${passed}개`);
  console.log(`❌ 실패: ${failed}개`);
  console.log(`📈 성공률: ${((passed / (passed + failed)) * 100).toFixed(2)}%\n`);
  
  // 상세 결과
  const userGroups = {};
  testReport.results.forEach(result => {
    if (!userGroups[result.user]) {
      userGroups[result.user] = [];
    }
    userGroups[result.user].push(result);
  });
  
  Object.entries(userGroups).forEach(([user, results]) => {
    console.log(`\n👤 ${user} 테스트 결과:`);
    results.forEach(result => {
      const icon = result.status === 'passed' ? '✅' : '❌';
      const detail = result.error || result.note || result.statusCode || '';
      console.log(`  ${icon} ${result.test}${detail ? `: ${detail}` : ''}`);
    });
  });
  
  // JSON 리포트 저장
  const reportPath = path.join(TEST_CONFIG.reportDir, 'api_test_report.json');
  fs.writeFileSync(reportPath, JSON.stringify(testReport, null, 2));
  console.log(`\n📄 상세 리포트 저장됨: ${reportPath}`);
}

// 테스트 실행
runTests().catch(console.error);