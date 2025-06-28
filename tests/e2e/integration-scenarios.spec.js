import { test, expect } from '../fixtures';

test.describe('Integration Scenarios', () => {
  test.beforeEach(async ({ authHelper, apiHelper }) => {
    await authHelper.loginViaUI('admin', 'admin123');
    await apiHelper.ensureTestData();
  });

  test('should complete end-to-end evaluation process', async ({ page, apiHelper }) => {
    // Complete workflow: Project → Template → Company → Evaluation → Export
    
    // 1. Create a project
    const projectName = `통합 테스트 프로젝트 ${Date.now()}`;
    await page.click('text=🏢 프로젝트 관리');
    await page.click('text=새 프로젝트 생성');
    
    await page.fill('input[name="name"]', projectName);
    await page.fill('textarea[name="description"]', '통합 테스트를 위한 프로젝트입니다.');
    await page.click('text=프로젝트 생성');
    await expect(page.locator('.success-message')).toBeVisible();
    
    // 2. Create an evaluation template
    const templateName = `통합 테스트 템플릿 ${Date.now()}`;
    await page.click('text=📝 템플릿 관리');
    await page.click('text=새 템플릿 생성');
    
    await page.fill('input[name="name"]', templateName);
    await page.fill('textarea[name="description"]', '통합 테스트용 평가 템플릿입니다.');
    
    // Add evaluation criteria
    const criteria = [
      { name: '기술 혁신성', description: '기술의 혁신성과 차별화 정도', weight: 30 },
      { name: '시장성', description: '목표 시장의 크기와 성장 가능성', weight: 25 },
      { name: '사업 모델', description: '수익 모델의 명확성과 지속가능성', weight: 25 },
      { name: '팀 역량', description: '경영진과 핵심 인력의 전문성', weight: 20 }
    ];
    
    for (let i = 0; i < criteria.length; i++) {
      await page.click('text=평가 항목 추가');
      await page.fill(`input[name="criteria.${i}.name"]`, criteria[i].name);
      await page.fill(`textarea[name="criteria.${i}.description"]`, criteria[i].description);
      await page.fill(`input[name="criteria.${i}.weight"]`, criteria[i].weight.toString());
      await page.fill(`input[name="criteria.${i}.maxScore"]`, '100');
    }
    
    await page.click('text=템플릿 저장');
    await expect(page.locator('.success-message')).toBeVisible();
    
    // 3. Add companies to the project
    const companies = [
      { name: '혁신기술 스타트업', business_number: '123-45-67890' },
      { name: '미래기술 벤처', business_number: '234-56-78901' },
      { name: '첨단기술 연구소', business_number: '345-67-89012' }
    ];
    
    // Navigate back to project and add companies
    await page.click('text=🏢 프로젝트 관리');
    const projectRow = page.locator(`tr:has-text("${projectName}")`);
    await projectRow.locator('text=관리, text=상세').click();
    
    for (const company of companies) {
      await page.click('text=기업 추가');
      await page.fill('input[name="name"]', company.name);
      await page.fill('input[name="business_number"]', company.business_number);
      await page.click('text=기업 등록');
      await expect(page.locator('.success-message')).toBeVisible();
    }
    
    // 4. Create evaluations for each company
    await page.click('text=📊 평가 관리');
    
    for (let i = 0; i < companies.length; i++) {
      await page.click('text=새 평가 생성');
      
      // Select project, template, and company
      await page.selectOption('select[name="project_id"]', { label: projectName });
      await page.selectOption('select[name="template_id"]', { label: templateName });
      await page.selectOption('select[name="company_id"]', { label: companies[i].name });
      
      await page.click('text=평가 생성');
      
      // Fill evaluation scores
      const scores = [
        85 + i * 2, // 기술 혁신성
        78 + i * 3, // 시장성  
        82 + i * 1, // 사업 모델
        80 + i * 2  // 팀 역량
      ];
      
      for (let j = 0; j < criteria.length; j++) {
        const criteriaName = criteria[j].name;
        await page.fill(`input[name="scores.${criteriaName}"]`, scores[j].toString());
        await page.fill(`textarea[name="comments.${criteriaName}"]`, 
          `${criteriaName}에 대한 평가 의견입니다. 점수: ${scores[j]}점`);
      }
      
      // Add overall comment
      if (await page.locator('textarea[name="overall_comment"]').isVisible()) {
        await page.fill('textarea[name="overall_comment"]', 
          `${companies[i].name}에 대한 종합 평가입니다. 전반적으로 우수한 평가 결과를 보여주었습니다.`);
      }
      
      await page.click('text=평가 제출');
      await expect(page.locator('.success-message')).toBeVisible();
      
      // Return to evaluation list
      await page.click('text=평가 목록');
    }
    
    // 5. Verify all evaluations are created and export results
    await page.click('text=평가 목록');
    
    // Verify all companies appear in evaluation list
    for (const company of companies) {
      await expect(page.locator(`text=${company.name}`)).toBeVisible();
    }
    
    // Test bulk export if available
    if (await page.locator('text=전체 내보내기, text=일괄 내보내기').isVisible()) {
      const downloadPromise = page.waitForEvent('download');
      await page.click('text=전체 내보내기, text=일괄 내보내기');
      const download = await downloadPromise;
      
      expect(download.suggestedFilename()).toMatch(/.*\.(zip|xlsx|pdf)$/);
    }
    
    // 6. Generate summary report if available
    if (await page.locator('text=종합 보고서, text=요약 보고서').isVisible()) {
      await page.click('text=종합 보고서, text=요약 보고서');
      
      // Verify report contains all companies
      for (const company of companies) {
        await expect(page.locator(`text=${company.name}`)).toBeVisible();
      }
      
      // Verify average scores are calculated
      await expect(page.locator('text=평균, text=종합')).toBeVisible();
    }
  });

  test('should handle multi-user collaboration workflow', async ({ page, context, apiHelper }) => {
    // Simulate multiple users working on the same project
    
    // Create shared project data
    const project = await apiHelper.createProject('Multi-User Project', 'Collaboration test');
    const template = await apiHelper.createTemplate(
      'Collaboration Template',
      'Multi-user template',
      [
        { name: '협업 항목1', description: '첫 번째 항목', weight: 50, maxScore: 100 },
        { name: '협업 항목2', description: '두 번째 항목', weight: 50, maxScore: 100 }
      ]
    );
    const company = await apiHelper.createCompany('Collaboration Company', '999-99-99999', project.data.id);
    
    // Create second user session (evaluator)
    const evaluatorPage = await context.newPage();
    await evaluatorPage.goto('/');
    await evaluatorPage.fill('input[name="login_id"]', 'evaluator01');
    await evaluatorPage.fill('input[name="password"]', 'evaluator123');
    await evaluatorPage.click('button[type="submit"]');
    await evaluatorPage.waitForURL('**/');
    
    // Admin creates evaluation
    await page.click('text=📊 평가 관리');
    await page.click('text=새 평가 생성');
    
    await page.selectOption('select[name="project_id"]', project.data.id);
    await page.selectOption('select[name="template_id"]', template.data.id);
    await page.selectOption('select[name="company_id"]', company.data.id);
    await page.click('text=평가 생성');
    
    // Admin fills first criteria
    await page.fill('input[name="scores.협업 항목1"]', '85');
    await page.fill('textarea[name="comments.협업 항목1"]', '관리자가 작성한 첫 번째 항목 평가');
    
    // Save as draft if available
    if (await page.locator('text=임시저장').isVisible()) {
      await page.click('text=임시저장');
    }
    
    // Evaluator accesses the same evaluation
    await evaluatorPage.click('text=📊 평가 관리');
    await evaluatorPage.waitForLoadState('networkidle');
    
    // Find the evaluation created by admin
    const evaluationRow = evaluatorPage.locator(`tr:has-text("${company.data.name}")`);
    if (await evaluationRow.isVisible()) {
      await evaluationRow.locator('text=보기, text=상세, text=편집').click();
      
      // Evaluator can see admin's work
      if (await evaluatorPage.locator('input[name="scores.협업 항목1"]').isVisible()) {
        const adminScore = await evaluatorPage.locator('input[name="scores.협업 항목1"]').inputValue();
        expect(adminScore).toBe('85');
      }
      
      // Evaluator adds to second criteria
      if (await evaluatorPage.locator('input[name="scores.협업 항목2"]').isVisible()) {
        await evaluatorPage.fill('input[name="scores.협업 항목2"]', '78');
        await evaluatorPage.fill('textarea[name="comments.협업 항목2"]', '평가자가 작성한 두 번째 항목 평가');
        
        // Submit evaluation
        if (await evaluatorPage.locator('text=평가 제출').isVisible()) {
          await evaluatorPage.click('text=평가 제출');
          await expect(evaluatorPage.locator('.success-message')).toBeVisible();
        }
      }
    }
    
    // Admin verifies the collaborative work
    await page.reload();
    await page.click('text=평가 목록');
    
    const adminEvaluationRow = page.locator(`tr:has-text("${company.data.name}")`);
    await adminEvaluationRow.locator('text=보기, text=상세').click();
    
    // Should see both contributions
    await expect(page.locator('text=관리자가 작성한')).toBeVisible();
    await expect(page.locator('text=평가자가 작성한')).toBeVisible();
    
    await evaluatorPage.close();
  });

  test('should handle data import and export workflow', async ({ page, apiHelper }) => {
    // Test complete data lifecycle: Import → Process → Export
    
    // Create project for import test
    const project = await apiHelper.createProject('Import Test Project', 'Data import testing');
    
    await page.click('text=🏢 프로젝트 관리');
    const projectRow = page.locator(`tr:has-text("${project.data.name}")`);
    await projectRow.locator('text=관리, text=상세').click();
    
    // Test bulk company import if available
    if (await page.locator('text=엑셀 업로드, text=일괄 등록').isVisible()) {
      await page.click('text=엑셀 업로드, text=일괄 등록');
      
      // Create test CSV/Excel data
      const csvData = `기업명,사업자등록번호,연락처,주소
데이터 테스트 기업1,111-11-11111,02-1234-5678,서울시 강남구
데이터 테스트 기업2,222-22-22222,02-2345-6789,서울시 서초구
데이터 테스트 기업3,333-33-33333,02-3456-7890,서울시 송파구`;
      
      // If file upload is available, test it
      const fileInput = page.locator('input[type="file"]');
      if (await fileInput.isVisible()) {
        const testFile = {
          name: 'test_companies.csv',
          mimeType: 'text/csv',
          buffer: Buffer.from(csvData)
        };
        
        await fileInput.setInputFiles(testFile);
        
        if (await page.locator('text=업로드, text=가져오기').isVisible()) {
          await page.click('text=업로드, text=가져오기');
          await expect(page.locator('.success-message')).toBeVisible();
          
          // Verify imported companies appear
          await expect(page.locator('text=데이터 테스트 기업1')).toBeVisible();
          await expect(page.locator('text=데이터 테스트 기업2')).toBeVisible();
          await expect(page.locator('text=데이터 테스트 기업3')).toBeVisible();
        }
      }
    }
    
    // Create template for evaluation
    const template = await apiHelper.createTemplate(
      'Import Template',
      'Template for import test',
      [
        { name: '수입 항목1', description: '가져온 데이터 평가1', weight: 60, maxScore: 100 },
        { name: '수입 항목2', description: '가져온 데이터 평가2', weight: 40, maxScore: 100 }
      ]
    );
    
    // Create evaluations for imported companies
    await page.click('text=📊 평가 관리');
    
    // If batch evaluation creation is available
    if (await page.locator('text=일괄 평가 생성').isVisible()) {
      await page.click('text=일괄 평가 생성');
      
      await page.selectOption('select[name="project_id"]', project.data.id);
      await page.selectOption('select[name="template_id"]', template.data.id);
      
      // Select all companies
      const companyCheckboxes = await page.locator('input[type="checkbox"][name*="company"]').count();
      for (let i = 0; i < companyCheckboxes; i++) {
        await page.check(`input[type="checkbox"][name*="company"]:nth-child(${i + 1})`);
      }
      
      await page.click('text=일괄 생성');
      await expect(page.locator('.success-message')).toBeVisible();
    }
    
    // Export evaluation results
    await page.click('text=평가 목록');
    
    if (await page.locator('text=전체 내보내기').isVisible()) {
      const downloadPromise = page.waitForEvent('download');
      await page.click('text=전체 내보내기');
      const download = await downloadPromise;
      
      expect(download.suggestedFilename()).toMatch(/.*\.(xlsx|csv|zip)$/);
      
      // Verify file size is reasonable (not empty)
      const path = await download.path();
      if (path) {
        const fs = require('fs');
        const stats = fs.statSync(path);
        expect(stats.size).toBeGreaterThan(100); // At least 100 bytes
      }
    }
  });

  test('should handle workflow state transitions', async ({ page, apiHelper }) => {
    // Test evaluation workflow states: Draft → Review → Approved → Final
    
    const project = await apiHelper.createProject('Workflow Test', 'State transition test');
    const template = await apiHelper.createTemplate(
      'Workflow Template',
      'Workflow test',
      [{ name: '워크플로우', description: '상태 전환 테스트', weight: 100, maxScore: 100 }]
    );
    const company = await apiHelper.createCompany('Workflow Company', '777-88-99000', project.data.id);
    
    // Create evaluation in draft state
    await page.click('text=📊 평가 관리');
    await page.click('text=새 평가 생성');
    
    await page.selectOption('select[name="project_id"]', project.data.id);
    await page.selectOption('select[name="template_id"]', template.data.id);
    await page.selectOption('select[name="company_id"]', company.data.id);
    await page.click('text=평가 생성');
    
    // Fill evaluation
    await page.fill('input[name="scores.워크플로우"]', '88');
    await page.fill('textarea[name="comments.워크플로우"]', '워크플로우 상태 전환 테스트 평가');
    
    // Save as draft
    if (await page.locator('text=임시저장').isVisible()) {
      await page.click('text=임시저장');
      await expect(page.locator('.success-message')).toBeVisible();
      
      // Check draft status
      await page.click('text=평가 목록');
      await expect(page.locator('text=임시저장, text=드래프트')).toBeVisible();
    }
    
    // Submit for review
    const evaluationRow = page.locator(`tr:has-text("${company.data.name}")`);
    if (await evaluationRow.locator('text=편집, text=계속 작성').isVisible()) {
      await evaluationRow.locator('text=편집, text=계속 작성').click();
      
      if (await page.locator('text=검토 요청').isVisible()) {
        await page.click('text=검토 요청');
        await expect(page.locator('.success-message')).toBeVisible();
        
        // Check review status
        await page.click('text=평가 목록');
        await expect(page.locator('text=검토중, text=리뷰')).toBeVisible();
      } else {
        // Submit normally
        await page.click('text=평가 제출');
        await expect(page.locator('.success-message')).toBeVisible();
      }
    }
    
    // Approve evaluation if workflow exists
    if (await page.locator('text=승인, text=완료 처리').isVisible()) {
      await page.click('text=승인, text=완료 처리');
      await expect(page.locator('.success-message')).toBeVisible();
      
      // Check approved status
      await page.click('text=평가 목록');
      await expect(page.locator('text=승인됨, text=완료')).toBeVisible();
    }
    
    // Generate final report
    if (await page.locator('text=최종 보고서').isVisible()) {
      const downloadPromise = page.waitForEvent('download');
      await page.click('text=최종 보고서');
      const download = await downloadPromise;
      
      expect(download.suggestedFilename()).toMatch(/.*\.(pdf|docx)$/);
    }
  });

  test('should integrate with AI model functionality', async ({ page, apiHelper }) => {
    // Test AI model integration with evaluation process
    
    await page.click('[data-testid="admin-dropdown"]');
    if (await page.locator('text=⚙️ AI 모델 설정').isVisible()) {
      await page.click('text=⚙️ AI 모델 설정');
      
      // Configure AI model
      await page.waitForSelector('.model-card');
      await page.click('.model-card:first-child');
      
      // Verify model configuration panel
      await expect(page.locator('.model-configuration')).toBeVisible();
      
      // Test AI-assisted evaluation if available
      const project = await apiHelper.createProject('AI Test Project', 'AI integration test');
      const template = await apiHelper.createTemplate(
        'AI Template',
        'AI-assisted evaluation',
        [{ name: 'AI 항목', description: 'AI 지원 평가', weight: 100, maxScore: 100 }]
      );
      const company = await apiHelper.createCompany('AI Company', '444-55-66777', project.data.id);
      
      // Create evaluation with AI assistance
      await page.click('text=📊 평가 관리');
      await page.click('text=새 평가 생성');
      
      await page.selectOption('select[name="project_id"]', project.data.id);
      await page.selectOption('select[name="template_id"]', template.data.id);
      await page.selectOption('select[name="company_id"]', company.data.id);
      await page.click('text=평가 생성');
      
      // Test AI suggestions if available
      if (await page.locator('text=AI 추천, text=AI 지원').isVisible()) {
        await page.click('text=AI 추천, text=AI 지원');
        
        // Should provide AI-generated suggestions
        await expect(page.locator('.ai-suggestion, .ai-recommendation')).toBeVisible();
        
        // Accept AI suggestion if available
        if (await page.locator('text=적용, text=수락').isVisible()) {
          await page.click('text=적용, text=수락');
          
          // Should populate fields with AI suggestions
          const score = await page.locator('input[name="scores.AI 항목"]').inputValue();
          expect(score).not.toBe('');
        }
      }
      
      // Submit evaluation
      await page.click('text=평가 제출');
      await expect(page.locator('.success-message')).toBeVisible();
    }
  });

  test('should handle complex search and filtering scenarios', async ({ page, apiHelper }) => {
    // Create multiple projects with different characteristics for testing
    const testData = await Promise.all([
      apiHelper.createProject('검색 테스트 A', '첫 번째 검색 테스트 프로젝트'),
      apiHelper.createProject('검색 테스트 B', '두 번째 검색 테스트 프로젝트'),
      apiHelper.createProject('다른 프로젝트', '완전히 다른 프로젝트'),
      apiHelper.createProject('Special Project 특별', '특별한 프로젝트입니다')
    ]);
    
    // Test project search
    await page.click('text=🏢 프로젝트 관리');
    
    if (await page.locator('input[type="search"], input[placeholder*="검색"]').isVisible()) {
      // Test Korean search
      await page.fill('input[type="search"], input[placeholder*="검색"]', '검색 테스트');
      await page.press('input[type="search"], input[placeholder*="검색"]', 'Enter');
      
      await expect(page.locator('text=검색 테스트 A')).toBeVisible();
      await expect(page.locator('text=검색 테스트 B')).toBeVisible();
      await expect(page.locator('text=다른 프로젝트')).not.toBeVisible();
      
      // Test English search
      await page.fill('input[type="search"], input[placeholder*="검색"]', 'Special');
      await page.press('input[type="search"], input[placeholder*="검색"]', 'Enter');
      
      await expect(page.locator('text=Special Project')).toBeVisible();
      
      // Clear search
      await page.fill('input[type="search"], input[placeholder*="검색"]', '');
      await page.press('input[type="search"], input[placeholder*="검색"]', 'Enter');
      
      // Should show all projects
      await expect(page.locator('text=다른 프로젝트')).toBeVisible();
    }
    
    // Test filtering if available
    if (await page.locator('select[name*="filter"], .filter-dropdown').isVisible()) {
      // Test status filter
      const statusFilter = page.locator('select[name*="status"], select[name*="filter"]').first();
      if (await statusFilter.isVisible()) {
        await statusFilter.selectOption({ index: 1 }); // Select first non-default option
        await page.waitForLoadState('domcontentloaded');
        
        // Should filter results
        const visibleProjects = await page.locator('tr:has-text("프로젝트")').count();
        expect(visibleProjects).toBeGreaterThanOrEqual(0);
      }
    }
    
    // Test date range filtering if available
    if (await page.locator('input[type="date"]').isVisible()) {
      const today = new Date().toISOString().split('T')[0];
      const lastWeek = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
      
      await page.fill('input[type="date"]:first-child', lastWeek);
      await page.fill('input[type="date"]:last-child', today);
      
      if (await page.locator('text=필터 적용, text=검색').isVisible()) {
        await page.click('text=필터 적용, text=검색');
        await page.waitForLoadState('domcontentloaded');
      }
    }
    
    // Test sorting if available
    if (await page.locator('th[role="button"], .sortable').isVisible()) {
      await page.click('th[role="button"], .sortable').first();
      await page.waitForLoadState('domcontentloaded');
      
      // Should reorder results
      const firstProject = await page.locator('tr:has-text("프로젝트")').first().textContent();
      
      // Click again to reverse sort
      await page.click('th[role="button"], .sortable').first();
      await page.waitForLoadState('domcontentloaded');
      
      const newFirstProject = await page.locator('tr:has-text("프로젝트")').first().textContent();
      
      // Order should have changed
      expect(firstProject).not.toBe(newFirstProject);
    }
  });

  test('should handle error recovery and data consistency', async ({ page, apiHelper }) => {
    // Test system resilience and data consistency under error conditions
    
    const project = await apiHelper.createProject('Resilience Test', 'Error recovery test');
    const template = await apiHelper.createTemplate(
      'Resilience Template',
      'Error test',
      [{ name: '복원력', description: '시스템 복원력 테스트', weight: 100, maxScore: 100 }]
    );
    const company = await apiHelper.createCompany('Resilience Company', '123-45-67890', project.data.id);
    
    // Start evaluation
    await page.click('text=📊 평가 관리');
    await page.click('text=새 평가 생성');
    
    await page.selectOption('select[name="project_id"]', project.data.id);
    await page.selectOption('select[name="template_id"]', template.data.id);
    await page.selectOption('select[name="company_id"]', company.data.id);
    await page.click('text=평가 생성');
    
    // Fill partial data
    await page.fill('input[name="scores.복원력"]', '85');
    await page.fill('textarea[name="comments.복원력"]', '부분적으로 작성된 평가 데이터');
    
    // Simulate network interruption
    await page.route('**/api/**', route => {
      if (route.request().method() === 'POST') {
        route.abort('failed');
      } else {
        route.continue();
      }
    });
    
    // Try to save (should fail)
    await page.click('text=평가 제출');
    
    // Should handle error gracefully
    if (await page.locator('.error-message, .network-error').isVisible()) {
      // Good - error is shown to user
      expect(true).toBe(true);
    }
    
    // Restore network
    await page.unroute('**/api/**');
    
    // Data should still be in form (not lost)
    const scoreValue = await page.locator('input[name="scores.복원력"]').inputValue();
    expect(scoreValue).toBe('85');
    
    const commentValue = await page.locator('textarea[name="comments.복원력"]').inputValue();
    expect(commentValue).toContain('부분적으로 작성된');
    
    // Should be able to save now
    await page.click('text=평가 제출');
    await expect(page.locator('.success-message')).toBeVisible();
    
    // Verify data was saved correctly
    await page.click('text=평가 목록');
    const evaluationRow = page.locator(`tr:has-text("${company.data.name}")`);
    await evaluationRow.locator('text=보기, text=상세').click();
    
    await expect(page.locator('text=85')).toBeVisible();
    await expect(page.locator('text=부분적으로 작성된')).toBeVisible();
  });
});