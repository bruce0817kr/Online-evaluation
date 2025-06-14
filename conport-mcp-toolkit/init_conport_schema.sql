-- ConPort MCP 데이터베이스 스키마 초기화 스크립트

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
    content TEXT NOT NULL  -- JSON으로 저장
);

-- Active Context History 테이블 (활성 컨텍스트 이력)
CREATE TABLE IF NOT EXISTS active_context_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version INTEGER NOT NULL,
    content TEXT NOT NULL  -- JSON으로 저장
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

-- Alembic 버전 테이블 업데이트 (이미 존재하는 경우)
UPDATE alembic_version SET version_num = 'head' WHERE version_num IS NOT NULL;
