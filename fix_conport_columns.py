# ConPort MCP 추가 컬럼 수정 스크립트

import sqlite3
import os

def add_missing_columns():
    """ConPort MCP 데이터베이스에 누락된 컬럼들을 추가하는 함수"""
    
    # 데이터베이스 연결
    os.chdir('c:\\Project\\Online-evaluation')
    conn = sqlite3.connect('context_portal/context.db')
    cursor = conn.cursor()
    
    print("ConPort 데이터베이스 누락 컬럼 추가 중...")
    
    # 히스토리 테이블에 change_source 컬럼 추가
    try:
        cursor.execute('ALTER TABLE product_context_history ADD COLUMN change_source TEXT DEFAULT "manual"')
        print('✅ product_context_history에 change_source 컬럼 추가 완료')
    except sqlite3.OperationalError as e:
        print(f'ℹ️ product_context_history 컬럼 추가: {e}')
    
    try:
        cursor.execute('ALTER TABLE active_context_history ADD COLUMN change_source TEXT DEFAULT "manual"')
        print('✅ active_context_history에 change_source 컬럼 추가 완료')
    except sqlite3.OperationalError as e:
        print(f'ℹ️ active_context_history 컬럼 추가: {e}')
    
    # context_links 테이블이 없으면 생성
    try:
        cursor.execute('''CREATE TABLE IF NOT EXISTS context_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_item_type TEXT,
            source_item_id TEXT,
            target_item_type TEXT,
            target_item_id TEXT,
            relationship_type TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        print('✅ context_links 테이블 생성 완료')
    except sqlite3.OperationalError as e:
        print(f'ℹ️ context_links 테이블 생성: {e}')
    
    # context_links에 description 컬럼 추가
    try:
        cursor.execute('ALTER TABLE context_links ADD COLUMN description TEXT')
        print('✅ context_links에 description 컬럼 추가 완료')
    except sqlite3.OperationalError as e:
        print(f'ℹ️ context_links description 컬럼 추가: {e}')
    
    conn.commit()
    
    # 최종 테이블 구조 확인
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"\n📋 총 테이블 수: {len(tables)}")
    
    # 각 테이블의 컬럼 정보 확인
    important_tables = ['product_context', 'active_context', 'decisions', 'progress_entries', 
                       'system_patterns', 'custom_data', 'context_links', 
                       'product_context_history', 'active_context_history']
    
    for table_name in important_tables:
        try:
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            print(f"\n📊 {table_name} 테이블:")
            for col in columns:
                print(f"  - {col[1]} {col[2]}")
        except sqlite3.OperationalError:
            print(f"❌ {table_name} 테이블이 존재하지 않음")
    
    conn.close()
    print("\n✅ 컬럼 추가 작업 완료!")

if __name__ == "__main__":
    add_missing_columns()
