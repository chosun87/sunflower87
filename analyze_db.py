import sqlite3
import json

conn = sqlite3.connect(r'c:\01_Projects\sunflower87\db\sunflower87.db')
cursor = conn.cursor()

# 모든 테이블 조회
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
tables = cursor.fetchall()

print('=== 테이블 목록 ===')
for table in tables:
    print(f'  - {table[0]}')

print('\n=== 각 테이블 스키마 ===')
for table in tables:
    print(f'\n[{table[0]}]')
    cursor.execute(f'PRAGMA table_info({table[0]});')
    columns = cursor.fetchall()
    for col in columns:
        col_name, col_type, notnull, default, pk = col[1], col[2], col[3], col[4], col[5]
        print(f'  {col_name:25} {col_type:15} null={notnull} default={default} pk={pk}')
    
    # 테이블의 행 수 조회
    cursor.execute(f'SELECT COUNT(*) FROM {table[0]};')
    row_count = cursor.fetchone()[0]
    print(f'  행 수: {row_count}')

# 인덱스 조회
print('\n=== 인덱스 목록 ===')
cursor.execute("SELECT name, tbl_name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%' ORDER BY tbl_name;")
indices = cursor.fetchall()
if indices:
    for idx in indices:
        print(f'  {idx[0]} on {idx[1]}')
else:
    print('  (인덱스 없음)')

# Foreign Key 확인
print('\n=== Foreign Key 확인 ===')
for table in tables:
    cursor.execute(f'PRAGMA foreign_key_list({table[0]});')
    fks = cursor.fetchall()
    if fks:
        print(f'\n[{table[0]}]')
        for fk in fks:
            from_col = fk[3]
            to_table = fk[2]
            to_col = fk[4]
            print(f'  {from_col} -> {to_table}.{to_col}')

conn.close()
