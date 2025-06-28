/**
 * 사용자 역할별 완전 자동화 E2E 테스트
 * 모든 사용자 유형의 전체 기능을 자동으로 검증
 */

const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

// 테스트 설정
const TEST_CONFIG = {
  baseUrl: process.env.TEST_URL || 'http://localhost:3019',
  apiUrl: process.env.API_URL || 'http://localhost:8019',
  headless: process.env.HEADLESS !== 'false',
  slowMo: parseInt(process.env.SLOW_MO || '0'),
  timeout: 30000,
  screenshotDir: path.join(__dirname, 'screenshots', new Date().toISOString().split('T')[0])
};

// 사용자 계정 정보
const USERS = {
  admin: {
    username: 'admin',
    password: 'admin123',
    role: '관리자',
    menus: [
      { name: '프로젝트 관리', path: '/projects' },
      { name: '사용자 관리', path: '/users' },
      { name: '템플릿 관리', path: '/templates' },
      { name: 'AI 공급자 관리', path: '/ai-providers' },
      { name: 'AI 모델 관리', path: '/ai-models' },
      { name: '배포 관리', path: '/deployment' }
    ]
  },
  secretary: {
    username: 'secretary',
    password: 'secretary123',
    role: '간사',
    menus: [
      { name: '프로젝트 관리', path: '/projects' },
      { name: '평가위원 배정', path: '/assignments' },
      { name: '평가 진행 현황', path: '/evaluation-status' },
      { name: '평가표 출력', path: '/evaluation-print' },
      { name: '결과 분석', path: '/analytics' }
    ]
  },
  evaluator: {
    username: 'evaluator',
    password: 'evaluator123',
    role: '평가위원',
    menus: [
      { name: '내 평가', path: '/my-evaluations' },
      { name: '평가 수행', path: '/evaluation' },
      { name: 'AI 도우미', path: '/ai-assistant' },
      { name: '제출 내역', path: '/submissions' }
    ]
  }
};

// 테스트 결과 리포트
const testReport = {
  startTime: new Date(),
  endTime: null,
  totalTests: 0,
  passedTests: 0,
  failedTests: 0,
  results: {}
};

// 유틸리티 함수들
async function ensureScreenshotDir() {
  if (!fs.existsSync(TEST_CONFIG.screenshotDir)) {
    fs.mkdirSync(TEST_CONFIG.screenshotDir, { recursive: true });
  }
}

async function takeScreenshot(page, name) {
  const filename = `${name.replace(/\s+/g, '_')}_${Date.now()}.png`;
  const filepath = path.join(TEST_CONFIG.screenshotDir, filename);
  await page.screenshot({ path: filepath, fullPage: true });
  return filepath;
}

async function logTestResult(userRole, testName, status, details = null) {
  testReport.totalTests++;
  if (status === 'passed') {
    testReport.passedTests++;
  } else {
    testReport.failedTests++;
  }
  
  if (!testReport.results[userRole]) {
    testReport.results[userRole] = [];
  }
  
  testReport.results[userRole].push({
    testName,
    status,
    details,
    timestamp: new Date().toISOString()
  });
  
  console.log(`[${userRole}] ${testName}: ${status.toUpperCase()}${details ? ` - ${details}` : ''}`);
}

// 로그인 테스트 함수
async function testLogin(page, user) {
  try {
    console.log(`\n🔐 ${user.role} 로그인 테스트 시작...`);
    
    await page.goto(TEST_CONFIG.baseUrl, { waitUntil: 'networkidle0' });
    await takeScreenshot(page, `${user.role}_홈페이지`);
    
    // 로그인 버튼 클릭
    await page.click('button:has-text("로그인")');
    await page.waitForTimeout(1000);
    
    // 로그인 폼 입력
    await page.type('#username', user.username);
    await page.type('#password', user.password);
    await takeScreenshot(page, `${user.role}_로그인_폼_입력`);
    
    // 로그인 제출
    await Promise.all([
      page.waitForNavigation({ waitUntil: 'networkidle0' }),
      page.click('button[type="submit"]')
    ]);
    
    // 로그인 성공 확인
    await page.waitForSelector('.user-info', { timeout: 5000 });
    const userInfo = await page.$eval('.user-info', el => el.textContent);
    
    if (userInfo.includes(user.role)) {
      await takeScreenshot(page, `${user.role}_로그인_성공`);
      await logTestResult(user.role, '로그인', 'passed');
      return true;
    } else {
      throw new Error('사용자 정보가 일치하지 않습니다');
    }
  } catch (error) {
    await takeScreenshot(page, `${user.role}_로그인_실패`);
    await logTestResult(user.role, '로그인', 'failed', error.message);
    return false;
  }
}

// 메뉴 접근 테스트
async function testMenuAccess(page, user) {
  console.log(`\n📋 ${user.role} 메뉴 접근 테스트 시작...`);
  
  for (const menu of user.menus) {
    try {
      // 메뉴 클릭 또는 직접 이동
      const menuSelector = `a:has-text("${menu.name}"), button:has-text("${menu.name}")`;
      const menuElement = await page.$(menuSelector);
      
      if (menuElement) {
        await menuElement.click();
        await page.waitForTimeout(2000);
      } else {
        // 직접 URL 이동
        await page.goto(`${TEST_CONFIG.baseUrl}${menu.path}`, { waitUntil: 'networkidle0' });
      }
      
      // 페이지 로드 확인
      await page.waitForSelector('main', { timeout: 10000 });
      await takeScreenshot(page, `${user.role}_${menu.name}`);
      
      // API 호출 확인 (네트워크 모니터링)
      const apiCalls = await page.evaluate(() => {
        return window.performance.getEntriesByType('resource')
          .filter(entry => entry.name.includes('/api/'))
          .map(entry => ({ url: entry.name, status: entry.responseStatus || 200 }));
      });
      
      await logTestResult(user.role, `${menu.name} 메뉴 접근`, 'passed', `API 호출: ${apiCalls.length}개`);
    } catch (error) {
      await takeScreenshot(page, `${user.role}_${menu.name}_오류`);
      await logTestResult(user.role, `${menu.name} 메뉴 접근`, 'failed', error.message);
    }
  }
}

// 역할별 특수 기능 테스트
async function testRoleSpecificFeatures(page, user) {
  console.log(`\n⚡ ${user.role} 특수 기능 테스트 시작...`);
  
  switch (user.role) {
    case '관리자':
      await testAdminFeatures(page);
      break;
    case '간사':
      await testSecretaryFeatures(page);
      break;
    case '평가위원':
      await testEvaluatorFeatures(page);
      break;
  }
}

// 관리자 특수 기능 테스트
async function testAdminFeatures(page) {
  // 사용자 생성 테스트
  try {
    await page.goto(`${TEST_CONFIG.baseUrl}/users`, { waitUntil: 'networkidle0' });
    const createButton = await page.$('button:has-text("사용자 추가")');
    
    if (createButton) {
      await createButton.click();
      await page.waitForTimeout(1000);
      await takeScreenshot(page, '관리자_사용자_생성_모달');
      await logTestResult('관리자', '사용자 생성 기능', 'passed');
    }
  } catch (error) {
    await logTestResult('관리자', '사용자 생성 기능', 'failed', error.message);
  }
  
  // AI 설정 테스트
  try {
    await page.goto(`${TEST_CONFIG.baseUrl}/ai-providers`, { waitUntil: 'networkidle0' });
    const aiStatus = await page.$('.ai-status');
    
    if (aiStatus) {
      const statusText = await aiStatus.textContent;
      await takeScreenshot(page, '관리자_AI_상태');
      await logTestResult('관리자', 'AI 공급자 관리', 'passed', statusText);
    }
  } catch (error) {
    await logTestResult('관리자', 'AI 공급자 관리', 'failed', error.message);
  }
}

// 간사 특수 기능 테스트
async function testSecretaryFeatures(page) {
  // 평가위원 배정 테스트
  try {
    await page.goto(`${TEST_CONFIG.baseUrl}/projects`, { waitUntil: 'networkidle0' });
    const firstProject = await page.$('.project-card');
    
    if (firstProject) {
      await firstProject.click();
      await page.waitForTimeout(2000);
      
      const assignButton = await page.$('button:has-text("평가위원 배정")');
      if (assignButton) {
        await takeScreenshot(page, '간사_평가위원_배정');
        await logTestResult('간사', '평가위원 배정 기능', 'passed');
      }
    }
  } catch (error) {
    await logTestResult('간사', '평가위원 배정 기능', 'failed', error.message);
  }
  
  // 평가표 출력 테스트
  try {
    await page.goto(`${TEST_CONFIG.baseUrl}/evaluation-print`, { waitUntil: 'networkidle0' });
    const printButton = await page.$('button:has-text("출력")');
    
    if (printButton) {
      await takeScreenshot(page, '간사_평가표_출력');
      await logTestResult('간사', '평가표 출력 기능', 'passed');
    }
  } catch (error) {
    await logTestResult('간사', '평가표 출력 기능', 'failed', error.message);
  }
}

// 평가위원 특수 기능 테스트
async function testEvaluatorFeatures(page) {
  // AI 도우미 테스트
  try {
    await page.goto(`${TEST_CONFIG.baseUrl}/ai-assistant`, { waitUntil: 'networkidle0' });
    const aiAssistant = await page.$('.ai-assistant-container');
    
    if (aiAssistant) {
      // AI 서비스 상태 확인
      const statusElement = await page.$('.ai-service-status');
      if (statusElement) {
        const statusText = await statusElement.textContent;
        await takeScreenshot(page, '평가위원_AI_도우미');
        await logTestResult('평가위원', 'AI 도우미 접근', 'passed', statusText);
      }
    }
  } catch (error) {
    await logTestResult('평가위원', 'AI 도우미 접근', 'failed', error.message);
  }
  
  // 평가 수행 테스트
  try {
    await page.goto(`${TEST_CONFIG.baseUrl}/my-evaluations`, { waitUntil: 'networkidle0' });
    const evaluationList = await page.$$('.evaluation-item');
    
    if (evaluationList.length > 0) {
      await takeScreenshot(page, '평가위원_내_평가_목록');
      await logTestResult('평가위원', '평가 목록 조회', 'passed', `${evaluationList.length}개 평가`);
    }
  } catch (error) {
    await logTestResult('평가위원', '평가 목록 조회', 'failed', error.message);
  }
}

// 로그아웃 테스트
async function testLogout(page, user) {
  try {
    console.log(`\n🚪 ${user.role} 로그아웃 테스트...`);
    
    const logoutButton = await page.$('button:has-text("로그아웃")');
    if (logoutButton) {
      await logoutButton.click();
      await page.waitForTimeout(2000);
      
      // 홈페이지로 리다이렉트 확인
      const loginButton = await page.$('button:has-text("로그인")');
      if (loginButton) {
        await takeScreenshot(page, `${user.role}_로그아웃_성공`);
        await logTestResult(user.role, '로그아웃', 'passed');
      }
    }
  } catch (error) {
    await logTestResult(user.role, '로그아웃', 'failed', error.message);
  }
}

// 메인 테스트 실행 함수
async function runUserRoleTests() {
  console.log('🚀 온라인 평가 시스템 사용자 역할별 자동화 테스트 시작\n');
  console.log(`📍 대상 URL: ${TEST_CONFIG.baseUrl}`);
  console.log(`📸 스크린샷 저장 경로: ${TEST_CONFIG.screenshotDir}\n`);
  
  await ensureScreenshotDir();
  
  const browser = await puppeteer.launch({
    headless: TEST_CONFIG.headless,
    slowMo: TEST_CONFIG.slowMo,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  try {
    // 각 사용자별 테스트 실행
    for (const [userType, user] of Object.entries(USERS)) {
      console.log(`\n${'='.repeat(50)}`);
      console.log(`👤 ${user.role} (${userType}) 테스트 시작`);
      console.log(`${'='.repeat(50)}`);
      
      const page = await browser.newPage();
      await page.setViewport({ width: 1920, height: 1080 });
      
      // 네트워크 요청 모니터링
      page.on('response', response => {
        if (response.url().includes('/api/')) {
          const status = response.status();
          if (status >= 400) {
            console.error(`❌ API 오류: ${response.url()} - ${status}`);
          }
        }
      });
      
      try {
        // 1. 로그인 테스트
        const loginSuccess = await testLogin(page, user);
        
        if (loginSuccess) {
          // 2. 메뉴 접근 테스트
          await testMenuAccess(page, user);
          
          // 3. 역할별 특수 기능 테스트
          await testRoleSpecificFeatures(page, user);
          
          // 4. 로그아웃 테스트
          await testLogout(page, user);
        }
      } catch (error) {
        console.error(`❌ ${user.role} 테스트 중 오류 발생:`, error);
        await takeScreenshot(page, `${user.role}_치명적_오류`);
      } finally {
        await page.close();
      }
    }
  } finally {
    await browser.close();
  }
  
  // 테스트 리포트 생성
  generateTestReport();
}

// 테스트 리포트 생성 함수
function generateTestReport() {
  testReport.endTime = new Date();
  const duration = (testReport.endTime - testReport.startTime) / 1000;
  
  console.log('\n' + '='.repeat(70));
  console.log('📊 테스트 결과 리포트');
  console.log('='.repeat(70));
  console.log(`\n⏱️  실행 시간: ${duration.toFixed(2)}초`);
  console.log(`✅ 성공: ${testReport.passedTests}개`);
  console.log(`❌ 실패: ${testReport.failedTests}개`);
  console.log(`📈 성공률: ${((testReport.passedTests / testReport.totalTests) * 100).toFixed(2)}%\n`);
  
  // 사용자별 상세 결과
  Object.entries(testReport.results).forEach(([role, results]) => {
    console.log(`\n👤 ${role} 테스트 결과:`);
    results.forEach(result => {
      const icon = result.status === 'passed' ? '✅' : '❌';
      console.log(`  ${icon} ${result.testName}: ${result.status}${result.details ? ` (${result.details})` : ''}`);
    });
  });
  
  // JSON 리포트 파일 저장
  const reportPath = path.join(TEST_CONFIG.screenshotDir, 'test_report.json');
  fs.writeFileSync(reportPath, JSON.stringify(testReport, null, 2));
  console.log(`\n📄 상세 리포트 저장됨: ${reportPath}`);
  console.log(`📸 스크린샷 저장 경로: ${TEST_CONFIG.screenshotDir}`);
}

// 테스트 실행
if (require.main === module) {
  runUserRoleTests().catch(console.error);
}

module.exports = { runUserRoleTests };