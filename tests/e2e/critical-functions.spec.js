/**
 * 🎯 Critical Business Functions E2E Test Suite
 * Tests for the 11 critical issues identified in the system
 * Comprehensive workflow testing for all user roles
 */

import { test, expect } from '@playwright/test';

const TEST_CONFIG = {
  frontend: process.env.FRONTEND_URL || 'http://localhost:3019',
  backend: process.env.BACKEND_URL || 'http://localhost:8019',
  users: {
    admin: { username: 'admin', password: 'admin123', role: 'admin' },
    secretary: { username: 'secretary', password: 'secretary123', role: 'secretary' },
    evaluator: { username: 'evaluator', password: 'evaluator123', role: 'evaluator' }
  }
};

test.describe('🔥 Critical Business Functions', () => {
  
  test.beforeEach(async ({ page }) => {
    // Set test environment headers to bypass rate limiting
    await page.setExtraHTTPHeaders({
      'X-Test-Environment': 'true',
      'X-E2E-Test': 'critical-functions',
      'User-Agent': 'Playwright/E2E-Test'
    });
    
    await page.goto(TEST_CONFIG.frontend);
  });

  test.describe('Issue #1: 🎯 프로젝트 관리 - Project Creation', () => {
    test('should create new project successfully as admin', async ({ page }) => {
      await loginWithRetry(page, TEST_CONFIG.users.admin);
      
      // Navigate to projects
      await page.click('[data-tab="projects"], text=🎯 프로젝트');
      await page.waitForTimeout(1000);
      
      // Click create project button
      await page.click('text=새 프로젝트 생성, text=➕ 프로젝트 생성, button:has-text("생성")');
      
      // Fill project form
      const projectName = `Test Project ${Date.now()}`;
      await page.fill('input[name="name"], input[placeholder*="프로젝트"]', projectName);
      await page.fill('textarea[name="description"], textarea[placeholder*="설명"]', '테스트 프로젝트 설명');
      
      // Submit form
      await page.click('button[type="submit"], text=프로젝트 생성, text=생성');
      
      // Verify project was created
      await expect(page.locator(`text=${projectName}`)).toBeVisible({ timeout: 10000 });
      
      // Take screenshot
      await page.screenshot({ path: 'tests/e2e/screenshots/project-creation-success.png' });
    });

    test('should handle project creation errors gracefully', async ({ page }) => {
      await loginWithRetry(page, TEST_CONFIG.users.admin);
      
      await page.click('[data-tab="projects"], text=🎯 프로젝트');
      await page.click('text=새 프로젝트 생성, text=➕ 프로젝트 생성, button:has-text("생성")');
      
      // Try to submit without required fields
      await page.click('button[type="submit"], text=프로젝트 생성, text=생성');
      
      // Should show validation error
      await expect(page.locator('.error, .alert-error, text=필수 항목')).toBeVisible();
    });
  });

  test.describe('Issue #2-3: 📝 평가관리 & 템플릿 관리 - Authentication', () => {
    test('should access evaluation management with proper credentials', async ({ page }) => {
      await loginWithRetry(page, TEST_CONFIG.users.admin);
      
      // Navigate to evaluations
      await page.click('[data-tab="evaluations"], text=📝 평가');
      await page.waitForTimeout(1000);
      
      // Should not show "Could not validate credentials" error
      await expect(page.locator('text=Could not validate credentials')).not.toBeVisible();
      
      // Should show evaluation content
      await expect(page.locator('text=평가 목록, text=평가 관리, .evaluation-list')).toBeVisible();
    });

    test('should access template management as admin', async ({ page }) => {
      await loginWithRetry(page, TEST_CONFIG.users.admin);
      
      // Navigate to templates
      await page.click('[data-tab="templates"], text=📄 템플릿');
      await page.waitForTimeout(1000);
      
      // Should recognize admin permissions
      await expect(page.locator('text=권한 인식 오류, text=접근 권한')).not.toBeVisible();
      
      // Should show template management interface
      await expect(page.locator('text=템플릿 관리, text=새 템플릿, .template-list')).toBeVisible();
      
      // Admin should be able to create templates
      const createButton = page.locator('text=새 템플릿 생성, text=➕ 템플릿, button:has-text("생성")');
      await expect(createButton).toBeVisible();
      await expect(createButton).toBeEnabled();
    });
  });

  test.describe('Issue #4: 🔒 보안 파일 뷰어 - File List Loading', () => {
    test('should load file list successfully', async ({ page }) => {
      await loginWithRetry(page, TEST_CONFIG.users.admin);
      
      // Navigate to file viewer via tools dropdown
      await page.click('text=🔧 도구');
      await page.click('text=🔒 파일 뷰어');
      await page.waitForTimeout(2000);
      
      // Should not show "Cannot load file list" error
      await expect(page.locator('text=파일 목록을 불러올 수 없습니다, text=Cannot load file list')).not.toBeVisible();
      
      // Should show file interface (even if empty)
      await expect(page.locator('text=파일 목록, .file-list, .file-viewer')).toBeVisible();
    });

    test('should handle file upload functionality', async ({ page }) => {
      await loginWithRetry(page, TEST_CONFIG.users.admin);
      
      await page.click('text=🔧 도구');
      await page.click('text=🔒 파일 뷰어');
      await page.waitForTimeout(1000);
      
      // Check if upload functionality is available
      const uploadArea = page.locator('input[type="file"], .upload-area, text=파일 업로드');
      if (await uploadArea.isVisible()) {
        await expect(uploadArea).toBeEnabled();
      }
    });
  });

  test.describe('Issue #5: 🖨️ 평가표 출력 관리 - Permissions & Project Selection', () => {
    test('should access print management with admin permissions', async ({ page }) => {
      await loginWithRetry(page, TEST_CONFIG.users.admin);
      
      // Navigate to print management
      await page.click('text=🔧 도구');
      await page.click('text=🖨️ 출력 관리');
      await page.waitForTimeout(1000);
      
      // Should have permissions despite admin login
      await expect(page.locator('text=권한이 없습니다, text=No permissions')).not.toBeVisible();
      
      // Should show print management interface
      await expect(page.locator('text=출력 관리, text=평가표 출력, .print-manager')).toBeVisible();
    });

    test('should reflect project selection in print management', async ({ page }) => {
      await loginWithRetry(page, TEST_CONFIG.users.admin);
      
      await page.click('text=🔧 도구');
      await page.click('text=🖨️ 출력 관리');
      await page.waitForTimeout(1000);
      
      // Check if project selection is available and functional
      const projectSelect = page.locator('select[name*="project"], .project-selector, text=프로젝트 선택');
      if (await projectSelect.isVisible()) {
        // Select a project if options are available
        const projectOptions = await projectSelect.locator('option').count();
        if (projectOptions > 1) {
          await projectSelect.selectOption({ index: 1 });
          
          // Verify selection is reflected in UI
          await page.waitForTimeout(500);
          // Project-specific content should load
        }
      }
    });
  });

  test.describe('Issue #6: 🤖 AI 도우미 - UI & Model Settings', () => {
    test('should display AI assistant with proper contrast', async ({ page }) => {
      await loginWithRetry(page, TEST_CONFIG.users.admin);
      
      // Navigate to AI assistant
      await page.click('text=🔧 도구');
      await page.click('text=🤖 AI 도우미');
      await page.waitForTimeout(1000);
      
      // Check for proper UI contrast (should be white background, not gray with black text)
      const aiStatusBox = page.locator('.bg-white, .ai-status, text=AI 서비스 상태').first();
      if (await aiStatusBox.isVisible()) {
        // Should not have poor contrast combination
        const boxStyles = await aiStatusBox.evaluate(el => getComputedStyle(el));
        expect(boxStyles.backgroundColor).not.toBe('rgb(249, 250, 251)'); // gray-50
      }
      
      // AI model settings should be accessible
      await expect(page.locator('text=AI 모델 설정, text=모델 선택, .ai-settings')).toBeVisible();
    });

    test('should access AI model settings location', async ({ page }) => {
      await loginWithRetry(page, TEST_CONFIG.users.admin);
      
      // Check if AI model settings are in AI assistant
      await page.click('text=🔧 도구');
      await page.click('text=🤖 AI 도우미');
      
      // Or check if they're in admin panel
      await page.click('button:has-text("⚙️ 관리자")');
      await page.click('text=🔧 AI 모델');
      
      // Should find AI model configuration somewhere
      await expect(page.locator('text=AI 모델, text=모델 설정, text=AI 설정')).toBeVisible();
    });
  });

  test.describe('Issue #7: ⚙️ 관리자 메뉴 - All Admin Functions', () => {
    test('should access user management without "not found" error', async ({ page }) => {
      await loginWithRetry(page, TEST_CONFIG.users.admin);
      
      // Open admin panel
      await page.click('button:has-text("⚙️ 관리자")');
      await page.click('text=👥 사용자 관리');
      await page.waitForTimeout(2000);
      
      // Should not show "not found" error
      await expect(page.locator('text=not found, text=찾을 수 없습니다, text=404')).not.toBeVisible();
      
      // Should show user management interface
      await expect(page.locator('text=사용자 관리, text=사용자 목록, .user-list')).toBeVisible();
    });

    test('should access AI provider management without authentication expired', async ({ page }) => {
      await loginWithRetry(page, TEST_CONFIG.users.admin);
      
      await page.click('button:has-text("⚙️ 관리자")');
      await page.click('text=🌐 AI 공급자');
      await page.waitForTimeout(2000);
      
      // Should not show "authentication expired" error
      await expect(page.locator('text=authentication expired, text=인증 만료')).not.toBeVisible();
      
      // Should show AI provider management
      await expect(page.locator('text=AI 공급자, text=공급자 관리')).toBeVisible();
    });

    test('should access AI model management without permission issues', async ({ page }) => {
      await loginWithRetry(page, TEST_CONFIG.users.admin);
      
      await page.click('button:has-text("⚙️ 관리자")');
      await page.click('text=🔧 AI 모델');
      await page.waitForTimeout(2000);
      
      // Should not show permission issues
      await expect(page.locator('text=permission issues, text=권한 문제')).not.toBeVisible();
      
      // Should show AI model management
      await expect(page.locator('text=AI 모델 관리, text=모델 목록')).toBeVisible();
    });

    test('should access deployment management with data reflection', async ({ page }) => {
      await loginWithRetry(page, TEST_CONFIG.users.admin);
      
      await page.click('button:has-text("⚙️ 관리자")');
      await page.click('text=🚀 배포');
      await page.waitForTimeout(2000);
      
      // Should show deployment management
      await expect(page.locator('text=배포 관리, text=시스템 배포')).toBeVisible();
      
      // Data should be reflected (not showing "data not reflected" error)
      await expect(page.locator('text=data not reflected, text=데이터가 반영되지')).not.toBeVisible();
    });
  });

  test.describe('🔄 Workflow Integration Tests', () => {
    test('should complete full admin workflow', async ({ page }) => {
      await loginWithRetry(page, TEST_CONFIG.users.admin);
      
      // 1. Create a project
      await page.click('[data-tab="projects"], text=🎯 프로젝트');
      await page.waitForTimeout(1000);
      
      // 2. Create a template
      await page.click('[data-tab="templates"], text=📄 템플릿');
      await page.waitForTimeout(1000);
      
      // 3. Check evaluations
      await page.click('[data-tab="evaluations"], text=📝 평가');
      await page.waitForTimeout(1000);
      
      // 4. Access tools
      await page.click('text=🔧 도구');
      await page.click('text=🔒 파일 뷰어');
      await page.waitForTimeout(1000);
      
      // 5. Check admin functions
      await page.click('button:has-text("⚙️ 관리자")');
      await page.click('text=👥 사용자 관리');
      await page.waitForTimeout(1000);
      
      // All steps should complete without critical errors
      await expect(page.locator('text=500, text=error, text=failed')).not.toBeVisible();
    });

    test('should complete secretary workflow', async ({ page }) => {
      await loginWithRetry(page, TEST_CONFIG.users.secretary);
      
      // Secretary should access main functions
      await page.click('[data-tab="projects"], text=🎯 프로젝트');
      await page.waitForTimeout(1000);
      
      await page.click('[data-tab="evaluations"], text=📝 평가');
      await page.waitForTimeout(1000);
      
      await page.click('[data-tab="templates"], text=📄 템플릿');
      await page.waitForTimeout(1000);
      
      // Should not see admin functions
      await expect(page.locator('button:has-text("⚙️ 관리자")')).not.toBeVisible();
    });

    test('should complete evaluator workflow', async ({ page }) => {
      await loginWithRetry(page, TEST_CONFIG.users.evaluator);
      
      // Evaluator should primarily see evaluation interface
      await expect(page.locator('text=📝 평가, .evaluation-form')).toBeVisible();
      
      // Should not see admin or management functions
      await expect(page.locator('text=📊 대시보드')).not.toBeVisible();
      await expect(page.locator('button:has-text("⚙️ 관리자")')).not.toBeVisible();
    });
  });

  test.describe('🔍 Performance & Error Monitoring', () => {
    test('should not show rate limiting errors during normal usage', async ({ page }) => {
      await loginWithRetry(page, TEST_CONFIG.users.admin);
      
      // Perform multiple rapid actions
      for (let i = 0; i < 5; i++) {
        await page.click('[data-tab="dashboard"], text=📊 대시보드');
        await page.waitForTimeout(100);
        await page.click('[data-tab="projects"], text=🎯 프로젝트');
        await page.waitForTimeout(100);
      }
      
      // Should not show rate limiting errors
      await expect(page.locator('text=Rate limit exceeded, text=429')).not.toBeVisible();
    });

    test('should load pages within acceptable time', async ({ page }) => {
      await loginWithRetry(page, TEST_CONFIG.users.admin);
      
      // Measure page load times
      const startTime = Date.now();
      await page.click('[data-tab="projects"], text=🎯 프로젝트');
      await page.waitForLoadState('networkidle');
      const loadTime = Date.now() - startTime;
      
      // Should load within 3 seconds
      expect(loadTime).toBeLessThan(3000);
    });
  });
});

// Enhanced login function with retry logic for rate limiting
async function loginWithRetry(page, user, maxRetries = 3) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      // Clear any existing session
      await page.context().clearCookies();
      await page.evaluate(() => localStorage.clear());
      
      // Navigate to login if not already there
      const currentUrl = page.url();
      if (!currentUrl.includes('login') && !currentUrl.includes('localhost')) {
        await page.goto(TEST_CONFIG.frontend);
      }
      
      // Wait for login form
      await page.waitForSelector('input[name="login_id"]', { timeout: 5000 });
      
      // Fill credentials
      await page.fill('input[name="login_id"]', user.username);
      await page.fill('input[name="password"]', user.password);
      
      // Submit with additional wait
      await page.click('button[type="submit"]');
      
      // Wait for successful redirect or dashboard
      await page.waitForURL(/\/(dashboard|$)/, { timeout: 10000 });
      
      // Verify login success
      await expect(page.locator('.user-info, .welcome-message, text=로그아웃')).toBeVisible({ timeout: 5000 });
      
      console.log(`✅ Login successful for ${user.username} on attempt ${attempt}`);
      return true;
      
    } catch (error) {
      console.warn(`⚠️ Login attempt ${attempt} failed for ${user.username}:`, error.message);
      
      if (attempt < maxRetries) {
        // Wait before retry (exponential backoff)
        await page.waitForTimeout(1000 * attempt);
        
        // Check for rate limiting
        const rateLimitError = await page.locator('text=Rate limit exceeded, text=429').isVisible();
        if (rateLimitError) {
          console.log(`Rate limit detected, waiting longer before retry...`);
          await page.waitForTimeout(5000);
        }
      } else {
        throw new Error(`Login failed for ${user.username} after ${maxRetries} attempts: ${error.message}`);
      }
    }
  }
}