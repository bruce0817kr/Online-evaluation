import sqlite3

conn = sqlite3.connect('context_portal/context.db')
cursor = conn.cursor()

try:
    cursor.execute('ALTER TABLE product_context_history ADD COLUMN change_source TEXT DEFAULT "manual"')
    print('product_context_history에 change_source 컬럼 추가 완료')
except sqlite3.OperationalError as e:
    print(f'product_context_history 컬럼 추가 오류: {e}')

try:
    cursor.execute('ALTER TABLE active_context_history ADD COLUMN change_source TEXT DEFAULT "manual"')
    print('active_context_history에 change_source 컬럼 추가 완료')
except sqlite3.OperationalError as e:
    print(f'active_context_history 컬럼 추가 오류: {e}')

conn.commit()
conn.close()
print('히스토리 테이블 컬럼 추가 완료')
