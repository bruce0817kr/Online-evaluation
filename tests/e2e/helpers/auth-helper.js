/**
 * Authentication Helper class for Online Evaluation System E2E tests
 * Handles login/logout operations and user management
 */
export class AuthHelper {
  constructor(page, apiHelper) {
    this.page = page;
    this.apiHelper = apiHelper;
    this.currentUser = null;
  }

  /**
   * Login via UI
   */
  async loginViaUI(username, password) {
    await this.page.goto('/login');
    
    // Fill login form
    await this.page.fill('input[name="login_id"]', username);
    await this.page.fill('input[name="password"]', password);
    
    // Submit form
    await this.page.click('button[type="submit"]');
    
    // Wait for navigation
    await this.page.waitForURL('/');
    
    // Verify login success by checking for user info or dashboard
    const isLoggedIn = await this.page.isVisible('[data-testid="user-menu"]') ||
                      await this.page.isVisible('.dashboard') ||
                      await this.page.textContent('body').then(text => text.includes('대시보드'));
    
    if (isLoggedIn) {
      this.currentUser = { username, role: 'unknown' };
      return true;
    }
    
    return false;
  }

  /**
   * Login via API
   */
  async loginViaAPI(username, password) {
    const result = await this.apiHelper.login(username, password);
    
    if (result.success && result.data) {
      this.currentUser = {
        username,
        role: result.data.role || 'unknown',
        token: result.data.access_token
      };
      
      // Set auth context in browser if needed
      await this.page.context().addCookies([{
        name: 'auth_token',
        value: result.data.access_token,
        domain: 'localhost',
        path: '/'
      }]);
      
      return true;
    }
    
    return false;
  }

  /**
   * Logout
   */
  async logout() {
    try {
      // Try UI logout first
      const logoutButton = this.page.locator('[data-testid="logout-button"]');
      if (await logoutButton.isVisible()) {
        await logoutButton.click();
      } else {
        // Try alternative logout methods
        const userMenu = this.page.locator('[data-testid="user-menu"]');
        if (await userMenu.isVisible()) {
          await userMenu.click();
          await this.page.click('text=로그아웃');
        }
      }
    } catch (error) {
      console.warn('UI logout failed, clearing context:', error.message);
    }
    
    // Clear authentication context
    await this.page.context().clearCookies();
    this.currentUser = null;
    this.apiHelper.setToken(null);
  }

  /**
   * Ensure logged in with specific role
   */
  async ensureLoggedIn(role = 'admin') {
    const credentials = this.getCredentialsForRole(role);
    
    if (!this.currentUser || this.currentUser.role !== role) {
      const success = await this.loginViaAPI(credentials.username, credentials.password);
      if (!success) {
        throw new Error(`Failed to login as ${role}`);
      }
    }
    
    return this.currentUser;
  }

  /**
   * Get credentials for role
   */
  getCredentialsForRole(role) {
    const credentialsMap = {
      admin: { username: 'admin', password: 'admin123' },
      secretary: { username: 'secretary', password: 'secretary123' },
      evaluator: { username: 'evaluator01', password: 'evaluator123' }
    };
    
    return credentialsMap[role] || credentialsMap.admin;
  }

  /**
   * Check if user is logged in
   */
  isLoggedIn() {
    return this.currentUser !== null;
  }

  /**
   * Get current user info
   */
  getCurrentUser() {
    return this.currentUser;
  }

  /**
   * Verify user role access
   */
  async verifyRoleAccess(expectedRole) {
    if (!this.currentUser) {
      throw new Error('No user logged in');
    }
    
    // Get user info from API
    const userInfo = await this.apiHelper.getCurrentUser();
    
    if (!userInfo.success) {
      throw new Error('Failed to get user info');
    }
    
    const actualRole = userInfo.data.role;
    
    if (actualRole !== expectedRole) {
      throw new Error(`Expected role ${expectedRole}, but got ${actualRole}`);
    }
    
    return true;
  }

  /**
   * Login as admin for setup operations
   */
  async loginAsAdmin() {
    return await this.ensureLoggedIn('admin');
  }

  /**
   * Login as evaluator for evaluation operations
   */
  async loginAsEvaluator() {
    return await this.ensureLoggedIn('evaluator');
  }

  /**
   * Login as secretary for management operations  
   */
  async loginAsSecretary() {
    return await this.ensureLoggedIn('secretary');
  }

  /**
   * Wait for authentication state
   */
  async waitForAuthState(timeout = 10000) {
    const startTime = Date.now();
    
    while (Date.now() - startTime < timeout) {
      try {
        const userInfo = await this.apiHelper.getCurrentUser();
        if (userInfo.success) {
          return true;
        }
      } catch (error) {
        // Continue waiting
      }
      
      await this.page.waitForTimeout(500);
    }
    
    return false;
  }

  /**
   * Setup test user if not exists
   */
  async setupTestUser(role, userData) {
    await this.ensureLoggedIn('admin');
    
    try {
      if (role === 'evaluator') {
        const result = await this.apiHelper.createEvaluator(
          userData.name,
          userData.phone,
          userData.email
        );
        return result.success ? result.data : null;
      }
      // Add other user type creation as needed
    } catch (error) {
      console.warn(`Failed to create test user: ${error.message}`);
      return null;
    }
  }
}
