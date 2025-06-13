# Test info

- Name: 템플릿 관리 워크플로우 E2E >> 1. 템플릿 생성 → 상세 → 수정 → 항목 드래그앤드롭 → 저장
- Location: C:\Project\Online-evaluation\frontend\tests_e2e\template_management_workflow.spec.js:28:3

# Error details

```
Error: page.click: Target page, context or browser has been closed
Call log:
  - waiting for locator('text=평가 템플릿 관리')

    at C:\Project\Online-evaluation\frontend\tests_e2e\template_management_workflow.spec.js:25:16
```

# Test source

```ts
   1 | // 템플릿 관리 워크플로우 기반 E2E 자동화 테스트 (Playwright)
   2 | // 실행: npx playwright test tests_e2e/template_management_workflow.spec.js
   3 |
   4 | import { test, expect } from '@playwright/test';
   5 |
   6 | test.describe('템플릿 관리 워크플로우 E2E', () => {
   7 |   test.beforeEach(async ({ page }) => {
   8 |     // 로그인 페이지로 이동
   9 |     await page.goto('http://localhost:3000');
  10 |     
  11 |     // 로그인이 필요한지 확인 (로그인 화면이 표시되는지)
  12 |     const loginForm = await page.locator('form').count();
  13 |     if (loginForm > 0) {
  14 |       // 테스트 계정으로 로그인 (관리자 계정 사용)
  15 |       await page.fill('input[type="text"]', 'admin');
  16 |       await page.fill('input[type="password"]', 'admin123');
  17 |       await page.click('button[type="submit"]');
  18 |       
  19 |       // 로그인 완료 대기 (대시보드 로딩 대기)
  20 |       await page.waitForURL('http://localhost:3000', { timeout: 10000 });
  21 |       await page.waitForLoadState('networkidle');
  22 |     }
  23 |     
  24 |     // 템플릿 관리 메뉴 클릭
> 25 |     await page.click('text=평가 템플릿 관리');
     |                ^ Error: page.click: Target page, context or browser has been closed
  26 |   });
  27 |
  28 |   test('1. 템플릿 생성 → 상세 → 수정 → 항목 드래그앤드롭 → 저장', async ({ page }) => {
  29 |     await page.click('button:has-text("새 템플릿 생성")');
  30 |     await page.fill('#templateName', '워크플로우 자동화 템플릿');
  31 |     await page.fill('#templateDescription', '자동화 워크플로우용 템플릿');
  32 |     await page.click('button:has-text("생성")');
  33 |     await expect(page.locator('.template-list li')).toContainText('워크플로우 자동화 템플릿');
  34 |     await page.click('.template-list li:has-text("워크플로우 자동화 템플릿")');
  35 |     await page.click('button:has-text("수정")');
  36 |     // 항목 드래그앤드롭 (첫 번째와 두 번째 항목 순서 변경)
  37 |     const dragHandle = page.locator('.item-input-row span[style*="cursor:grab"]').first();
  38 |     const targetRow = page.locator('.item-input-row').nth(1);
  39 |     await dragHandle.dragTo(targetRow);
  40 |     await page.click('button:has-text("저장")');
  41 |     await expect(page.locator('.template-list li')).toContainText('워크플로우 자동화 템플릿');
  42 |   });
  43 |
  44 |   test('2. 카드뷰/리스트뷰 전환 및 필터/정렬/검색/페이지네이션', async ({ page }) => {
  45 |     await page.selectOption('#viewMode', 'card');
  46 |     await expect(page.locator('.card-view .template-card')).toHaveCountGreaterThan(0);
  47 |     await page.selectOption('#viewMode', 'list');
  48 |     await expect(page.locator('.template-list li')).toHaveCountGreaterThan(0);
  49 |     await page.selectOption('#filterStatus', 'active');
  50 |     await page.selectOption('#sortOption', 'name_asc');
  51 |     await page.fill('#filterCreator', 'admin');
  52 |     await page.fill('input[aria-label="템플릿 검색"]', '워크플로우');
  53 |     if (await page.locator('.pagination button').count() > 0) {
  54 |       await page.click('.pagination button:has-text(\'>\')');
  55 |     }
  56 |   });
  57 |
  58 |   test('3. 템플릿 복제/공유/상태변경/버전/미리보기', async ({ page }) => {
  59 |     await page.click('.template-list li:has-text("워크플로우 자동화 템플릿") button:has-text("복제")');
  60 |     await page.click('.template-list li:has-text("워크플로우 자동화 템플릿") button:has-text("공유")');
  61 |     await page.fill('#userToShare', 'testuser');
  62 |     await page.selectOption('#sharePermission', 'edit');
  63 |     await page.click('button:has-text("공유하기")');
  64 |     await page.click('button:has-text("취소")');
  65 |     await page.click('.template-list li:has-text("워크플로우 자동화 템플릿") select');
  66 |     await page.selectOption('.template-list li:has-text("워크플로우 자동화 템플릿") select', 'archived');
  67 |     await page.click('.template-list li:has-text("워크플로우 자동화 템플릿")');
  68 |     await page.click('button:has-text("새 버전 만들기")');
  69 |     await page.on('dialog', dialog => dialog.accept());
  70 |     await page.click('button:has-text("미리보기")');
  71 |     await page.click('button:has-text("닫기")');
  72 |   });
  73 |
  74 |   test('4. 오류/피드백/접근성/반응형', async ({ page }) => {
  75 |     // 네트워크 차단 등으로 오류 유발 후 error-message 노출 확인(수동 또는 mock)
  76 |     // 키보드 내비게이션(탭, 엔터 등)으로 주요 UI 접근 가능 여부
  77 |     await page.keyboard.press('Tab');
  78 |     await expect(page.locator(':focus-visible')).toBeVisible();
  79 |     // 반응형(브라우저 크기 조정)
  80 |     await page.setViewportSize({ width: 400, height: 800 });
  81 |     await expect(page.locator('.filter-bar')).toBeVisible();
  82 |     await expect(page.locator('.card-view, .template-list')).toBeVisible();
  83 |   });
  84 | });
  85 |
```