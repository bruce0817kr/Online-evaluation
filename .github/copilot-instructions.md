# 🤖 AI 코딩 핵심 가이드

## 🎯 기본 원칙

### TDD 기본 사이클
1. **RED**: 실패하는 테스트 작성
2. **GREEN**: 최소한의 코드로 테스트 통과
3. **REFACTOR**: 코드 개선 및 최적화

### Clean Architecture 핵심
- **단일 책임 원칙**: 한 클래스는 하나의 이유로만 변경
- **의존성 역전**: 추상화에 의존, 구체화에 의존하지 않음
- **인터페이스 분리**: 클라이언트별 전용 인터페이스

### 보안 우선순위
- **입력 검증**: 모든 사용자 입력 sanitization
- **출력 인코딩**: XSS 방지를 위한 데이터 인코딩
- **최소 권한**: 필요한 최소한의 권한만 부여
- **오류 처리**: 민감한 정보 노출 방지

### 코드 품질 기준
- **타입 안전성**: TypeScript strict 모드 활용
- **테스트 커버리지**: 90% 이상 유지
- **성능**: Lighthouse 점수 95+ 목표
- **가독성**: 자체 문서화되는 명확한 코드

---

## 🔧 MCP 도구 활용

### 필수 도구들
```bash
# 문서 동기화
Context7 → 최신 API 문서 실시간 확인

# 문제 해결
Sequential Thinking → 복잡한 문제 단계별 분해

# 작업 관리  
Task Manager → 작업 분할 및 진행 추적

# 개발 환경
GitHub → 버전 관리 및 협업
Desktop Commander → UI 자동화
```

### 워크플로우
1. **계획**: Task Manager로 작업 분할
2. **조사**: Context7로 최신 문서 확인  
3. **분석**: Sequential Thinking으로 문제 해결
4. **구현**: TDD 사이클 적용
5. **검증**: 자동화된 테스트 및 보안 검사

---

## ⚡ 빠른 체크리스트

### 코딩 시작 전
- [ ] Context7로 관련 API 문서 확인
- [ ] Task Manager에서 작업 정의
- [ ] 테스트 케이스 먼저 작성

### 코딩 중
- [ ] TypeScript strict 모드 활용
- [ ] 입력 검증 및 타입 체크
- [ ] 단위 테스트 지속적 실행

### 코딩 완료 후  
- [ ] 보안 취약점 점검
- [ ] 성능 최적화 검토
- [ ] 문서화 업데이트

---

## 🚀 성능 목표

- **빌드 시간**: < 30초
- **테스트 실행**: < 10초  
- **페이지 로드**: < 1.2초
- **Lighthouse 점수**: 95+

## 🔒 보안 체크포인트

- SQL Injection 방지 (매개변수화 쿼리)
- XSS 방지 (출력 인코딩)
- CSRF 방지 (토큰 검증)
- 인증/인가 검증