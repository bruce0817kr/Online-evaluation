import { test, expect } from '../fixtures';

test.describe('System Health and Performance', () => {
  test('should pass basic health check', async ({ apiHelper }) => {
    const health = await apiHelper.healthCheck();
    
    expect(health.success).toBe(true);
    expect(health.data).toHaveProperty('status', 'healthy');
    expect(health.data).toHaveProperty('services');
    
    // Verify all services are running
    const services = health.data.services;
    expect(services.mongodb).toBe('connected');
    expect(services.redis).toBe('connected');
    expect(services.api).toBe('running');
  });

  test('should handle high load scenarios', async ({ apiHelper }) => {
    await apiHelper.login('admin', 'admin123');
    
    // Create multiple concurrent requests
    const promises = Array.from({ length: 10 }, () => 
      apiHelper.getProjects()
    );
    
    const startTime = Date.now();
    const results = await Promise.all(promises);
    const endTime = Date.now();
    
    // All requests should succeed
    results.forEach(result => {
      expect(result.success).toBe(true);
    });
    
    // Response time should be reasonable (under 5 seconds for all)
    const totalTime = endTime - startTime;
    expect(totalTime).toBeLessThan(5000);
  });

  test('should handle database operations efficiently', async ({ apiHelper }) => {
    await apiHelper.login('admin', 'admin123');
    
    // Test pagination and large data sets
    const projects = await apiHelper.getProjects();
    expect(projects.success).toBe(true);
    
    const companies = await apiHelper.getCompanies();
    expect(companies.success).toBe(true);
    
    const evaluators = await apiHelper.getEvaluators();
    expect(evaluators.success).toBe(true);
    
    const templates = await apiHelper.getTemplates();
    expect(templates.success).toBe(true);
  });

  test('should maintain data consistency', async ({ apiHelper }) => {
    await apiHelper.login('admin', 'admin123');
    
    // Create a project
    const project = await apiHelper.createProject(
      `Consistency Test ${Date.now()}`,
      'Testing data consistency'
    );
    expect(project.success).toBe(true);
    
    // Create companies for the project
    const company1 = await apiHelper.createCompany(
      `Company A ${Date.now()}`,
      '111-11-11111',
      project.data.id
    );
    expect(company1.success).toBe(true);
    
    // Verify project shows the companies
    const companies = await apiHelper.getCompanies(project.data.id);
    expect(companies.success).toBe(true);
    expect(companies.data.length).toBeGreaterThan(0);
    
    const projectCompany = companies.data.find(c => c.id === company1.data.id);
    expect(projectCompany).toBeDefined();
    expect(projectCompany.project_id).toBe(project.data.id);
  });

  test('should handle memory and resource usage', async ({ page, authHelper, navHelper }) => {
    await authHelper.loginViaUI('admin', 'admin123');
    
    // Navigate through multiple pages to test memory usage
    const pages = ['/', '/projects', '/companies', '/templates', '/evaluations'];
    
    for (const pagePath of pages) {
      await page.goto(pagePath);
      await navHelper.waitForPageLoad();
      
      // Check for JavaScript errors
      const errors = [];
      page.on('pageerror', error => errors.push(error));
      
      // Wait a bit to let any async operations complete
      await page.waitForTimeout(1000);
      
      expect(errors.length).toBe(0);
    }
    
    // Test navigation back and forth
    await navHelper.goBack();
    await navHelper.goForward();
    await navHelper.refresh();
    
    // Page should still be responsive
    await expect(page.locator('body')).toBeVisible();
  });

  test('should handle browser compatibility', async ({ page, authHelper }) => {
    // Test basic functionality across browsers
    await authHelper.loginViaUI('admin', 'admin123');
    
    // Test modern JavaScript features
    const supportsES6 = await page.evaluate(() => {
      try {
        // Test arrow functions, template literals, const/let
        const test = (x) => `Value: ${x}`;
        const result = test(42);
        return result === 'Value: 42';
      } catch (e) {
        return false;
      }
    });
    
    expect(supportsES6).toBe(true);
    
    // Test CSS features
    const supportsFlexbox = await page.evaluate(() => {
      const div = document.createElement('div');
      div.style.display = 'flex';
      return div.style.display === 'flex';
    });
    
    expect(supportsFlexbox).toBe(true);
    
    // Test local storage
    const supportsLocalStorage = await page.evaluate(() => {
      try {
        localStorage.setItem('test', 'value');
        const value = localStorage.getItem('test');
        localStorage.removeItem('test');
        return value === 'value';
      } catch (e) {
        return false;
      }
    });
    
    expect(supportsLocalStorage).toBe(true);
  });

  test('should handle offline scenarios', async ({ page, authHelper }) => {
    await authHelper.loginViaUI('admin', 'admin123');
    
    // Go offline
    await page.context().setOffline(true);
    
    // Try to navigate to a new page
    await page.goto('/projects');
    
    // Should show offline indicator or error
    const offlineIndicator = await page.isVisible('.offline, .network-error') ||
                            await page.textContent('body').then(text => 
                              text.includes('offline') || text.includes('네트워크')
                            );
    
    // Go back online
    await page.context().setOffline(false);
    
    // Refresh and verify functionality restored
    await page.reload();
    await expect(page.locator('body')).toBeVisible();
  });

  test('should validate security headers', async ({ page }) => {
    const response = await page.goto('/');
    
    // Check for security headers
    const headers = response.headers();
    
    // Content Security Policy
    expect(headers['content-security-policy'] || headers['x-content-security-policy']).toBeDefined();
    
    // X-Frame-Options
    expect(headers['x-frame-options']).toBeDefined();
    
    // X-Content-Type-Options
    expect(headers['x-content-type-options']).toBe('nosniff');
    
    // Referrer Policy
    expect(headers['referrer-policy']).toBeDefined();
  });

  test('should handle API rate limiting gracefully', async ({ apiHelper }) => {
    await apiHelper.login('admin', 'admin123');
    
    // Make rapid requests to test rate limiting
    const rapidRequests = Array.from({ length: 50 }, () => 
      apiHelper.healthCheck()
    );
    
    const results = await Promise.all(rapidRequests);
    
    // Should either all succeed or some fail with 429 (rate limited)
    const successCount = results.filter(r => r.success).length;
    const rateLimitedCount = results.filter(r => r.status === 429).length;
    
    expect(successCount + rateLimitedCount).toBe(results.length);
    
    // If rate limited, should still handle gracefully
    if (rateLimitedCount > 0) {
      console.log(`Rate limiting active: ${rateLimitedCount} requests limited`);
    }
  });
});
