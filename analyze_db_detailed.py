import sqlite3
import json

def analyze_database(db_path):
    """SQLite 데이터베이스 상세 분석"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. 테이블 목록
    print("\n" + "="*80)
    print("📊 테이블 목록")
    print("="*80)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = cursor.fetchall()
    print(f"총 테이블 수: {len(tables)}")
    for table in tables:
        print(f"  - {table[0]}")
    
    # 2. 각 테이블의 상세 정보
    print("\n" + "="*80)
    print("📋 테이블별 스키마 및 통계")
    print("="*80)
    
    table_stats = {}
    for table in tables:
        table_name = table[0]
        
        # 컬럼 정보
        cursor.execute(f'PRAGMA table_info({table_name});')
        columns = cursor.fetchall()
        
        # 행 수
        cursor.execute(f'SELECT COUNT(*) FROM {table_name};')
        row_count = cursor.fetchone()[0]
        
        # 테이블 크기
        cursor.execute(f"SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size();")
        table_size = cursor.fetchone()[0]
        
        print(f"\n[{table_name}] - 행 수: {row_count:,} | 크기: {table_size:,} bytes")
        print("  컬럼 정보:")
        
        for col in columns:
            cid, col_name, col_type, notnull, default, pk = col
            col_info = f"    {col_name:25} {col_type:15}"
            if pk:
                col_info += f" [PK]"
            if notnull:
                col_info += f" [NOT NULL]"
            if default is not None:
                col_info += f" [DEFAULT: {default}]"
            print(col_info)
        
        table_stats[table_name] = {
            'row_count': row_count,
            'column_count': len(columns),
            'size': table_size
        }
    
    # 3. 인덱스 분석
    print("\n" + "="*80)
    print("🔍 인덱스 분석")
    print("="*80)
    
    cursor.execute("SELECT name, tbl_name, sql FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%' ORDER BY tbl_name;")
    indices = cursor.fetchall()
    
    if indices:
        print(f"총 인덱스 수: {len(indices)}")
        for idx in indices:
            idx_name, tbl_name, sql = idx
            print(f"  - {idx_name} (on {tbl_name})")
            if sql:
                print(f"    SQL: {sql}")
    else:
        print("❌ 커스텀 인덱스 없음 (성능 문제 가능성)")
    
    # 4. Foreign Key 분석
    print("\n" + "="*80)
    print("🔗 Foreign Key 관계")
    print("="*80)
    
    fk_found = False
    for table in tables:
        table_name = table[0]
        cursor.execute(f'PRAGMA foreign_key_list({table_name});')
        fks = cursor.fetchall()
        if fks:
            fk_found = True
            print(f"\n[{table_name}]")
            for fk in fks:
                from_col = fk[3]
                to_table = fk[2]
                to_col = fk[4]
                on_delete = fk[5]
                on_update = fk[6]
                print(f"  {from_col} → {to_table}.{to_col} (ON DELETE: {on_delete}, ON UPDATE: {on_update})")
    
    if not fk_found:
        print("❌ Foreign Key 관계 정의 없음 (스키마에 정의되었으나 DB에서 활성화 안 됨)")
    
    # 5. 컬럼 타입 분석
    print("\n" + "="*80)
    print("🔣 컬럼 타입 통계")
    print("="*80)
    
    type_stats = {}
    for table in tables:
        table_name = table[0]
        cursor.execute(f'PRAGMA table_info({table_name});')
        columns = cursor.fetchall()
        for col in columns:
            col_type = col[2] if col[2] else "UNKNOWN"
            type_stats[col_type] = type_stats.get(col_type, 0) + 1
    
    print("타입별 컬럼 수:")
    for col_type, count in sorted(type_stats.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {col_type:20} {count:3}개")
    
    # 6. NULL 허용 분석
    print("\n" + "="*80)
    print("❓ NULL 허용 여부 분석")
    print("="*80)
    
    nullable_stats = {'NOT NULL': 0, 'NULLABLE': 0}
    for table in tables:
        table_name = table[0]
        cursor.execute(f'PRAGMA table_info({table_name});')
        columns = cursor.fetchall()
        for col in columns:
            if col[3]:  # notnull=1
                nullable_stats['NOT NULL'] += 1
            else:
                nullable_stats['NULLABLE'] += 1
    
    total = sum(nullable_stats.values())
    print(f"총 컬럼: {total}")
    print(f"  - NOT NULL: {nullable_stats['NOT NULL']} ({nullable_stats['NOT NULL']/total*100:.1f}%)")
    print(f"  - NULLABLE: {nullable_stats['NULLABLE']} ({nullable_stats['NULLABLE']/total*100:.1f}%)")
    
    # 7. Primary Key 분석
    print("\n" + "="*80)
    print("🔑 Primary Key 분석")
    print("="*80)
    
    for table in tables:
        table_name = table[0]
        cursor.execute(f'PRAGMA table_info({table_name});')
        columns = cursor.fetchall()
        pk_cols = [col for col in columns if col[5]]  # pk=1
        if pk_cols:
            if len(pk_cols) == 1:
                print(f"[{table_name}] 단일 PK: {pk_cols[0][1]}")
            else:
                pk_names = ", ".join([col[1] for col in pk_cols])
                print(f"[{table_name}] 복합 PK: ({pk_names})")
        else:
            print(f"[{table_name}] ❌ PRIMARY KEY 없음")
    
    # 8. 테이블 크기 분석
    print("\n" + "="*80)
    print("💾 데이터 크기 분석")
    print("="*80)
    
    total_size = sum([stats['size'] for stats in table_stats.values()])
    print(f"전체 DB 크기: {total_size:,} bytes ({total_size/1024/1024:.2f} MB)")
    print("\n테이블별 크기:")
    for table_name in sorted(table_stats.keys(), key=lambda x: table_stats[x]['size'], reverse=True):
        stats = table_stats[table_name]
        size_mb = stats['size'] / 1024 / 1024
        print(f"  - {table_name:30} {size_mb:8.2f} MB  ({stats['row_count']:8,} rows)")
    
    conn.close()

if __name__ == '__main__':
    db_path = r'c:\01_Projects\sunflower87\db\sunflower87.db'
    analyze_database(db_path)
