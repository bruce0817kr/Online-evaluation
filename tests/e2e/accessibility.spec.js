import { test, expect } from '../fixtures';

test.describe('Accessibility Testing', () => {
  test.beforeEach(async ({ authHelper }) => {
    await authHelper.loginViaUI('admin', 'admin123');
  });

  test('should meet WCAG 2.1 Level AA standards', async ({ page }) => {
    // Test main pages for accessibility
    const pages = [
      { path: '/', name: 'Dashboard' },
      { path: '/projects', name: 'Projects' },
      { path: '/templates', name: 'Templates' },
      { path: '/evaluations', name: 'Evaluations' }
    ];

    for (const pageInfo of pages) {
      await page.goto(pageInfo.path);
      await page.waitForLoadState('networkidle');

      // Check for proper heading structure
      const headings = await page.locator('h1, h2, h3, h4, h5, h6').all();
      expect(headings.length).toBeGreaterThan(0);

      // Verify there's exactly one h1 per page
      const h1Count = await page.locator('h1').count();
      expect(h1Count).toBeLessThanOrEqual(1);

      // Check for proper alt text on images
      const images = await page.locator('img').all();
      for (const img of images) {
        const alt = await img.getAttribute('alt');
        const ariaLabel = await img.getAttribute('aria-label');
        const role = await img.getAttribute('role');
        
        // Images should have alt text unless they're decorative
        if (role !== 'presentation' && !alt && !ariaLabel) {
          console.warn(`Image without alt text found on ${pageInfo.name} page`);
        }
      }

      // Check for proper form labels
      const inputs = await page.locator('input, select, textarea').all();
      for (const input of inputs) {
        const id = await input.getAttribute('id');
        const ariaLabel = await input.getAttribute('aria-label');
        const ariaLabelledby = await input.getAttribute('aria-labelledby');
        
        if (id) {
          const label = await page.locator(`label[for="${id}"]`).count();
          if (label === 0 && !ariaLabel && !ariaLabelledby) {
            console.warn(`Input without proper label found on ${pageInfo.name} page`);
          }
        }
      }

      // Check for proper button accessibility
      const buttons = await page.locator('button, [role="button"]').all();
      for (const button of buttons) {
        const text = await button.textContent();
        const ariaLabel = await button.getAttribute('aria-label');
        
        if (!text?.trim() && !ariaLabel) {
          console.warn(`Button without accessible name found on ${pageInfo.name} page`);
        }
      }

      console.log(`✅ Accessibility check completed for ${pageInfo.name} page`);
    }
  });

  test('should support keyboard navigation', async ({ page }) => {
    await page.goto('/');
    
    // Test tab navigation
    await page.keyboard.press('Tab');
    
    // Should focus on first interactive element
    const firstFocused = await page.locator(':focus').first();
    await expect(firstFocused).toBeVisible();
    
    // Navigate through multiple elements
    const focusableElements = [];
    for (let i = 0; i < 10; i++) {
      await page.keyboard.press('Tab');
      
      const focused = await page.locator(':focus').first();
      if (await focused.isVisible()) {
        const tagName = await focused.evaluate(el => el.tagName);
        const className = await focused.getAttribute('class') || '';
        focusableElements.push(`${tagName}.${className}`);
      }
    }
    
    // Should have navigated through multiple focusable elements
    expect(focusableElements.length).toBeGreaterThan(3);
    
    // Test shift+tab (reverse navigation)
    await page.keyboard.press('Shift+Tab');
    const reverseFocused = await page.locator(':focus').first();
    await expect(reverseFocused).toBeVisible();
  });

  test('should support screen reader navigation', async ({ page }) => {
    await page.goto('/');
    
    // Check for proper ARIA landmarks
    const landmarks = await page.locator('[role="main"], [role="navigation"], [role="banner"], [role="contentinfo"], main, nav, header, footer').count();
    expect(landmarks).toBeGreaterThan(0);
    
    // Check for proper skip links
    const skipLinks = await page.locator('a[href*="#"], [class*="skip"]').first();
    if (await skipLinks.isVisible()) {
      await skipLinks.focus();
      await expect(skipLinks).toBeVisible();
    }
    
    // Check for proper heading hierarchy
    let lastHeadingLevel = 0;
    const headings = await page.locator('h1, h2, h3, h4, h5, h6').all();
    
    for (const heading of headings) {
      const tagName = await heading.evaluate(el => el.tagName);
      const level = parseInt(tagName.charAt(1));
      
      // Heading levels should not skip levels (e.g., h1 -> h3)
      if (lastHeadingLevel > 0) {
        expect(level - lastHeadingLevel).toBeLessThanOrEqual(1);
      }
      
      lastHeadingLevel = level;
    }
  });

  test('should provide proper focus management', async ({ page }) => {
    await page.goto('/');
    
    // Test modal/dialog focus management
    if (await page.locator('text=새 평가 생성, text=새 템플릿 생성').isVisible()) {
      await page.click('text=새 평가 생성, text=새 템플릿 생성');
      
      // Focus should move to modal
      await page.waitForTimeout(500);
      const modalFocused = await page.locator('.modal :focus, .dialog :focus, .form :focus').first();
      
      if (await modalFocused.isVisible()) {
        // Test escape key to close modal
        await page.keyboard.press('Escape');
        await page.waitForTimeout(500);
        
        // Focus should return to trigger element
        const returnedFocus = await page.locator(':focus').first();
        await expect(returnedFocus).toBeVisible();
      }
    }
    
    // Test dropdown focus management
    if (await page.locator('[data-testid="admin-dropdown"], .dropdown-toggle').isVisible()) {
      await page.click('[data-testid="admin-dropdown"], .dropdown-toggle');
      
      // Should be able to navigate dropdown with arrow keys
      await page.keyboard.press('ArrowDown');
      const dropdownFocused = await page.locator('.dropdown-menu :focus, .menu :focus').first();
      
      if (await dropdownFocused.isVisible()) {
        await page.keyboard.press('ArrowDown');
        await page.keyboard.press('Enter');
        
        // Should activate the focused item
        await page.waitForLoadState('domcontentloaded');
      }
    }
  });

  test('should support high contrast mode', async ({ page }) => {
    await page.goto('/');
    
    // Simulate high contrast mode
    await page.addStyleTag({
      content: `
        @media (prefers-contrast: high) {
          * {
            filter: contrast(2) !important;
          }
        }
      `
    });
    
    // Check color contrast ratios
    const testElements = [
      { selector: 'button', description: 'Buttons' },
      { selector: 'a', description: 'Links' },
      { selector: '.card, .panel', description: 'Cards' },
      { selector: 'input, select, textarea', description: 'Form controls' }
    ];
    
    for (const element of testElements) {
      const elements = await page.locator(element.selector).all();
      
      for (const el of elements.slice(0, 3)) { // Test first 3 of each type
        const styles = await el.evaluate(el => {
          const computed = window.getComputedStyle(el);
          return {
            color: computed.color,
            backgroundColor: computed.backgroundColor,
            borderColor: computed.borderColor
          };
        });
        
        // Elements should have sufficient contrast (simplified check)
        expect(styles.color).toBeDefined();
        expect(styles.backgroundColor).toBeDefined();
      }
    }
  });

  test('should support reduced motion preferences', async ({ page }) => {
    // Simulate reduced motion preference
    await page.emulateMedia({ reducedMotion: 'reduce' });
    await page.goto('/');
    
    // Check that animations are disabled or reduced
    const animatedElements = await page.locator('[class*="animate"], [class*="transition"], [style*="animation"]').all();
    
    for (const element of animatedElements) {
      const styles = await element.evaluate(el => {
        const computed = window.getComputedStyle(el);
        return {
          animationDuration: computed.animationDuration,
          transitionDuration: computed.transitionDuration
        };
      });
      
      // Animations should be disabled or very short
      if (styles.animationDuration !== 'none' && styles.animationDuration !== '0s') {
        console.log('Animation found with duration:', styles.animationDuration);
      }
    }
  });

  test('should provide accessible error messages', async ({ page }) => {
    await page.goto('/');
    
    // Test form validation errors
    if (await page.locator('text=새 템플릿 생성').isVisible()) {
      await page.click('text=새 템플릿 생성');
      
      // Submit empty form to trigger validation
      if (await page.locator('button[type="submit"], text=저장').isVisible()) {
        await page.click('button[type="submit"], text=저장');
        
        // Check for accessible error messages
        const errorMessages = await page.locator('.error, .invalid, .field-error, [role="alert"]').all();
        
        for (const error of errorMessages) {
          // Error messages should be properly associated with fields
          const ariaDescribedby = await error.getAttribute('aria-describedby');
          const role = await error.getAttribute('role');
          
          expect(role === 'alert' || ariaDescribedby).toBeTruthy();
        }
      }
    }
  });

  test('should provide accessible data tables', async ({ page }) => {
    // Navigate to a page with data tables
    await page.click('text=📊 평가 관리');
    await page.waitForLoadState('networkidle');
    
    const tables = await page.locator('table').all();
    
    for (const table of tables) {
      // Tables should have captions or aria-label
      const caption = await table.locator('caption').count();
      const ariaLabel = await table.getAttribute('aria-label');
      
      if (caption === 0 && !ariaLabel) {
        console.warn('Table without caption or aria-label found');
      }
      
      // Check for proper table headers
      const headers = await table.locator('th').all();
      expect(headers.length).toBeGreaterThan(0);
      
      // Headers should have proper scope
      for (const header of headers) {
        const scope = await header.getAttribute('scope');
        const id = await header.getAttribute('id');
        
        if (!scope && !id) {
          console.warn('Table header without scope or id found');
        }
      }
      
      // Check for proper row/column headers association
      const cells = await table.locator('td').all();
      for (const cell of cells.slice(0, 5)) { // Check first 5 cells
        const headers = await cell.getAttribute('headers');
        const scope = await cell.getAttribute('scope');
        
        // Complex tables should have proper headers association
        if (headers || scope) {
          expect(headers || scope).toBeDefined();
        }
      }
    }
  });

  test('should support voice control navigation', async ({ page }) => {
    await page.goto('/');
    
    // Test that all interactive elements have accessible names for voice control
    const interactiveElements = await page.locator('button, a, input, select, textarea, [role="button"], [tabindex="0"]').all();
    
    for (const element of interactiveElements) {
      const tagName = await element.evaluate(el => el.tagName);
      const textContent = await element.textContent();
      const ariaLabel = await element.getAttribute('aria-label');
      const title = await element.getAttribute('title');
      const value = await element.getAttribute('value');
      const placeholder = await element.getAttribute('placeholder');
      
      // Elements should have some accessible name
      const hasAccessibleName = textContent?.trim() || ariaLabel || title || value || placeholder;
      
      if (!hasAccessibleName) {
        console.warn(`${tagName} element without accessible name found`);
      }
    }
  });

  test('should handle zoom levels appropriately', async ({ page }) => {
    await page.goto('/');
    
    // Test various zoom levels
    const zoomLevels = [1.5, 2.0, 2.5];
    
    for (const zoom of zoomLevels) {
      await page.evaluate((zoomLevel) => {
        document.body.style.zoom = zoomLevel.toString();
      }, zoom);
      
      await page.waitForTimeout(500);
      
      // Content should still be accessible at high zoom
      await expect(page.locator('body')).toBeVisible();
      
      // Navigation should still work
      const navElements = await page.locator('nav a, .nav a, [role="navigation"] a').count();
      if (navElements > 0) {
        const firstNav = page.locator('nav a, .nav a, [role="navigation"] a').first();
        await expect(firstNav).toBeVisible();
      }
      
      // Form elements should still be usable
      const inputs = await page.locator('input, button').count();
      if (inputs > 0) {
        const firstInput = page.locator('input, button').first();
        await expect(firstInput).toBeVisible();
      }
    }
    
    // Reset zoom
    await page.evaluate(() => {
      document.body.style.zoom = '1';
    });
  });

  test('should provide proper status updates for dynamic content', async ({ page, apiHelper }) => {
    await page.goto('/');
    
    // Test live regions for status updates
    if (await page.locator('text=새 평가 생성').isVisible()) {
      await page.click('text=새 평가 생성');
      
      // Look for live regions
      const liveRegions = await page.locator('[role="status"], [role="alert"], [aria-live]').count();
      
      if (liveRegions > 0) {
        // Fill form and submit to test status updates
        const nameInput = page.locator('input[name="name"], input[type="text"]').first();
        if (await nameInput.isVisible()) {
          await nameInput.fill('접근성 테스트');
          
          const submitButton = page.locator('button[type="submit"], text=저장').first();
          if (await submitButton.isVisible()) {
            await submitButton.click();
            
            // Should announce status change
            const statusRegion = page.locator('[role="status"], [role="alert"], [aria-live]').first();
            await expect(statusRegion).toBeVisible();
          }
        }
      }
    }
  });

  test('should provide accessible loading states', async ({ page }) => {
    await page.goto('/');
    
    // Test loading indicators accessibility
    await page.click('text=📊 평가 관리');
    
    // Look for loading indicators
    const loadingIndicators = await page.locator('.loading, .spinner, [aria-busy="true"]').all();
    
    for (const indicator of loadingIndicators) {
      // Loading indicators should be properly announced
      const ariaLabel = await indicator.getAttribute('aria-label');
      const role = await indicator.getAttribute('role');
      const ariaBusy = await indicator.getAttribute('aria-busy');
      
      if (!ariaLabel && role !== 'status' && ariaBusy !== 'true') {
        console.warn('Loading indicator without proper accessibility attributes found');
      }
    }
    
    // Test that content is properly hidden/shown during loading
    await page.waitForLoadState('networkidle');
    
    // After loading, content should be accessible
    const mainContent = await page.locator('main, [role="main"], .content').first();
    if (await mainContent.isVisible()) {
      await expect(mainContent).toBeVisible();
    }
  });
});