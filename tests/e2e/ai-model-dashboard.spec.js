import { test, expect } from '../fixtures';

test.describe('AI Model Dashboard', () => {
  test.beforeEach(async ({ authHelper }) => {
    // Login as admin to access AI model dashboard
    await authHelper.loginViaUI('admin', 'admin123');
  });

  test('should display AI Model Dashboard with admin access', async ({ page, navHelper }) => {
    // Navigate to AI Model Dashboard
    await page.click('[data-testid="admin-dropdown"]');
    await page.click('text=⚙️ AI 모델 설정');
    
    // Verify we're on the AI Model Dashboard page
    await expect(page.locator('h2')).toContainText('AI 모델 관리 대시보드');
    await expect(page.locator('.ai-model-dashboard')).toBeVisible();
    
    // Verify summary cards are displayed
    await expect(page.locator('.summary-cards')).toBeVisible();
    await expect(page.locator('.summary-card')).toHaveCount(4);
    
    // Verify tab navigation is present
    await expect(page.locator('.tab-navigation')).toBeVisible();
    
    const tabs = ['🤖 모델 관리', '📊 성능 모니터링', '⚖️ 모델 비교', '🧪 스마트 테스트', '⚙️ 설정'];
    for (const tab of tabs) {
      await expect(page.locator(`text=${tab}`)).toBeVisible();
    }
  });

  test('should deny access to non-admin users', async ({ page, authHelper }) => {
    // Logout and login as evaluator
    await authHelper.logout();
    await authHelper.loginViaUI('evaluator01', 'evaluator123');
    
    // Try to access AI Model Dashboard
    await page.goto('/ai-model-settings');
    
    // Should show access denied message
    await expect(page.locator('.access-denied')).toBeVisible();
    await expect(page.locator('h2')).toContainText('접근 권한 없음');
  });

  test('should load available models in Models tab', async ({ page, apiHelper }) => {
    await page.click('[data-testid="admin-dropdown"]');
    await page.click('text=⚙️ AI 모델 설정');
    
    // Click on Models tab (should be active by default)
    await page.click('text=🤖 모델 관리');
    
    // Wait for models to load
    await page.waitForSelector('.model-cards', { timeout: 10000 });
    
    // Verify model cards are displayed
    const modelCards = await page.locator('.model-card').count();
    expect(modelCards).toBeGreaterThan(0);
    
    // Verify each model card has required elements
    const firstModelCard = page.locator('.model-card').first();
    await expect(firstModelCard.locator('.model-icon')).toBeVisible();
    await expect(firstModelCard.locator('.model-info h4')).toBeVisible();
    await expect(firstModelCard.locator('.model-status')).toBeVisible();
    await expect(firstModelCard.locator('.model-metrics')).toBeVisible();
  });

  test('should allow model selection and configuration', async ({ page }) => {
    await page.click('[data-testid="admin-dropdown"]');
    await page.click('text=⚙️ AI 모델 설정');
    
    // Wait for models to load and select the first model
    await page.waitForSelector('.model-card');
    await page.click('.model-card:first-child');
    
    // Verify model is selected
    await expect(page.locator('.model-card.selected')).toBeVisible();
    
    // Verify configuration panel appears
    await expect(page.locator('.model-configuration')).toBeVisible();
    await expect(page.locator('.model-configuration h3')).toContainText('모델 설정');
    
    // Verify configuration form elements
    await expect(page.locator('.config-field')).toHaveCount.toBeGreaterThan(3);
    await expect(page.locator('.save-config-btn')).toBeVisible();
  });

  test('should display performance monitoring', async ({ page }) => {
    await page.click('[data-testid="admin-dropdown"]');
    await page.click('text=⚙️ AI 모델 설정');
    
    // Select a model first
    await page.waitForSelector('.model-card');
    await page.click('.model-card:first-child');
    
    // Click on Performance tab
    await page.click('text=📊 성능 모니터링');
    
    // Verify performance panel is displayed
    await expect(page.locator('.performance-monitor-panel')).toBeVisible();
    await expect(page.locator('.performance-header h3')).toBeVisible();
    
    // Verify timeframe selector
    await expect(page.locator('.timeframe-selector')).toBeVisible();
    const timeframeButtons = ['1일', '7일', '30일'];
    for (const button of timeframeButtons) {
      await expect(page.locator(`text=${button}`)).toBeVisible();
    }
    
    // Verify performance metrics
    await expect(page.locator('.performance-metrics')).toBeVisible();
    await expect(page.locator('.metric-card')).toHaveCount(4);
  });

  test('should handle model comparison', async ({ page }) => {
    await page.click('[data-testid="admin-dropdown"]');
    await page.click('text=⚙️ AI 모델 설정');
    
    // Click on Comparison tab
    await page.click('text=⚖️ 모델 비교');
    
    // Verify comparison tool is displayed
    await expect(page.locator('.model-comparison-tool')).toBeVisible();
    await expect(page.locator('h3')).toContainText('모델 성능 비교');
    
    // Verify model selector
    await expect(page.locator('.model-selector')).toBeVisible();
    await expect(page.locator('.model-checkboxes')).toBeVisible();
    
    // Verify prompt input
    await expect(page.locator('.prompt-input')).toBeVisible();
    await expect(page.locator('textarea')).toBeVisible();
    
    // Verify comparison button
    await expect(page.locator('.run-comparison-btn')).toBeVisible();
    
    // Test model selection
    const modelCheckboxes = await page.locator('.model-checkbox').count();
    if (modelCheckboxes >= 2) {
      // Select first two models
      await page.click('.model-checkbox:nth-child(1) input');
      await page.click('.model-checkbox:nth-child(2) input');
      
      // Add test prompt
      await page.fill('textarea', '테스트 프롬프트: 이 회사의 기술력을 평가해주세요.');
      
      // Verify button is enabled
      await expect(page.locator('.run-comparison-btn:not(:disabled)')).toBeVisible();
    }
  });

  test('should display smart testing interface', async ({ page }) => {
    await page.click('[data-testid="admin-dropdown"]');
    await page.click('text=⚙️ AI 모델 설정');
    
    // Click on Smart Test tab
    await page.click('text=🧪 스마트 테스트');
    
    // Verify smart tester is displayed
    await expect(page.locator('.smart-model-tester')).toBeVisible();
    await expect(page.locator('.tester-header h3')).toContainText('스마트 모델 테스터');
    
    // Verify test configuration section
    await expect(page.locator('.test-configuration')).toBeVisible();
    await expect(page.locator('.config-section')).toBeVisible();
    
    // Verify model selection
    await expect(page.locator('.model-selection')).toBeVisible();
    await expect(page.locator('.model-grid')).toBeVisible();
    
    // Verify scenario selection
    await expect(page.locator('.scenario-selection')).toBeVisible();
    await expect(page.locator('.scenario-grid')).toBeVisible();
    
    // Verify test scenarios are present
    const scenarioCards = await page.locator('.scenario-card').count();
    expect(scenarioCards).toBeGreaterThan(0);
    
    // Verify test actions
    await expect(page.locator('.test-actions')).toBeVisible();
    await expect(page.locator('.run-test-btn')).toBeVisible();
  });

  test('should provide smart recommendations', async ({ page }) => {
    await page.click('[data-testid="admin-dropdown"]');
    await page.click('text=⚙️ AI 모델 설정');
    
    // Click on Settings tab
    await page.click('text=⚙️ 설정');
    
    // Verify settings panel is displayed
    await expect(page.locator('.model-settings-panel')).toBeVisible();
    await expect(page.locator('.settings-section h3')).toContainText('스마트 모델 추천');
    
    // Verify recommendation form
    await expect(page.locator('.recommendation-form')).toBeVisible();
    
    // Fill out recommendation form
    await page.selectOption('select:has-text("예산 수준")', 'medium');
    await page.selectOption('select:has-text("품질 요구사항")', 'high');
    await page.selectOption('select:has-text("속도 요구사항")', 'medium');
    await page.selectOption('select:has-text("작업 유형")', 'evaluation');
    await page.fill('input[type="number"]:near(:text("예상 토큰 수"))', '500');
    await page.fill('input[type="number"]:near(:text("월간 예상 요청 수"))', '200');
    
    // Verify recommendation button is enabled
    await expect(page.locator('.get-recommendation-btn:not(:disabled)')).toBeVisible();
  });

  test('should handle error states gracefully', async ({ page }) => {
    await page.click('[data-testid="admin-dropdown"]');
    await page.click('text=⚙️ AI 모델 설정');
    
    // Test network error handling by intercepting requests
    await page.route('**/api/ai-models/**', route => {
      route.fulfill({
        status: 500,
        body: JSON.stringify({ detail: 'Internal server error' })
      });
    });
    
    // Try to refresh the page
    await page.reload();
    
    // Should show error message
    await expect(page.locator('.error-alert')).toBeVisible();
    
    // Error should be dismissible
    await page.click('.close-error');
    await expect(page.locator('.error-alert')).not.toBeVisible();
  });

  test('should be responsive on mobile devices', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    await page.click('[data-testid="admin-dropdown"]');
    await page.click('text=⚙️ AI 모델 설정');
    
    // Verify mobile responsiveness
    await expect(page.locator('.ai-model-dashboard')).toBeVisible();
    
    // Tab navigation should be scrollable on mobile
    await expect(page.locator('.tab-navigation')).toBeVisible();
    
    // Model cards should stack vertically
    await expect(page.locator('.model-cards')).toBeVisible();
    
    // Summary cards should adapt to mobile
    await expect(page.locator('.summary-cards')).toBeVisible();
  });

  test('should maintain state across tab switches', async ({ page }) => {
    await page.click('[data-testid="admin-dropdown"]');
    await page.click('text=⚙️ AI 모델 설정');
    
    // Select a model in Models tab
    await page.waitForSelector('.model-card');
    await page.click('.model-card:first-child');
    
    // Switch to Performance tab
    await page.click('text=📊 성능 모니터링');
    await expect(page.locator('.performance-monitor-panel')).toBeVisible();
    
    // Switch back to Models tab
    await page.click('text=🤖 모델 관리');
    
    // Verify model selection is maintained
    await expect(page.locator('.model-card.selected')).toBeVisible();
    await expect(page.locator('.model-configuration')).toBeVisible();
  });
});