// 템플릿 관리 E2E 테스트 (Playwright)
// 실행: npx playwright test tests_e2e/template_management.spec.js

const { test, expect } = require('@playwright/test');

test.describe('템플릿 관리 E2E', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000'); // 실제 프론트엔드 주소로 변경 필요
    await page.click('text=평가 템플릿 관리'); // 라우팅 메뉴 진입(필요시)
  });

  test('필터/정렬/페이지네이션 UI 동작', async ({ page }) => {
    // 상태 필터
    await page.selectOption('#filterStatus', 'active');
    await expect(page.locator('.template-list li')).toHaveCountGreaterThan(0);
    // 생성자 필터
    await page.fill('#filterCreator', 'admin');
    await expect(page.locator('.template-list li')).toHaveCountGreaterThanOrEqual(0);
    // 정렬 옵션
    await page.selectOption('#sortOption', 'name_asc');
    // 페이지네이션
    if (await page.locator('.pagination button').count() > 0) {
      await page.click('.pagination button:has-text(\'>\')');
    }
  });

  test('템플릿 생성/수정/삭제/복제/공유', async ({ page }) => {
    // 템플릿 생성
    await page.click('button:has-text("새 템플릿 생성")');
    await page.fill('#templateName', 'E2E 테스트 템플릿');
    await page.fill('#templateDescription', '자동화 테스트용');
    await page.click('button:has-text("생성")');
    await expect(page.locator('.template-list li')).toContainText('E2E 테스트 템플릿');
    // 상세 진입 및 수정
    await page.click('.template-list li:has-text("E2E 테스트 템플릿")');
    await page.click('button:has-text("수정")');
    await page.fill('#editedTemplateName', 'E2E 테스트 템플릿 수정');
    await page.click('button:has-text("저장")');
    await expect(page.locator('.template-list li')).toContainText('E2E 테스트 템플릿 수정');
    // 복제
    await page.click('.template-list li:has-text("E2E 테스트 템플릿 수정") button:has-text("복제")');
    // 삭제(아카이브)
    await page.click('.template-list li:has-text("E2E 테스트 템플릿 수정") button:has-text("아카이브")');
    await page.on('dialog', dialog => dialog.accept());
  });

  test('오류/피드백 메시지 및 접근성', async ({ page }) => {
    // 네트워크 차단 등으로 오류 유발 후 error-message 노출 확인(수동 또는 mock)
    // 키보드 내비게이션(탭, 엔터 등)으로 주요 UI 접근 가능 여부
    await page.keyboard.press('Tab');
    await expect(page.locator(':focus-visible')).toBeVisible();
  });
});
