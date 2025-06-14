#!/usr/bin/env python3
"""
ConPort MCP 데이터베이스 초기화 스크립트

ConPort MCP에 필요한 모든 테이블을 생성하고 기본 데이터를 삽입합니다.
이 스크립트는 Alembic 마이그레이션의 대안으로 사용할 수 있습니다.

사용법:
    python init_conport_db.py [database_path]

매개변수:
    database_path: 데이터베이스 파일 경로 (기본값: context_portal/context.db)
"""

import sqlite3
import os
import sys
from pathlib import Path

def init_conport_database(db_path="context_portal/context.db", schema_path=None):
    """
    ConPort 데이터베이스를 초기화합니다.
    
    Args:
        db_path: 데이터베이스 파일 경로
        schema_path: SQL 스키마 파일 경로 (기본값: 같은 디렉토리의 init_conport_schema.sql)
    """
    
    # 스키마 파일 경로 설정
    if schema_path is None:
        script_dir = Path(__file__).parent
        schema_path = script_dir / "init_conport_schema.sql"
    
    # 데이터베이스 디렉토리 생성 (필요한 경우)
    db_dir = Path(db_path).parent
    db_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"ConPort 데이터베이스 초기화 중... ({db_path})")
    
    # 스키마 파일 확인
    if not Path(schema_path).exists():
        print(f"오류: 스키마 파일을 찾을 수 없습니다: {schema_path}")
        return False
    
    try:
        # 데이터베이스 연결
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # SQL 스크립트 읽기 및 실행
        with open(schema_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # 스크립트를 문장별로 분할하여 실행
        sql_statements = sql_script.split(';')
        for statement in sql_statements:
            statement = statement.strip()
            if statement and not statement.startswith('--'):
                try:
                    cursor.execute(statement)
                    print(f"✓ 실행 완료: {statement[:50]}...")
                except sqlite3.Error as e:
                    print(f"✗ 오류: {e} - 문장: {statement[:50]}...")
        
        conn.commit()
        
        # 테이블 목록 확인
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        print(f"\n생성된 테이블 목록: {table_names}")
        
        # 각 테이블의 레코드 수 확인
        for table in tables:
            table_name = table[0]
            if table_name not in ['sqlite_sequence', 'alembic_version']:  # 내부 테이블 제외
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                    count = cursor.fetchone()[0]
                    print(f"  {table_name}: {count} 레코드")
                except sqlite3.Error:
                    print(f"  {table_name}: 오류 - 가상 테이블일 수 있음")
        
        conn.close()
        print("\n✅ 데이터베이스 초기화 완료!")
        return True
        
    except Exception as e:
        print(f"❌ 데이터베이스 초기화 실패: {e}")
        return False

def main():
    """메인 함수"""
    
    # 명령행 인수 처리
    db_path = "context_portal/context.db"
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    
    # 데이터베이스 초기화 실행
    success = init_conport_database(db_path)
    
    if success:
        print("\n📝 다음 단계:")
        print("1. ConPort MCP 서버 실행: python -m context_portal_mcp")
        print("2. MCP 클라이언트에서 ConPort 도구 사용")
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
