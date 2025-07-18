# ❓ AI 모델 관리 시스템 - FAQ 및 문제해결 가이드

## 📚 목차

1. [자주 묻는 질문 (FAQ)](#자주-묻는-질문-faq)
2. [문제 해결 가이드](#문제-해결-가이드)
3. [에러 코드 및 해결 방법](#에러-코드-및-해결-방법)
4. [성능 문제 해결](#성능-문제-해결)
5. [보안 관련 문제](#보안-관련-문제)
6. [시스템 복구 절차](#시스템-복구-절차)
7. [고급 문제 해결](#고급-문제-해결)
8. [지원 요청 가이드](#지원-요청-가이드)

---

## ❓ 자주 묻는 질문 (FAQ)

### 🔧 기본 사용 관련

#### Q1: AI 모델 관리 시스템에 접근할 수 없어요
**A:** 다음 사항을 확인해 주세요:
```
1. 사용자 권한 확인
   - 관리자 또는 간사 권한이 있는지 확인
   - 평가위원은 접근할 수 없습니다

2. 로그인 상태 확인
   - 로그아웃 후 다시 로그인
   - 브라우저 쿠키/캐시 삭제

3. 네트워크 연결 확인
   - 인터넷 연결 상태 점검
   - VPN 사용 시 설정 확인
```

#### Q2: 새 모델을 생성했는데 목록에 나타나지 않아요
**A:** 다음을 시도해 보세요:
```
✅ 즉시 해결책:
1. 페이지 새로고침 (F5 또는 Ctrl+R)
2. "🔄 새로고침" 버튼 클릭
3. 브라우저 캐시 삭제

🔍 원인 확인:
1. 모델 생성 성공 메시지 확인
2. 네트워크 연결 상태 점검
3. 콘솔 오류 메시지 확인
```

#### Q3: 모델 삭제가 안 돼요
**A:** 다음 경우에 삭제가 제한됩니다:
```
🚫 삭제 불가 상황:
- 기본 시스템 모델 (openai-gpt35-turbo 등)
- 현재 사용 중인 모델
- 평가 프로젝트에 연결된 모델

✅ 해결 방법:
1. 기본 모델이 아닌지 확인
2. 연결된 프로젝트 해제 후 삭제
3. 관리자 권한으로 강제 삭제
```

#### Q4: 템플릿이 작동하지 않아요
**A:** 템플릿 문제 해결 방법:
```
🔧 단계별 확인:
1. 템플릿 목록 새로고침
2. 다른 템플릿으로 테스트
3. 직접 모델 생성으로 대체

🛠️ 고급 해결:
1. 브라우저 개발자 도구 확인
2. API 응답 상태 점검
3. 관리자에게 문의
```

### 🧪 연결 테스트 관련

#### Q5: 모든 연결 테스트가 실패해요
**A:** 시스템 차원의 문제일 가능성이 높습니다:
```
🚨 긴급 점검:
1. 인터넷 연결 상태 확인
2. 방화벽 설정 점검
3. API 서비스 상태 확인

📞 즉시 조치:
1. 시스템 관리자에게 연락
2. 모든 AI 기능 일시 중단
3. 수동 평가 모드로 전환
```

#### Q6: 특정 모델만 연결 테스트가 실패해요
**A:** 모델별 문제 해결:
```
🔍 단계별 진단:
1. 해당 모델의 API 키 확인
2. 엔드포인트 URL 검증
3. 모델명 정확성 점검

🛠️ 수정 방법:
1. 모델 설정 수정
2. API 키 재발급
3. 다른 유사 모델로 대체
```

#### Q7: 연결은 되는데 응답이 너무 느려요
**A:** 성능 최적화가 필요합니다:
```
⚡ 즉시 개선:
1. 더 빠른 모델로 교체
2. 요청 크기 줄이기
3. 동시 요청 수 제한

📊 근본적 해결:
1. 모델 성능 분석
2. 네트워크 품질 점검
3. 서버 리소스 모니터링
```

### 💰 비용 및 사용량 관련

#### Q8: 비용이 예상보다 많이 나와요
**A:** 비용 급증 원인 분석:
```
📊 사용량 분석:
1. 성능 메트릭에서 토큰 사용량 확인
2. 최근 1주일간 사용 패턴 분석
3. 고비용 모델 사용 빈도 점검

💡 비용 절약:
1. 경제적 모델로 전환
2. 사용량 제한 설정
3. 예산 알림 활성화
```

#### Q9: 성능 통계가 정확하지 않은 것 같아요
**A:** 데이터 정확성 확보:
```
🔄 데이터 새로고침:
1. 통계 캐시 초기화
2. 24시간 후 재확인
3. 다른 기간으로 조회

📋 정확성 검증:
1. 수동 계산과 비교
2. 외부 모니터링 도구 활용
3. 관리자에게 검증 요청
```

### 🔒 권한 및 보안 관련

#### Q10: 권한이 있는데도 기능이 제한돼요
**A:** 권한 관련 문제 해결:
```
🔐 권한 재확인:
1. 현재 로그인 사용자 확인
2. 역할(admin/secretary) 점검
3. 세션 만료 여부 확인

🔄 권한 갱신:
1. 로그아웃 후 재로그인
2. 관리자에게 권한 재설정 요청
3. 브라우저 보안 설정 점검
```

---

## 🛠️ 문제 해결 가이드

### 🔴 심각도별 문제 분류

#### 🚨 긴급 (Critical)
**즉시 대응 필요한 문제들**
```
💥 시스템 전체 장애:
- 모든 AI 모델 접근 불가
- API 서버 응답 없음
- 데이터베이스 연결 실패

📞 대응 방법:
1. 즉시 관리자 팀 소집
2. 백업 시스템 활성화
3. 사용자 공지 발송
4. 수동 운영 모드 전환
```

#### 🟡 높음 (High)
**24시간 내 해결 필요**
```
⚠️ 부분적 장애:
- 특정 모델 그룹 오류
- 성능 현저한 저하
- 보안 경고 발생

🔧 대응 방법:
1. 영향받는 기능 일시 중단
2. 대체 모델로 전환
3. 근본 원인 분석
4. 48시간 내 완전 복구
```

#### 🟢 보통 (Medium)
**1주일 내 해결**
```
📊 기능적 문제:
- 사용자 인터페이스 버그
- 통계 데이터 오류
- 작은 성능 이슈

✅ 대응 방법:
1. 임시 해결책 적용
2. 다음 업데이트에 수정 반영
3. 사용자 가이드 제공
```

### 📋 단계별 문제 해결 프로세스

#### 1단계: 문제 식별 및 분류
```
🔍 정보 수집:
1. 에러 메시지 전체 내용 기록
2. 발생 시점 및 빈도 파악
3. 영향받는 사용자 범위 확인
4. 재현 가능 여부 테스트

📊 분류 기준:
- 영향 범위: 개별/그룹/전체
- 심각도: 낮음/보통/높음/긴급
- 긴급성: 즉시/24시간/1주일
```

#### 2단계: 초기 대응
```
⚡ 즉시 조치:
1. 영향받는 기능 격리
2. 사용자 알림 발송
3. 대체 방안 제시
4. 로그 및 증거 수집

🛡️ 피해 최소화:
1. 추가 확산 방지
2. 데이터 손실 방지
3. 사용자 불편 최소화
```

#### 3단계: 근본 원인 분석
```
🔍 심층 분석:
1. 로그 파일 상세 검토
2. 시스템 메트릭 분석
3. 코드 변경사항 확인
4. 외부 의존성 점검

📋 문서화:
1. 문제 발생 타임라인
2. 분석 과정 및 결과
3. 시도한 해결책들
4. 최종 원인 확정
```

#### 4단계: 해결책 적용
```
🔧 해결 과정:
1. 테스트 환경에서 검증
2. 단계적 프로덕션 적용
3. 모니터링 강화
4. 부작용 점검

✅ 검증 절차:
1. 기능 정상 작동 확인
2. 성능 지표 점검
3. 사용자 피드백 수집
4. 완전 복구 선언
```

#### 5단계: 사후 관리
```
📚 학습 및 개선:
1. 사후 분석 보고서 작성
2. 재발 방지 대책 수립
3. 모니터링 시스템 보완
4. 팀 지식 공유

🔄 프로세스 개선:
1. 대응 절차 업데이트
2. 도구 및 시스템 보완
3. 교육 자료 갱신
4. 예방 점검 강화
```

---

## 🚨 에러 코드 및 해결 방법

### HTTP 상태 코드

#### 4xx 클라이언트 오류

**400 Bad Request**
```
🔍 의미: 잘못된 요청 형식
📋 일반적 원인:
- 필수 필드 누락
- 잘못된 데이터 형식
- 유효하지 않은 JSON

✅ 해결 방법:
1. 입력 데이터 형식 확인
2. 필수 필드 모두 입력
3. 브라우저 개발자 도구로 요청 검증
4. API 문서와 대조
```

**401 Unauthorized**
```
🔍 의미: 인증 실패
📋 일반적 원인:
- 로그인하지 않음
- 세션 만료
- 잘못된 토큰

✅ 해결 방법:
1. 다시 로그인
2. 브라우저 쿠키 삭제
3. 새 브라우저 창으로 접속
4. 관리자에게 계정 상태 확인 요청
```

**403 Forbidden**
```
🔍 의미: 권한 부족
📋 일반적 원인:
- 평가위원이 관리 기능 접근
- 간사가 수정/삭제 시도
- 권한 설정 오류

✅ 해결 방법:
1. 사용자 역할 확인
2. 관리자에게 권한 부여 요청
3. 허용된 기능만 사용
4. 관리자 계정으로 로그인
```

**404 Not Found**
```
🔍 의미: 요청한 리소스를 찾을 수 없음
📋 일반적 원인:
- 삭제된 모델에 접근
- 잘못된 URL
- 서버 라우팅 오류

✅ 해결 방법:
1. 모델 목록 새로고침
2. 올바른 모델 ID 확인
3. 브라우저 주소창 확인
4. 관리자에게 시스템 상태 문의
```

**429 Too Many Requests**
```
🔍 의미: 요청 한도 초과
📋 일반적 원인:
- API 호출 한도 초과
- 너무 빠른 연속 요청
- DDoS 방어 활성화

✅ 해결 방법:
1. 잠시 대기 후 재시도
2. 요청 빈도 줄이기
3. 배치 작업 나누어 처리
4. 관리자에게 한도 증가 요청
```

#### 5xx 서버 오류

**500 Internal Server Error**
```
🔍 의미: 서버 내부 오류
📋 일반적 원인:
- 데이터베이스 연결 실패
- API 키 오류
- 코드 버그

✅ 해결 방법:
1. 페이지 새로고침 시도
2. 잠시 후 재시도
3. 관리자에게 즉시 보고
4. 서버 로그 확인 요청
```

**502 Bad Gateway**
```
🔍 의미: 게이트웨이 오류
📋 일반적 원인:
- 백엔드 서버 다운
- 네트워크 연결 문제
- 로드 밸런서 오류

✅ 해결 방법:
1. 5분 후 재시도
2. 관리자에게 서버 상태 확인 요청
3. 다른 네트워크로 접속 시도
4. 시스템 상태 페이지 확인
```

**503 Service Unavailable**
```
🔍 의미: 서비스 일시 중단
📋 일반적 원인:
- 서버 점검 중
- 과부하 상태
- 계획된 유지보수

✅ 해결 방법:
1. 공지사항 확인
2. 점검 완료까지 대기
3. 대체 작업 방식 사용
4. 긴급 시 관리자 연락
```

### AI 모델 관련 에러

**CONNECTION_FAILED**
```
🔍 의미: AI 모델 연결 실패
📋 가능한 원인:
- API 키 만료/오류
- 네트워크 연결 문제
- AI 서비스 장애

✅ 해결 방법:
1. 다른 모델로 테스트
2. 연결 테스트 재실행
3. API 키 유효성 확인
4. AI 서비스 상태 페이지 확인
```

**QUOTA_EXCEEDED**
```
🔍 의미: 사용 한도 초과
📋 가능한 원인:
- 월간 토큰 한도 초과
- 분당 요청 한도 초과
- 계정 잔액 부족

✅ 해결 방법:
1. 사용량 현황 확인
2. 다음 주기까지 대기
3. 경제적 모델로 전환
4. 예산 증액 검토
```

**MODEL_DEPRECATED**
```
🔍 의미: 모델 사용 중단
📋 가능한 원인:
- AI 제공업체 모델 중단
- 버전 업데이트
- 서비스 정책 변경

✅ 해결 방법:
1. 최신 모델로 업그레이드
2. 유사한 대체 모델 찾기
3. 제공업체 공지 확인
4. 모델 설정 업데이트
```

**INVALID_API_KEY**
```
🔍 의미: 잘못된 API 키
📋 가능한 원인:
- API 키 입력 오류
- 키 만료
- 계정 비활성화

✅ 해결 방법:
1. API 키 재입력
2. 새 키 발급
3. 계정 상태 확인
4. 제공업체 설정 점검
```

---

## 🚀 성능 문제 해결

### 응답 시간 최적화

#### 느린 응답 시간 해결
```
⚡ 즉시 개선 방법:
1. 더 빠른 모델 사용
   - GPT-3.5 Turbo 선택
   - 로컬 모델 활용
   - 캐시된 응답 사용

2. 요청 최적화
   - 프롬프트 길이 단축
   - 불필요한 매개변수 제거
   - 동시 요청 수 제한

3. 네트워크 최적화
   - 지역별 최적 엔드포인트 사용
   - CDN 활용
   - 압축 기능 활성화
```

#### 성능 모니터링 설정
```
📊 모니터링 지표:
- 평균 응답 시간: 2초 이하 목표
- 95 퍼센타일: 5초 이하 유지
- 타임아웃율: 1% 이하
- 처리량: 분당 요청 수

🔔 알림 설정:
- 응답 시간 > 3초: 경고
- 응답 시간 > 5초: 위험
- 타임아웃율 > 2%: 긴급
- 오류율 > 5%: 즉시 대응
```

### 메모리 및 리소스 최적화

#### 메모리 사용량 관리
```
🧹 메모리 정리:
1. 브라우저 캐시 정기 삭제
2. 사용하지 않는 탭 닫기
3. 큰 데이터 조회 시 페이지네이션 사용
4. 정기적인 브라우저 재시작

📊 서버 리소스:
1. 데이터베이스 연결 풀 최적화
2. 캐시 메모리 적절한 크기 설정
3. 가비지 컬렉션 튜닝
4. 로그 파일 정기 정리
```

#### 데이터베이스 성능 튜닝
```
🗄️ 쿼리 최적화:
1. 인덱스 적절히 설정
2. 불필요한 JOIN 제거
3. 쿼리 결과 캐싱
4. 배치 처리 활용

🔍 성능 분석:
1. 느린 쿼리 로그 분석
2. 실행 계획 검토
3. 통계 정보 업데이트
4. 정기적인 성능 점검
```

---

## 🔒 보안 관련 문제

### 인증 및 권한 문제

#### 로그인 실패 해결
```
🔐 일반적인 로그인 문제:
1. 비밀번호 오류
   - 대소문자 구분 확인
   - 특수문자 정확히 입력
   - Caps Lock 상태 확인

2. 계정 잠김
   - 5회 실패 시 자동 잠김
   - 15분 후 자동 해제
   - 관리자에게 즉시 해제 요청

3. 세션 문제
   - 브라우저 쿠키 삭제
   - 시크릿 모드로 접속
   - 다른 브라우저 사용
```

#### 권한 관련 오류
```
👥 권한 계층:
- 관리자(Admin): 모든 기능 접근
- 간사(Secretary): 조회 및 테스트만
- 평가위원(Evaluator): 접근 불가

🔧 권한 문제 해결:
1. 현재 사용자 역할 확인
2. 필요한 권한 수준 파악
3. 관리자에게 권한 상향 요청
4. 임시 관리자 계정 사용
```

### API 보안 문제

#### API 키 관리
```
🔑 API 키 보안:
1. 키 노출 방지
   - 소스 코드에 하드코딩 금지
   - 로그 파일에 기록 방지
   - 버전 관리 시스템 제외

2. 키 순환 관리
   - 3개월마다 키 교체
   - 구 키 비활성화 전 테스트
   - 모든 시스템에 동시 적용

3. 키 오류 대응
   - 즉시 새 키 발급
   - 모든 설정 동시 업데이트
   - 연결 테스트로 검증
```

#### 네트워크 보안
```
🛡️ 네트워크 보호:
1. HTTPS 강제 사용
2. API 요청 암호화
3. 방화벽 규칙 적용
4. VPN 접근 제한

🔍 보안 모니터링:
1. 비정상 접근 패턴 감지
2. 실패한 인증 시도 추적
3. API 호출 패턴 분석
4. 의심스러운 활동 알림
```

---

## 🆘 시스템 복구 절차

### 긴급 상황 대응

#### 전체 시스템 장애
```
🚨 즉시 조치 (5분 내):
1. 장애 공지 발송
   - 모든 사용자에게 알림
   - 예상 복구 시간 안내
   - 대체 방안 제시

2. 백업 시스템 활성화
   - 읽기 전용 모드 전환
   - 중요 데이터 보호
   - 최소 기능 유지

3. 기술팀 소집
   - 관리자 및 개발자 연락
   - 긴급 대응 팀 구성
   - 복구 작업 시작
```

#### 단계별 복구 프로세스
```
🔧 복구 1단계 (30분 내):
1. 문제 원인 식별
2. 임시 해결책 적용
3. 핵심 기능 복구
4. 기본 서비스 재개

🔧 복구 2단계 (2시간 내):
1. 전체 기능 복구
2. 데이터 무결성 검증
3. 성능 테스트 수행
4. 안정성 확인

🔧 복구 3단계 (24시간 내):
1. 근본 원인 분석
2. 재발 방지 대책 수립
3. 모니터링 강화
4. 사후 분석 보고서 작성
```

### 데이터 복구

#### 데이터 손실 대응
```
💾 데이터 보호:
1. 즉시 백업 중단
   - 추가 손상 방지
   - 현재 상태 보존
   - 복구 지점 확보

2. 백업에서 복원
   - 최신 백업 확인
   - 단계적 복원 수행
   - 데이터 무결성 검증

3. 수동 복구 작업
   - 로그 파일 분석
   - 부분 데이터 복구
   - 사용자 재입력 요청
```

#### 설정 복원
```
⚙️ 시스템 설정:
1. 모델 설정 백업에서 복원
2. API 키 재설정
3. 성능 임계값 복구
4. 사용자 권한 재적용

🔄 서비스 재시작:
1. 순차적 서비스 재시작
2. 의존성 순서 고려
3. 건강 상태 점검
4. 사용자 접근 허용
```

---

## 🎓 고급 문제 해결

### 로그 분석 및 디버깅

#### 로그 파일 분석
```
📋 주요 로그 위치:
- 백엔드: /logs/app.log, /logs/error.log
- 프론트엔드: 브라우저 개발자 도구
- 데이터베이스: MongoDB 로그
- 웹서버: Nginx 액세스/에러 로그

🔍 로그 분석 기법:
1. 타임스탬프 기준 문제 구간 확인
2. 에러 메시지 패턴 분석
3. 요청/응답 추적
4. 성능 병목 구간 식별
```

#### 개발자 도구 활용
```
🛠️ 브라우저 디버깅:
1. Network 탭:
   - API 요청/응답 확인
   - 상태 코드 점검
   - 응답 시간 측정

2. Console 탭:
   - JavaScript 에러 확인
   - 로그 메시지 검토
   - 직접 명령 실행

3. Application 탭:
   - 로컬 스토리지 점검
   - 쿠키 상태 확인
   - 캐시 데이터 검토
```

### 성능 프로파일링

#### 병목 구간 식별
```
📊 성능 분석 도구:
1. 백엔드 프로파일링:
   - API 응답 시간 측정
   - 데이터베이스 쿼리 분석
   - 메모리 사용량 추적

2. 프론트엔드 분석:
   - 렌더링 시간 측정
   - 리소스 로딩 시간
   - JavaScript 실행 시간

3. 네트워크 분석:
   - 대역폭 사용량
   - 지연 시간 측정
   - 패킷 손실률 확인
```

### 확장성 문제

#### 사용자 증가 대응
```
📈 확장성 계획:
1. 수직 확장 (Scale Up):
   - 서버 사양 업그레이드
   - 메모리/CPU 증설
   - 스토리지 확대

2. 수평 확장 (Scale Out):
   - 로드 밸런서 구성
   - 다중 서버 배포
   - 데이터베이스 샤딩

3. 캐싱 전략:
   - Redis 클러스터 구성
   - CDN 활용
   - 브라우저 캐싱 최적화
```

---

## 📞 지원 요청 가이드

### 효과적인 문제 보고

#### 보고서 작성 템플릿
```
📋 문제 보고 양식:

제목: [긴급도] 간단한 문제 설명

1. 문제 상황:
   - 발생 시간: YYYY-MM-DD HH:MM
   - 영향 범위: 개인/팀/전체
   - 재현 가능 여부: 예/아니오

2. 구체적 증상:
   - 에러 메시지 전체 내용
   - 스크린샷 첨부
   - 관련 파일이나 데이터

3. 시도한 해결책:
   - 수행한 단계들
   - 결과 및 변화사항
   - 추가로 시도할 수 있는 방법

4. 시스템 환경:
   - 브라우저 및 버전
   - 운영체제
   - 네트워크 환경

5. 기대하는 결과:
   - 원하는 동작 설명
   - 긴급성 및 우선순위
   - 대체 방안 필요 여부
```

#### 심각도 분류 가이드
```
🚨 긴급 (4시간 내 응답):
- 시스템 전체 중단
- 보안 사고 발생
- 데이터 손실 위험
- 비즈니스 중단

🔴 높음 (24시간 내 응답):
- 주요 기능 장애
- 다수 사용자 영향
- 성능 심각한 저하
- 중요 기능 오류

🟡 보통 (72시간 내 응답):
- 부분적 기능 문제
- 소수 사용자 영향
- 성능 약간 저하
- 사용성 개선 필요

🟢 낮음 (1주일 내 응답):
- 기능 개선 요청
- 사용자 편의성
- 문서 수정 요청
- 교육 자료 필요
```

### 지원 채널

#### 연락처 정보
```
📞 지원 연락처:

🆘 긴급 상황 (24시간):
- 핫라인: [긴급 전화번호]
- 이메일: emergency@company.com
- 메신저: [긴급 대응팀 채널]

📋 일반 문의:
- 헬프데스크: help@company.com
- 내선번호: [기술지원팀 번호]
- 온라인 티켓: [지원 포털 URL]

📚 자가 해결:
- 사용자 가이드: [문서 링크]
- FAQ: [FAQ 페이지 링크]
- 동영상 튜토리얼: [비디오 링크]
```

#### 지원 요청 시 주의사항
```
✅ 효과적인 지원 요청:
1. 구체적이고 명확한 설명
2. 관련 파일 및 스크린샷 첨부
3. 재현 단계 상세히 기술
4. 환경 정보 포함
5. 긴급도 적절히 설정

❌ 피해야 할 사항:
1. 감정적이거나 비난조 표현
2. 불완전한 정보 제공
3. 중복 요청 발송
4. 부적절한 긴급도 설정
5. 개인정보 노출
```

### 자가 해결 리소스

#### 온라인 도움말
```
📖 문서 자료:
- 사용자 교육 가이드
- 관리자 운영 매뉴얼
- 간사용 사용자 가이드
- 본 FAQ 및 문제해결 가이드

🎥 비디오 자료:
- 기본 사용법 튜토리얼
- 고급 기능 활용법
- 문제 해결 시연
- 최신 기능 소개

🔍 검색 및 커뮤니티:
- 내부 지식 베이스
- 사용자 포럼
- 질문과 답변 섹션
- 개발자 블로그
```

---

## 🎯 결론

이 **FAQ 및 문제해결 가이드**는 AI 모델 관리 시스템 사용 중 발생할 수 있는 다양한 문제들에 대한 체계적인 해결 방법을 제공합니다.

### 🔄 지속적 개선

- **사용자 피드백 반영**: 새로운 문제와 해결책 추가
- **정기적 업데이트**: 시스템 변경사항 반영
- **교육 자료 연동**: 다른 가이드와 상호 참조
- **모니터링 연계**: 실제 발생 패턴 분석

### 📞 추가 지원

문제가 해결되지 않거나 이 가이드에 없는 상황이 발생하면 언제든 기술 지원팀에 연락해 주세요. **신속하고 정확한 지원을 위해 최선을 다하겠습니다!** 🚀