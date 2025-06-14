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
