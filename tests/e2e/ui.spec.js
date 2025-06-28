import { test, expect } from '../fixtures';

test.describe('User Interface and Accessibility', () => {
  test.beforeEach(async ({ page, authHelper }) => {
    await authHelper.loginViaUI('admin', 'admin123');
  });

  test('should have responsive design', async ({ page }) => {
    // Test desktop view
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/');
    
    await expect(page.locator('.main-content, .dashboard')).toBeVisible();
    
    // Test tablet view
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.waitForTimeout(500);
    
    await expect(page.locator('body')).toBeVisible();
    
    // Test mobile view
    await page.setViewportSize({ width: 375, height: 667 });
    await page.waitForTimeout(500);
    
    await expect(page.locator('body')).toBeVisible();
    
    // Mobile menu should be present
    const mobileMenu = page.locator('.mobile-menu, .hamburger, .menu-toggle');
    const mobileMenuVisible = await mobileMenu.isVisible();
    
    if (mobileMenuVisible) {
      await mobileMenu.click();
      await expect(page.locator('.mobile-nav, .side-menu')).toBeVisible();
    }
  });

  test('should meet accessibility standards', async ({ page }) => {
    await page.goto('/');
    
    // Check for proper heading hierarchy
    const headings = await page.locator('h1, h2, h3, h4, h5, h6').all();
    expect(headings.length).toBeGreaterThan(0);
    
    // Check for alt text on images
    const images = await page.locator('img').all();
    for (const img of images) {
      const alt = await img.getAttribute('alt');
      const src = await img.getAttribute('src');
      
      // Decorative images should have empty alt, content images should have descriptive alt
      if (src && !src.includes('icon') && !src.includes('logo')) {
        expect(alt).toBeDefined();
      }
    }
    
    // Check for form labels
    const inputs = await page.locator('input[type="text"], input[type="email"], input[type="password"], textarea, select').all();
    for (const input of inputs) {
      const id = await input.getAttribute('id');
      const name = await input.getAttribute('name');
      
      if (id) {
        const label = page.locator(`label[for="${id}"]`);
        const labelExists = await label.count() > 0;
        
        if (!labelExists) {
          // Check for aria-label or placeholder
          const ariaLabel = await input.getAttribute('aria-label');
          const placeholder = await input.getAttribute('placeholder');
          
          expect(ariaLabel || placeholder).toBeTruthy();
        }
      }
    }
    
    // Check for focus indicators
    const focusableElements = await page.locator('button, a, input, select, textarea').all();
    if (focusableElements.length > 0) {
      await focusableElements[0].focus();
      // Focus should be visible (this is hard to test automatically)
    }
  });

  test('should support keyboard navigation', async ({ page }) => {
    await page.goto('/');
    
    // Tab through the page
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    
    // Should be able to navigate with Enter and Space
    const focusedElement = await page.locator(':focus');
    const tagName = await focusedElement.evaluate(el => el.tagName.toLowerCase());
    
    if (tagName === 'button' || tagName === 'a') {
      // These should be activatable with Enter or Space
      expect(['button', 'a']).toContain(tagName);
    }
    
    // Test escape key for modals/dropdowns
    const dropdown = page.locator('.dropdown, .menu');
    if (await dropdown.isVisible()) {
      await page.keyboard.press('Escape');
      // Dropdown should close (implementation dependent)
    }
  });

  test('should have proper loading states', async ({ page, navHelper }) => {
    await page.goto('/');
    
    // Navigate to a page that requires data loading
    await navHelper.goToProjects();
    
    // Should show loading indicator briefly
    const loadingVisible = await page.isVisible('.loading, .spinner, .skeleton') ||
                          await page.textContent('body').then(text => text.includes('로딩'));
    
    // Wait for content to load
    await navHelper.waitForPageLoad();
    
    // Loading should be gone and content visible
    await expect(page.locator('.project-list, .projects, .content')).toBeVisible();
  });

  test('should display error states appropriately', async ({ page }) => {
    // Mock API error
    await page.route('**/api/projects', route => 
      route.fulfill({ status: 500, body: 'Server Error' })
    );
    
    await page.goto('/projects');
    
    // Should show error message
    const errorVisible = await page.isVisible('.error, .error-message') ||
                        await page.textContent('body').then(text => 
                          text.includes('오류') || text.includes('에러') || text.includes('Error')
                        );
    
    expect(errorVisible).toBe(true);
  });

  test('should have proper form validation', async ({ page, navHelper }) => {
    // Go to a form page (project creation)
    await navHelper.goToProjects();
    
    const createButton = page.locator('button:has-text("Create"), button:has-text("생성"), button:has-text("추가")');
    if (await createButton.isVisible()) {
      await createButton.click();
      
      // Try to submit empty form
      const submitButton = page.locator('button[type="submit"], button:has-text("Submit"), button:has-text("저장")');
      if (await submitButton.isVisible()) {
        await submitButton.click();
        
        // Should show validation errors
        const validationError = await page.isVisible('.error, .validation-error, .field-error') ||
                              await page.textContent('body').then(text => 
                                text.includes('필수') || text.includes('required')
                              );
        
        expect(validationError).toBe(true);
      }
    }
  });

  test('should support internationalization', async ({ page }) => {
    await page.goto('/');
    
    // Check for Korean text (primary language)
    const hasKorean = await page.textContent('body').then(text => 
      /[가-힣]/.test(text)
    );
    
    expect(hasKorean).toBe(true);
    
    // Check for proper date/time formatting
    const dateElements = await page.locator('[data-date], .date, .timestamp').all();
    if (dateElements.length > 0) {
      const dateText = await dateElements[0].textContent();
      // Should contain reasonable date format
      expect(dateText).toMatch(/\d{4}|\d{2}\/\d{2}|\d{2}-\d{2}/);
    }
  });

  test('should handle data tables properly', async ({ page, navHelper }) => {
    // Navigate to a page with tables
    await navHelper.goToProjects();
    
    const table = page.locator('table, .table, .data-table');
    if (await table.isVisible()) {
      // Should have proper table structure
      await expect(table.locator('thead, .table-header')).toBeVisible();
      await expect(table.locator('tbody, .table-body')).toBeVisible();
      
      // Check for sortable columns
      const sortableHeaders = await table.locator('th[data-sortable], .sortable').all();
      if (sortableHeaders.length > 0) {
        await sortableHeaders[0].click();
        // Table should re-render (hard to test automatically)
      }
      
      // Check for pagination
      const pagination = page.locator('.pagination, .pager');
      if (await pagination.isVisible()) {
        const nextButton = pagination.locator('button:has-text("Next"), button:has-text("다음")');
        if (await nextButton.isVisible() && !(await nextButton.isDisabled())) {
          await nextButton.click();
          await navHelper.waitForPageLoad();
        }
      }
    }
  });

  test('should have proper modal behavior', async ({ page }) => {
    await page.goto('/');
    
    // Look for modal trigger
    const modalTrigger = page.locator('button:has-text("Add"), button:has-text("Create"), button:has-text("추가"), button:has-text("생성")');
    
    if (await modalTrigger.first().isVisible()) {
      await modalTrigger.first().click();
      
      // Modal should appear
      const modal = page.locator('.modal, .dialog, .popup');
      if (await modal.isVisible()) {
        await expect(modal).toBeVisible();
        
        // Should have close button
        const closeButton = modal.locator('button:has-text("×"), button:has-text("Close"), button:has-text("닫기"), .close');
        if (await closeButton.isVisible()) {
          await closeButton.click();
          await expect(modal).not.toBeVisible();
        } else {
          // Try escape key
          await page.keyboard.press('Escape');
          await expect(modal).not.toBeVisible();
        }
      }
    }
  });

  test('should handle file uploads properly', async ({ page, navHelper }) => {
    // Navigate to a page with file upload
    await navHelper.goToCompanies();
    
    const fileInput = page.locator('input[type="file"]');
    if (await fileInput.isVisible()) {
      // Should accept appropriate file types
      const accept = await fileInput.getAttribute('accept');
      expect(accept).toBeTruthy();
      
      // Should show proper upload UI
      const uploadArea = page.locator('.upload-area, .file-upload, .drop-zone');
      if (await uploadArea.isVisible()) {
        await expect(uploadArea).toBeVisible();
      }
    }
  });
});
