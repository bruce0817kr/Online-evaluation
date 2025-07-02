const { chromium } = require('playwright');
const percySnapshot = require('@percy/playwright');

// Test configuration
const TEST_CONFIG = {
  baseUrl: process.env.FRONTEND_URL || 'http://localhost:3000',
  timeout: 30000,
  viewports: [
    { width: 375, height: 667, name: 'mobile' },
    { width: 768, height: 1024, name: 'tablet' },
    { width: 1280, height: 800, name: 'desktop' },
    { width: 1920, height: 1080, name: 'large-desktop' }
  ],
  users: {
    admin: { username: 'admin', password: 'admin123!@#' },
    secretary: { username: 'secretary', password: 'secretary123!@#' },
    evaluator: { username: 'evaluator', password: 'evaluator123!@#' }
  }
};

// Helper function to login
async function login(page, userType) {
  const user = TEST_CONFIG.users[userType];
  await page.goto(`${TEST_CONFIG.baseUrl}/login`);
  await page.fill('input[name="login_id"]', user.username);
  await page.fill('input[name="password"]', user.password);
  await page.click('button[type="submit"]');
  await page.waitForSelector('.dashboard', { timeout: TEST_CONFIG.timeout });
}

// Visual regression test suite
async function runVisualRegressionTests() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();
  
  try {
    console.log('🎨 Starting visual regression tests...');
    
    // Test 1: Landing Page
    console.log('📸 Testing landing page...');
    await page.goto(TEST_CONFIG.baseUrl);
    await page.waitForLoadState('networkidle');
    await percySnapshot(page, 'Landing Page', {
      widths: TEST_CONFIG.viewports.map(v => v.width)
    });
    
    // Test 2: Login Page
    console.log('📸 Testing login page...');
    await page.goto(`${TEST_CONFIG.baseUrl}/login`);
    await page.waitForSelector('form', { timeout: TEST_CONFIG.timeout });
    await percySnapshot(page, 'Login Page', {
      widths: TEST_CONFIG.viewports.map(v => v.width)
    });
    
    // Test 3: Admin Dashboard
    console.log('📸 Testing admin dashboard...');
    await login(page, 'admin');
    await percySnapshot(page, 'Admin Dashboard', {
      widths: TEST_CONFIG.viewports.map(v => v.width)
    });
    
    // Test 4: Template Management
    console.log('📸 Testing template management...');
    await page.click('button:has-text("템플릿")');
    await page.waitForSelector('.template-list', { timeout: TEST_CONFIG.timeout });
    await percySnapshot(page, 'Template Management', {
      widths: TEST_CONFIG.viewports.map(v => v.width)
    });
    
    // Test 5: Template Creation Form
    console.log('📸 Testing template creation form...');
    await page.click('button:has-text("새 템플릿")');
    await page.waitForSelector('.template-form', { timeout: TEST_CONFIG.timeout });
    await percySnapshot(page, 'Template Creation Form', {
      widths: TEST_CONFIG.viewports.map(v => v.width)
    });
    
    // Test 6: Evaluation Management
    console.log('📸 Testing evaluation management...');
    await page.click('button:has-text("평가관리")');
    await page.waitForSelector('.evaluation-list', { timeout: TEST_CONFIG.timeout });
    await percySnapshot(page, 'Evaluation Management', {
      widths: TEST_CONFIG.viewports.map(v => v.width)
    });
    
    // Test 7: Project Management
    console.log('📸 Testing project management...');
    await page.click('button:has-text("프로젝트")');
    await page.waitForSelector('.project-list', { timeout: TEST_CONFIG.timeout });
    await percySnapshot(page, 'Project Management', {
      widths: TEST_CONFIG.viewports.map(v => v.width)
    });
    
    // Test 8: AI Model Management
    console.log('📸 Testing AI model management...');
    await page.click('button:has-text("AI 모델")');
    await page.waitForSelector('.ai-model-dashboard', { timeout: TEST_CONFIG.timeout });
    await percySnapshot(page, 'AI Model Management', {
      widths: TEST_CONFIG.viewports.map(v => v.width)
    });
    
    // Test 9: Dark Mode
    console.log('📸 Testing dark mode...');
    await page.click('button[aria-label="Toggle dark mode"]');
    await page.waitForTimeout(500); // Wait for theme transition
    await percySnapshot(page, 'Dark Mode - Dashboard', {
      widths: TEST_CONFIG.viewports.map(v => v.width)
    });
    
    // Test 10: Mobile Navigation
    console.log('📸 Testing mobile navigation...');
    await page.setViewportSize({ width: 375, height: 667 });
    await page.click('button[aria-label="메뉴 열기"]');
    await page.waitForSelector('.mobile-menu', { timeout: TEST_CONFIG.timeout });
    await percySnapshot(page, 'Mobile Navigation Menu', {
      widths: [375]
    });
    
    // Test 11: Secretary View
    console.log('📸 Testing secretary view...');
    await page.context().clearCookies();
    await login(page, 'secretary');
    await percySnapshot(page, 'Secretary Dashboard', {
      widths: TEST_CONFIG.viewports.map(v => v.width)
    });
    
    // Test 12: Evaluator View
    console.log('📸 Testing evaluator view...');
    await page.context().clearCookies();
    await login(page, 'evaluator');
    await percySnapshot(page, 'Evaluator Dashboard', {
      widths: TEST_CONFIG.viewports.map(v => v.width)
    });
    
    // Test 13: Error States
    console.log('📸 Testing error states...');
    await page.goto(`${TEST_CONFIG.baseUrl}/404`);
    await percySnapshot(page, '404 Error Page', {
      widths: TEST_CONFIG.viewports.map(v => v.width)
    });
    
    // Test 14: Loading States
    console.log('📸 Testing loading states...');
    await page.evaluate(() => {
      document.body.classList.add('loading');
    });
    await percySnapshot(page, 'Loading State', {
      widths: TEST_CONFIG.viewports.map(v => v.width)
    });
    
    // Test 15: Form Validation States
    console.log('📸 Testing form validation states...');
    await page.goto(`${TEST_CONFIG.baseUrl}/login`);
    await page.click('button[type="submit"]'); // Submit empty form
    await page.waitForTimeout(500);
    await percySnapshot(page, 'Form Validation Errors', {
      widths: TEST_CONFIG.viewports.map(v => v.width)
    });
    
    console.log('✅ Visual regression tests completed successfully!');
    
  } catch (error) {
    console.error('❌ Visual regression test failed:', error);
    throw error;
  } finally {
    await browser.close();
  }
}

// Run tests if executed directly
if (require.main === module) {
  runVisualRegressionTests()
    .then(() => process.exit(0))
    .catch(() => process.exit(1));
}

module.exports = { runVisualRegressionTests };