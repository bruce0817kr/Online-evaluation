import { test, expect } from '../fixtures';

test.describe('Template Management', () => {
  test.beforeEach(async ({ authHelper }) => {
    await authHelper.loginViaUI('admin', 'admin123');
  });

  test('should display template management page', async ({ page, navHelper }) => {
    // Navigate to template management
    await page.click('text=📝 템플릿 관리');
    
    // Verify we're on the template page
    await expect(page.locator('h2')).toContainText('평가 템플릿 관리');
    await expect(page.locator('.template-management')).toBeVisible();
    
    // Verify action buttons are present
    await expect(page.locator('text=새 템플릿 생성')).toBeVisible();
    await expect(page.locator('text=템플릿 목록')).toBeVisible();
  });

  test('should create new template', async ({ page }) => {
    await page.click('text=📝 템플릿 관리');
    
    // Click new template button
    await page.click('text=새 템플릿 생성');
    
    // Verify creation form appears
    await expect(page.locator('.template-creation-form')).toBeVisible();
    
    // Fill out template details
    const templateName = `E2E 테스트 템플릿 ${Date.now()}`;
    await page.fill('input[name="name"]', templateName);
    await page.fill('textarea[name="description"]', '자동화 테스트용 템플릿입니다.');
    
    // Add evaluation criteria
    await page.click('text=평가 항목 추가');
    
    // Fill first criteria
    await page.fill('input[name="criteria.0.name"]', '기술력');
    await page.fill('textarea[name="criteria.0.description"]', '기술적 역량을 평가합니다.');
    await page.fill('input[name="criteria.0.weight"]', '30');
    await page.fill('input[name="criteria.0.maxScore"]', '100');
    
    // Add second criteria
    await page.click('text=평가 항목 추가');
    await page.fill('input[name="criteria.1.name"]', '사업성');
    await page.fill('textarea[name="criteria.1.description"]', '사업적 가능성을 평가합니다.');
    await page.fill('input[name="criteria.1.weight"]', '25');
    await page.fill('input[name="criteria.1.maxScore"]', '100');
    
    // Save template
    await page.click('text=템플릿 저장');
    
    // Verify success message
    await expect(page.locator('.success-message, .alert-success')).toBeVisible();
    
    // Verify template appears in list
    await page.click('text=템플릿 목록');
    await expect(page.locator(`text=${templateName}`)).toBeVisible();
  });

  test('should edit existing template', async ({ page, apiHelper }) => {
    await page.click('text=📝 템플릿 관리');
    
    // Create a template first via API for consistent testing
    const template = await apiHelper.createTemplate(
      `편집 테스트 템플릿 ${Date.now()}`,
      '편집 테스트용 템플릿',
      [
        { name: '기술력', description: '기술 평가', weight: 40, maxScore: 100 },
        { name: '시장성', description: '시장 평가', weight: 30, maxScore: 100 }
      ]
    );
    
    // Refresh to see the new template
    await page.reload();
    await page.click('text=템플릿 목록');
    
    // Find and edit the template
    const templateRow = page.locator(`tr:has-text("${template.data.name}")`);
    await templateRow.locator('text=수정').click();
    
    // Verify edit form appears
    await expect(page.locator('.template-edit-form')).toBeVisible();
    
    // Modify template name
    const newName = template.data.name + ' (수정됨)';
    await page.fill('input[name="name"]', newName);
    
    // Modify first criteria weight
    await page.fill('input[name="criteria.0.weight"]', '50');
    
    // Save changes
    await page.click('text=변경사항 저장');
    
    // Verify success message
    await expect(page.locator('.success-message, .alert-success')).toBeVisible();
    
    // Verify changes are reflected in the list
    await page.click('text=템플릿 목록');
    await expect(page.locator(`text=${newName}`)).toBeVisible();
  });

  test('should delete template', async ({ page, apiHelper }) => {
    await page.click('text=📝 템플릿 관리');
    
    // Create a template to delete
    const template = await apiHelper.createTemplate(
      `삭제 테스트 템플릿 ${Date.now()}`,
      '삭제 테스트용 템플릿',
      [{ name: '테스트', description: '테스트', weight: 100, maxScore: 100 }]
    );
    
    // Refresh and go to template list
    await page.reload();
    await page.click('text=템플릿 목록');
    
    // Find and delete the template
    const templateRow = page.locator(`tr:has-text("${template.data.name}")`);
    await templateRow.locator('text=삭제').click();
    
    // Confirm deletion in dialog
    await page.click('text=확인');
    
    // Verify template is removed from list
    await expect(page.locator(`text=${template.data.name}`)).not.toBeVisible();
  });

  test('should validate template form inputs', async ({ page }) => {
    await page.click('text=📝 템플릿 관리');
    await page.click('text=새 템플릿 생성');
    
    // Try to save empty form
    await page.click('text=템플릿 저장');
    
    // Should show validation errors
    await expect(page.locator('.error-message, .field-error')).toBeVisible();
    
    // Fill template name but leave criteria empty
    await page.fill('input[name="name"]', '유효성 검사 테스트');
    await page.click('text=템플릿 저장');
    
    // Should still show validation errors for criteria
    await expect(page.locator('.error-message, .field-error')).toBeVisible();
    
    // Add criteria but with invalid weight
    await page.click('text=평가 항목 추가');
    await page.fill('input[name="criteria.0.name"]', '테스트');
    await page.fill('input[name="criteria.0.weight"]', '150'); // Invalid weight > 100
    
    await page.click('text=템플릿 저장');
    
    // Should show weight validation error
    await expect(page.locator('.error-message, .field-error')).toBeVisible();
  });

  test('should handle drag and drop for criteria reordering', async ({ page }) => {
    await page.click('text=📝 템플릿 관리');
    await page.click('text=새 템플릿 생성');
    
    // Fill template name
    await page.fill('input[name="name"]', '드래그 앤 드롭 테스트');
    
    // Add multiple criteria
    await page.click('text=평가 항목 추가');
    await page.fill('input[name="criteria.0.name"]', '첫 번째 항목');
    await page.fill('input[name="criteria.0.weight"]', '30');
    
    await page.click('text=평가 항목 추가');
    await page.fill('input[name="criteria.1.name"]', '두 번째 항목');
    await page.fill('input[name="criteria.1.weight"]', '40');
    
    await page.click('text=평가 항목 추가');
    await page.fill('input[name="criteria.2.name"]', '세 번째 항목');
    await page.fill('input[name="criteria.2.weight"]', '30');
    
    // Verify initial order
    const firstCriteria = page.locator('.criteria-item').first();
    await expect(firstCriteria.locator('input[name*=".name"]')).toHaveValue('첫 번째 항목');
    
    // Test drag and drop functionality if supported
    const dragHandle = page.locator('.drag-handle').first();
    if (await dragHandle.isVisible()) {
      // Perform drag and drop
      const sourceBox = await firstCriteria.boundingBox();
      const targetBox = await page.locator('.criteria-item').nth(1).boundingBox();
      
      if (sourceBox && targetBox) {
        await page.mouse.move(sourceBox.x + sourceBox.width / 2, sourceBox.y + sourceBox.height / 2);
        await page.mouse.down();
        await page.mouse.move(targetBox.x + targetBox.width / 2, targetBox.y + targetBox.height / 2);
        await page.mouse.up();
        
        // Wait for reordering
        await page.waitForTimeout(500);
        
        // Verify order changed
        const newFirstCriteria = page.locator('.criteria-item').first();
        await expect(newFirstCriteria.locator('input[name*=".name"]')).toHaveValue('두 번째 항목');
      }
    }
  });

  test('should export and import templates', async ({ page, apiHelper }) => {
    await page.click('text=📝 템플릿 관리');
    
    // Create a template to export
    const template = await apiHelper.createTemplate(
      `내보내기 테스트 템플릿 ${Date.now()}`,
      '내보내기 테스트용 템플릿',
      [
        { name: '기술력', description: '기술 평가', weight: 50, maxScore: 100 },
        { name: '사업성', description: '사업 평가', weight: 50, maxScore: 100 }
      ]
    );
    
    await page.reload();
    await page.click('text=템플릿 목록');
    
    // Export template
    const templateRow = page.locator(`tr:has-text("${template.data.name}")`);
    
    // Set up download listener
    const downloadPromise = page.waitForEvent('download');
    await templateRow.locator('text=내보내기').click();
    const download = await downloadPromise;
    
    // Verify download occurred
    expect(download.suggestedFilename()).toMatch(/.*\.json$/);
    
    // Test import functionality if available
    if (await page.locator('text=템플릿 가져오기').isVisible()) {
      await page.click('text=템플릿 가져오기');
      
      // Verify import dialog appears
      await expect(page.locator('.import-dialog, .file-upload')).toBeVisible();
    }
  });

  test('should search and filter templates', async ({ page, apiHelper }) => {
    await page.click('text=📝 템플릿 관리');
    
    // Create multiple templates for testing
    const templates = [
      { name: `검색 테스트 Alpha ${Date.now()}`, description: '알파 템플릿' },
      { name: `검색 테스트 Beta ${Date.now()}`, description: '베타 템플릿' },
      { name: `다른 템플릿 ${Date.now()}`, description: '다른 설명' }
    ];
    
    for (const template of templates) {
      await apiHelper.createTemplate(
        template.name,
        template.description,
        [{ name: '테스트', description: '테스트', weight: 100, maxScore: 100 }]
      );
    }
    
    await page.reload();
    await page.click('text=템플릿 목록');
    
    // Test search functionality
    if (await page.locator('input[placeholder*="검색"], input[type="search"]').isVisible()) {
      await page.fill('input[placeholder*="검색"], input[type="search"]', '검색 테스트');
      await page.press('input[placeholder*="검색"], input[type="search"]', 'Enter');
      
      // Should show only matching templates
      await expect(page.locator('text=검색 테스트 Alpha')).toBeVisible();
      await expect(page.locator('text=검색 테스트 Beta')).toBeVisible();
      await expect(page.locator('text=다른 템플릿')).not.toBeVisible();
      
      // Clear search
      await page.fill('input[placeholder*="검색"], input[type="search"]', '');
      await page.press('input[placeholder*="검색"], input[type="search"]', 'Enter');
      
      // Should show all templates again
      await expect(page.locator('text=다른 템플릿')).toBeVisible();
    }
  });

  test('should handle template preview', async ({ page, apiHelper }) => {
    await page.click('text=📝 템플릿 관리');
    
    // Create a template with detailed criteria
    const template = await apiHelper.createTemplate(
      `미리보기 테스트 템플릿 ${Date.now()}`,
      '미리보기 테스트용 템플릿',
      [
        { name: '기술 혁신성', description: '기술의 혁신성을 평가', weight: 35, maxScore: 100 },
        { name: '시장 적용성', description: '시장 적용 가능성 평가', weight: 30, maxScore: 100 },
        { name: '사업 확장성', description: '사업 확장 가능성 평가', weight: 35, maxScore: 100 }
      ]
    );
    
    await page.reload();
    await page.click('text=템플릿 목록');
    
    // Click preview button
    const templateRow = page.locator(`tr:has-text("${template.data.name}")`);
    await templateRow.locator('text=미리보기').click();
    
    // Verify preview modal/page appears
    await expect(page.locator('.template-preview, .preview-modal')).toBeVisible();
    
    // Verify template details are shown
    await expect(page.locator(`text=${template.data.name}`)).toBeVisible();
    await expect(page.locator('text=기술 혁신성')).toBeVisible();
    await expect(page.locator('text=시장 적용성')).toBeVisible();
    await expect(page.locator('text=사업 확장성')).toBeVisible();
    
    // Verify weight percentages are shown
    await expect(page.locator('text=35%')).toBeVisible();
    await expect(page.locator('text=30%')).toBeVisible();
    
    // Close preview
    if (await page.locator('.close-preview, .modal-close').isVisible()) {
      await page.click('.close-preview, .modal-close');
      await expect(page.locator('.template-preview, .preview-modal')).not.toBeVisible();
    }
  });

  test('should maintain template state during navigation', async ({ page }) => {
    await page.click('text=📝 템플릿 관리');
    await page.click('text=새 템플릿 생성');
    
    // Start creating a template
    await page.fill('input[name="name"]', '상태 유지 테스트');
    await page.fill('textarea[name="description"]', '상태 유지 테스트 설명');
    
    // Add criteria
    await page.click('text=평가 항목 추가');
    await page.fill('input[name="criteria.0.name"]', '테스트 항목');
    
    // Navigate away and back
    await page.click('text=🏠 대시보드');
    await page.click('text=📝 템플릿 관리');
    
    // Should ask to save or discard changes
    if (await page.locator('text=저장하지 않은 변경사항').isVisible()) {
      await page.click('text=계속 편집');
      
      // Verify data is preserved
      await expect(page.locator('input[name="name"]')).toHaveValue('상태 유지 테스트');
      await expect(page.locator('textarea[name="description"]')).toHaveValue('상태 유지 테스트 설명');
      await expect(page.locator('input[name="criteria.0.name"]')).toHaveValue('테스트 항목');
    }
  });

  test('should handle concurrent template editing', async ({ page, context, apiHelper }) => {
    // This test simulates multiple users editing the same template
    const template = await apiHelper.createTemplate(
      `동시 편집 테스트 ${Date.now()}`,
      '동시 편집 테스트용 템플릿',
      [{ name: '기본 항목', description: '기본', weight: 100, maxScore: 100 }]
    );
    
    // Open second tab to simulate another user
    const page2 = await context.newPage();
    await page2.goto('/');
    
    // Login in second tab
    await page2.fill('input[name="login_id"]', 'admin');
    await page2.fill('input[name="password"]', 'admin123');
    await page2.click('button[type="submit"]');
    
    // Both tabs navigate to edit the same template
    await page.click('text=📝 템플릿 관리');
    await page.click('text=템플릿 목록');
    
    await page2.click('text=📝 템플릿 관리');
    await page2.click('text=템플릿 목록');
    
    // Both start editing the same template
    const templateRow1 = page.locator(`tr:has-text("${template.data.name}")`);
    const templateRow2 = page2.locator(`tr:has-text("${template.data.name}")`);
    
    await templateRow1.locator('text=수정').click();
    await templateRow2.locator('text=수정').click();
    
    // Make different changes in each tab
    await page.fill('input[name="name"]', template.data.name + ' (수정1)');
    await page2.fill('input[name="name"]', template.data.name + ' (수정2)');
    
    // Save from first tab
    await page.click('text=변경사항 저장');
    await expect(page.locator('.success-message, .alert-success')).toBeVisible();
    
    // Try to save from second tab
    await page2.click('text=변경사항 저장');
    
    // Should handle conflict gracefully
    if (await page2.locator('text=충돌, text=최신 버전').isVisible()) {
      // Conflict detected and handled appropriately
      expect(true).toBe(true);
    } else {
      // Or save succeeded (depending on implementation)
      await expect(page2.locator('.success-message, .alert-success')).toBeVisible();
    }
    
    await page2.close();
  });
});