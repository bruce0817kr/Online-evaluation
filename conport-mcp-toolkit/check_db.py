#!/usr/bin/env python3
"""
데이터베이스 연결 및 테이블 확인 도구

ConPort MCP 데이터베이스의 기본적인 연결성과 테이블 상태를 빠르게 확인합니다.

사용법:
    python check_db.py [database_path]

매개변수:
    database_path: 데이터베이스 파일 경로 (기본값: context_portal/context.db)
"""

import sqlite3
import os
import sys
from pathlib import Path

def check_database_connection(db_path="context_portal/context.db"):
    """데이터베이스 연결 및 기본 상태 확인"""
    
    print(f"🔍 데이터베이스 연결 확인: {db_path}")
    
    # 파일 존재 확인
    if not os.path.exists(db_path):
        print(f"❌ 데이터베이스 파일이 없습니다: {db_path}")
        return False
    
    try:
        # 데이터베이스 연결
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 기본 연결 테스트
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        
        if result and result[0] == 1:
            print("✅ 데이터베이스 연결 성공")
        else:
            print("❌ 데이터베이스 연결 실패")
            return False
        
        # 테이블 목록 조회
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        
        print(f"📊 총 테이블 수: {len(tables)}")
        print("📋 테이블 목록:")
        for table_name in sorted(table_names):
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                count = cursor.fetchone()[0]
                print(f"  - {table_name}: {count} 레코드")
            except sqlite3.Error as e:
                print(f"  - {table_name}: 오류 ({e})")
        
        # ConPort 필수 테이블 확인
        required_tables = [
            'product_context', 'active_context', 'decisions', 
            'progress_entries', 'system_patterns', 'custom_data'
        ]
        
        print("\n🎯 ConPort 필수 테이블 확인:")
        missing_tables = []
        for table in required_tables:
            if table in table_names:
                print(f"  ✅ {table}")
            else:
                print(f"  ❌ {table} (누락)")
                missing_tables.append(table)
        
        if missing_tables:
            print(f"\n⚠️ 누락된 테이블: {', '.join(missing_tables)}")
            print("💡 init_conport_db.py를 실행하여 스키마를 초기화하세요.")
        else:
            print("\n✅ 모든 필수 테이블이 존재합니다.")
        
        conn.close()
        return len(missing_tables) == 0
        
    except Exception as e:
        print(f"❌ 데이터베이스 확인 실패: {e}")
        return False

def main():
    """메인 함수"""
    
    # 명령행 인수 처리
    db_path = "context_portal/context.db"
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    
    print("=" * 50)
    print("🔍 ConPort MCP 데이터베이스 확인 도구")
    print("=" * 50)
    
    success = check_database_connection(db_path)
    
    print("=" * 50)
    if success:
        print("🎉 데이터베이스 상태가 정상입니다!")
    else:
        print("⚠️ 데이터베이스에 문제가 있습니다.")
        print("📋 diagnose_conport.py를 실행하여 상세한 진단을 받으세요.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
