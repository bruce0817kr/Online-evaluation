import { test, expect } from '../fixtures';

test.describe('Authentication and Authorization', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should display login page for unauthenticated users', async ({ page }) => {
    await expect(page).toHaveURL(/.*login/);
    await expect(page.locator('h1, h2')).toContainText(/로그인|Login/);
    await expect(page.locator('input[name="login_id"]')).toBeVisible();
    await expect(page.locator('input[name="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test('should login successfully with admin credentials', async ({ authHelper, navHelper }) => {
    const success = await authHelper.loginViaUI('admin', 'admin123');
    expect(success).toBe(true);
    
    // Verify redirect to dashboard
    await navHelper.verifyCurrentPage('/');
    
    // Verify user is logged in
    expect(authHelper.isLoggedIn()).toBe(true);
  });

  test('should login successfully with evaluator credentials', async ({ authHelper, navHelper }) => {
    const success = await authHelper.loginViaUI('evaluator01', 'evaluator123');
    expect(success).toBe(true);
    
    await navHelper.verifyCurrentPage('/');
    expect(authHelper.isLoggedIn()).toBe(true);
  });

  test('should fail login with invalid credentials', async ({ page, authHelper }) => {
    await page.goto('/login');
    
    await page.fill('input[name="login_id"]', 'invalid_user');
    await page.fill('input[name="password"]', 'wrong_password');
    await page.click('button[type="submit"]');
    
    // Should remain on login page
    await expect(page).toHaveURL(/.*login/);
    
    // Should show error message
    await expect(page.locator('.error, .alert')).toBeVisible();
  });

  test('should handle API-based authentication', async ({ apiHelper }) => {
    const result = await apiHelper.login('admin', 'admin123');
    
    expect(result.success).toBe(true);
    expect(result.data).toHaveProperty('access_token');
    expect(result.data).toHaveProperty('token_type', 'bearer');
    
    // Verify token works for protected endpoints
    const userInfo = await apiHelper.getCurrentUser();
    expect(userInfo.success).toBe(true);
    expect(userInfo.data).toHaveProperty('role', 'admin');
  });

  test('should logout successfully', async ({ page, authHelper, navHelper }) => {
    // Login first
    await authHelper.loginViaUI('admin', 'admin123');
    
    // Logout
    await authHelper.logout();
    
    // Should redirect to login
    await expect(page).toHaveURL(/.*login/);
    expect(authHelper.isLoggedIn()).toBe(false);
  });

  test('should verify role-based access control', async ({ authHelper, apiHelper }) => {
    // Test admin access
    await authHelper.loginViaAPI('admin', 'admin123');
    await authHelper.verifyRoleAccess('admin');
    
    const adminDashboard = await apiHelper.getAdminDashboard();
    expect(adminDashboard.success).toBe(true);
    
    // Test evaluator access
    await authHelper.loginViaAPI('evaluator01', 'evaluator123');
    await authHelper.verifyRoleAccess('evaluator');
    
    const evaluatorDashboard = await apiHelper.getEvaluatorDashboard();
    expect(evaluatorDashboard.success).toBe(true);
  });

  test('should maintain session across page refreshes', async ({ page, authHelper, navHelper }) => {
    // Login
    await authHelper.loginViaUI('admin', 'admin123');
    
    // Refresh page
    await navHelper.refresh();
    
    // Should still be logged in
    await navHelper.verifyCurrentPage('/');
    expect(authHelper.isLoggedIn()).toBe(true);
  });

  test('should handle concurrent login sessions', async ({ apiHelper }) => {
    // Login with same user multiple times
    const login1 = await apiHelper.login('admin', 'admin123');
    expect(login1.success).toBe(true);
    
    const login2 = await apiHelper.login('admin', 'admin123');
    expect(login2.success).toBe(true);
    
    // Both tokens should work
    apiHelper.setToken(login1.data.access_token);
    const user1 = await apiHelper.getCurrentUser();
    expect(user1.success).toBe(true);
    
    apiHelper.setToken(login2.data.access_token);
    const user2 = await apiHelper.getCurrentUser();
    expect(user2.success).toBe(true);
  });
});
