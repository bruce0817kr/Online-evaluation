import { test, expect } from '../fixtures';

test.describe('Performance Monitoring', () => {
  test.beforeEach(async ({ authHelper }) => {
    await authHelper.loginViaUI('admin', 'admin123');
  });

  test('should monitor page load performance', async ({ page }) => {
    const performanceMetrics = {
      loadTime: 0,
      domContentLoaded: 0,
      firstContentfulPaint: 0,
      largestContentfulPaint: 0,
      cumulativeLayoutShift: 0
    };

    // Monitor navigation timing
    await page.addInitScript(() => {
      window.addEventListener('load', () => {
        const navigation = performance.getEntriesByType('navigation')[0];
        window.performanceMetrics = {
          loadTime: navigation.loadEventEnd - navigation.fetchStart,
          domContentLoaded: navigation.domContentLoadedEventEnd - navigation.fetchStart,
          transferSize: navigation.transferSize,
          encodedBodySize: navigation.encodedBodySize
        };
      });
    });

    // Navigate to main pages and measure performance
    const pages = [
      { path: '/', name: 'Dashboard' },
      { path: '/projects', name: 'Projects' },
      { path: '/companies', name: 'Companies' },
      { path: '/templates', name: 'Templates' },
      { path: '/evaluations', name: 'Evaluations' }
    ];

    for (const pageInfo of pages) {
      const startTime = Date.now();
      await page.goto(pageInfo.path);
      
      // Wait for page to be fully loaded
      await page.waitForLoadState('networkidle');
      const endTime = Date.now();
      
      const loadTime = endTime - startTime;
      
      // Verify page loads within acceptable time (5 seconds)
      expect(loadTime).toBeLessThan(5000);
      
      // Get detailed performance metrics
      const metrics = await page.evaluate(() => window.performanceMetrics);
      if (metrics) {
        expect(metrics.loadTime).toBeLessThan(3000); // 3 seconds max load time
        expect(metrics.domContentLoaded).toBeLessThan(2000); // 2 seconds max DOM ready
      }
      
      console.log(`${pageInfo.name} page load time: ${loadTime}ms`);
    }
  });

  test('should handle high-frequency user interactions', async ({ page }) => {
    await page.goto('/');
    
    // Simulate rapid clicking and navigation
    const startTime = Date.now();
    
    for (let i = 0; i < 10; i++) {
      // Rapid navigation between tabs/sections
      if (await page.locator('text=📊 평가 관리').isVisible()) {
        await page.click('text=📊 평가 관리');
        await page.waitForLoadState('domcontentloaded');
      }
      
      if (await page.locator('text=📝 템플릿 관리').isVisible()) {
        await page.click('text=📝 템플릿 관리');
        await page.waitForLoadState('domcontentloaded');
      }
      
      if (await page.locator('text=🏢 프로젝트 관리').isVisible()) {
        await page.click('text=🏢 프로젝트 관리');
        await page.waitForLoadState('domcontentloaded');
      }
      
      // Brief pause to avoid overwhelming
      await page.waitForTimeout(100);
    }
    
    const endTime = Date.now();
    const totalTime = endTime - startTime;
    
    // Should handle rapid interactions within reasonable time
    expect(totalTime).toBeLessThan(10000); // 10 seconds for all interactions
    
    // Page should still be responsive
    await expect(page.locator('body')).toBeVisible();
  });

  test('should monitor memory usage during extended use', async ({ page }) => {
    await page.goto('/');
    
    // Track memory usage
    const getMemoryUsage = async () => {
      return await page.evaluate(() => {
        if (performance.memory) {
          return {
            usedJSHeapSize: performance.memory.usedJSHeapSize,
            totalJSHeapSize: performance.memory.totalJSHeapSize,
            jsHeapSizeLimit: performance.memory.jsHeapSizeLimit
          };
        }
        return null;
      });
    };
    
    const initialMemory = await getMemoryUsage();
    
    // Simulate extended usage
    for (let i = 0; i < 20; i++) {
      // Navigate to different pages
      await page.click('text=📊 평가 관리');
      await page.waitForLoadState('domcontentloaded');
      
      // Create some DOM elements and interactions
      if (await page.locator('text=새 평가 생성').isVisible()) {
        await page.click('text=새 평가 생성');
        await page.waitForTimeout(500);
        
        // Go back to list
        if (await page.locator('text=평가 목록').isVisible()) {
          await page.click('text=평가 목록');
        }
      }
      
      await page.waitForTimeout(200);
    }
    
    const finalMemory = await getMemoryUsage();
    
    if (initialMemory && finalMemory) {
      const memoryIncrease = finalMemory.usedJSHeapSize - initialMemory.usedJSHeapSize;
      const memoryIncreasePercent = (memoryIncrease / initialMemory.usedJSHeapSize) * 100;
      
      // Memory should not increase by more than 200% during normal usage
      expect(memoryIncreasePercent).toBeLessThan(200);
      
      console.log(`Memory usage increase: ${(memoryIncrease / 1024 / 1024).toFixed(2)}MB (${memoryIncreasePercent.toFixed(1)}%)`);
    }
  });

  test('should measure API response times', async ({ page, apiHelper }) => {
    await apiHelper.login('admin', 'admin123');
    
    // Test various API endpoints
    const apiTests = [
      { endpoint: 'projects', method: 'GET', name: 'Get Projects' },
      { endpoint: 'companies', method: 'GET', name: 'Get Companies' },
      { endpoint: 'templates', method: 'GET', name: 'Get Templates' },
      { endpoint: 'evaluations', method: 'GET', name: 'Get Evaluations' },
      { endpoint: 'health', method: 'GET', name: 'Health Check' }
    ];
    
    for (const apiTest of apiTests) {
      const startTime = Date.now();
      
      let response;
      switch (apiTest.method) {
        case 'GET':
          response = await apiHelper.get(apiTest.endpoint);
          break;
        default:
          continue;
      }
      
      const endTime = Date.now();
      const responseTime = endTime - startTime;
      
      // API responses should be under 2 seconds
      expect(responseTime).toBeLessThan(2000);
      expect(response.success).toBe(true);
      
      console.log(`${apiTest.name} response time: ${responseTime}ms`);
    }
  });

  test('should handle concurrent user sessions', async ({ page, context }) => {
    // Create multiple browser contexts to simulate different users
    const userSessions = [];
    const numberOfSessions = 5;
    
    for (let i = 0; i < numberOfSessions; i++) {
      const newContext = await context.browser().newContext();
      const newPage = await newContext.newPage();
      userSessions.push({ context: newContext, page: newPage });
    }
    
    // Login all sessions concurrently
    const loginPromises = userSessions.map(async (session, index) => {
      await session.page.goto('/');
      await session.page.fill('input[name="login_id"]', 'admin');
      await session.page.fill('input[name="password"]', 'admin123');
      await session.page.click('button[type="submit"]');
      await session.page.waitForURL('**/');
    });
    
    const startTime = Date.now();
    await Promise.all(loginPromises);
    const loginTime = Date.now() - startTime;
    
    // All sessions should login within reasonable time
    expect(loginTime).toBeLessThan(10000); // 10 seconds for all sessions
    
    // Have all sessions perform actions concurrently
    const actionPromises = userSessions.map(async (session, index) => {
      // Each session navigates to different pages
      const actions = [
        () => session.page.click('text=📊 평가 관리'),
        () => session.page.click('text=📝 템플릿 관리'),
        () => session.page.click('text=🏢 프로젝트 관리'),
        () => session.page.click('text=🏠 대시보드')
      ];
      
      for (const action of actions) {
        try {
          await action();
          await session.page.waitForLoadState('domcontentloaded');
          await session.page.waitForTimeout(500);
        } catch (error) {
          console.warn(`Session ${index} action failed:`, error.message);
        }
      }
    });
    
    const actionsStartTime = Date.now();
    await Promise.all(actionPromises);
    const actionsTime = Date.now() - actionsStartTime;
    
    // Concurrent actions should complete within reasonable time
    expect(actionsTime).toBeLessThan(15000); // 15 seconds for all actions
    
    // Verify all sessions are still functional
    for (const session of userSessions) {
      await expect(session.page.locator('body')).toBeVisible();
    }
    
    // Clean up sessions
    for (const session of userSessions) {
      await session.context.close();
    }
  });

  test('should measure form submission performance', async ({ page, apiHelper }) => {
    // Create test data for consistent testing
    const project = await apiHelper.createProject('Performance Test Project', 'Performance testing');
    const template = await apiHelper.createTemplate(
      'Performance Template',
      'Performance testing template',
      [
        { name: '성능1', description: '성능 테스트 1', weight: 25, maxScore: 100 },
        { name: '성능2', description: '성능 테스트 2', weight: 25, maxScore: 100 },
        { name: '성능3', description: '성능 테스트 3', weight: 25, maxScore: 100 },
        { name: '성능4', description: '성능 테스트 4', weight: 25, maxScore: 100 }
      ]
    );
    
    // Test template creation performance
    await page.click('text=📝 템플릿 관리');
    await page.click('text=새 템플릿 생성');
    
    const formStartTime = Date.now();
    
    // Fill out complex form
    await page.fill('input[name="name"]', `성능 테스트 템플릿 ${Date.now()}`);
    await page.fill('textarea[name="description"]', '성능 테스트를 위한 복잡한 템플릿입니다.');
    
    // Add multiple criteria
    for (let i = 0; i < 5; i++) {
      await page.click('text=평가 항목 추가');
      await page.fill(`input[name="criteria.${i}.name"]`, `성능 항목 ${i + 1}`);
      await page.fill(`textarea[name="criteria.${i}.description"]`, `성능 테스트 항목 ${i + 1}에 대한 설명입니다.`);
      await page.fill(`input[name="criteria.${i}.weight"]`, '20');
      await page.fill(`input[name="criteria.${i}.maxScore"]`, '100');
    }
    
    // Submit form and measure time
    await page.click('text=템플릿 저장');
    
    // Wait for success message
    await expect(page.locator('.success-message, .alert-success')).toBeVisible({ timeout: 10000 });
    
    const formEndTime = Date.now();
    const formSubmissionTime = formEndTime - formStartTime;
    
    // Form submission should complete within 5 seconds
    expect(formSubmissionTime).toBeLessThan(5000);
    
    console.log(`Complex form submission time: ${formSubmissionTime}ms`);
  });

  test('should monitor network performance', async ({ page }) => {
    // Track network requests
    const networkRequests = [];
    
    page.on('request', request => {
      networkRequests.push({
        url: request.url(),
        method: request.method(),
        startTime: Date.now()
      });
    });
    
    page.on('response', response => {
      const request = networkRequests.find(req => req.url === response.url());
      if (request) {
        request.endTime = Date.now();
        request.duration = request.endTime - request.startTime;
        request.status = response.status();
        request.size = response.headers()['content-length'];
      }
    });
    
    // Navigate through application
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    await page.click('text=📊 평가 관리');
    await page.waitForLoadState('networkidle');
    
    await page.click('text=📝 템플릿 관리');
    await page.waitForLoadState('networkidle');
    
    // Analyze network performance
    const apiRequests = networkRequests.filter(req => 
      req.url.includes('/api/') && req.endTime
    );
    
    const staticRequests = networkRequests.filter(req => 
      (req.url.includes('.js') || req.url.includes('.css') || req.url.includes('.png')) && req.endTime
    );
    
    // API requests should be fast
    for (const request of apiRequests) {
      expect(request.duration).toBeLessThan(3000); // 3 seconds max for API calls
      expect(request.status).toBeLessThan(400); // No client or server errors
    }
    
    // Static resources should load quickly
    for (const request of staticRequests) {
      expect(request.duration).toBeLessThan(2000); // 2 seconds max for static resources
    }
    
    console.log(`API requests: ${apiRequests.length}, avg time: ${
      apiRequests.reduce((sum, req) => sum + req.duration, 0) / apiRequests.length || 0
    }ms`);
    
    console.log(`Static requests: ${staticRequests.length}, avg time: ${
      staticRequests.reduce((sum, req) => sum + req.duration, 0) / staticRequests.length || 0
    }ms`);
  });

  test('should handle large data sets efficiently', async ({ page, apiHelper }) => {
    await apiHelper.login('admin', 'admin123');
    
    // Create a project with many companies for testing
    const project = await apiHelper.createProject('Large Dataset Test', 'Testing large datasets');
    
    // Create multiple companies (simulate large dataset)
    const companies = [];
    const companyCreationStart = Date.now();
    
    for (let i = 0; i < 20; i++) {
      const company = await apiHelper.createCompany(
        `Large Dataset Company ${i + 1}`,
        `${String(i + 1).padStart(3, '0')}-11-11111`,
        project.data.id
      );
      companies.push(company);
    }
    
    const companyCreationTime = Date.now() - companyCreationStart;
    console.log(`Created 20 companies in ${companyCreationTime}ms`);
    
    // Test loading large company list
    await page.click('text=🏢 프로젝트 관리');
    
    const loadStartTime = Date.now();
    
    // Navigate to project detail to see companies
    const projectRow = page.locator(`tr:has-text("${project.data.name}")`);
    if (await projectRow.isVisible()) {
      await projectRow.locator('text=상세, text=보기').click();
    }
    
    // Wait for companies to load
    await page.waitForSelector('.company-list, .companies-grid', { timeout: 10000 });
    
    const loadEndTime = Date.now();
    const loadTime = loadEndTime - loadStartTime;
    
    // Should load large dataset within reasonable time
    expect(loadTime).toBeLessThan(5000); // 5 seconds max
    
    // Verify all companies are displayed or paginated properly
    const displayedCompanies = await page.locator('.company-card, .company-item').count();
    
    // Should show companies (either all or first page)
    expect(displayedCompanies).toBeGreaterThan(0);
    
    // Test pagination if available
    if (await page.locator('.pagination, .page-numbers').isVisible()) {
      const nextButton = page.locator('text=다음, .next-page');
      if (await nextButton.isVisible()) {
        await nextButton.click();
        await page.waitForLoadState('domcontentloaded');
        
        // Should still have companies on next page
        const nextPageCompanies = await page.locator('.company-card, .company-item').count();
        expect(nextPageCompanies).toBeGreaterThan(0);
      }
    }
    
    console.log(`Loaded large dataset in ${loadTime}ms, showing ${displayedCompanies} items`);
  });

  test('should monitor error handling performance', async ({ page }) => {
    // Test how quickly the app recovers from errors
    const errorRecoveryTests = [
      {
        name: 'Network Error Recovery',
        action: async () => {
          // Simulate network failure
          await page.route('**/api/**', route => {
            route.abort('failed');
          });
          
          await page.click('text=📊 평가 관리');
          await page.waitForTimeout(1000);
          
          // Restore network
          await page.unroute('**/api/**');
        }
      },
      {
        name: '404 Error Handling',
        action: async () => {
          // Navigate to non-existent page
          await page.goto('/non-existent-page');
          await page.waitForTimeout(1000);
          
          // Should show error page or redirect
          const hasErrorPage = await page.locator('text=404, text=페이지를 찾을 수 없습니다').isVisible();
          const wasRedirected = page.url().includes('/') && !page.url().includes('non-existent');
          
          expect(hasErrorPage || wasRedirected).toBe(true);
        }
      },
      {
        name: 'Server Error Recovery',
        action: async () => {
          // Simulate server error
          await page.route('**/api/**', route => {
            route.fulfill({
              status: 500,
              body: JSON.stringify({ detail: 'Internal server error' })
            });
          });
          
          await page.goto('/');
          await page.waitForTimeout(1000);
          
          // Should handle error gracefully
          await expect(page.locator('body')).toBeVisible();
          
          // Restore API
          await page.unroute('**/api/**');
        }
      }
    ];
    
    for (const test of errorRecoveryTests) {
      const startTime = Date.now();
      
      try {
        await test.action();
      } catch (error) {
        console.warn(`Error in ${test.name}:`, error.message);
      }
      
      const recoveryTime = Date.now() - startTime;
      
      // Error handling should be fast
      expect(recoveryTime).toBeLessThan(3000);
      
      console.log(`${test.name} recovery time: ${recoveryTime}ms`);
      
      // App should still be responsive after error
      await expect(page.locator('body')).toBeVisible();
    }
  });
});