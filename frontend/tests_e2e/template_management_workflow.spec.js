// 템플릿 관리 워크플로우 기반 E2E 자동화 테스트 (Playwright)
// 실행: npx playwright test tests_e2e/template_management_workflow.spec.js

import { test, expect } from '@playwright/test';

test.describe('템플릿 관리 워크플로우 E2E', () => {
  test.beforeEach(async ({ page }) => {
    // 로그인 페이지로 이동
    await page.goto('http://localhost:3000');
    
    // 로그인이 필요한지 확인 (로그인 화면이 표시되는지)
    const loginForm = await page.locator('form').count();
    if (loginForm > 0) {
      // 테스트 계정으로 로그인 (관리자 계정 사용)
      await page.fill('input[type="text"]', 'admin');
      await page.fill('input[type="password"]', 'admin123');
      await page.click('button[type="submit"]');
      
      // 로그인 완료 대기 (대시보드 로딩 대기)
      await page.waitForURL('http://localhost:3000', { timeout: 10000 });
      await page.waitForLoadState('networkidle');
    }
    
    // 템플릿 관리 메뉴 클릭
    await page.click('text=평가 템플릿 관리');
  });

  test('1. 템플릿 생성 → 상세 → 수정 → 항목 드래그앤드롭 → 저장', async ({ page }) => {
    await page.click('button:has-text("새 템플릿 생성")');
    await page.fill('#templateName', '워크플로우 자동화 템플릿');
    await page.fill('#templateDescription', '자동화 워크플로우용 템플릿');
    await page.click('button:has-text("생성")');
    await expect(page.locator('.template-list li')).toContainText('워크플로우 자동화 템플릿');
    await page.click('.template-list li:has-text("워크플로우 자동화 템플릿")');
    await page.click('button:has-text("수정")');
    // 항목 드래그앤드롭 (첫 번째와 두 번째 항목 순서 변경)
    const dragHandle = page.locator('.item-input-row span[style*="cursor:grab"]').first();
    const targetRow = page.locator('.item-input-row').nth(1);
    await dragHandle.dragTo(targetRow);
    await page.click('button:has-text("저장")');
    await expect(page.locator('.template-list li')).toContainText('워크플로우 자동화 템플릿');
  });

  test('2. 카드뷰/리스트뷰 전환 및 필터/정렬/검색/페이지네이션', async ({ page }) => {
    await page.selectOption('#viewMode', 'card');
    await expect(page.locator('.card-view .template-card')).toHaveCountGreaterThan(0);
    await page.selectOption('#viewMode', 'list');
    await expect(page.locator('.template-list li')).toHaveCountGreaterThan(0);
    await page.selectOption('#filterStatus', 'active');
    await page.selectOption('#sortOption', 'name_asc');
    await page.fill('#filterCreator', 'admin');
    await page.fill('input[aria-label="템플릿 검색"]', '워크플로우');
    if (await page.locator('.pagination button').count() > 0) {
      await page.click('.pagination button:has-text(\'>\')');
    }
  });

  test('3. 템플릿 복제/공유/상태변경/버전/미리보기', async ({ page }) => {
    await page.click('.template-list li:has-text("워크플로우 자동화 템플릿") button:has-text("복제")');
    await page.click('.template-list li:has-text("워크플로우 자동화 템플릿") button:has-text("공유")');
    await page.fill('#userToShare', 'testuser');
    await page.selectOption('#sharePermission', 'edit');
    await page.click('button:has-text("공유하기")');
    await page.click('button:has-text("취소")');
    await page.click('.template-list li:has-text("워크플로우 자동화 템플릿") select');
    await page.selectOption('.template-list li:has-text("워크플로우 자동화 템플릿") select', 'archived');
    await page.click('.template-list li:has-text("워크플로우 자동화 템플릿")');
    await page.click('button:has-text("새 버전 만들기")');
    await page.on('dialog', dialog => dialog.accept());
    await page.click('button:has-text("미리보기")');
    await page.click('button:has-text("닫기")');
  });

  test('4. 오류/피드백/접근성/반응형', async ({ page }) => {
    // 네트워크 차단 등으로 오류 유발 후 error-message 노출 확인(수동 또는 mock)
    // 키보드 내비게이션(탭, 엔터 등)으로 주요 UI 접근 가능 여부
    await page.keyboard.press('Tab');
    await expect(page.locator(':focus-visible')).toBeVisible();
    // 반응형(브라우저 크기 조정)
    await page.setViewportSize({ width: 400, height: 800 });
    await expect(page.locator('.filter-bar')).toBeVisible();
    await expect(page.locator('.card-view, .template-list')).toBeVisible();
  });
});
