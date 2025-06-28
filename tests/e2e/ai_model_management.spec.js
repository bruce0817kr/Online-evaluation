/**
 * End-to-End Tests for AI Model Management
 * Complete user journey testing with Playwright
 */

const { test, expect } = require('@playwright/test');

class AIModelManagementPage {
  constructor(page) {
    this.page = page;
  }

  // Locators
  get managementHeader() {
    return this.page.locator('h2:has-text("🤖 AI 모델 관리")');
  }

  get manageTab() {
    return this.page.locator('button:has-text("🔧 모델 관리")');
  }

  get templatesTab() {
    return this.page.locator('button:has-text("📋 템플릿")');
  }

  get testTab() {
    return this.page.locator('button:has-text("🧪 연결 테스트")');
  }

  get createModelButton() {
    return this.page.locator('button:has-text("➕ 새 모델 생성")');
  }

  get refreshButton() {
    return this.page.locator('button:has-text("🔄 새로고침")');
  }

  get modelCards() {
    return this.page.locator('.model-management-card');
  }

  get templateCards() {
    return this.page.locator('.template-card');
  }

  get testCards() {
    return this.page.locator('.test-card');
  }

  get createModal() {
    return this.page.locator('.modal-overlay:has-text("➕ 새 AI 모델 생성")');
  }

  get editModal() {
    return this.page.locator('.modal-overlay:has-text("✏️ 모델 편집:")');
  }

  // Actions
  async navigateToAIModelManagement() {
    await this.page.locator('button:has-text("관리자 메뉴")').click();
    await this.page.locator('a:has-text("🔧 AI 모델 관리")').click();
  }

  async switchToTab(tabName) {
    const tabs = {
      'manage': this.manageTab,
      'templates': this.templatesTab,
      'test': this.testTab
    };
    await tabs[tabName].click();
  }

  async createNewModel(modelData) {
    await this.createModelButton.click();
    await expect(this.createModal).toBeVisible();

    // Fill form fields
    await this.page.fill('input[value=""]', modelData.model_id);
    await this.page.selectOption('select', modelData.provider);
    await this.page.fill('input[placeholder*="gpt-4"]', modelData.model_name);
    await this.page.fill('input[placeholder*="GPT-4"]', modelData.display_name);
    
    if (modelData.api_endpoint) {
      await this.page.fill('input[placeholder*="커스텀 API"]', modelData.api_endpoint);
    }
    
    if (modelData.capabilities) {
      await this.page.fill('input[placeholder*="text-generation"]', modelData.capabilities);
    }

    // Submit form
    await this.page.locator('button:has-text("모델 생성")').click();
  }

  async editModel(modelDisplayName, updates) {
    const modelCard = this.page.locator(`.model-management-card:has-text("${modelDisplayName}")`);
    await modelCard.locator('button:has-text("✏️ 수정")').click();
    await expect(this.editModal).toBeVisible();

    // Update fields
    if (updates.display_name) {
      await this.page.fill('input[value*=""]', updates.display_name);
    }

    // Submit form
    await this.page.locator('button:has-text("모델 업데이트")').click();
  }

  async deleteModel(modelDisplayName) {
    const modelCard = this.page.locator(`.model-management-card:has-text("${modelDisplayName}")`);
    
    // Setup dialog handler
    this.page.on('dialog', dialog => dialog.accept());
    
    await modelCard.locator('button:has-text("🗑️ 삭제")').click();
  }

  async createFromTemplate(templateName) {
    await this.switchToTab('templates');
    const templateCard = this.page.locator(`.template-card:has-text("${templateName}")`);
    await templateCard.locator('button:has-text("🚀 템플릿으로 생성")').click();
  }

  async testModelConnection(modelDisplayName) {
    await this.switchToTab('test');
    const testCard = this.page.locator(`.test-card:has-text("${modelDisplayName}")`);
    await testCard.locator('button:has-text("🔗 연결 테스트")').click();
  }
}

test.describe('AI Model Management E2E Tests', () => {
  let page, aiModelPage;

  test.beforeEach(async ({ browser }) => {
    page = await browser.newPage();
    aiModelPage = new AIModelManagementPage(page);

    // Login as admin
    await page.goto('/');
    await page.fill('input[placeholder="사용자 ID"]', 'admin');
    await page.fill('input[placeholder="비밀번호"]', 'admin123');
    await page.click('button:has-text("로그인")');
    
    // Wait for dashboard
    await expect(page.locator('h1:has-text("온라인 평가 시스템")')).toBeVisible();
    
    // Navigate to AI Model Management
    await aiModelPage.navigateToAIModelManagement();
    await expect(aiModelPage.managementHeader).toBeVisible();
  });

  test.afterEach(async () => {
    await page.close();
  });

  test('AI Model Management Access and Interface', async () => {
    // Check header is displayed
    await expect(aiModelPage.managementHeader).toBeVisible();
    
    // Check all tabs are present
    await expect(aiModelPage.manageTab).toBeVisible();
    await expect(aiModelPage.templatesTab).toBeVisible();
    await expect(aiModelPage.testTab).toBeVisible();
    
    // Check manage tab is active by default
    await expect(aiModelPage.manageTab).toHaveClass(/active/);
    
    // Check action buttons
    await expect(aiModelPage.createModelButton).toBeVisible();
    await expect(aiModelPage.refreshButton).toBeVisible();
  });

  test('Tab Navigation Functionality', async () => {
    // Start on manage tab
    await expect(aiModelPage.manageTab).toHaveClass(/active/);
    await expect(aiModelPage.createModelButton).toBeVisible();
    
    // Switch to templates tab
    await aiModelPage.switchToTab('templates');
    await expect(aiModelPage.templatesTab).toHaveClass(/active/);
    await expect(page.locator('h3:has-text("📋 모델 템플릿")')).toBeVisible();
    
    // Switch to test tab
    await aiModelPage.switchToTab('test');
    await expect(aiModelPage.testTab).toHaveClass(/active/);
    await expect(page.locator('h3:has-text("🧪 모델 연결 테스트")')).toBeVisible();
    
    // Switch back to manage tab
    await aiModelPage.switchToTab('manage');
    await expect(aiModelPage.manageTab).toHaveClass(/active/);
    await expect(aiModelPage.createModelButton).toBeVisible();
  });

  test('Display Existing Models', async () => {
    // Wait for models to load
    await expect(aiModelPage.modelCards.first()).toBeVisible({ timeout: 10000 });
    
    // Check that at least one model is displayed
    const modelCount = await aiModelPage.modelCards.count();
    expect(modelCount).toBeGreaterThan(0);
    
    // Check model card content
    const firstModel = aiModelPage.modelCards.first();
    await expect(firstModel.locator('.model-info h4')).toBeVisible();
    await expect(firstModel.locator('.model-actions')).toBeVisible();
    
    // Check for edit and delete buttons
    await expect(firstModel.locator('button:has-text("✏️ 수정")')).toBeVisible();
    await expect(firstModel.locator('button:has-text("🗑️ 삭제")')).toBeVisible();
  });

  test('Create New Model Flow', async () => {
    const newModelData = {
      model_id: 'e2e-test-model',
      provider: 'novita',
      model_name: 'deepseek-r1',
      display_name: 'E2E Test Model',
      capabilities: 'text-generation, analysis'
    };
    
    // Open create modal
    await aiModelPage.createModelButton.click();
    await expect(aiModelPage.createModal).toBeVisible();
    
    // Fill form
    await page.fill('input[pattern="^[a-z0-9-]+$"]', newModelData.model_id);
    await page.selectOption('select', newModelData.provider);
    await page.fill('input[placeholder*="gpt-4"]', newModelData.model_name);
    await page.fill('input[placeholder*="GPT-4"]', newModelData.display_name);
    await page.fill('input[placeholder*="text-generation"]', newModelData.capabilities);
    
    // Submit form
    await page.click('button:has-text("모델 생성")');
    
    // Wait for modal to close and success message
    await expect(aiModelPage.createModal).toBeHidden();
    
    // Verify new model appears in the list
    await expect(page.locator(`text=${newModelData.display_name}`)).toBeVisible({ timeout: 5000 });
  });

  test('Edit Existing Model', async () => {
    // Wait for models to load
    await expect(aiModelPage.modelCards.first()).toBeVisible({ timeout: 10000 });
    
    // Get first non-default model
    const editableModel = await page.locator('.model-management-card:not(:has(.default-badge))').first();
    const originalName = await editableModel.locator('.model-info h4').textContent();
    
    // Click edit button
    await editableModel.locator('button:has-text("✏️ 수정")').click();
    await expect(aiModelPage.editModal).toBeVisible();
    
    // Update display name
    const newDisplayName = `Updated ${originalName}`;
    await page.fill('input[value*=""]', newDisplayName);
    
    // Submit changes
    await page.click('button:has-text("모델 업데이트")');
    
    // Wait for modal to close
    await expect(aiModelPage.editModal).toBeHidden();
    
    // Verify updated name appears
    await expect(page.locator(`text=${newDisplayName}`)).toBeVisible({ timeout: 5000 });
  });

  test('Template System Functionality', async () => {
    // Switch to templates tab
    await aiModelPage.switchToTab('templates');
    
    // Wait for templates to load
    await expect(aiModelPage.templateCards.first()).toBeVisible({ timeout: 10000 });
    
    // Check that templates are displayed
    const templateCount = await aiModelPage.templateCards.count();
    expect(templateCount).toBeGreaterThan(0);
    
    // Check template card content
    const firstTemplate = aiModelPage.templateCards.first();
    await expect(firstTemplate.locator('h4')).toBeVisible();
    await expect(firstTemplate.locator('.provider-badge')).toBeVisible();
    await expect(firstTemplate.locator('button:has-text("🚀 템플릿으로 생성")')).toBeVisible();
    
    // Create model from template
    await firstTemplate.locator('button:has-text("🚀 템플릿으로 생성")').click();
    
    // Switch back to manage tab to verify creation
    await aiModelPage.switchToTab('manage');
    
    // Should see success message or new model
    await page.waitForTimeout(2000); // Allow time for creation
  });

  test('Connection Testing Functionality', async () => {
    // Switch to test tab
    await aiModelPage.switchToTab('test');
    
    // Wait for test cards to load
    await expect(aiModelPage.testCards.first()).toBeVisible({ timeout: 10000 });
    
    // Check that only active models are shown
    const testCount = await aiModelPage.testCards.count();
    expect(testCount).toBeGreaterThan(0);
    
    // Test connection for first model
    const firstTestCard = aiModelPage.testCards.first();
    await expect(firstTestCard.locator('button:has-text("🔗 연결 테스트")')).toBeVisible();
    
    await firstTestCard.locator('button:has-text("🔗 연결 테스트")').click();
    
    // Button should change to testing state
    await expect(firstTestCard.locator('button:has-text("🔄 테스트 중...")')).toBeVisible();
    
    // Wait for test result
    await expect(firstTestCard.locator('.test-result')).toBeVisible({ timeout: 15000 });
    
    // Should show either success or error result
    const resultExists = await page.locator('.test-result.success, .test-result.error').count();
    expect(resultExists).toBeGreaterThan(0);
  });

  test('Error Handling and Recovery', async () => {
    // Test API error handling by trying to create invalid model
    await aiModelPage.createModelButton.click();
    await expect(aiModelPage.createModal).toBeVisible();
    
    // Submit empty form to trigger validation
    await page.click('button:has-text("모델 생성")');
    
    // Form should remain open for required fields
    await expect(aiModelPage.createModal).toBeVisible();
    
    // Close modal
    await page.click('button:has-text("✕")');
    await expect(aiModelPage.createModal).toBeHidden();
  });

  test('Responsive Design Verification', async () => {
    // Test mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Header should still be visible
    await expect(aiModelPage.managementHeader).toBeVisible();
    
    // Tabs should be responsive
    await expect(aiModelPage.manageTab).toBeVisible();
    await expect(aiModelPage.templatesTab).toBeVisible();
    await expect(aiModelPage.testTab).toBeVisible();
    
    // Test tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });
    
    // Interface should adapt
    await expect(aiModelPage.createModelButton).toBeVisible();
    
    // Reset to desktop
    await page.setViewportSize({ width: 1920, height: 1080 });
  });

  test('Performance and Loading States', async () => {
    // Test refresh functionality
    await aiModelPage.refreshButton.click();
    
    // Button should be disabled during loading
    await expect(aiModelPage.refreshButton).toBeDisabled();
    
    // Wait for loading to complete
    await expect(aiModelPage.refreshButton).toBeEnabled({ timeout: 10000 });
    
    // Models should still be visible
    await expect(aiModelPage.modelCards.first()).toBeVisible();
  });

  test('Complete User Journey', async () => {
    // Complete workflow: Create -> Edit -> Test -> Delete
    const testModelData = {
      model_id: 'journey-test-model',
      provider: 'openai',
      model_name: 'gpt-3.5-turbo',
      display_name: 'Journey Test Model',
      capabilities: 'text-generation'
    };
    
    // Step 1: Create new model
    await aiModelPage.createModelButton.click();
    await expect(aiModelPage.createModal).toBeVisible();
    
    await page.fill('input[pattern="^[a-z0-9-]+$"]', testModelData.model_id);
    await page.selectOption('select', testModelData.provider);
    await page.fill('input[placeholder*="gpt-4"]', testModelData.model_name);
    await page.fill('input[placeholder*="GPT-4"]', testModelData.display_name);
    await page.fill('input[placeholder*="text-generation"]', testModelData.capabilities);
    
    await page.click('button:has-text("모델 생성")');
    await expect(aiModelPage.createModal).toBeHidden();
    
    // Step 2: Verify creation and edit
    await expect(page.locator(`text=${testModelData.display_name}`)).toBeVisible({ timeout: 5000 });
    
    const newModelCard = page.locator(`.model-management-card:has-text("${testModelData.display_name}")`);
    await newModelCard.locator('button:has-text("✏️ 수정")').click();
    await expect(aiModelPage.editModal).toBeVisible();
    
    await page.fill('input[value*="Journey"]', 'Journey Test Model - Updated');
    await page.click('button:has-text("모델 업데이트")');
    await expect(aiModelPage.editModal).toBeHidden();
    
    // Step 3: Test connection
    await aiModelPage.switchToTab('test');
    await page.waitForTimeout(1000);
    
    const testCard = page.locator(`.test-card:has-text("Journey Test Model - Updated")`);
    if (await testCard.count() > 0) {
      await testCard.locator('button:has-text("🔗 연결 테스트")').click();
      await expect(testCard.locator('.test-result')).toBeVisible({ timeout: 15000 });
    }
    
    // Step 4: Return to manage tab and delete
    await aiModelPage.switchToTab('manage');
    
    const updatedModelCard = page.locator(`.model-management-card:has-text("Journey Test Model - Updated")`);
    
    // Setup dialog handler for confirmation
    page.on('dialog', dialog => dialog.accept());
    
    await updatedModelCard.locator('button:has-text("🗑️ 삭제")').click();
    
    // Verify deletion
    await expect(page.locator(`text=Journey Test Model - Updated`)).toBeHidden({ timeout: 5000 });
  });
});

test.describe('AI Model Management - Access Control E2E', () => {
  test('Secretary user has limited access', async ({ page }) => {
    // Login as secretary
    await page.goto('/');
    await page.fill('input[placeholder="사용자 ID"]', 'secretary');
    await page.fill('input[placeholder="비밀번호"]', 'secretary123');
    await page.click('button:has-text("로그인")');
    
    // Navigate to AI Model Management
    const aiModelPage = new AIModelManagementPage(page);
    await aiModelPage.navigateToAIModelManagement();
    
    // Should have access
    await expect(aiModelPage.managementHeader).toBeVisible();
    
    // Should be able to view and test, but create/edit/delete might be restricted
    await expect(aiModelPage.manageTab).toBeVisible();
    await expect(aiModelPage.templatesTab).toBeVisible();
    await expect(aiModelPage.testTab).toBeVisible();
  });

  test('Evaluator user is denied access', async ({ page }) => {
    // Login as evaluator
    await page.goto('/');
    await page.fill('input[placeholder="사용자 ID"]', 'evaluator');
    await page.fill('input[placeholder="비밀번호"]', 'evaluator123');
    await page.click('button:has-text("로그인")');
    
    // Try to navigate to AI Model Management
    await page.locator('button:has-text("관리자 메뉴")').click();
    
    // AI Model Management option should not be visible or accessible
    const aiModelLink = page.locator('a:has-text("🔧 AI 모델 관리")');
    const linkCount = await aiModelLink.count();
    
    if (linkCount > 0) {
      await aiModelLink.click();
      // Should show access denied message
      await expect(page.locator('text=🚫 접근 권한 없음')).toBeVisible();
      await expect(page.locator('text=관리자와 간사만 사용할 수 있습니다')).toBeVisible();
    }
  });
});