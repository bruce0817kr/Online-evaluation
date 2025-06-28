# 🔒 AI 모델 관리 시스템 - 보안 테스트 스위트

이 디렉터리는 AI 모델 관리 시스템의 종합적인 보안 테스트를 위한 도구와 스크립트를 포함합니다.

## 📁 디렉터리 구조

```
security_tests/
├── python/
│   ├── security_test_runner.py      # 메인 보안 테스트 실행기
│   ├── authentication_tests.py      # 인증/권한 테스트 (포함됨)
│   ├── input_validation_tests.py    # 입력 검증 테스트 (포함됨)
│   ├── api_security_tests.py        # API 보안 테스트 (포함됨)
│   ├── data_security_tests.py       # 데이터 보안 테스트 (포함됨)
│   └── session_security_tests.py    # 세션 보안 테스트 (포함됨)
├── tools/
│   ├── vulnerability_scanner.py     # 취약점 스캐너
│   ├── penetration_test.py         # 침투 테스트 (계획됨)
│   └── security_audit.py           # 보안 감사 (계획됨)
├── config/
│   ├── security_test_config.yml    # 보안 테스트 설정
│   └── test_payloads.json          # 테스트 페이로드
├── reports/                        # 생성된 리포트 저장
├── run_security_tests.py          # 통합 실행 스크립트
└── README.md                      # 이 파일
```

## 🚀 빠른 시작

### 1. 의존성 설치

```bash
# 기본 의존성
pip install requests aiohttp beautifulsoup4 lxml
pip install pyyaml python-dotenv

# 보안 테스트 도구 (선택사항)
pip install bandit safety
pip install python-owasp-zap-v2.4  # OWASP ZAP Python API
```

### 2. 기본 실행

```bash
# 기본 보안 테스트 실행
python security_tests/run_security_tests.py

# 특정 URL 대상으로 테스트
python security_tests/run_security_tests.py \
  --target-url http://localhost:3000 \
  --api-url http://localhost:8000

# 강화된 테스트 모드
python security_tests/run_security_tests.py --test-mode aggressive
```

### 3. 개별 테스트 실행

```bash
# 동적 보안 테스트만 실행
python security_tests/python/security_test_runner.py

# 정적 취약점 스캔만 실행
python security_tests/tools/vulnerability_scanner.py
```

## 🧪 테스트 카테고리

### 1. 인증 및 권한 테스트
- **약한 비밀번호 정책 테스트**: 기본 비밀번호, 짧은 비밀번호 검증
- **브루트 포스 공격 방어**: 로그인 시도 제한 확인
- **JWT 토큰 보안**: 토큰 조작, 만료시간, 알고리즘 검증
- **권한 상승 공격**: IDOR, 권한 우회 시도
- **세션 고정**: 세션 ID 고정 공격 테스트

### 2. 입력 검증 테스트
- **NoSQL 인젝션**: MongoDB 인젝션 페이로드 테스트
- **XSS (Cross-Site Scripting)**: 반사형, 저장형, DOM 기반 XSS
- **파일 업로드 보안**: 악성 파일, 경로 탐색 공격
- **헤더 인젝션**: HTTP 헤더 조작 시도
- **입력 크기 제한**: 버퍼 오버플로우, DoS 공격

### 3. API 보안 테스트
- **REST API 보안**: 엔드포인트별 보안 검증
- **HTTP 메소드 조작**: OPTIONS, TRACE 등 메소드 확인
- **Rate Limiting**: API 호출 제한 확인
- **CORS 설정**: 크로스 오리진 정책 검증
- **API 키 보안**: 인증 토큰 관리 검증

### 4. 세션 보안 테스트
- **세션 관리**: 세션 생성, 소멸, 타임아웃
- **CSRF 방어**: 크로스 사이트 요청 위조 방지
- **쿠키 보안**: HttpOnly, Secure, SameSite 속성
- **동시 세션**: 다중 로그인 관리
- **세션 하이재킹**: 세션 토큰 탈취 방지

### 5. 데이터 보안 테스트
- **민감 정보 노출**: API 키, 비밀번호, 토큰 하드코딩
- **데이터 암호화**: 저장 및 전송 중 암호화
- **로그 보안**: 로그 파일 내 민감 정보 확인
- **백업 보안**: 백업 파일 보안 검증
- **메모리 덤프**: 메모리 내 민감 정보 확인

### 6. SSL/TLS 보안 테스트
- **인증서 검증**: SSL 인증서 유효성 확인
- **암호화 강도**: 사용 중인 암호화 알고리즘 검증
- **프로토콜 버전**: 지원하는 TLS 버전 확인
- **보안 헤더**: HSTS, CSP 등 보안 헤더 확인

## ⚙️ 설정

### security_test_config.yml
테스트 설정을 커스터마이징할 수 있습니다:

```yaml
# 테스트 대상
target:
  frontend_url: "http://localhost:3000"
  backend_url: "http://localhost:8000"

# 테스트 모드
test_mode: "safe"  # safe, aggressive

# 테스트 사용자 계정
test_users:
  admin:
    email: "admin@test.com"
    password: "testpass123"
    role: "admin"
```

### 환경 변수
`.env.security` 파일을 생성하여 환경별 설정을 관리할 수 있습니다:

```bash
# 테스트 대상 URL
SECURITY_TEST_TARGET=http://localhost:3000
SECURITY_TEST_API=http://localhost:8000

# 테스트 모드
SECURITY_TEST_MODE=safe

# 테스트 계정 정보
TEST_ADMIN_EMAIL=admin@test.com
TEST_ADMIN_PASSWORD=testpass123
```

## 📊 리포트

테스트 완료 후 다음과 같은 형태의 리포트가 생성됩니다:

### 1. JSON 리포트
- 구조화된 데이터 형태
- 자동화 도구와 연동 가능
- 상세한 테스트 결과 포함

### 2. HTML 리포트
- 시각적으로 보기 좋은 형태
- 그래프와 차트 포함
- 웹 브라우저에서 바로 확인 가능

### 3. 텍스트 리포트
- 콘솔 출력 및 로그 파일
- CI/CD 파이프라인에서 활용
- 간단한 요약 정보 제공

## 🔧 고급 사용법

### 1. 커스텀 페이로드 추가
`config/test_payloads.json`에 새로운 공격 페이로드를 추가할 수 있습니다:

```json
{
  "custom_injection": [
    "'; DROP TABLE users; --",
    "' OR '1'='1",
    "admin'/**/OR/**/1=1--"
  ]
}
```

### 2. 새로운 테스트 카테고리 추가
새로운 보안 테스트를 `security_test_runner.py`에 추가할 수 있습니다:

```python
async def test_custom_security(self):
    """커스텀 보안 테스트"""
    # 테스트 로직 구현
    pass
```

### 3. CI/CD 통합
GitHub Actions, Jenkins 등 CI/CD 파이프라인에 통합:

```yaml
- name: Security Test
  run: |
    python security_tests/run_security_tests.py
    # 테스트 결과에 따른 빌드 중단 로직
```

## 🚨 주의사항

### 1. 테스트 환경
- **프로덕션 환경에서 절대 실행하지 마세요**
- 테스트 전용 환경에서만 사용
- 테스트 데이터와 실제 데이터 분리

### 2. 법적 고려사항
- 본인 소유의 시스템에서만 테스트
- 침투 테스트 전 적절한 승인 필요
- 관련 법규 및 정책 준수

### 3. 리소스 사용
- aggressive 모드는 시스템 부하 증가
- 네트워크 대역폭 사용량 고려
- 테스트 시간과 리소스 계획

## 🔍 문제 해결

### 일반적인 오류

1. **연결 오류**
   ```
   해결: 대상 시스템이 실행 중인지 확인
   ```

2. **권한 오류**
   ```
   해결: 테스트 계정 권한 확인
   ```

3. **타임아웃 오류**
   ```
   해결: 네트워크 상태 및 시스템 부하 확인
   ```

### 로그 확인
```bash
# 상세 로그 확인
tail -f security_test_*.log

# 에러 로그만 확인
grep ERROR security_test_*.log
```

## 📚 참고 자료

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [CWE - Common Weakness Enumeration](https://cwe.mitre.org/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

## 🤝 기여

보안 테스트 개선에 기여하려면:

1. 새로운 테스트 케이스 제안
2. 버그 리포트 제출
3. 문서 개선 제안
4. 코드 리뷰 참여

---

**⚠️ 중요**: 이 도구는 보안 테스트 목적으로만 사용하며, 악의적인 목적으로 사용해서는 안 됩니다.