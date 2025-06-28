import { test, expect } from '../fixtures';
import path from 'path';
import fs from 'fs';

test.describe('Complete User Workflow', () => {
  let testData = {};

  test.beforeAll(async () => {
    // Load test data created in global setup
    const testDataPath = path.join(__dirname, '../test-data/setup-data.json');
    if (fs.existsSync(testDataPath)) {
      testData = JSON.parse(fs.readFileSync(testDataPath, 'utf8'));
    }
  });

  test.describe('Admin Workflow', () => {
    test('should complete full admin workflow', async ({ authHelper, apiHelper, navHelper, page }) => {
      // Step 1: Login as admin
      await authHelper.loginViaAPI('admin', 'admin123');
      await page.goto('/');
      
      // Step 2: Create a new project
      const project = await apiHelper.createProject(
        `Test Project ${Date.now()}`,
        'Project for complete workflow testing'
      );
      expect(project.success).toBe(true);
      expect(project.data).toHaveProperty('id');
      
      // Step 3: Create companies for the project
      const company1 = await apiHelper.createCompany(
        `Test Company 1 ${Date.now()}`,
        '111-11-11111',
        project.data.id
      );
      expect(company1.success).toBe(true);
      
      const company2 = await apiHelper.createCompany(
        `Test Company 2 ${Date.now()}`,
        '222-22-22222',
        project.data.id
      );
      expect(company2.success).toBe(true);
      
      // Step 4: Create evaluators
      const evaluator1 = await apiHelper.createEvaluator(
        `Test Evaluator 1 ${Date.now()}`,
        '010-1111-1111',
        `evaluator1.${Date.now()}@test.com`
      );
      expect(evaluator1.success).toBe(true);
      
      const evaluator2 = await apiHelper.createEvaluator(
        `Test Evaluator 2 ${Date.now()}`,
        '010-2222-2222',
        `evaluator2.${Date.now()}@test.com`
      );
      expect(evaluator2.success).toBe(true);
      
      // Step 5: Create evaluation template
      const template = await apiHelper.createTemplate(
        `Test Template ${Date.now()}`,
        'Template for complete workflow testing',
        project.data.id
      );
      expect(template.success).toBe(true);
      expect(template.data).toHaveProperty('id');
      
      // Step 6: Create assignments
      const assignments = await apiHelper.createAssignments(
        [evaluator1.data.id, evaluator2.data.id],
        [company1.data.id, company2.data.id],
        template.data.id,
        new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString() // 30 days from now
      );
      expect(assignments.success).toBe(true);
      
      // Step 7: Verify admin dashboard shows the data
      const adminDashboard = await apiHelper.getAdminDashboard();
      expect(adminDashboard.success).toBe(true);
      expect(adminDashboard.data).toHaveProperty('stats');
      
      // Step 8: Check project analytics
      const analytics = await apiHelper.getProjectAnalytics(project.data.id);
      expect(analytics.success).toBe(true);
      
      // Store data for evaluator workflow
      testData.workflowProject = project.data;
      testData.workflowCompanies = [company1.data, company2.data];
      testData.workflowEvaluators = [evaluator1.data, evaluator2.data];
      testData.workflowTemplate = template.data;
    });
  });

  test.describe('Evaluator Workflow', () => {
    test('should complete full evaluator workflow', async ({ authHelper, apiHelper, page }) => {
      // Step 1: Login as evaluator
      const evaluatorCredentials = testData.workflowEvaluators?.[0];
      if (!evaluatorCredentials) {
        test.skip('No evaluator credentials available from admin workflow');
      }
      
      await authHelper.loginViaAPI(
        evaluatorCredentials.login_id,
        evaluatorCredentials.password
      );
      
      // Step 2: Check evaluator dashboard
      const dashboard = await apiHelper.getEvaluatorDashboard();
      expect(dashboard.success).toBe(true);
      expect(Array.isArray(dashboard.data)).toBe(true);
      
      if (dashboard.data.length === 0) {
        test.skip('No evaluation assignments available');
      }
      
      const assignment = dashboard.data[0];
      const sheetId = assignment.sheet.id;
      
      // Step 3: Get evaluation sheet
      const sheet = await apiHelper.getEvaluationSheet(sheetId);
      expect(sheet.success).toBe(true);
      expect(sheet.data).toHaveProperty('template');
      expect(sheet.data).toHaveProperty('company');
      
      // Step 4: Save evaluation as draft (auto-save simulation)
      const draftScores = sheet.data.template.items.reduce((scores, item, index) => {
        scores[item.name] = Math.floor(Math.random() * item.max_score) + 1;
        return scores;
      }, {});
      
      const saveResult = await apiHelper.saveEvaluation(sheetId, draftScores);
      expect(saveResult.success).toBe(true);
      
      // Step 5: Submit final evaluation
      const finalScores = sheet.data.template.items.reduce((scores, item, index) => {
        scores[item.name] = Math.floor(Math.random() * item.max_score) + 1;
        return scores;
      }, {});
      
      const submitResult = await apiHelper.submitEvaluation(sheetId, finalScores);
      expect(submitResult.success).toBe(true);
      
      // Step 6: Verify dashboard shows updated status
      const updatedDashboard = await apiHelper.getEvaluatorDashboard();
      expect(updatedDashboard.success).toBe(true);
      
      const submittedAssignment = updatedDashboard.data.find(a => a.sheet.id === sheetId);
      expect(submittedAssignment.sheet.status).toBe('submitted');
    });
  });

  test.describe('File Management Workflow', () => {
    test('should handle file upload and preview workflow', async ({ authHelper, apiHelper, page, navHelper }) => {
      await authHelper.loginViaAPI('admin', 'admin123');
      
      // Create test file for upload
      const testFilePath = path.join(__dirname, '../test-data/test-document.pdf');
      if (!fs.existsSync(path.dirname(testFilePath))) {
        fs.mkdirSync(path.dirname(testFilePath), { recursive: true });
      }
      
      // Create a simple PDF-like file for testing
      fs.writeFileSync(testFilePath, '%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000010 00000 n \n0000000053 00000 n \n0000000100 00000 n \ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n149\n%%EOF');
      
      // Navigate to company page for file upload
      const company = testData.workflowCompanies?.[0];
      if (!company) {
        test.skip('No company available for file upload test');
      }
      
      await navHelper.goToCompany(company.id);
      
      // Upload file via UI
      await navHelper.uploadFile('input[type="file"]', testFilePath);
      
      // Wait for upload to complete
      await page.waitForTimeout(2000);
      
      // Verify file appears in company files list
      await expect(page.locator('.file-list, .uploaded-files')).toBeVisible();
      await expect(page.locator('text=test-document.pdf')).toBeVisible();
      
      // Test file preview
      await page.click('text=test-document.pdf');
      
      // Should open preview (either modal or new tab)
      const previewVisible = await page.isVisible('.pdf-preview, .file-preview') ||
                            await page.isVisible('embed[type="application/pdf"]');
      
      expect(previewVisible).toBe(true);
      
      // Cleanup
      fs.unlinkSync(testFilePath);
    });
  });

  test.describe('Analytics and Reporting Workflow', () => {
    test('should generate and access analytics reports', async ({ authHelper, apiHelper, page, navHelper }) => {
      await authHelper.loginViaAPI('admin', 'admin123');
      
      const project = testData.workflowProject;
      if (!project) {
        test.skip('No project available for analytics test');
      }
      
      // Get project analytics
      const analytics = await apiHelper.getProjectAnalytics(project.id);
      expect(analytics.success).toBe(true);
      expect(analytics.data).toHaveProperty('total_companies');
      expect(analytics.data).toHaveProperty('companies_evaluated');
      expect(analytics.data).toHaveProperty('completion_rate');
      
      // Navigate to analytics page
      await navHelper.goToAnalytics();
      
      // Verify charts and data are displayed
      await expect(page.locator('.chart, canvas, svg')).toBeVisible();
      await expect(page.locator('.analytics-stats, .metrics')).toBeVisible();
      
      // Test export functionality (if available)
      const exportButton = page.locator('button:has-text("Export"), button:has-text("다운로드")');
      if (await exportButton.isVisible()) {
        await exportButton.click();
        
        // Should trigger download or show export options
        await page.waitForTimeout(1000);
        
        const downloadDialog = page.locator('.export-dialog, .download-options');
        if (await downloadDialog.isVisible()) {
          await expect(downloadDialog).toBeVisible();
        }
      }
    });
  });

  test.describe('Error Handling and Edge Cases', () => {
    test('should handle network errors gracefully', async ({ page, authHelper }) => {
      await authHelper.loginViaUI('admin', 'admin123');
      
      // Simulate network failure
      await page.route('**/api/**', route => route.abort());
      
      // Try to navigate to a page that requires API calls
      await page.goto('/projects');
      
      // Should show error state or loading state
      const errorVisible = await page.isVisible('.error, .network-error, .loading-error') ||
                          await page.isVisible('text=에러, text=오류, text=Error');
      
      expect(errorVisible).toBe(true);
    });

    test('should handle invalid data gracefully', async ({ apiHelper }) => {
      await apiHelper.login('admin', 'admin123');
      
      // Try to create project with invalid data
      const invalidProject = await apiHelper.createProject('', ''); // Empty name
      expect(invalidProject.success).toBe(false);
      expect(invalidProject.status).toBeGreaterThanOrEqual(400);
      
      // Try to create company with invalid business number
      const project = testData.workflowProject;
      if (project) {
        const invalidCompany = await apiHelper.createCompany(
          'Test Company',
          'invalid-business-number',
          project.id
        );
        expect(invalidCompany.success).toBe(false);
      }
    });

    test('should handle concurrent operations', async ({ apiHelper }) => {
      await apiHelper.login('admin', 'admin123');
      
      // Create multiple projects concurrently
      const projectPromises = Array.from({ length: 3 }, (_, i) =>
        apiHelper.createProject(
          `Concurrent Project ${i} ${Date.now()}`,
          `Description ${i}`
        )
      );
      
      const results = await Promise.all(projectPromises);
      
      // All should succeed or fail gracefully
      results.forEach(result => {
        expect(result.status).toBeLessThan(500); // No server errors
      });
      
      const successCount = results.filter(r => r.success).length;
      expect(successCount).toBeGreaterThan(0); // At least one should succeed
    });
  });
});
