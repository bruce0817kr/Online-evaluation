# 🎯 온라인 평가 시스템 - 종합 테스트 자동화 가이드

## 📊 개요

이 문서는 온라인 평가 시스템의 종합적인 테스트 자동화 구현을 상세히 설명합니다. 네비게이션 향상, 중요 비즈니스 기능, 성능 및 접근성 테스트를 포함한 완전한 QA 프레임워크를 제공합니다.

## 🏗️ 테스트 아키텍처

### 테스트 계층 구조

```
tests/
├── e2e/                           # End-to-End 테스트
│   ├── navigation-enhancement.spec.js    # 네비게이션 시스템 테스트
│   ├── critical-functions.spec.js        # 핵심 비즈니스 기능 테스트
│   ├── auth.spec.js                      # 인증/권한 테스트
│   ├── system.spec.js                    # 시스템 통합 테스트
│   └── workflow.spec.js                  # 사용자 워크플로 테스트
├── performance/                   # 성능 테스트
│   └── lighthouse-audit.spec.js          # Lighthouse 성능 감사
├── integration/                   # 통합 테스트
├── frontend/src/components/__tests__/    # 단위 테스트
│   └── AIModelManagement.test.js        # 컴포넌트 단위 테스트
└── run_all_tests.py              # 통합 테스트 러너
```

## 🎭 E2E 테스트 시스템

### 1. 네비게이션 향상 테스트 (`navigation-enhancement.spec.js`)

**목적**: 개선된 네비게이션 시스템의 모든 측면을 검증

#### 테스트 범위:
- **모바일 반응형**: 다양한 뷰포트 크기에서 네비게이션 동작 확인
- **브레드크럼 탐색**: 계층적 네비게이션 경로 표시 검증
- **관리자 사이드 패널**: 관리 기능 접근성 및 권한 검증
- **도구 드롭다운**: 기능별 도구 접근성 확인
- **접근성 표준**: WCAG 2.1 AA 준수 확인
- **키보드 네비게이션**: 전체 키보드 접근성 지원
- **시각적 상태**: 호버, 활성, 포커스 상태 확인

#### 주요 기능:
```javascript
// 모바일 메뉴 토글 테스트
test('should toggle mobile menu correctly', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 667 });
  const mobileMenuButton = page.locator('[aria-label="메뉴 열기"]');
  await mobileMenuButton.click();
  await expect(mobileMenu).toHaveClass(/block/);
});

// 역할 기반 네비게이션 테스트
test('should show appropriate navigation for admin users', async ({ page }) => {
  await loginUser(page, TEST_CONFIG.users.admin);
  await expect(page.locator('button:has-text("⚙️ 관리자")')).toBeVisible();
});
```

### 2. 중요 비즈니스 기능 테스트 (`critical-functions.spec.js`)

**목적**: 보고된 11개 중요 이슈의 해결 상태 검증

#### 테스트된 이슈들:
1. **프로젝트 관리**: 프로젝트 생성 기능 정상 동작 확인
2. **평가관리**: 인증 자격 증명 검증 오류 해결 확인
3. **템플릿 관리**: 관리자 권한 인식 정상화 확인
4. **보안 파일 뷰어**: 파일 목록 로딩 문제 해결 확인
5. **평가표 출력 관리**: 권한 및 프로젝트 선택 반영 확인
6. **AI 도우미**: UI 대비 개선 및 설정 접근성 확인
7. **관리자 메뉴**: 전체 관리 기능 정상 동작 확인

#### 테스트 전략:
```javascript
// 향상된 로그인 재시도 로직
async function loginWithRetry(page, user, maxRetries = 3) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      // 속도 제한 우회를 위한 환경 설정
      await page.setExtraHTTPHeaders({
        'X-Test-Environment': 'true',
        'X-E2E-Test': 'critical-functions'
      });
      
      await page.fill('input[name="login_id"]', user.username);
      await page.fill('input[name="password"]', user.password);
      await page.click('button[type="submit"]');
      
      return true;
    } catch (error) {
      if (attempt < maxRetries) {
        await page.waitForTimeout(1000 * attempt); // 지수적 백오프
      }
    }
  }
}
```

## 🚀 성능 및 접근성 테스트

### Lighthouse 감사 시스템 (`lighthouse-audit.spec.js`)

**목적**: 웹 성능, 접근성, 모범 사례 자동 평가

#### 성능 목표:
- **성능**: ≥85점
- **접근성**: ≥95점
- **모범 사례**: ≥90점
- **SEO**: ≥80점

#### 테스트 범위:
```javascript
// 모바일 반응형 테스트
const mobileViewports = [
  { name: 'iPhone SE', width: 375, height: 667 },
  { name: 'iPhone 12', width: 390, height: 844 },
  { name: 'Samsung Galaxy S21', width: 360, height: 800 },
  { name: 'iPad Mini', width: 768, height: 1024 }
];

// 접근성 준수 검증
test('should meet WCAG 2.1 AA standards', async ({ page }) => {
  // 모든 이미지에 alt 텍스트 확인
  const images = await page.locator('img').count();
  for (let i = 0; i < images; i++) {
    const img = page.locator('img').nth(i);
    const alt = await img.getAttribute('alt');
    const ariaLabel = await img.getAttribute('aria-label');
    expect(alt || ariaLabel).toBeTruthy();
  }
});
```

## 🧪 단위 테스트 시스템

### React 컴포넌트 테스트

**예시**: `AIModelManagement.test.js`

#### 테스트 범위:
- **접근 제어**: 역할 기반 권한 검증
- **탭 네비게이션**: UI 상태 전환 확인
- **모델 관리**: CRUD 작업 기능성 확인
- **연결 테스트**: AI 모델 상태 확인 기능
- **오류 처리**: 예외 상황 대응 확인

#### 주요 테스트 패턴:
```javascript
// 접근 제어 테스트
test('renders access denied for evaluator users', () => {
  render(<AIModelManagement user={mockEvaluatorUser} />);
  expect(screen.getByText('🚫 접근 권한 없음')).toBeInTheDocument();
});

// 비동기 작업 테스트
test('creates new model successfully', async () => {
  const user = userEvent.setup();
  
  fetch.mockImplementationOnce(() => Promise.resolve({
    ok: true,
    json: () => Promise.resolve({ model: { model_id: 'new-model' } })
  }));
  
  await user.type(screen.getByLabelText('모델 ID *'), 'new-model');
  fireEvent.click(screen.getByText('모델 생성'));
  
  await waitFor(() => {
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/ai-models/create'),
      expect.objectContaining({ method: 'POST' })
    );
  });
});
```

## 🔄 통합 테스트 러너

### `run_all_tests.py` 기능

#### 지원 테스트 유형:
1. **백엔드 테스트**: Python pytest 기반
2. **프론트엔드 테스트**: Jest/React Testing Library
3. **통합 테스트**: API 엔드포인트 검증
4. **E2E 테스트**: Playwright 다중 브라우저
5. **성능 테스트**: Lighthouse 감사 포함
6. **보안 테스트**: 취약점 스캔

#### 향상된 기능:
```python
# 포괄적인 E2E 테스트 실행
e2e_suites = {
    'navigation': 'tests/e2e/navigation-enhancement.spec.js',
    'critical_functions': 'tests/e2e/critical-functions.spec.js',
    'auth': 'tests/e2e/auth.spec.js',
    'system': 'tests/e2e/system.spec.js',
    'workflow': 'tests/e2e/workflow.spec.js'
}

# 커버리지 분석 및 권장사항
def analyze_component_coverage(self, frontend_dir: str) -> Dict[str, Any]:
    # React 컴포넌트 테스트 커버리지 분석
    # 테스트되지 않은 컴포넌트 식별
    # 개선 권장사항 생성
```

## 📊 커버리지 분석

### 코드 커버리지 목표

| 메트릭 | 목표 | 현재 상태 | 권장사항 |
|--------|------|-----------|----------|
| 라인 커버리지 | ≥80% | 측정 중 | 단위 테스트 확장 |
| 함수 커버리지 | ≥80% | 측정 중 | 미사용 함수 정리 |
| 분기 커버리지 | ≥75% | 측정 중 | 조건부 로직 테스트 |
| 컴포넌트 커버리지 | ≥80% | ~5% | 컴포넌트 테스트 추가 |

### 컴포넌트 테스트 우선순위

#### 높은 우선순위:
1. **AIModelManagement** ✅ - 완료
2. **TemplateManagement** - 개발 필요
3. **EvaluationManagement** - 개발 필요
4. **ProjectManagement** - 개발 필요

#### 중간 우선순위:
5. **FileSecureViewer** - 개발 필요
6. **EvaluationPrintManager** - 개발 필요
7. **AIAssistant** - 개발 필요

## 🛠️ 실행 가이드

### 전체 테스트 실행
```bash
# 모든 테스트 스위트 실행
python tests/run_all_tests.py

# 특정 스위트만 실행
python tests/run_all_tests.py --suites e2e performance

# 크로스 브라우저 테스트
python tests/run_all_tests.py --browsers chromium firefox webkit
```

### 개별 테스트 실행
```bash
# 네비게이션 테스트
npx playwright test tests/e2e/navigation-enhancement.spec.js

# 중요 기능 테스트
npx playwright test tests/e2e/critical-functions.spec.js

# 성능 테스트
npx playwright test tests/performance/lighthouse-audit.spec.js

# 단위 테스트 (프론트엔드)
cd frontend && npm test
```

## 📈 성능 모니터링

### 지속적 성능 추적

#### 핵심 메트릭:
- **First Contentful Paint**: <1.5초
- **Largest Contentful Paint**: <2.5초
- **Cumulative Layout Shift**: <0.1
- **Time to Interactive**: <3.0초

#### 모니터링 전략:
```javascript
// 성능 메트릭 수집
const performanceMetrics = await page.evaluate(() => {
  return {
    domContentLoaded: performance.timing.domContentLoadedEventEnd - performance.timing.navigationStart,
    loadComplete: performance.timing.loadEventEnd - performance.timing.navigationStart,
    firstPaint: performance.getEntriesByType('paint')[0]?.startTime || 0
  };
});

// 성능 임계값 검증
expect(performanceMetrics.domContentLoaded).toBeLessThan(3000);
expect(performanceMetrics.loadComplete).toBeLessThan(5000);
```

## 🔒 보안 테스트

### 자동화된 보안 검사

#### 검사 항목:
1. **의존성 취약점**: npm audit, safety
2. **코드 보안**: bandit (Python), ESLint security
3. **헤더 보안**: HTTPS, CSP, HSTS 검증
4. **민감 정보 노출**: 하드코딩된 비밀번호/키 검사

#### 구현 예시:
```python
# 보안 도구 자동 실행
security_tools = [
    {
        'name': 'npm audit',
        'command': ['npm', 'audit', '--json'],
        'type': 'npm_security'
    },
    {
        'name': 'bandit',
        'command': ['python', '-m', 'bandit', '-r', 'backend/', '-f', 'json'],
        'type': 'python_security'
    }
]
```

## 📋 CI/CD 통합

### GitHub Actions 워크플로

```yaml
name: Comprehensive Test Suite
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run All Tests
        run: python tests/run_all_tests.py
      - name: Upload Test Reports
        uses: actions/upload-artifact@v2
        with:
          name: test-reports
          path: tests/reports/
```

## 🎯 품질 게이트

### 릴리스 기준

#### 필수 통과 기준:
- [ ] 모든 E2E 테스트 통과 (100%)
- [ ] 단위 테스트 커버리지 ≥80%
- [ ] 성능 점수 ≥85점
- [ ] 접근성 점수 ≥95점
- [ ] 보안 취약점 0개 (높음/치명적)

#### 권장 기준:
- [ ] 크로스 브라우저 호환성 확인
- [ ] 모바일 반응형 테스트 통과
- [ ] 로드 테스트 성능 기준 충족

## 🚀 향후 계획

### 단기 개선사항 (1-2주)
1. **컴포넌트 테스트 확장**: 나머지 20개 컴포넌트 테스트 추가
2. **시각적 회귀 테스트**: Percy/Chromatic 통합
3. **API 테스트 자동화**: Postman/Newman 스크립트

### 중기 개선사항 (1-2개월)
1. **성능 벤치마킹**: 지속적 성능 추적 대시보드
2. **접근성 자동화**: axe-core 통합 확장
3. **부하 테스트**: Artillery/K6 시나리오 개발

### 장기 계획 (3-6개월)
1. **AI 기반 테스트**: 자동 테스트 생성 및 유지보수
2. **클라우드 테스트**: AWS/Azure 기반 분산 테스트
3. **실시간 모니터링**: 프로덕션 환경 연속 품질 모니터링

## 📞 지원 및 문의

### 문제 해결
- **테스트 실패**: logs 디렉토리의 상세 로그 확인
- **성능 이슈**: Lighthouse 보고서의 권장사항 검토
- **접근성 문제**: axe-core 보고서의 개선사항 적용

### 기여 가이드
1. 새로운 기능에 대한 테스트 추가 필수
2. PR 전 전체 테스트 스위트 실행
3. 커버리지 감소 없이 변경사항 적용
4. 성능 영향 최소화 확인

---

**💡 참고**: 이 가이드는 온라인 평가 시스템의 품질 보증을 위한 종합적인 테스트 전략을 제공합니다. 지속적인 개선과 확장을 통해 시스템의 안정성과 사용자 경험을 향상시킬 수 있습니다.