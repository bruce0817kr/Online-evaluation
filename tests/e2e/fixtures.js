import { test as base, expect } from '@playwright/test';
import { APIHelper } from './helpers/api-helper';
import { AuthHelper } from './helpers/auth-helper';
import { NavigationHelper } from './helpers/navigation-helper';

// Extend basic test by providing "apiHelper", "authHelper", "navHelper" fixtures.
export const test = base.extend<{
  apiHelper: APIHelper;
  authHelper: AuthHelper;
  navHelper: NavigationHelper;
}>({
  apiHelper: async ({ request }, use) => {
    const apiHelper = new APIHelper(request);
    await use(apiHelper);
  },

  authHelper: async ({ page, apiHelper }, use) => {
    const authHelper = new AuthHelper(page, apiHelper);
    await use(authHelper);
  },

  navHelper: async ({ page }, use) => {
    const navHelper = new NavigationHelper(page);
    await use(navHelper);
  },
});

export { expect } from '@playwright/test';
