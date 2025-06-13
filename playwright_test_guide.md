# Playwright UI 자동화 테스트 설정 및 실행 가이드

## 📦 필요한 패키지 설치

### Python 패키지 설치
```bash
pip install playwright pytest-playwright
```

### Playwright 브라우저 설치
```bash
playwright install
```

## 🧪 테스트 실행 방법

### 1. 기본 테스트 실행
```bash
python playwright_ui_automation_test.py
```

### 2. 헤드리스 모드로 실행 (백그라운드)
테스트 파일에서 `headless=True`로 변경 후 실행

### 3. 특정 브라우저로 테스트
- Chrome: chromium
- Firefox: firefox  
- Safari: webkit

## 📊 테스트 결과

### 생성되는 파일
- `playwright_ui_test_results_YYYYMMDD_HHMMSS.json` - 상세 테스트 결과
- `test_screenshots/` - 각 테스트 단계별 스크린샷

### 테스트 매트릭스
| 테스트 항목 | 관리자 | 간사 | 평가위원 |
|-------------|--------|------|----------|
| 로그인 | ✓ | ✓ | ✓ |
| 대시보드 | ✓ | ✓ | ✓ |
| 네비게이션 | ✓ | ✓ | X |
| 반응형 | ✓ | - | - |
| 로그아웃 | ✓ | ✓ | ✓ |

## 🔍 테스트 시나리오 상세

### 로그인 테스트
- 정상 로그인 (각 역할별)
- 잘못된 비밀번호 처리
- 로그아웃 기능

### UI/UX 테스트  
- 대시보드 요소 표시
- 네비게이션 탭 동작
- 반응형 디자인 (Desktop/Tablet/Mobile)

### 보안 테스트
- 역할별 접근 권한
- 잘못된 인증 정보 처리

## 🚨 주의사항

1. **시스템 상태 확인**
   - Docker 컨테이너가 모두 실행 중인지 확인
   - 프론트엔드(3000포트), 백엔드(8080포트) 정상 작동 확인

2. **테스트 환경**
   - 테스트용 데이터베이스 사용 권장
   - 프로덕션 환경에서는 실행 금지

3. **브라우저 호환성**
   - Chrome/Chromium 최신 버전 권장
   - 일부 기능은 브라우저별로 다를 수 있음
