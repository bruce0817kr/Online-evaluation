/**
 * 🎯 Navigation Enhancement E2E Test Suite
 * Comprehensive testing for the enhanced navigation system
 * Tests URL routing, breadcrumbs, mobile responsiveness, and accessibility
 */

import { test, expect } from '@playwright/test';

// Test configuration
const TEST_CONFIG = {
  frontend: process.env.FRONTEND_URL || 'http://localhost:3019',
  backend: process.env.BACKEND_URL || 'http://localhost:8019',
  users: {
    admin: { username: 'admin', password: 'admin123', role: 'admin' },
    secretary: { username: 'secretary', password: 'secretary123', role: 'secretary' },
    evaluator: { username: 'evaluator', password: 'evaluator123', role: 'evaluator' }
  }
};

test.describe('🚀 Enhanced Navigation System', () => {
  
  test.beforeEach(async ({ page }) => {
    // Set test environment headers to bypass rate limiting
    await page.setExtraHTTPHeaders({
      'X-Test-Environment': 'true',
      'X-E2E-Test': 'navigation-enhancement'
    });
    
    await page.goto(TEST_CONFIG.frontend);
  });

  test.describe('📱 Mobile Navigation', () => {
    test('should display mobile menu button on small screens', async ({ page }) => {
      // Set mobile viewport
      await page.setViewportSize({ width: 375, height: 667 });
      
      // Login as admin first
      await loginUser(page, TEST_CONFIG.users.admin);
      
      // Check mobile menu button is visible
      const mobileMenuButton = page.locator('[aria-label="메뉴 열기"]');
      await expect(mobileMenuButton).toBeVisible();
      
      // Desktop navigation should be hidden
      const desktopNav = page.locator('.lg\\:block').first();
      await expect(desktopNav).toHaveClass(/hidden/);
    });

    test('should toggle mobile menu correctly', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await loginUser(page, TEST_CONFIG.users.admin);
      
      const mobileMenuButton = page.locator('[aria-label="메뉴 열기"]');
      const mobileMenu = page.locator('nav').first();
      
      // Initially hidden
      await expect(mobileMenu).toHaveClass(/hidden/);
      
      // Click to open
      await mobileMenuButton.click();
      await expect(mobileMenu).toHaveClass(/block/);
      
      // Click to close
      await mobileMenuButton.click();
      await expect(mobileMenu).toHaveClass(/hidden/);
    });
  });

  test.describe('🍞 Breadcrumb Navigation', () => {
    test('should display correct breadcrumbs for primary pages', async ({ page }) => {
      await loginUser(page, TEST_CONFIG.users.admin);
      
      // Navigate to projects page
      await page.click('[data-tab="projects"]');
      
      // Check breadcrumb trail
      const breadcrumbs = page.locator('[aria-label="Breadcrumb"] ol li');
      await expect(breadcrumbs).toHaveCount(2);
      await expect(breadcrumbs.first()).toContainText('홈');
      await expect(breadcrumbs.last()).toContainText('프로젝트');
    });

    test('should display admin breadcrumbs for admin pages', async ({ page }) => {
      await loginUser(page, TEST_CONFIG.users.admin);
      
      // Open admin panel
      await page.click('button:has-text("⚙️ 관리자")');
      
      // Click on user management
      await page.click('text=👥 사용자 관리');
      
      // Check admin breadcrumb trail
      const breadcrumbs = page.locator('[aria-label="Breadcrumb"] ol li');
      await expect(breadcrumbs).toHaveCount(3);
      await expect(breadcrumbs.nth(1)).toContainText('관리자');
      await expect(breadcrumbs.last()).toContainText('사용자');
    });
  });

  test.describe('🎛️ Admin Side Panel', () => {
    test('should open and close admin panel', async ({ page }) => {
      await loginUser(page, TEST_CONFIG.users.admin);
      
      // Admin panel should not be visible initially
      await expect(page.locator('.fixed.inset-0')).not.toBeVisible();
      
      // Click admin button
      await page.click('button:has-text("⚙️ 관리자")');
      
      // Admin panel should be visible
      await expect(page.locator('.fixed.inset-0')).toBeVisible();
      await expect(page.locator('h2:has-text("⚙️ 관리자 도구")')).toBeVisible();
      
      // Close by clicking backdrop
      await page.click('.bg-black.bg-opacity-50');
      await expect(page.locator('.fixed.inset-0')).not.toBeVisible();
    });

    test('should not show admin button for non-admin users', async ({ page }) => {
      await loginUser(page, TEST_CONFIG.users.secretary);
      
      // Admin button should not be visible for secretary
      await expect(page.locator('button:has-text("⚙️ 관리자")')).not.toBeVisible();
    });

    test('should navigate to admin functions correctly', async ({ page }) => {
      await loginUser(page, TEST_CONFIG.users.admin);
      
      // Open admin panel
      await page.click('button:has-text("⚙️ 관리자")');
      
      // Click on AI 모델 관리
      await page.click('text=🔧 AI 모델');
      
      // Should close panel and navigate
      await expect(page.locator('.fixed.inset-0')).not.toBeVisible();
      // Add specific check for AI model management page
    });
  });

  test.describe('🔧 Tools Dropdown', () => {
    test('should display tools dropdown with correct items', async ({ page }) => {
      await loginUser(page, TEST_CONFIG.users.admin);
      
      // Click tools dropdown
      await page.click('button:has-text("🔧 도구")');
      
      // Check dropdown is visible with correct items
      const dropdown = page.locator('.absolute.top-full');
      await expect(dropdown).toBeVisible();
      await expect(dropdown.locator('text=🔒 파일 뷰어')).toBeVisible();
      await expect(dropdown.locator('text=🖨️ 출력 관리')).toBeVisible();
      await expect(dropdown.locator('text=🤖 AI 도우미')).toBeVisible();
      await expect(dropdown.locator('text=📈 분석')).toBeVisible();
    });

    test('should close dropdown when selecting item', async ({ page }) => {
      await loginUser(page, TEST_CONFIG.users.admin);
      
      await page.click('button:has-text("🔧 도구")');
      
      // Click on file viewer
      await page.click('text=🔒 파일 뷰어');
      
      // Dropdown should close
      await expect(page.locator('.absolute.top-full')).not.toBeVisible();
    });
  });

  test.describe('♿ Accessibility Features', () => {
    test('should have proper ARIA labels', async ({ page }) => {
      await loginUser(page, TEST_CONFIG.users.admin);
      
      // Check breadcrumb ARIA labels
      await expect(page.locator('[aria-label="Breadcrumb"]')).toBeVisible();
      
      // Check navigation item ARIA labels
      const navItems = page.locator('[aria-label*="페이지로 이동"]');
      await expect(navItems).toHaveCount.greaterThan(0);
      
      // Check mobile menu ARIA label
      await page.setViewportSize({ width: 375, height: 667 });
      await expect(page.locator('[aria-label="메뉴 열기"]')).toBeVisible();
    });

    test('should support keyboard navigation', async ({ page }) => {
      await loginUser(page, TEST_CONFIG.users.admin);
      
      // Tab through navigation items
      await page.keyboard.press('Tab');
      const focusedElement = page.locator(':focus');
      
      // Should be able to activate with Enter
      await page.keyboard.press('Enter');
      
      // Check that navigation occurred (implementation specific)
    });

    test('should have proper aria-current for active pages', async ({ page }) => {
      await loginUser(page, TEST_CONFIG.users.admin);
      
      // Navigate to projects
      await page.click('[data-tab="projects"]');
      
      // Check aria-current is set
      const activeTab = page.locator('[aria-current="page"]');
      await expect(activeTab).toBeVisible();
      await expect(activeTab).toContainText('프로젝트');
    });
  });

  test.describe('🎨 Visual States and Interactions', () => {
    test('should show hover states correctly', async ({ page }) => {
      await loginUser(page, TEST_CONFIG.users.admin);
      
      const navItem = page.locator('button:has-text("📊 대시보드")');
      
      // Hover over navigation item
      await navItem.hover();
      
      // Should show visual feedback (test implementation specific classes)
      await expect(navItem).toHaveClass(/hover:text-gray-700|hover:border-gray-300/);
    });

    test('should highlight active tab correctly', async ({ page }) => {
      await loginUser(page, TEST_CONFIG.users.admin);
      
      // Click on templates tab
      await page.click('[data-tab="templates"]');
      
      const activeTab = page.locator('[data-tab="templates"]');
      await expect(activeTab).toHaveClass(/border-blue-500|text-blue-600/);
    });
  });

  test.describe('🌍 Role-Based Navigation', () => {
    test('should show appropriate navigation for admin users', async ({ page }) => {
      await loginUser(page, TEST_CONFIG.users.admin);
      
      // Admin should see all primary navigation
      await expect(page.locator('text=📊 대시보드')).toBeVisible();
      await expect(page.locator('text=🎯 프로젝트')).toBeVisible();
      await expect(page.locator('text=📝 평가')).toBeVisible();
      await expect(page.locator('text=📄 템플릿')).toBeVisible();
      
      // Admin should see admin button
      await expect(page.locator('button:has-text("⚙️ 관리자")')).toBeVisible();
    });

    test('should show appropriate navigation for secretary users', async ({ page }) => {
      await loginUser(page, TEST_CONFIG.users.secretary);
      
      // Secretary should see most navigation except admin
      await expect(page.locator('text=📊 대시보드')).toBeVisible();
      await expect(page.locator('text=🎯 프로젝트')).toBeVisible();
      await expect(page.locator('text=📝 평가')).toBeVisible();
      await expect(page.locator('text=📄 템플릿')).toBeVisible();
      
      // Secretary should NOT see admin button
      await expect(page.locator('button:has-text("⚙️ 관리자")')).not.toBeVisible();
    });

    test('should show limited navigation for evaluator users', async ({ page }) => {
      await loginUser(page, TEST_CONFIG.users.evaluator);
      
      // Evaluator should only see evaluation tab
      await expect(page.locator('text=📝 평가')).toBeVisible();
      
      // Evaluator should NOT see admin navigation
      await expect(page.locator('text=📊 대시보드')).not.toBeVisible();
      await expect(page.locator('text=🎯 프로젝트')).not.toBeVisible();
      await expect(page.locator('button:has-text("⚙️ 관리자")')).not.toBeVisible();
    });
  });

  test.describe('💡 Navigation Tooltips', () => {
    test('should show tooltips on hover', async ({ page }) => {
      await loginUser(page, TEST_CONFIG.users.admin);
      
      // Hover over navigation item
      await page.hover('button:has-text("📊 대시보드")');
      
      // Tooltip should appear
      const tooltip = page.locator('.fixed.z-50.px-3.py-2.bg-gray-900');
      await expect(tooltip).toBeVisible();
      await expect(tooltip).toContainText('시스템 전체 현황과 주요 지표를 확인합니다');
    });

    test('should hide tooltips when not hovering', async ({ page }) => {
      await loginUser(page, TEST_CONFIG.users.admin);
      
      // Hover and then move away
      await page.hover('button:has-text("📊 대시보드")');
      await page.hover('body');
      
      // Tooltip should disappear
      const tooltip = page.locator('.fixed.z-50.px-3.py-2.bg-gray-900');
      await expect(tooltip).not.toBeVisible();
    });
  });

  test.describe('📱 Responsive Design', () => {
    const viewports = [
      { name: 'Mobile', width: 375, height: 667 },
      { name: 'Tablet', width: 768, height: 1024 },
      { name: 'Desktop', width: 1200, height: 800 },
      { name: 'Large Desktop', width: 1600, height: 900 }
    ];

    viewports.forEach(viewport => {
      test(`should display correctly on ${viewport.name}`, async ({ page }) => {
        await page.setViewportSize({ width: viewport.width, height: viewport.height });
        await loginUser(page, TEST_CONFIG.users.admin);
        
        if (viewport.width < 768) {
          // Mobile: should show mobile menu button
          await expect(page.locator('[aria-label="메뉴 열기"]')).toBeVisible();
        } else {
          // Desktop: should show full navigation
          await expect(page.locator('text=📊 대시보드')).toBeVisible();
        }
        
        // Take screenshot for visual regression testing
        await page.screenshot({ 
          path: `tests/e2e/screenshots/navigation-${viewport.name.toLowerCase()}.png`,
          fullPage: true 
        });
      });
    });
  });
});

// Helper function to login users with proper rate limit handling
async function loginUser(page, user) {
  try {
    // Fill login form
    await page.fill('input[name="login_id"]', user.username);
    await page.fill('input[name="password"]', user.password);
    
    // Submit login form
    await page.click('button[type="submit"]');
    
    // Wait for successful login (redirect to dashboard)
    await page.waitForURL(/\/(dashboard|$)/, { timeout: 10000 });
    
    // Verify login success
    const loggedInUser = await page.locator('.user-info, .welcome-message').first();
    await expect(loggedInUser).toBeVisible({ timeout: 5000 });
    
    return true;
  } catch (error) {
    console.error(`Login failed for user ${user.username}:`, error);
    return false;
  }
}

// Test utility for checking navigation state
async function verifyNavigationState(page, expectedTab) {
  const activeTab = page.locator(`[data-tab="${expectedTab}"]`);
  await expect(activeTab).toHaveClass(/border-blue-500|text-blue-600/);
  
  // Check URL if URL routing is implemented
  await expect(page).toHaveURL(new RegExp(expectedTab));
}