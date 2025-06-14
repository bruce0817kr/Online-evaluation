import sqlite3
import os

os.chdir('c:\\Project\\Online-evaluation')
conn = sqlite3.connect('context_portal/context.db')
cursor = conn.cursor()

# 테이블 목록 확인
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print('Tables:', tables)

# 스키마 정보 확인
for table in tables:
    print(f"\nTable: {table[0]}")
    cursor.execute(f"PRAGMA table_info({table[0]});")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[1]} {col[2]}")

conn.close()
