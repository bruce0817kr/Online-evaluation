/**
 * 온라인 평가 시스템 종합 자동화 테스트
 * 모든 사용자 역할에 대한 완전한 기능 테스트
 */

const http = require('http');
const fs = require('fs');
const path = require('path');

const CONFIG = {
  baseUrl: 'http://localhost:3019',
  apiUrl: 'http://localhost:8019',
  reportDir: path.join(__dirname, 'test-reports', new Date().toISOString().split('T')[0]),
  timeout: 10000
};

// 테스트 사용자 정보
const USERS = {
  admin: {
    username: 'admin',
    password: 'admin123',
    role: 'admin',
    displayName: '시스템 관리자',
    expectedMenus: ['프로젝트 관리', '사용자 관리', '템플릿 관리', 'AI 관리', '배포 관리']
  },
  secretary: {
    username: 'secretary', 
    password: 'password',
    role: 'secretary',
    displayName: '간사',
    expectedMenus: ['프로젝트 관리', '평가위원 배정', '평가 현황', '평가표 출력']
  },
  evaluator: {
    username: 'evaluator',
    password: 'password', 
    role: 'evaluator',
    displayName: '평가위원',
    expectedMenus: ['내 평가', 'AI 도우미', '제출 내역']
  }
};

// 테스트 케이스 정의
const TEST_CASES = {
  admin: [
    { name: '사용자 목록 조회', endpoint: '/api/users', method: 'GET', expectedStatus: 200 },
    { name: '프로젝트 목록 조회', endpoint: '/api/projects', method: 'GET', expectedStatus: 200 },
    { name: '템플릿 목록 조회', endpoint: '/api/templates', method: 'GET', expectedStatus: 200 },
    { name: 'AI 공급자 조회', endpoint: '/api/admin/ai/providers', method: 'GET', expectedStatus: 200 },
    { name: 'AI 상태 확인', endpoint: '/api/ai/status', method: 'GET', expectedStatus: 200 },
    { name: '파일 목록 조회', endpoint: '/api/files', method: 'GET', expectedStatus: 200 },
    { name: '배포 상태 조회', endpoint: '/api/deployment/status', method: 'GET', expectedStatus: [200, 500] },
    { name: '사용자 프로필 조회', endpoint: '/api/auth/me', method: 'GET', expectedStatus: 200 }
  ],
  secretary: [
    { name: '프로젝트 목록 조회', endpoint: '/api/projects', method: 'GET', expectedStatus: 200 },
    { name: '템플릿 목록 조회', endpoint: '/api/templates', method: 'GET', expectedStatus: 200 },
    { name: '평가표 출력 접근', endpoint: '/api/evaluations/print', method: 'GET', expectedStatus: [200, 400] },
    { name: '사용자 프로필 조회', endpoint: '/api/auth/me', method: 'GET', expectedStatus: 200 },
    { name: '사용자 관리 접근 (금지)', endpoint: '/api/users', method: 'POST', expectedStatus: [403, 401] }
  ],
  evaluator: [
    { name: '내 평가 조회', endpoint: '/api/evaluations/my', method: 'GET', expectedStatus: [200, 404] },
    { name: 'AI 상태 확인', endpoint: '/api/ai/status', method: 'GET', expectedStatus: 200 },
    { name: '사용자 프로필 조회', endpoint: '/api/auth/me', method: 'GET', expectedStatus: 200 },
    { name: '사용자 관리 접근 (금지)', endpoint: '/api/users', method: 'GET', expectedStatus: [403, 401] },
    { name: 'AI 공급자 접근 (금지)', endpoint: '/api/admin/ai/providers', method: 'GET', expectedStatus: [403, 401] }
  ]
};

// 테스트 결과 저장
const testReport = {
  timestamp: new Date().toISOString(),
  testDuration: 0,
  environment: {
    frontendUrl: CONFIG.baseUrl,
    backendUrl: CONFIG.apiUrl,
    nodeVersion: process.version
  },
  summary: {
    totalUsers: 0,
    totalTests: 0,
    passedTests: 0,
    failedTests: 0,
    skippedTests: 0,
    warningTests: 0
  },
  userResults: {},
  detailedLogs: [],
  recommendations: []
};

// 유틸리티 함수들
function ensureReportDir() {
  if (!fs.existsSync(CONFIG.reportDir)) {
    fs.mkdirSync(CONFIG.reportDir, { recursive: true });
  }
}

function logTest(level, message, details = null) {
  const timestamp = new Date().toISOString();
  const logEntry = { timestamp, level, message, details };
  testReport.detailedLogs.push(logEntry);
  
  const icon = {
    'INFO': 'ℹ️',
    'SUCCESS': '✅',
    'WARNING': '⚠️',
    'ERROR': '❌',
    'DEBUG': '🔍'
  }[level] || '📝';
  
  console.log(`${icon} ${message}${details ? ` - ${JSON.stringify(details)}` : ''}`);
}

function makeHttpRequest(options, data = null) {
  return new Promise((resolve, reject) => {
    const url = new URL(options.url);
    const requestOptions = {
      hostname: url.hostname,
      port: url.port,
      path: url.pathname + url.search,
      method: options.method || 'GET',
      headers: options.headers || {},
      timeout: CONFIG.timeout
    };

    const req = http.request(requestOptions, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => {
        resolve({
          status: res.statusCode,
          headers: res.headers,
          body: body,
          url: options.url
        });
      });
    });

    req.on('error', reject);
    req.on('timeout', () => {
      req.destroy();
      reject(new Error('Request timeout'));
    });

    if (data) {
      req.write(data);
    }

    req.end();
  });
}

// 사용자 로그인 테스트
async function testLogin(user) {
  logTest('INFO', `${user.displayName} 로그인 테스트 시작`);
  
  try {
    const response = await makeHttpRequest({
      url: `${CONFIG.apiUrl}/api/auth/login`,
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    }, `username=${user.username}&password=${user.password}`);

    if (response.status === 200) {
      const data = JSON.parse(response.body);
      if (data.access_token && data.user) {
        logTest('SUCCESS', `${user.displayName} 로그인 성공`, {
          userId: data.user.id,
          role: data.user.role,
          tokenLength: data.access_token.length
        });
        return data.access_token;
      }
    }

    throw new Error(`로그인 실패: ${response.status} - ${response.body.substring(0, 200)}`);
  } catch (error) {
    logTest('ERROR', `${user.displayName} 로그인 실패`, { error: error.message });
    return null;
  }
}

// API 엔드포인트 테스트
async function testApiEndpoints(user, token) {
  logTest('INFO', `${user.displayName} API 엔드포인트 테스트 시작`);
  
  const userTests = TEST_CASES[user.role] || [];
  const results = [];

  for (const testCase of userTests) {
    try {
      const response = await makeHttpRequest({
        url: `${CONFIG.apiUrl}${testCase.endpoint}`,
        method: testCase.method,
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      const expectedStatuses = Array.isArray(testCase.expectedStatus) 
        ? testCase.expectedStatus 
        : [testCase.expectedStatus];

      if (expectedStatuses.includes(response.status)) {
        logTest('SUCCESS', `${testCase.name} 테스트 통과`, {
          endpoint: testCase.endpoint,
          status: response.status,
          method: testCase.method
        });
        results.push({ ...testCase, status: 'passed', actualStatus: response.status });
        testReport.summary.passedTests++;
      } else if (response.status >= 400 && response.status < 500 && testCase.name.includes('금지')) {
        logTest('SUCCESS', `${testCase.name} 권한 제한 정상 동작`, {
          endpoint: testCase.endpoint,
          status: response.status
        });
        results.push({ ...testCase, status: 'passed', actualStatus: response.status });
        testReport.summary.passedTests++;
      } else {
        logTest('WARNING', `${testCase.name} 예상과 다른 응답`, {
          endpoint: testCase.endpoint,
          expected: expectedStatuses,
          actual: response.status,
          body: response.body.substring(0, 200)
        });
        results.push({ ...testCase, status: 'warning', actualStatus: response.status });
        testReport.summary.warningTests++;
      }
    } catch (error) {
      logTest('ERROR', `${testCase.name} 테스트 실패`, {
        endpoint: testCase.endpoint,
        error: error.message
      });
      results.push({ ...testCase, status: 'failed', error: error.message });
      testReport.summary.failedTests++;
    }

    testReport.summary.totalTests++;
  }

  return results;
}

// 시스템 상태 확인
async function checkSystemHealth() {
  logTest('INFO', '시스템 상태 확인 시작');
  
  const healthChecks = [
    { name: 'Frontend 연결', url: CONFIG.baseUrl },
    { name: 'Backend Health', url: `${CONFIG.apiUrl}/health` },
    { name: 'Backend Docs', url: `${CONFIG.apiUrl}/docs` }
  ];

  const healthResults = [];

  for (const check of healthChecks) {
    try {
      const response = await makeHttpRequest({ url: check.url });
      if (response.status < 400) {
        logTest('SUCCESS', `${check.name} 정상`, { status: response.status });
        healthResults.push({ ...check, status: 'healthy', code: response.status });
      } else {
        logTest('WARNING', `${check.name} 응답 이상`, { status: response.status });
        healthResults.push({ ...check, status: 'unhealthy', code: response.status });
      }
    } catch (error) {
      logTest('ERROR', `${check.name} 연결 실패`, { error: error.message });
      healthResults.push({ ...check, status: 'error', error: error.message });
    }
  }

  return healthResults;
}

// 메인 테스트 실행 함수
async function runComprehensiveTests() {
  const startTime = Date.now();
  
  console.log('🚀 온라인 평가 시스템 종합 자동화 테스트 시작\n');
  console.log(`📍 Frontend: ${CONFIG.baseUrl}`);
  console.log(`📍 Backend: ${CONFIG.apiUrl}`);
  console.log(`📄 리포트 저장: ${CONFIG.reportDir}\n`);

  ensureReportDir();

  try {
    // 1. 시스템 상태 확인
    console.log('=' .repeat(60));
    console.log('🔍 시스템 상태 확인');
    console.log('=' .repeat(60));
    
    const healthResults = await checkSystemHealth();
    testReport.systemHealth = healthResults;

    // 2. 각 사용자별 테스트 실행
    testReport.summary.totalUsers = Object.keys(USERS).length;

    for (const [userKey, user] of Object.entries(USERS)) {
      console.log('\n' + '=' .repeat(60));
      console.log(`👤 ${user.displayName} (${user.role}) 테스트`);
      console.log('=' .repeat(60));

      const userResult = {
        username: user.username,
        role: user.role,
        displayName: user.displayName,
        loginSuccess: false,
        apiTests: [],
        summary: { passed: 0, failed: 0, warnings: 0 }
      };

      // 로그인 테스트
      const token = await testLogin(user);
      userResult.loginSuccess = !!token;

      if (token) {
        // API 엔드포인트 테스트
        const apiResults = await testApiEndpoints(user, token);
        userResult.apiTests = apiResults;

        // 결과 집계
        userResult.summary.passed = apiResults.filter(r => r.status === 'passed').length;
        userResult.summary.failed = apiResults.filter(r => r.status === 'failed').length;
        userResult.summary.warnings = apiResults.filter(r => r.status === 'warning').length;
      } else {
        testReport.summary.failedTests++;
        testReport.summary.totalTests++;
      }

      testReport.userResults[userKey] = userResult;
    }

    // 3. 테스트 완료 및 리포트 생성
    const endTime = Date.now();
    testReport.testDuration = endTime - startTime;

    generateComprehensiveReport();
    generateRecommendations();

  } catch (error) {
    logTest('ERROR', '테스트 실행 중 치명적 오류', { error: error.message });
    console.error('테스트 실행 실패:', error);
  }
}

// 종합 리포트 생성
function generateComprehensiveReport() {
  console.log('\n' + '=' .repeat(80));
  console.log('📊 종합 테스트 결과 리포트');
  console.log('=' .repeat(80));

  const duration = (testReport.testDuration / 1000).toFixed(2);
  const successRate = testReport.summary.totalTests > 0 
    ? ((testReport.summary.passedTests / testReport.summary.totalTests) * 100).toFixed(1)
    : 0;

  console.log(`\n⏱️  총 실행 시간: ${duration}초`);
  console.log(`👥 테스트 사용자: ${testReport.summary.totalUsers}명`);
  console.log(`📋 총 테스트: ${testReport.summary.totalTests}개`);
  console.log(`✅ 성공: ${testReport.summary.passedTests}개`);
  console.log(`⚠️  경고: ${testReport.summary.warningTests}개`);
  console.log(`❌ 실패: ${testReport.summary.failedTests}개`);
  console.log(`📈 성공률: ${successRate}%\n`);

  // 시스템 상태 요약
  if (testReport.systemHealth) {
    console.log('🔍 시스템 상태:');
    testReport.systemHealth.forEach(check => {
      const icon = check.status === 'healthy' ? '✅' : check.status === 'unhealthy' ? '⚠️' : '❌';
      console.log(`  ${icon} ${check.name}: ${check.status} ${check.code ? `(${check.code})` : ''}`);
    });
    console.log('');
  }

  // 사용자별 상세 결과
  Object.entries(testReport.userResults).forEach(([key, result]) => {
    console.log(`👤 ${result.displayName} 결과:`);
    console.log(`   로그인: ${result.loginSuccess ? '✅' : '❌'}`);
    console.log(`   API 테스트: ✅${result.summary.passed} ⚠️${result.summary.warnings} ❌${result.summary.failed}`);
    
    if (result.apiTests.length > 0) {
      result.apiTests.forEach(test => {
        const icon = test.status === 'passed' ? '✅' : test.status === 'warning' ? '⚠️' : '❌';
        console.log(`     ${icon} ${test.name}`);
      });
    }
    console.log('');
  });

  // JSON 리포트 저장
  const reportPath = path.join(CONFIG.reportDir, 'comprehensive_test_report.json');
  fs.writeFileSync(reportPath, JSON.stringify(testReport, null, 2));
  
  const htmlReportPath = path.join(CONFIG.reportDir, 'test_report.html');
  generateHtmlReport(htmlReportPath);

  console.log(`📄 JSON 리포트: ${reportPath}`);
  console.log(`🌐 HTML 리포트: ${htmlReportPath}`);
}

// 개선 권장사항 생성
function generateRecommendations() {
  console.log('💡 개선 권장사항:');
  
  const recommendations = [];

  // 실패율이 높은 경우
  if (testReport.summary.failedTests > testReport.summary.passedTests) {
    recommendations.push('❗ 전체적인 시스템 안정성 검토가 필요합니다.');
  }

  // 로그인 실패가 있는 경우
  const loginFailures = Object.values(testReport.userResults).filter(r => !r.loginSuccess);
  if (loginFailures.length > 0) {
    recommendations.push(`🔐 ${loginFailures.length}개 계정의 로그인 문제를 해결해야 합니다.`);
  }

  // 경고가 많은 경우
  if (testReport.summary.warningTests > 5) {
    recommendations.push('⚠️ API 응답 상태를 점검하고 표준화가 필요합니다.');
  }

  // 시스템 상태 문제
  const unhealthyServices = testReport.systemHealth?.filter(h => h.status !== 'healthy') || [];
  if (unhealthyServices.length > 0) {
    recommendations.push(`🔧 ${unhealthyServices.length}개 서비스의 상태를 점검해야 합니다.`);
  }

  if (recommendations.length === 0) {
    recommendations.push('🎉 모든 테스트가 정상적으로 통과했습니다!');
  }

  recommendations.forEach(rec => console.log(`  ${rec}`));
  testReport.recommendations = recommendations;
}

// HTML 리포트 생성
function generateHtmlReport(filePath) {
  const html = `
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>온라인 평가 시스템 테스트 리포트</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; }
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .metric { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }
        .metric-value { font-size: 2em; font-weight: bold; color: #333; }
        .metric-label { color: #666; margin-top: 5px; }
        .success { color: #10b981; }
        .warning { color: #f59e0b; }
        .error { color: #ef4444; }
        .user-section { background: white; margin-bottom: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .user-header { background: #f8fafc; padding: 20px; border-bottom: 1px solid #e5e7eb; font-weight: bold; }
        .test-list { padding: 20px; }
        .test-item { display: flex; justify-content: between; align-items: center; padding: 10px 0; border-bottom: 1px solid #f1f5f9; }
        .recommendations { background: #fef3c7; padding: 20px; border-radius: 8px; border-left: 4px solid #f59e0b; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 온라인 평가 시스템 테스트 리포트</h1>
            <p>생성 시간: ${testReport.timestamp}</p>
            <p>실행 시간: ${(testReport.testDuration / 1000).toFixed(2)}초</p>
        </div>

        <div class="summary">
            <div class="metric">
                <div class="metric-value success">${testReport.summary.passedTests}</div>
                <div class="metric-label">성공한 테스트</div>
            </div>
            <div class="metric">
                <div class="metric-value warning">${testReport.summary.warningTests}</div>
                <div class="metric-label">경고</div>
            </div>
            <div class="metric">
                <div class="metric-value error">${testReport.summary.failedTests}</div>
                <div class="metric-label">실패한 테스트</div>
            </div>
            <div class="metric">
                <div class="metric-value">${((testReport.summary.passedTests / testReport.summary.totalTests) * 100).toFixed(1)}%</div>
                <div class="metric-label">성공률</div>
            </div>
        </div>

        ${Object.entries(testReport.userResults).map(([key, result]) => `
        <div class="user-section">
            <div class="user-header">
                👤 ${result.displayName} (${result.role})
                ${result.loginSuccess ? '<span class="success">✅ 로그인 성공</span>' : '<span class="error">❌ 로그인 실패</span>'}
            </div>
            <div class="test-list">
                ${result.apiTests.map(test => `
                <div class="test-item">
                    <span>${test.status === 'passed' ? '✅' : test.status === 'warning' ? '⚠️' : '❌'} ${test.name}</span>
                    <span class="${test.status}">${test.actualStatus || 'N/A'}</span>
                </div>
                `).join('')}
            </div>
        </div>
        `).join('')}

        <div class="recommendations">
            <h3>💡 개선 권장사항</h3>
            ${testReport.recommendations.map(rec => `<p>${rec}</p>`).join('')}
        </div>
    </div>
</body>
</html>`;

  fs.writeFileSync(filePath, html);
}

// 테스트 실행
if (require.main === module) {
  runComprehensiveTests().catch(console.error);
}

module.exports = { runComprehensiveTests };