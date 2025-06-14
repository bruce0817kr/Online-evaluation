# ConPort MCP 설치 문제 해결 완전 가이드

## 📋 문제 요약

ConPort MCP (Context Portal Model Context Protocol) 설치 과정에서 발생한 주요 문제들과 해결 방법을 정리한 문서입니다.

## 🚨 발생한 주요 문제들

### 1. IndentationError in database.py
```
IndentationError: expected an indented block after 'if' statement on line 275
```

### 2. Log Level Validation Error  
```
pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings
log_level
  Input should be 'DEBUG', 'INFO', 'WARNING', 'ERROR' or 'CRITICAL' [type=literal_error, input_value='info', input_type=str]
```

### 3. Alembic Migration 오류
```
alembic.util.exc.CommandError: No 'script_location' key found in configuration
```

### 4. 데이터베이스 테이블 누락
```
Database error getting product context: Failed to retrieve product context: no such table: product_context
```

## 🔧 해결 방법

### 1. IndentationError 수정

**문제 위치**: `context-portal/src/context_portal_mcp/db/database.py` 라인 275 근처

**문제 원인**: `finally:` 블록에서 들여쓰기된 코드가 누락됨

**해결 방법**:
```python
# 수정 전 (잘못된 형태):
    finally:
        if cursor:
def get_active_context(workspace_id: str) -> models.ActiveContext:

# 수정 후 (올바른 형태):
    finally:
        if cursor:
            cursor.close()

def get_active_context(workspace_id: str) -> models.ActiveContext:
```

**적용 명령**:
```python
# database.py 파일에서 275번째 줄 근처 수정
cursor.close()  # 이 줄을 finally 블록에 추가
```

### 2. Log Level Validation 오류 수정

**문제 원인**: `.env` 파일에서 `LOG_LEVEL=info` (소문자)로 설정되어 있었지만, Pydantic 검증에서는 대문자를 요구함

**해결 방법**:
```properties
# .env 파일 수정
# 수정 전:
LOG_LEVEL=info

# 수정 후:
LOG_LEVEL=INFO
```

**확인할 환경 변수들**:
```powershell
# 환경 변수 확인
Get-ChildItem Env: | Where-Object {$_.Name -like "*log*" -or $_.Name -like "*LOG*"}
Get-ChildItem Env: | Where-Object {$_.Name -like "*FASTMCP*"}

# 문제되는 환경 변수 제거 (필요시)
Remove-Item env:LOG_LEVEL
Remove-Item env:LOG_FILE
```

### 3. Alembic Configuration 문제 해결

**문제 원인**: ConPort가 Alembic 마이그레이션 파일을 찾지 못함

**해결 방법 1**: alembic.ini 파일 수정
```ini
# alembic.ini 파일에서 script_location 수정
[alembic]
# 수정 전:
script_location = alembic_conport

# 수정 후:
script_location = alembic
```

**해결 방법 2**: 필요한 파일들 복사
```powershell
# alembic_conport의 파일들을 alembic 디렉토리로 복사
copy alembic_conport\env.py alembic\env.py -Force
copy alembic_conport\script.py.mako alembic\script.py.mako -Force
copy alembic_conport\README alembic\README -Force
```

### 4. 데이터베이스 스키마 수동 초기화

**문제 원인**: Alembic 마이그레이션이 실행되지 않아 테이블이 생성되지 않음

**해결 방법**: 수동 스키마 초기화 스크립트 생성 및 실행

#### 4-1. 스키마 초기화 SQL 파일 생성
```sql
-- init_conport_schema.sql
-- Product Context 테이블 (프로젝트 전체 컨텍스트)
CREATE TABLE IF NOT EXISTS product_context (
    id INTEGER PRIMARY KEY DEFAULT 1,
    content TEXT NOT NULL,  -- JSON으로 저장
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Active Context 테이블 (현재 작업 컨텍스트)  
CREATE TABLE IF NOT EXISTS active_context (
    id INTEGER PRIMARY KEY DEFAULT 1,
    content TEXT NOT NULL,  -- JSON으로 저장
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Decisions 테이블 (결정사항 로그)
CREATE TABLE IF NOT EXISTS decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    summary TEXT NOT NULL,
    rationale TEXT,
    implementation_details TEXT,
    tags TEXT  -- JSON array로 저장
);

-- Progress Entries 테이블 (진행상황 추적)
CREATE TABLE IF NOT EXISTS progress_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL,
    description TEXT NOT NULL,
    parent_id INTEGER,
    FOREIGN KEY (parent_id) REFERENCES progress_entries (id)
);

-- System Patterns 테이블 (시스템 패턴)
CREATE TABLE IF NOT EXISTS system_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    tags TEXT  -- JSON array로 저장
);

-- Custom Data 테이블 (사용자 정의 데이터)
CREATE TABLE IF NOT EXISTS custom_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    category TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,  -- JSON으로 저장
    UNIQUE(category, key)
);

-- Product Context History 테이블 (제품 컨텍스트 이력)
CREATE TABLE IF NOT EXISTS product_context_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version INTEGER NOT NULL,
    content TEXT NOT NULL,  -- JSON으로 저장
    change_source TEXT DEFAULT "manual"
);

-- Active Context History 테이블 (활성 컨텍스트 이력)
CREATE TABLE IF NOT EXISTS active_context_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version INTEGER NOT NULL,
    content TEXT NOT NULL,  -- JSON으로 저장
    change_source TEXT DEFAULT "manual"
);

-- ConPort Items Links 테이블 (항목 간 관계)
CREATE TABLE IF NOT EXISTS conport_items_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source_item_type TEXT NOT NULL,
    source_item_id TEXT NOT NULL,
    target_item_type TEXT NOT NULL,
    target_item_id TEXT NOT NULL,
    relationship_type TEXT NOT NULL,
    description TEXT
);

-- Context Links 테이블 (추가 컨텍스트 링크)
CREATE TABLE IF NOT EXISTS context_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_item_type TEXT,
    source_item_id TEXT,
    target_item_type TEXT,
    target_item_id TEXT,
    relationship_type TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

-- 벡터 데이터를 위한 테이블들 (시맨틱 검색용)
CREATE TABLE IF NOT EXISTS vector_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_type TEXT NOT NULL,
    item_id TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding BLOB,  -- 벡터 임베딩 데이터
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(item_type, item_id)
);

-- FTS (Full Text Search) 인덱스 생성
CREATE VIRTUAL TABLE IF NOT EXISTS decisions_fts USING fts5(
    summary, rationale, implementation_details, tags,
    content='decisions', content_rowid='id'
);

CREATE VIRTUAL TABLE IF NOT EXISTS custom_data_fts USING fts5(
    category, key, value,
    content='custom_data', content_rowid='id'
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_decisions_timestamp ON decisions(timestamp);
CREATE INDEX IF NOT EXISTS idx_progress_entries_timestamp ON progress_entries(timestamp);
CREATE INDEX IF NOT EXISTS idx_progress_entries_status ON progress_entries(status);
CREATE INDEX IF NOT EXISTS idx_system_patterns_timestamp ON system_patterns(timestamp);
CREATE INDEX IF NOT EXISTS idx_custom_data_category ON custom_data(category);
CREATE INDEX IF NOT EXISTS idx_custom_data_category_key ON custom_data(category, key);
CREATE INDEX IF NOT EXISTS idx_vector_data_item ON vector_data(item_type, item_id);
CREATE INDEX IF NOT EXISTS idx_conport_links_source ON conport_items_links(source_item_type, source_item_id);
CREATE INDEX IF NOT EXISTS idx_conport_links_target ON conport_items_links(target_item_type, target_item_id);

-- 기본 데이터 삽입 (빈 컨텍스트)
INSERT OR IGNORE INTO product_context (id, content) VALUES (1, '{}');
INSERT OR IGNORE INTO active_context (id, content) VALUES (1, '{}');
```

#### 4-2. 스키마 초기화 Python 스크립트 생성
```python
# init_conport_db.py
import sqlite3
import os

# 데이터베이스 연결
os.chdir('c:\\Project\\Online-evaluation')
conn = sqlite3.connect('context_portal/context.db')
cursor = conn.cursor()

print("ConPort 데이터베이스 스키마 초기화 중...")

# SQL 스크립트 읽기 및 실행
with open('init_conport_schema.sql', 'r', encoding='utf-8') as f:
    sql_script = f.read()

# 스크립트를 문장별로 분할하여 실행
sql_statements = sql_script.split(';')
for statement in sql_statements:
    statement = statement.strip()
    if statement:
        try:
            cursor.execute(statement)
            print(f"실행 완료: {statement[:50]}...")
        except sqlite3.Error as e:
            print(f"오류: {e} - 문장: {statement[:50]}...")

conn.commit()

# 테이블 목록 확인
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print(f"\n생성된 테이블 목록: {[table[0] for table in tables]}")

# 각 테이블의 레코드 수 확인
for table in tables:
    table_name = table[0]
    if table_name != 'sqlite_sequence':  # 내부 테이블 제외
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        count = cursor.fetchone()[0]
        print(f"{table_name}: {count} 레코드")

conn.close()
print("\n데이터베이스 초기화 완료!")
```

#### 4-3. 스크립트 실행
```powershell
# ConPort 가상환경의 Python으로 스크립트 실행
C:\Project\Online-evaluation\context-portal\.venv\Scripts\python.exe init_conport_db.py
```

### 5. 추가 컬럼 누락 문제 해결

일부 기능에서 필요한 컬럼이 누락되어 발생하는 오류들을 해결:

```python
# 히스토리 테이블에 change_source 컬럼 추가
import sqlite3
conn = sqlite3.connect('context_portal/context.db')
cursor = conn.cursor()
cursor.execute('ALTER TABLE product_context_history ADD COLUMN change_source TEXT DEFAULT "manual"')
cursor.execute('ALTER TABLE active_context_history ADD COLUMN change_source TEXT DEFAULT "manual"')
cursor.execute('ALTER TABLE context_links ADD COLUMN description TEXT')
conn.commit()
conn.close()
```

## 🎯 최종 검증

### ConPort MCP 서버 실행
```powershell
# ConPort MCP 서버 시작
C:\Project\Online-evaluation\context-portal\.venv\Scripts\python.exe C:\Project\Online-evaluation\context-portal\src\context_portal_mcp\main.py --mode http --workspace_id "c:\Project\Online-evaluation" --log-level INFO --port 8002
```

### 기능 테스트
```python
# ConPort MCP 도구 테스트 예시
mcp_conport_get_product_context(workspace_id="c:\Project\Online-evaluation")
mcp_conport_update_product_context(content={...}, workspace_id="c:\Project\Online-evaluation")
mcp_conport_log_decision(summary="테스트 결정", workspace_id="c:\Project\Online-evaluation")
```

## 📚 참고 자료

- **GitHub Issue**: [No 'script_location' key found in configuration #21](https://github.com/GreatScottyMac/context-portal/issues/21)
- **ConPort 공식 문서**: [README.md](https://github.com/GreatScottyMac/context-portal/blob/main/README.md)
- **Alembic 문서**: [Alembic Documentation](https://alembic.sqlalchemy.org/)

## ✅ 해결 완료 상태

- ✅ IndentationError 수정 완료
- ✅ Log Level Validation 오류 해결 완료  
- ✅ Alembic Configuration 문제 우회 완료
- ✅ 데이터베이스 스키마 초기화 완료
- ✅ 모든 필수 테이블 및 컬럼 생성 완료
- ✅ ConPort MCP 서버 정상 실행 확인
- ✅ 모든 ConPort 도구 정상 작동 확인

## 🔄 향후 개선 사항

1. **Alembic 마이그레이션 자동화**: ConPort 업데이트 시 자동 마이그레이션 스크립트 개선
2. **설치 스크립트 개발**: 원클릭 설치 스크립트 개발
3. **오류 처리 강화**: 더 명확한 오류 메시지 및 복구 방안 제시
4. **문서화 개선**: 공식 문서에 트러블슈팅 섹션 추가

## 📞 문제 발생 시 체크리스트

1. **환경 변수 확인**: LOG_LEVEL이 대문자인지 확인
2. **파일 권한 확인**: 가상환경 및 프로젝트 디렉토리 접근 권한
3. **파이썬 버전 확인**: Python 3.8+ 사용 여부
4. **가상환경 활성화**: ConPort 전용 가상환경 활성화 상태
5. **데이터베이스 파일**: context_portal/context.db 파일 존재 여부
6. **포트 충돌**: 사용하려는 포트가 다른 서비스에서 사용 중인지 확인

---

**작성일**: 2025-06-14  
**작성자**: AI Assistant  
**프로젝트**: 온라인 평가 시스템  
**ConPort MCP 버전**: 설치된 버전 기준
