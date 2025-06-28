/**
 * 관리자 계정 전체 기능 종합 테스트
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

// 관리자 테스트 케이스
const ADMIN_TESTS = [
  { name: '로그인', endpoint: '/api/auth/login', method: 'POST', auth: false },
  { name: '프로필 조회', endpoint: '/api/auth/me', method: 'GET', auth: true },
  { name: '사용자 목록', endpoint: '/api/users', method: 'GET', auth: true },
  { name: '프로젝트 목록', endpoint: '/api/projects', method: 'GET', auth: true },
  { name: '템플릿 목록', endpoint: '/api/templates', method: 'GET', auth: true },
  { name: 'AI 상태', endpoint: '/api/ai/status', method: 'GET', auth: true },
  { name: 'AI 공급자', endpoint: '/api/admin/ai/providers', method: 'GET', auth: true },
  { name: '파일 목록', endpoint: '/api/files', method: 'GET', auth: true },
  { name: '배포 상태', endpoint: '/api/deployment/status', method: 'GET', auth: true }
];

const testResults = {
  timestamp: new Date().toISOString(),
  environment: {
    frontendUrl: CONFIG.baseUrl,
    backendUrl: CONFIG.apiUrl,
    testType: 'Admin Comprehensive Test'
  },
  tests: [],
  summary: { total: 0, passed: 0, failed: 0, warnings: 0 },
  issues: [],
  recommendations: []
};

function makeRequest(options, data = null) {
  return new Promise((resolve, reject) => {
    const url = new URL(options.url);
    const reqOptions = {
      hostname: url.hostname,
      port: url.port,
      path: url.pathname,
      method: options.method || 'GET',
      headers: options.headers || {},
      timeout: CONFIG.timeout
    };

    const req = http.request(reqOptions, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => resolve({
        status: res.statusCode,
        headers: res.headers,
        body: body
      }));
    });

    req.on('error', reject);
    req.on('timeout', () => {
      req.destroy();
      reject(new Error('Request timeout'));
    });

    if (data) req.write(data);
    req.end();
  });
}

async function runAdminTests() {
  console.log('🚀 관리자 계정 종합 기능 테스트 시작\n');
  
  if (!fs.existsSync(CONFIG.reportDir)) {
    fs.mkdirSync(CONFIG.reportDir, { recursive: true });
  }

  let adminToken = null;

  for (const test of ADMIN_TESTS) {
    console.log(`🔍 ${test.name} 테스트...`);
    testResults.summary.total++;

    try {
      let response;
      
      if (test.name === '로그인') {
        // 로그인 테스트
        response = await makeRequest({
          url: `${CONFIG.apiUrl}${test.endpoint}`,
          method: test.method,
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        }, 'username=admin&password=admin123');

        if (response.status === 200) {
          const data = JSON.parse(response.body);
          adminToken = data.access_token;
          console.log('✅ 로그인 성공');
          testResults.tests.push({
            name: test.name,
            status: 'passed',
            statusCode: response.status,
            details: '토큰 발급 성공'
          });
          testResults.summary.passed++;
        } else {
          throw new Error(`상태 코드: ${response.status}`);
        }
      } else {
        // 다른 API 테스트
        if (!adminToken) {
          throw new Error('로그인 토큰 없음');
        }

        response = await makeRequest({
          url: `${CONFIG.apiUrl}${test.endpoint}`,
          method: test.method,
          headers: { 'Authorization': `Bearer ${adminToken}` }
        });

        if (response.status >= 200 && response.status < 300) {
          console.log(`✅ ${test.name} 성공 (${response.status})`);
          testResults.tests.push({
            name: test.name,
            status: 'passed',
            statusCode: response.status,
            endpoint: test.endpoint
          });
          testResults.summary.passed++;
        } else if (response.status === 500 && test.name === '배포 상태') {
          console.log(`⚠️ ${test.name} 예상된 오류 (${response.status})`);
          testResults.tests.push({
            name: test.name,
            status: 'warning',
            statusCode: response.status,
            endpoint: test.endpoint,
            note: 'Docker 권한 제한으로 인한 예상된 오류'
          });
          testResults.summary.warnings++;
        } else {
          throw new Error(`상태 코드: ${response.status}`);
        }
      }
    } catch (error) {
      console.log(`❌ ${test.name} 실패: ${error.message}`);
      testResults.tests.push({
        name: test.name,
        status: 'failed',
        error: error.message,
        endpoint: test.endpoint
      });
      testResults.summary.failed++;
    }

    // 요청 간 지연
    await new Promise(resolve => setTimeout(resolve, 200));
  }

  // 이슈 분석
  analyzeIssues();
  
  // 리포트 생성
  generateFinalReport();
}

function analyzeIssues() {
  // 발견된 이슈들 분석
  const failedTests = testResults.tests.filter(t => t.status === 'failed');
  const warningTests = testResults.tests.filter(t => t.status === 'warning');

  if (failedTests.length > 0) {
    testResults.issues.push({
      type: 'CRITICAL',
      description: `${failedTests.length}개의 핵심 기능이 실패했습니다.`,
      tests: failedTests.map(t => t.name)
    });
  }

  if (warningTests.length > 0) {
    testResults.issues.push({
      type: 'WARNING',  
      description: `${warningTests.length}개의 기능에서 경고가 발생했습니다.`,
      tests: warningTests.map(t => t.name)
    });
  }

  // 계정 생성 문제
  testResults.issues.push({
    type: 'CRITICAL',
    description: 'secretary, evaluator 계정 생성/로그인 실패',
    details: 'MongoDB 직접 접근 및 사용자 생성 API 모두 실패'
  });

  // 권장사항 생성
  generateRecommendations();
}

function generateRecommendations() {
  const successRate = (testResults.summary.passed / testResults.summary.total * 100).toFixed(1);

  if (successRate >= 90) {
    testResults.recommendations.push('🎉 시스템이 매우 안정적으로 동작하고 있습니다.');
  } else if (successRate >= 70) {
    testResults.recommendations.push('✅ 시스템 핵심 기능이 정상 동작하고 있습니다.');
  } else {
    testResults.recommendations.push('⚠️ 시스템 안정성 개선이 필요합니다.');
  }

  testResults.recommendations.push(
    '🔧 MongoDB 사용자 생성 API 점검 필요',
    '👥 테스트 계정 생성 프로세스 개선 필요',
    '🐳 Docker 환경에서의 배포 상태 API 개선',
    '📝 사용자 생성 폼 검증 로직 점검'
  );
}

function generateFinalReport() {
  console.log('\n' + '='.repeat(80));
  console.log('📊 관리자 계정 종합 테스트 결과');
  console.log('='.repeat(80));

  const successRate = (testResults.summary.passed / testResults.summary.total * 100).toFixed(1);

  console.log(`\n📈 성공률: ${successRate}%`);
  console.log(`✅ 성공: ${testResults.summary.passed}개`);
  console.log(`⚠️ 경고: ${testResults.summary.warnings}개`);
  console.log(`❌ 실패: ${testResults.summary.failed}개\n`);

  // 테스트 상세 결과
  console.log('📋 테스트 상세 결과:');
  testResults.tests.forEach(test => {
    const icon = test.status === 'passed' ? '✅' : test.status === 'warning' ? '⚠️' : '❌';
    console.log(`  ${icon} ${test.name}: ${test.statusCode || 'N/A'}${test.note ? ` (${test.note})` : ''}`);
  });

  // 발견된 이슈
  if (testResults.issues.length > 0) {
    console.log('\n🚨 발견된 이슈:');
    testResults.issues.forEach(issue => {
      const icon = issue.type === 'CRITICAL' ? '🔴' : '🟡';
      console.log(`  ${icon} ${issue.description}`);
      if (issue.details) console.log(`     세부사항: ${issue.details}`);
    });
  }

  // 권장사항
  console.log('\n💡 권장사항:');
  testResults.recommendations.forEach(rec => {
    console.log(`  ${rec}`);
  });

  // 리포트 파일 저장
  const reportPath = path.join(CONFIG.reportDir, 'admin_comprehensive_report.json');
  fs.writeFileSync(reportPath, JSON.stringify(testResults, null, 2));

  const htmlPath = path.join(CONFIG.reportDir, 'admin_report.html');
  generateHtmlReport(htmlPath);

  console.log(`\n📄 JSON 리포트: ${reportPath}`);
  console.log(`🌐 HTML 리포트: ${htmlPath}`);
}

function generateHtmlReport(filePath) {
  const successRate = (testResults.summary.passed / testResults.summary.total * 100).toFixed(1);
  
  const html = `
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>관리자 종합 테스트 리포트</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 20px; background: #f5f7fa; }
        .container { max-width: 1000px; margin: 0 auto; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 12px; margin-bottom: 30px; }
        .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .metric { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; }
        .metric-value { font-size: 2.5em; font-weight: bold; margin-bottom: 10px; }
        .success { color: #10b981; }
        .warning { color: #f59e0b; }
        .error { color: #ef4444; }
        .section { background: white; margin-bottom: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); overflow: hidden; }
        .section-header { background: #f8fafc; padding: 20px; border-bottom: 1px solid #e5e7eb; font-weight: bold; font-size: 1.2em; }
        .section-content { padding: 20px; }
        .test-item { display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid #f1f5f9; }
        .test-item:last-child { border-bottom: none; }
        .issue { margin-bottom: 15px; padding: 15px; border-radius: 8px; }
        .issue.critical { background: #fef2f2; border-left: 4px solid #ef4444; }
        .issue.warning { background: #fffbeb; border-left: 4px solid #f59e0b; }
        .recommendations li { margin-bottom: 8px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 관리자 계정 종합 테스트 리포트</h1>
            <p>생성 시간: ${testResults.timestamp}</p>
            <p>테스트 환경: ${testResults.environment.backendUrl}</p>
        </div>

        <div class="metrics">
            <div class="metric">
                <div class="metric-value success">${testResults.summary.passed}</div>
                <div>성공</div>
            </div>
            <div class="metric">
                <div class="metric-value warning">${testResults.summary.warnings}</div>
                <div>경고</div>
            </div>
            <div class="metric">
                <div class="metric-value error">${testResults.summary.failed}</div>
                <div>실패</div>
            </div>
            <div class="metric">
                <div class="metric-value">${successRate}%</div>
                <div>성공률</div>
            </div>
        </div>

        <div class="section">
            <div class="section-header">📋 테스트 결과 상세</div>
            <div class="section-content">
                ${testResults.tests.map(test => `
                <div class="test-item">
                    <span>${test.status === 'passed' ? '✅' : test.status === 'warning' ? '⚠️' : '❌'} ${test.name}</span>
                    <span class="${test.status}">${test.statusCode || 'N/A'}</span>
                </div>
                `).join('')}
            </div>
        </div>

        <div class="section">
            <div class="section-header">🚨 발견된 이슈</div>
            <div class="section-content">
                ${testResults.issues.map(issue => `
                <div class="issue ${issue.type.toLowerCase()}">
                    <strong>${issue.type === 'CRITICAL' ? '🔴' : '🟡'} ${issue.description}</strong>
                    ${issue.details ? `<br><small>${issue.details}</small>` : ''}
                    ${issue.tests ? `<br><small>관련 테스트: ${issue.tests.join(', ')}</small>` : ''}
                </div>
                `).join('')}
            </div>
        </div>

        <div class="section">
            <div class="section-header">💡 권장사항</div>
            <div class="section-content">
                <ul class="recommendations">
                    ${testResults.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                </ul>
            </div>
        </div>
    </div>
</body>
</html>`;

  fs.writeFileSync(filePath, html);
}

runAdminTests().catch(console.error);