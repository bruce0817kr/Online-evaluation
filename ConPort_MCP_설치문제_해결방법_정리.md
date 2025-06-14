# ConPort MCP 설치 문제 해결 방법 정리

## 📋 개요
ConPort MCP (Model Context Protocol) 설치 및 구성 과정에서 발생한 주요 문제들과 해결 방법을 정리한 문서입니다.

---

## 🚨 발생한 주요 문제들

### 1. 데이터베이스 테이블 누락 문제
**문제**: ConPort MCP 서버 실행 시 필수 테이블들이 생성되지 않음
- `product_context`, `active_context`, `decisions`, `progress_entries`, `system_patterns` 등

**원인**: 
- Alembic 마이그레이션 스크립트 누락
- `alembic.ini` 설정 오류
- 데이터베이스 초기화 스크립트 부재

### 2. Alembic 설정 문제
**문제**: `No script_location key found` 오류
- `alembic.ini`에서 `script_location` 설정 오류
- 마이그레이션 디렉토리 구조 불일치

### 3. 데이터베이스 스키마 불완전
**문제**: 일부 테이블에 필수 컬럼 누락
- `history` 테이블의 `change_source`, `description` 컬럼
- `context_links` 테이블의 `description` 컬럼

### 4. 환경 설정 오류
**문제**: 
- `.env` 파일의 `LOG_LEVEL` 값 형식 오류 ('info' → 'INFO')
- `database.py` 파일의 IndentationError

---

## ✅ 해결 방법

### 1. 데이터베이스 스키마 수동 생성

#### 1.1 완전한 SQL 스키마 스크립트 작성
```sql
-- init_conport_schema.sql
-- ConPort MCP 데이터베이스 테이블 생성

-- Product Context 테이블
CREATE TABLE IF NOT EXISTS product_context (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Active Context 테이블
CREATE TABLE IF NOT EXISTS active_context (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 기타 모든 필수 테이블들...
```

#### 1.2 Python 스크립트를 통한 스키마 적용
```python
# init_conport_db.py
import sqlite3

def init_database():
    # SQL 스크립트 실행하여 테이블 생성
    with open('init_conport_schema.sql', 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    
    conn = sqlite3.connect('context_portal/context.db')
    conn.executescript(schema_sql)
    conn.close()
```

### 2. Alembic 설정 수정

#### 2.1 alembic.ini 수정
```ini
[alembic]
# 스크립트 위치를 올바른 디렉토리로 설정
script_location = alembic
sqlalchemy.url = sqlite:///context_portal/context.db
```

#### 2.2 Alembic 디렉토리 구조 정리
```
alembic/
├── env.py
├── script.py.mako
├── README
└── versions/
```

### 3. 누락된 컬럼 추가

#### 3.1 Python 스크립트를 통한 컬럼 추가
```python
# add_columns.py
import sqlite3

def add_missing_columns():
    conn = sqlite3.connect('context_portal/context.db')
    cursor = conn.cursor()
    
    try:
        # history 테이블에 컬럼 추가
        cursor.execute("ALTER TABLE history ADD COLUMN change_source TEXT")
        cursor.execute("ALTER TABLE history ADD COLUMN description TEXT")
        
        # context_links 테이블에 컬럼 추가
        cursor.execute("ALTER TABLE context_links ADD COLUMN description TEXT")
        
        conn.commit()
    except sqlite3.OperationalError as e:
        print(f"컬럼이 이미 존재하거나 다른 오류: {e}")
    finally:
        conn.close()
```

### 4. 환경 설정 수정

#### 4.1 .env 파일 수정
```env
# LOG_LEVEL 값을 대문자로 수정
LOG_LEVEL=INFO
```

#### 4.2 database.py IndentationError 수정
```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        if db:  # 누락된 코드 블록 추가
            db.close()
```

---

## 🔧 사용한 도구 및 스크립트

### 1. 진단 도구
- `check_db.py`: 데이터베이스 연결 및 테이블 확인
- `diagnose_conport.py`: ConPort 환경 종합 진단

### 2. 수정 도구
- `init_conport_db.py`: 데이터베이스 초기 스키마 생성
- `add_columns.py`: 누락된 컬럼 추가
- `fix_conport_columns.py`: 컬럼 스키마 수정

### 3. 테스트 도구
- ConPort MCP 도구 함수들을 통한 기능 검증
- 데이터베이스 CRUD 작업 테스트

---

## 📝 해결 순서

1. **환경 진단**
   - ConPort MCP 서버 실행 테스트
   - 오류 메시지 분석

2. **Alembic 문제 해결 시도**
   - `alembic.ini` 수정
   - 마이그레이션 스크립트 확인
   - 마이그레이션 실행 (실패)

3. **수동 스키마 생성**
   - 완전한 SQL 스키마 스크립트 작성
   - Python을 통한 스키마 적용

4. **누락 컬럼 보완**
   - 데이터베이스 구조 분석
   - ALTER TABLE 명령으로 컬럼 추가

5. **기능 검증**
   - ConPort MCP 도구 함수 테스트
   - 프로젝트 컨텍스트 입력 및 조회

---

## 💡 핵심 교훈

### 1. Alembic 의존성 회피
- Alembic 마이그레이션이 복잡하거나 문제가 있을 경우
- 직접 SQL 스키마 스크립트를 작성하여 안정적인 초기화 가능

### 2. 단계적 문제 해결
- 큰 문제를 작은 단위로 분해
- 각 단계별로 검증하며 진행

### 3. 진단 도구의 중요성
- 문제 상황을 정확히 파악할 수 있는 진단 스크립트 필수
- 해결 과정에서 지속적인 검증 필요

### 4. 문서화의 가치
- 해결 과정을 상세히 기록
- 향후 유사한 문제 발생 시 빠른 해결 가능

---

## 🎯 결과

✅ **ConPort MCP 서버 정상 실행**
✅ **모든 필수 테이블 생성 완료**
✅ **ConPort MCP 도구 함수들 정상 작동**
✅ **프로젝트 컨텍스트 관리 기능 활성화**

---

## 📚 참고 자료

- [ConPort MCP GitHub Repository](https://github.com/cline/context-portal)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLite ALTER TABLE Documentation](https://www.sqlite.org/lang_altertable.html)

---

## 🔄 재사용 가능한 스크립트

이 해결 과정에서 작성된 모든 스크립트들은 다른 프로젝트에서도 재사용할 수 있도록 설계되었습니다:

- `init_conport_schema.sql`: 완전한 ConPort 데이터베이스 스키마
- `init_conport_db.py`: 데이터베이스 초기화 자동화
- `diagnose_conport.py`: ConPort 환경 진단 도구
- `fix_conport_columns.py`: 스키마 수정 도구

---

**작성일**: 2025년 6월 14일  
**프로젝트**: Online Evaluation System  
**상태**: 해결 완료 ✅
