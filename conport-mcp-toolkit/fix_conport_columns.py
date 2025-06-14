#!/usr/bin/env python3
"""
ConPort MCP 데이터베이스 스키마 수정 도구

누락된 컬럼을 추가하고 테이블 구조를 업데이트합니다.
기존 데이터를 보존하면서 스키마를 안전하게 수정합니다.

사용법:
    python fix_conport_columns.py [database_path]

매개변수:
    database_path: 데이터베이스 파일 경로 (기본값: context_portal/context.db)
"""

import sqlite3
import os
import sys
from pathlib import Path

def fix_conport_columns(db_path="context_portal/context.db"):
    """ConPort MCP 데이터베이스에 누락된 컬럼들을 추가하는 함수"""
    
    print(f"ConPort 데이터베이스 스키마 수정 중... ({db_path})")
    
    # 데이터베이스 파일 존재 확인
    if not os.path.exists(db_path):
        print(f"❌ 데이터베이스 파일이 없습니다: {db_path}")
        return False
    
    try:
        # 데이터베이스 연결
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 백업 (선택적)
        backup_path = f"{db_path}.backup"
        if not os.path.exists(backup_path):
            print(f"📋 데이터베이스 백업 생성: {backup_path}")
            backup_conn = sqlite3.connect(backup_path)
            conn.backup(backup_conn)
            backup_conn.close()
        
        # 히스토리 테이블에 change_source 컬럼 추가
        print("\n🔧 누락된 컬럼 추가 중...")
        
        history_tables = ['product_context_history', 'active_context_history']
        for table in history_tables:
            try:
                cursor.execute(f'ALTER TABLE {table} ADD COLUMN change_source TEXT DEFAULT "manual"')
                print(f'✅ {table}에 change_source 컬럼 추가 완료')
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e).lower():
                    print(f'ℹ️ {table}: change_source 컬럼이 이미 존재함')
                else:
                    print(f'⚠️ {table} 컬럼 추가 오류: {e}')
        
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
            print('✅ context_links 테이블 확인/생성 완료')
        except sqlite3.OperationalError as e:
            print(f'⚠️ context_links 테이블 생성 오류: {e}')
        
        # context_links에 description 컬럼 추가
        try:
            cursor.execute('ALTER TABLE context_links ADD COLUMN description TEXT')
            print('✅ context_links에 description 컬럼 추가 완료')
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print('ℹ️ context_links: description 컬럼이 이미 존재함')
            else:
                print(f'⚠️ context_links description 컬럼 추가 오류: {e}')
        
        # conport_items_links 테이블에 description 컬럼 추가 (중복 방지)
        try:
            cursor.execute('ALTER TABLE conport_items_links ADD COLUMN description TEXT')
            print('✅ conport_items_links에 description 컬럼 추가 완료')
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print('ℹ️ conport_items_links: description 컬럼이 이미 존재함')
            elif "no such table" in str(e).lower():
                print('ℹ️ conport_items_links 테이블이 존재하지 않음 (정상)')
            else:
                print(f'⚠️ conport_items_links description 컬럼 추가 오류: {e}')
        
        conn.commit()
        
        # 테이블 구조 검증
        print("\n📋 테이블 구조 검증:")
        
        # 모든 테이블 나열
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        print(f"총 테이블 수: {len(tables)}")
        
        # 중요 테이블의 컬럼 정보 확인
        important_tables = [
            'product_context', 'active_context', 'decisions', 'progress_entries', 
            'system_patterns', 'custom_data', 'context_links', 
            'product_context_history', 'active_context_history', 'conport_items_links'
        ]
        
        for table_name in important_tables:
            if table_name in table_names:
                try:
                    cursor.execute(f"PRAGMA table_info({table_name});")
                    columns = cursor.fetchall()
                    print(f"\n📊 {table_name} ({len(columns)} 컬럼):")
                    for col in columns:
                        print(f"  - {col[1]} {col[2]}")
                except sqlite3.OperationalError as e:
                    print(f"❌ {table_name} 정보 조회 오류: {e}")
            else:
                print(f"⚠️ {table_name} 테이블이 존재하지 않음")
        
        conn.close()
        print("\n✅ 스키마 수정 작업 완료!")
        return True
        
    except Exception as e:
        print(f"❌ 스키마 수정 실패: {e}")
        return False

def main():
    """메인 함수"""
    
    # 명령행 인수 처리
    db_path = "context_portal/context.db"
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    
    print("=" * 60)
    print("🔧 ConPort MCP 데이터베이스 스키마 수정 도구")
    print("=" * 60)
    
    success = fix_conport_columns(db_path)
    
    if success:
        print("\n📝 다음 단계:")
        print("1. diagnose_conport.py로 전체 시스템 상태 확인")
        print("2. ConPort MCP 서버 재시작")
        return 0
    else:
        print("\n❌ 스키마 수정에 실패했습니다.")
        print("📋 diagnose_conport.py를 실행하여 문제를 진단해보세요.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
