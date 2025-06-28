/**
 * Navigation Helper class for Online Evaluation System E2E tests
 * Handles common navigation patterns and page interactions
 */
export class NavigationHelper {
  constructor(page) {
    this.page = page;
  }

  /**
   * Navigate to home page
   */
  async goToHome() {
    await this.page.goto('/');
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Navigate to login page
   */
  async goToLogin() {
    await this.page.goto('/login');
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Navigate to admin dashboard
   */
  async goToAdminDashboard() {
    await this.page.goto('/admin');
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Navigate to evaluator dashboard
   */
  async goToEvaluatorDashboard() {
    await this.page.goto('/evaluator');
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Navigate to projects page
   */
  async goToProjects() {
    await this.page.goto('/projects');
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Navigate to specific project
   */
  async goToProject(projectId) {
    await this.page.goto(`/projects/${projectId}`);
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Navigate to companies page
   */
  async goToCompanies() {
    await this.page.goto('/companies');
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Navigate to specific company
   */
  async goToCompany(companyId) {
    await this.page.goto(`/companies/${companyId}`);
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Navigate to templates page
   */
  async goToTemplates() {
    await this.page.goto('/templates');
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Navigate to evaluations page
   */
  async goToEvaluations() {
    await this.page.goto('/evaluations');
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Navigate to specific evaluation
   */
  async goToEvaluation(evaluationId) {
    await this.page.goto(`/evaluations/${evaluationId}`);
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Navigate to analytics page
   */
  async goToAnalytics() {
    await this.page.goto('/analytics');
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Click navigation menu item
   */
  async clickNavMenuItem(menuText) {
    const menuItem = this.page.locator(`nav a:has-text("${menuText}")`);
    await menuItem.click();
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Open sidebar if not open
   */
  async openSidebar() {
    const sidebarToggle = this.page.locator('[data-testid="sidebar-toggle"]');
    if (await sidebarToggle.isVisible()) {
      await sidebarToggle.click();
    }
  }

  /**
   * Close sidebar if open
   */
  async closeSidebar() {
    const sidebarClose = this.page.locator('[data-testid="sidebar-close"]');
    if (await sidebarClose.isVisible()) {
      await sidebarClose.click();
    }
  }

  /**
   * Wait for page to load completely
   */
  async waitForPageLoad() {
    await this.page.waitForLoadState('networkidle');
    
    // Wait for any loading spinners to disappear
    try {
      await this.page.waitForSelector('.loading, .spinner', { 
        state: 'hidden', 
        timeout: 5000 
      });
    } catch (error) {
      // Ignore if no loading indicators found
    }
  }

  /**
   * Verify current page URL
   */
  async verifyCurrentPage(expectedPath) {
    const currentURL = this.page.url();
    const currentPath = new URL(currentURL).pathname;
    
    if (currentPath !== expectedPath) {
      throw new Error(`Expected to be on ${expectedPath}, but was on ${currentPath}`);
    }
    
    return true;
  }

  /**
   * Check if element is visible
   */
  async isElementVisible(selector) {
    try {
      return await this.page.isVisible(selector);
    } catch (error) {
      return false;
    }
  }

  /**
   * Wait for element to be visible
   */
  async waitForElement(selector, timeout = 10000) {
    await this.page.waitForSelector(selector, { 
      state: 'visible', 
      timeout 
    });
  }

  /**
   * Wait for text to appear
   */
  async waitForText(text, timeout = 10000) {
    await this.page.waitForSelector(`text=${text}`, { timeout });
  }

  /**
   * Scroll to element
   */
  async scrollToElement(selector) {
    const element = this.page.locator(selector);
    await element.scrollIntoViewIfNeeded();
  }

  /**
   * Take screenshot with timestamp
   */
  async takeScreenshot(name) {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `${name}-${timestamp}.png`;
    await this.page.screenshot({ 
      path: `test-results/screenshots/${filename}`,
      fullPage: true 
    });
    return filename;
  }

  /**
   * Handle modal/dialog
   */
  async handleModal(action = 'accept') {
    this.page.on('dialog', async dialog => {
      if (action === 'accept') {
        await dialog.accept();
      } else {
        await dialog.dismiss();
      }
    });
  }

  /**
   * Upload file
   */
  async uploadFile(fileInputSelector, filePath) {
    const fileInput = this.page.locator(fileInputSelector);
    await fileInput.setInputFiles(filePath);
  }

  /**
   * Download file and return path
   */
  async downloadFile(downloadTriggerSelector) {
    const [download] = await Promise.all([
      this.page.waitForEvent('download'),
      this.page.click(downloadTriggerSelector)
    ]);
    
    const downloadPath = await download.path();
    return downloadPath;
  }

  /**
   * Switch to new tab/window
   */
  async switchToNewTab() {
    const [newPage] = await Promise.all([
      this.page.context().waitForEvent('page'),
      // Trigger that opens new tab should be called before this
    ]);
    
    await newPage.waitForLoadState();
    return newPage;
  }

  /**
   * Go back in browser history
   */
  async goBack() {
    await this.page.goBack();
    await this.waitForPageLoad();
  }

  /**
   * Go forward in browser history
   */
  async goForward() {
    await this.page.goForward();
    await this.waitForPageLoad();
  }

  /**
   * Refresh current page
   */
  async refresh() {
    await this.page.reload();
    await this.waitForPageLoad();
  }
}
