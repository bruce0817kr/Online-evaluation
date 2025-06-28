import { test, expect } from '../fixtures';

test.describe('Evaluation Workflow', () => {
  test.beforeEach(async ({ authHelper, apiHelper }) => {
    await authHelper.loginViaUI('admin', 'admin123');
    
    // Create test data if needed
    await apiHelper.ensureTestData();
  });

  test('should complete full evaluation workflow', async ({ page, apiHelper }) => {
    // Create a project with companies and template
    const project = await apiHelper.createProject(
      `워크플로우 테스트 프로젝트 ${Date.now()}`,
      '전체 평가 워크플로우 테스트'
    );
    
    const template = await apiHelper.createTemplate(
      `워크플로우 템플릿 ${Date.now()}`,
      '워크플로우 테스트용 템플릿',
      [
        { name: '기술력', description: '기술적 역량', weight: 40, maxScore: 100 },
        { name: '사업성', description: '사업적 가능성', weight: 35, maxScore: 100 },
        { name: '시장성', description: '시장 진입 가능성', weight: 25, maxScore: 100 }
      ]
    );
    
    const company = await apiHelper.createCompany(
      `워크플로우 기업 ${Date.now()}`,
      '123-45-67890',
      project.data.id
    );
    
    // Navigate to evaluation creation
    await page.click('text=📊 평가 관리');
    await page.click('text=새 평가 생성');
    
    // Fill evaluation form
    await page.selectOption('select[name="project_id"]', project.data.id);
    await page.selectOption('select[name="template_id"]', template.data.id);
    await page.selectOption('select[name="company_id"]', company.data.id);
    
    // Submit evaluation creation
    await page.click('text=평가 생성');
    
    // Verify evaluation was created and redirect to evaluation page
    await expect(page.locator('.evaluation-form, .evaluation-page')).toBeVisible();
    
    // Fill out evaluation scores
    const criteriaCards = await page.locator('.criteria-card, .evaluation-criteria').count();
    expect(criteriaCards).toBe(3);
    
    // Score each criteria
    await page.fill('input[name="scores.기술력"], input[data-criteria="기술력"]', '85');
    await page.fill('textarea[name="comments.기술력"], textarea[data-criteria="기술력"]', '우수한 기술력을 보유하고 있음');
    
    await page.fill('input[name="scores.사업성"], input[data-criteria="사업성"]', '78');
    await page.fill('textarea[name="comments.사업성"], textarea[data-criteria="사업성"]', '사업 모델이 명확하고 실현 가능성이 높음');
    
    await page.fill('input[name="scores.시장성"], input[data-criteria="시장성"]', '82');
    await page.fill('textarea[name="comments.시장성"], textarea[data-criteria="시장성"]', '시장 요구가 높고 경쟁력이 있음');
    
    // Submit evaluation
    await page.click('text=평가 제출, text=평가 저장');
    
    // Verify success message
    await expect(page.locator('.success-message, .alert-success')).toBeVisible();
    
    // Verify evaluation appears in list
    await page.click('text=평가 목록');
    await expect(page.locator(`text=${company.data.name}`)).toBeVisible();
    
    // Calculate expected total score
    const expectedScore = (85 * 0.4) + (78 * 0.35) + (82 * 0.25);
    await expect(page.locator(`text=${expectedScore.toFixed(1)}`)).toBeVisible();
  });

  test('should handle evaluation draft and auto-save', async ({ page, apiHelper }) => {
    // Create test data
    const project = await apiHelper.createProject('Draft Test Project', 'Test project');
    const template = await apiHelper.createTemplate(
      'Draft Template',
      'Test template',
      [{ name: '테스트', description: '테스트', weight: 100, maxScore: 100 }]
    );
    const company = await apiHelper.createCompany('Draft Company', '111-11-11111', project.data.id);
    
    // Start evaluation
    await page.click('text=📊 평가 관리');
    await page.click('text=새 평가 생성');
    
    await page.selectOption('select[name="project_id"]', project.data.id);
    await page.selectOption('select[name="template_id"]', template.data.id);
    await page.selectOption('select[name="company_id"]', company.data.id);
    await page.click('text=평가 생성');
    
    // Fill partial evaluation
    await page.fill('input[name="scores.테스트"]', '75');
    await page.fill('textarea[name="comments.테스트"]', '부분적으로 작성된 평가입니다.');
    
    // Save as draft
    if (await page.locator('text=임시저장, text=드래프트 저장').isVisible()) {
      await page.click('text=임시저장, text=드래프트 저장');
      await expect(page.locator('.success-message')).toBeVisible();
    }
    
    // Navigate away and back
    await page.click('text=🏠 대시보드');
    await page.click('text=📊 평가 관리');
    await page.click('text=평가 목록');
    
    // Find draft evaluation
    const draftRow = page.locator(`tr:has-text("${company.data.name}"):has-text("임시저장, 드래프트")`);
    if (await draftRow.isVisible()) {
      await draftRow.locator('text=계속 작성, text=편집').click();
      
      // Verify data was saved
      await expect(page.locator('input[name="scores.테스트"]')).toHaveValue('75');
      await expect(page.locator('textarea[name="comments.테스트"]')).toHaveValue('부분적으로 작성된 평가입니다.');
    }
  });

  test('should validate evaluation input constraints', async ({ page, apiHelper }) => {
    // Create test data
    const project = await apiHelper.createProject('Validation Test', 'Test');
    const template = await apiHelper.createTemplate(
      'Validation Template',
      'Test',
      [{ name: '검증', description: '검증', weight: 100, maxScore: 100 }]
    );
    const company = await apiHelper.createCompany('Validation Company', '222-22-22222', project.data.id);
    
    await page.click('text=📊 평가 관리');
    await page.click('text=새 평가 생성');
    
    await page.selectOption('select[name="project_id"]', project.data.id);
    await page.selectOption('select[name="template_id"]', template.data.id);
    await page.selectOption('select[name="company_id"]', company.data.id);
    await page.click('text=평가 생성');
    
    // Test invalid score (over maximum)
    await page.fill('input[name="scores.검증"]', '150');
    await page.click('text=평가 제출, text=평가 저장');
    
    // Should show validation error
    await expect(page.locator('.error-message, .field-error')).toBeVisible();
    
    // Test negative score
    await page.fill('input[name="scores.검증"]', '-10');
    await page.click('text=평가 제출, text=평가 저장');
    
    // Should show validation error
    await expect(page.locator('.error-message, .field-error')).toBeVisible();
    
    // Test empty required fields
    await page.fill('input[name="scores.검증"]', '');
    await page.click('text=평가 제출, text=평가 저장');
    
    // Should show validation error
    await expect(page.locator('.error-message, .field-error')).toBeVisible();
    
    // Test valid input
    await page.fill('input[name="scores.검증"]', '85');
    await page.fill('textarea[name="comments.검증"]', '적절한 평가 점수입니다.');
    await page.click('text=평가 제출, text=평가 저장');
    
    // Should succeed
    await expect(page.locator('.success-message')).toBeVisible();
  });

  test('should handle file uploads in evaluation', async ({ page, apiHelper }) => {
    // Create test data
    const project = await apiHelper.createProject('File Upload Test', 'Test');
    const template = await apiHelper.createTemplate(
      'File Template',
      'Test',
      [{ name: '파일', description: '파일', weight: 100, maxScore: 100 }]
    );
    const company = await apiHelper.createCompany('File Company', '333-33-33333', project.data.id);
    
    await page.click('text=📊 평가 관리');
    await page.click('text=새 평가 생성');
    
    await page.selectOption('select[name="project_id"]', project.data.id);
    await page.selectOption('select[name="template_id"]', template.data.id);
    await page.selectOption('select[name="company_id"]', company.data.id);
    await page.click('text=평가 생성');
    
    // Check if file upload is available
    if (await page.locator('input[type="file"], .file-upload').isVisible()) {
      // Test file upload
      const fileInput = page.locator('input[type="file"]').first();
      
      // Create a test file
      const testFile = {
        name: 'test-document.pdf',
        mimeType: 'application/pdf',
        buffer: Buffer.from('Test PDF content')
      };
      
      await fileInput.setInputFiles(testFile);
      
      // Verify file appears in upload list
      await expect(page.locator('text=test-document.pdf')).toBeVisible();
      
      // Fill evaluation with uploaded file
      await page.fill('input[name="scores.파일"]', '90');
      await page.fill('textarea[name="comments.파일"]', '첨부 파일과 함께 평가를 진행했습니다.');
      
      // Submit evaluation
      await page.click('text=평가 제출, text=평가 저장');
      await expect(page.locator('.success-message')).toBeVisible();
    }
  });

  test('should support batch evaluation creation', async ({ page, apiHelper }) => {
    // Create test data
    const project = await apiHelper.createProject('Batch Test Project', 'Batch evaluation test');
    const template = await apiHelper.createTemplate(
      'Batch Template',
      'Batch test',
      [{ name: '일괄', description: '일괄', weight: 100, maxScore: 100 }]
    );
    
    // Create multiple companies
    const companies = [];
    for (let i = 1; i <= 3; i++) {
      const company = await apiHelper.createCompany(
        `Batch Company ${i}`,
        `${i}${i}${i}-${i}${i}-${i}${i}${i}${i}${i}`,
        project.data.id
      );
      companies.push(company);
    }
    
    await page.click('text=📊 평가 관리');
    
    // Check if batch creation is available
    if (await page.locator('text=일괄 평가 생성, text=여러 평가 생성').isVisible()) {
      await page.click('text=일괄 평가 생성, text=여러 평가 생성');
      
      // Select project and template
      await page.selectOption('select[name="project_id"]', project.data.id);
      await page.selectOption('select[name="template_id"]', template.data.id);
      
      // Select all companies
      for (const company of companies) {
        await page.check(`input[value="${company.data.id}"]`);
      }
      
      // Create batch evaluations
      await page.click('text=일괄 생성');
      
      // Verify success
      await expect(page.locator('.success-message')).toBeVisible();
      
      // Verify all evaluations were created
      await page.click('text=평가 목록');
      for (const company of companies) {
        await expect(page.locator(`text=${company.data.name}`)).toBeVisible();
      }
    }
  });

  test('should export evaluation results', async ({ page, apiHelper }) => {
    // Create evaluation with completed scores
    const project = await apiHelper.createProject('Export Test', 'Export test');
    const template = await apiHelper.createTemplate(
      'Export Template',
      'Export test',
      [
        { name: '수출1', description: '수출1', weight: 50, maxScore: 100 },
        { name: '수출2', description: '수출2', weight: 50, maxScore: 100 }
      ]
    );
    const company = await apiHelper.createCompany('Export Company', '444-44-44444', project.data.id);
    
    // Create evaluation via API for faster setup
    const evaluation = await apiHelper.createEvaluation(
      project.data.id,
      company.data.id,
      template.data.id,
      { '수출1': 80, '수출2': 90 },
      { '수출1': '좋은 점수', '수출2': '매우 좋은 점수' }
    );
    
    await page.click('text=📊 평가 관리');
    await page.click('text=평가 목록');
    
    // Find evaluation and export
    const evaluationRow = page.locator(`tr:has-text("${company.data.name}")`);
    
    // Test individual export
    const downloadPromise = page.waitForEvent('download');
    await evaluationRow.locator('text=내보내기, text=다운로드').click();
    const download = await downloadPromise;
    
    expect(download.suggestedFilename()).toMatch(/.*\.(pdf|xlsx|json)$/);
    
    // Test bulk export if available
    if (await page.locator('text=전체 내보내기, text=일괄 내보내기').isVisible()) {
      const bulkDownloadPromise = page.waitForEvent('download');
      await page.click('text=전체 내보내기, text=일괄 내보내기');
      const bulkDownload = await bulkDownloadPromise;
      
      expect(bulkDownload.suggestedFilename()).toMatch(/.*\.(zip|xlsx)$/);
    }
  });

  test('should handle evaluation comments and feedback', async ({ page, apiHelper }) => {
    // Create test data
    const project = await apiHelper.createProject('Comment Test', 'Comment test');
    const template = await apiHelper.createTemplate(
      'Comment Template',
      'Comment test',
      [{ name: '댓글', description: '댓글', weight: 100, maxScore: 100 }]
    );
    const company = await apiHelper.createCompany('Comment Company', '555-55-55555', project.data.id);
    
    await page.click('text=📊 평가 관리');
    await page.click('text=새 평가 생성');
    
    await page.selectOption('select[name="project_id"]', project.data.id);
    await page.selectOption('select[name="template_id"]', template.data.id);
    await page.selectOption('select[name="company_id"]', company.data.id);
    await page.click('text=평가 생성');
    
    // Fill evaluation with detailed comments
    await page.fill('input[name="scores.댓글"]', '88');
    
    const detailedComment = `
상세 평가 의견:
1. 기술적 우수성: 최신 기술을 적절히 활용하고 있음
2. 시장 접근성: 타겟 시장이 명확하고 진입 전략이 구체적임
3. 팀 역량: 핵심 인력의 전문성이 높음
4. 개선사항: 마케팅 전략의 구체화 필요

전반적으로 우수한 평가 대상으로 판단됨.
    `.trim();
    
    await page.fill('textarea[name="comments.댓글"]', detailedComment);
    
    // Add overall evaluation summary if available
    if (await page.locator('textarea[name="overall_comments"], textarea[name="summary"]').isVisible()) {
      await page.fill(
        'textarea[name="overall_comments"], textarea[name="summary"]',
        '종합적으로 투자 가치가 높은 기업으로 평가됩니다.'
      );
    }
    
    // Submit evaluation
    await page.click('text=평가 제출');
    await expect(page.locator('.success-message')).toBeVisible();
    
    // Verify comments are saved by viewing the evaluation
    await page.click('text=평가 목록');
    const evaluationRow = page.locator(`tr:has-text("${company.data.name}")`);
    await evaluationRow.locator('text=보기, text=상세').click();
    
    // Verify detailed comments are displayed
    await expect(page.locator('text=기술적 우수성')).toBeVisible();
    await expect(page.locator('text=마케팅 전략의 구체화')).toBeVisible();
  });

  test('should track evaluation history and revisions', async ({ page, apiHelper }) => {
    // Create test data
    const project = await apiHelper.createProject('History Test', 'History test');
    const template = await apiHelper.createTemplate(
      'History Template',
      'History test',
      [{ name: '이력', description: '이력', weight: 100, maxScore: 100 }]
    );
    const company = await apiHelper.createCompany('History Company', '666-66-66666', project.data.id);
    
    // Create initial evaluation
    await page.click('text=📊 평가 관리');
    await page.click('text=새 평가 생성');
    
    await page.selectOption('select[name="project_id"]', project.data.id);
    await page.selectOption('select[name="template_id"]', template.data.id);
    await page.selectOption('select[name="company_id"]', company.data.id);
    await page.click('text=평가 생성');
    
    // Initial evaluation
    await page.fill('input[name="scores.이력"]', '75');
    await page.fill('textarea[name="comments.이력"]', '초기 평가 의견입니다.');
    await page.click('text=평가 제출');
    await expect(page.locator('.success-message')).toBeVisible();
    
    // Edit evaluation if possible
    await page.click('text=평가 목록');
    const evaluationRow = page.locator(`tr:has-text("${company.data.name}")`);
    
    if (await evaluationRow.locator('text=수정, text=편집').isVisible()) {
      await evaluationRow.locator('text=수정, text=편집').click();
      
      // Modify scores
      await page.fill('input[name="scores.이력"]', '85');
      await page.fill('textarea[name="comments.이력"]', '수정된 평가 의견입니다. 추가적인 정보를 반영했습니다.');
      await page.click('text=변경사항 저장');
      await expect(page.locator('.success-message')).toBeVisible();
      
      // Check if revision history is available
      if (await page.locator('text=이력 보기, text=변경 기록').isVisible()) {
        await page.click('text=이력 보기, text=변경 기록');
        
        // Verify both versions are shown
        await expect(page.locator('text=75')).toBeVisible(); // Original score
        await expect(page.locator('text=85')).toBeVisible(); // Updated score
        await expect(page.locator('text=초기 평가 의견')).toBeVisible();
        await expect(page.locator('text=수정된 평가 의견')).toBeVisible();
      }
    }
  });

  test('should handle evaluation status workflow', async ({ page, apiHelper }) => {
    // Create test data
    const project = await apiHelper.createProject('Status Test', 'Status workflow test');
    const template = await apiHelper.createTemplate(
      'Status Template',
      'Status test',
      [{ name: '상태', description: '상태', weight: 100, maxScore: 100 }]
    );
    const company = await apiHelper.createCompany('Status Company', '777-77-77777', project.data.id);
    
    await page.click('text=📊 평가 관리');
    await page.click('text=새 평가 생성');
    
    await page.selectOption('select[name="project_id"]', project.data.id);
    await page.selectOption('select[name="template_id"]', template.data.id);
    await page.selectOption('select[name="company_id"]', company.data.id);
    await page.click('text=평가 생성');
    
    // Fill evaluation
    await page.fill('input[name="scores.상태"]', '92');
    await page.fill('textarea[name="comments.상태"]', '상태 변화 테스트 평가');
    
    // Submit for review if workflow exists
    if (await page.locator('text=검토 요청, text=승인 요청').isVisible()) {
      await page.click('text=검토 요청, text=승인 요청');
      await expect(page.locator('.success-message')).toBeVisible();
      
      // Check status in list
      await page.click('text=평가 목록');
      const statusCell = page.locator(`tr:has-text("${company.data.name}") .status, tr:has-text("${company.data.name}") td:has-text("검토")`);
      await expect(statusCell).toBeVisible();
      
      // If there's an approve/reject function
      if (await page.locator('text=승인, text=반려').isVisible()) {
        await page.click('text=승인');
        await expect(page.locator('text=승인됨, text=완료')).toBeVisible();
      }
    } else {
      // Simple submit
      await page.click('text=평가 제출');
      await expect(page.locator('.success-message')).toBeVisible();
    }
  });
});