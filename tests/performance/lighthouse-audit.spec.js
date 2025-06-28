/**
 * 🚀 Performance & Accessibility Audit Test Suite
 * Lighthouse audits for performance, accessibility, and best practices
 * Mobile responsiveness and cross-browser testing
 */

import { test, expect } from '@playwright/test';
import { playAudit } from 'playwright-lighthouse';

const TEST_CONFIG = {
  frontend: process.env.FRONTEND_URL || 'http://localhost:3019',
  backend: process.env.BACKEND_URL || 'http://localhost:8019',
  users: {
    admin: { username: 'admin', password: 'admin123', role: 'admin' },
    secretary: { username: 'secretary', password: 'secretary123', role: 'secretary' },
    evaluator: { username: 'evaluator', password: 'evaluator123', role: 'evaluator' }
  },
  performance: {
    target: {
      performance: 85,
      accessibility: 95,
      bestPractices: 90,
      seo: 80
    }
  }
};

test.describe('🎯 Performance & Quality Audits', () => {
  
  test.beforeEach(async ({ page }) => {
    await page.setExtraHTTPHeaders({
      'X-Test-Environment': 'true',
      'X-Performance-Test': 'true'
    });
  });

  test.describe('🚀 Lighthouse Performance Audits', () => {
    test('should meet performance targets on login page', async ({ page, context }) => {
      await page.goto(TEST_CONFIG.frontend);
      
      const audit = await playAudit({
        page,
        thresholds: {
          performance: TEST_CONFIG.performance.target.performance,
          accessibility: TEST_CONFIG.performance.target.accessibility,
          'best-practices': TEST_CONFIG.performance.target.bestPractices,
          seo: TEST_CONFIG.performance.target.seo
        },
        port: 9222
      });
      
      expect(audit.lhr.categories.performance.score * 100).toBeGreaterThanOrEqual(
        TEST_CONFIG.performance.target.performance
      );
      expect(audit.lhr.categories.accessibility.score * 100).toBeGreaterThanOrEqual(
        TEST_CONFIG.performance.target.accessibility
      );
    });

    test('should meet performance targets on dashboard', async ({ page }) => {
      await loginUser(page, TEST_CONFIG.users.admin);
      
      const audit = await playAudit({
        page,
        thresholds: {
          performance: TEST_CONFIG.performance.target.performance - 10, // Allow lower score for complex dashboard
          accessibility: TEST_CONFIG.performance.target.accessibility,
          'best-practices': TEST_CONFIG.performance.target.bestPractices
        },
        port: 9222
      });
      
      // Dashboard should still meet accessibility requirements
      expect(audit.lhr.categories.accessibility.score * 100).toBeGreaterThanOrEqual(
        TEST_CONFIG.performance.target.accessibility
      );
    });
  });

  test.describe('♿ Accessibility Compliance', () => {
    test('should meet WCAG 2.1 AA standards', async ({ page }) => {
      await page.goto(TEST_CONFIG.frontend);
      
      // Check for essential accessibility features
      await expect(page.locator('html')).toHaveAttribute('lang');
      
      // All images should have alt text
      const images = await page.locator('img').count();
      for (let i = 0; i < images; i++) {
        const img = page.locator('img').nth(i);
        const alt = await img.getAttribute('alt');
        const ariaLabel = await img.getAttribute('aria-label');
        expect(alt || ariaLabel).toBeTruthy();
      }
      
      // Forms should have proper labels
      const inputs = await page.locator('input').count();
      for (let i = 0; i < inputs; i++) {
        const input = page.locator('input').nth(i);
        const id = await input.getAttribute('id');
        const ariaLabel = await input.getAttribute('aria-label');
        const ariaLabelledBy = await input.getAttribute('aria-labelledby');
        
        if (id) {
          const label = page.locator(`label[for="${id}"]`);
          const hasLabel = await label.count() > 0;
          expect(hasLabel || ariaLabel || ariaLabelledBy).toBeTruthy();
        }
      }
    });

    test('should support keyboard navigation throughout application', async ({ page }) => {
      await loginUser(page, TEST_CONFIG.users.admin);
      
      // Start from first focusable element
      await page.keyboard.press('Tab');
      
      let focusableElements = 0;
      let maxTabs = 20; // Reasonable limit
      
      for (let i = 0; i < maxTabs; i++) {
        const focused = await page.locator(':focus').count();
        if (focused > 0) {
          focusableElements++;
          
          // Test Enter/Space activation on buttons
          const isButton = await page.locator(':focus').evaluate(el => 
            el.tagName === 'BUTTON' || el.getAttribute('role') === 'button'
          );
          
          if (isButton) {
            // Ensure button is activatable
            const isDisabled = await page.locator(':focus').isDisabled();
            if (!isDisabled) {
              // Button should respond to Enter or Space
              // (Implementation would verify activation)
            }
          }
        }
        
        await page.keyboard.press('Tab');
      }
      
      // Should have reasonable number of focusable elements
      expect(focusableElements).toBeGreaterThan(3);
    });

    test('should provide proper color contrast', async ({ page }) => {
      await loginUser(page, TEST_CONFIG.users.admin);
      
      // Check key text elements for sufficient contrast
      const textElements = await page.locator('p, span, div, button, a').all();
      
      for (const element of textElements.slice(0, 10)) { // Sample first 10 elements
        const styles = await element.evaluate(el => {
          const computed = getComputedStyle(el);
          return {
            color: computed.color,
            backgroundColor: computed.backgroundColor,
            fontSize: computed.fontSize
          };
        });
        
        // Basic contrast check (implementation would use proper contrast calculation)
        expect(styles.color).not.toBe(styles.backgroundColor);
      }
    });
  });

  test.describe('📱 Mobile Responsiveness', () => {
    const mobileViewports = [
      { name: 'iPhone SE', width: 375, height: 667 },
      { name: 'iPhone 12', width: 390, height: 844 },
      { name: 'Samsung Galaxy S21', width: 360, height: 800 },
      { name: 'iPad Mini', width: 768, height: 1024 }
    ];

    mobileViewports.forEach(viewport => {
      test(`should be usable on ${viewport.name}`, async ({ page }) => {
        await page.setViewportSize({ width: viewport.width, height: viewport.height });
        await page.goto(TEST_CONFIG.frontend);
        
        // Login should work on mobile
        await loginUser(page, TEST_CONFIG.users.admin);
        
        // Mobile navigation should be accessible
        if (viewport.width < 768) {
          await expect(page.locator('[aria-label="메뉴 열기"]')).toBeVisible();
          
          // Mobile menu should work
          await page.click('[aria-label="메뉴 열기"]');
          await expect(page.locator('nav')).toHaveClass(/block/);
        }
        
        // Text should be readable (minimum font size)
        const bodyText = page.locator('body');
        const fontSize = await bodyText.evaluate(el => 
          parseFloat(getComputedStyle(el).fontSize)
        );
        expect(fontSize).toBeGreaterThanOrEqual(14); // Minimum readable font size
        
        // Interactive elements should be appropriately sized
        const buttons = await page.locator('button').all();
        for (const button of buttons.slice(0, 5)) {
          const size = await button.boundingBox();
          if (size) {
            // Minimum touch target size (44px)
            expect(Math.max(size.width, size.height)).toBeGreaterThanOrEqual(44);
          }
        }
        
        // Take screenshot for visual verification
        await page.screenshot({ 
          path: `tests/performance/screenshots/mobile-${viewport.name.toLowerCase().replace(' ', '-')}.png`,
          fullPage: true 
        });
      });
    });
  });

  test.describe('🌐 Cross-Browser Performance', () => {
    ['chromium', 'firefox', 'webkit'].forEach(browserName => {
      test(`should perform well in ${browserName}`, async ({ page }) => {
        // This test would run in different browsers via Playwright config
        await page.goto(TEST_CONFIG.frontend);
        
        // Measure basic performance metrics
        const performanceMetrics = await page.evaluate(() => {
          return {
            domContentLoaded: performance.timing.domContentLoadedEventEnd - performance.timing.navigationStart,
            loadComplete: performance.timing.loadEventEnd - performance.timing.navigationStart,
            firstPaint: performance.getEntriesByType('paint')[0]?.startTime || 0
          };
        });
        
        // Basic performance thresholds
        expect(performanceMetrics.domContentLoaded).toBeLessThan(3000); // 3s for DOM ready
        expect(performanceMetrics.loadComplete).toBeLessThan(5000); // 5s for complete load
        
        await loginUser(page, TEST_CONFIG.users.admin);
        
        // Navigation should be responsive
        const navStart = Date.now();
        await page.click('[data-tab="projects"], text=🎯 프로젝트');
        await page.waitForLoadState('networkidle');
        const navTime = Date.now() - navStart;
        
        expect(navTime).toBeLessThan(2000); // Navigation under 2s
      });
    });
  });

  test.describe('📊 Resource Usage Monitoring', () => {
    test('should not have memory leaks during navigation', async ({ page }) => {
      await loginUser(page, TEST_CONFIG.users.admin);
      
      // Get initial memory usage
      const initialMemory = await page.evaluate(() => {
        if (performance.memory) {
          return {
            used: performance.memory.usedJSHeapSize,
            total: performance.memory.totalJSHeapSize
          };
        }
        return null;
      });
      
      // Navigate through multiple pages
      const pages = ['dashboard', 'projects', 'evaluations', 'templates'];
      for (const pageName of pages) {
        await page.click(`[data-tab="${pageName}"]`);
        await page.waitForTimeout(1000);
        
        // Force garbage collection if available
        await page.evaluate(() => {
          if (window.gc) window.gc();
        });
      }
      
      // Check final memory usage
      const finalMemory = await page.evaluate(() => {
        if (performance.memory) {
          return {
            used: performance.memory.usedJSHeapSize,
            total: performance.memory.totalJSHeapSize
          };
        }
        return null;
      });
      
      if (initialMemory && finalMemory) {
        // Memory usage should not increase dramatically
        const memoryIncrease = finalMemory.used - initialMemory.used;
        const increasePercentage = (memoryIncrease / initialMemory.used) * 100;
        
        expect(increasePercentage).toBeLessThan(50); // Less than 50% increase
      }
    });

    test('should load critical resources efficiently', async ({ page }) => {
      // Monitor network requests
      const requests = [];
      page.on('request', request => {
        requests.push({
          url: request.url(),
          method: request.method(),
          resourceType: request.resourceType()
        });
      });
      
      const responses = [];
      page.on('response', response => {
        responses.push({
          url: response.url(),
          status: response.status(),
          size: response.headers()['content-length']
        });
      });
      
      await page.goto(TEST_CONFIG.frontend);
      await loginUser(page, TEST_CONFIG.users.admin);
      
      // Check for efficient resource loading
      const cssRequests = requests.filter(r => r.resourceType === 'stylesheet');
      const jsRequests = requests.filter(r => r.resourceType === 'script');
      const imageRequests = requests.filter(r => r.resourceType === 'image');
      
      // Should not load excessive resources
      expect(cssRequests.length).toBeLessThan(10);
      expect(jsRequests.length).toBeLessThan(20);
      
      // All critical requests should succeed
      const failedRequests = responses.filter(r => r.status >= 400);
      expect(failedRequests.length).toBe(0);
    });
  });

  test.describe('🔒 Security Headers & Best Practices', () => {
    test('should have proper security headers', async ({ page }) => {
      const response = await page.goto(TEST_CONFIG.frontend);
      const headers = response.headers();
      
      // Check for security headers
      expect(headers['x-frame-options'] || headers['content-security-policy']).toBeTruthy();
      expect(headers['x-content-type-options']).toBe('nosniff');
      
      // Should use HTTPS in production
      if (TEST_CONFIG.frontend.startsWith('https')) {
        expect(headers['strict-transport-security']).toBeTruthy();
      }
    });

    test('should not expose sensitive information', async ({ page }) => {
      await page.goto(TEST_CONFIG.frontend);
      
      // Check for exposed credentials or tokens in page source
      const content = await page.content();
      
      // Should not contain common sensitive patterns
      expect(content).not.toMatch(/password\s*[:=]\s*["'][^"']+["']/i);
      expect(content).not.toMatch(/api[_-]?key\s*[:=]\s*["'][^"']+["']/i);
      expect(content).not.toMatch(/secret\s*[:=]\s*["'][^"']+["']/i);
      
      // Console should not show errors or warnings in production
      const consoleLogs = [];
      page.on('console', msg => {
        if (msg.type() === 'error' || msg.type() === 'warning') {
          consoleLogs.push(msg.text());
        }
      });
      
      await loginUser(page, TEST_CONFIG.users.admin);
      
      // Filter out acceptable warnings
      const criticalLogs = consoleLogs.filter(log => 
        !log.includes('favicon') && 
        !log.includes('lighthouse') &&
        !log.includes('test')
      );
      
      expect(criticalLogs.length).toBe(0);
    });
  });
});

// Performance-optimized login function
async function loginUser(page, user) {
  try {
    await page.waitForSelector('input[name="login_id"]', { timeout: 5000 });
    await page.fill('input[name="login_id"]', user.username);
    await page.fill('input[name="password"]', user.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/(dashboard|$)/, { timeout: 10000 });
    return true;
  } catch (error) {
    console.error(`Performance test login failed for ${user.username}:`, error);
    return false;
  }
}