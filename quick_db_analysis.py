#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sqlite3
import sys

db_path = r'c:\01_Projects\sunflower87\db\sunflower87.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("\n" + "="*80)
print("DB ANALYSIS: Tables and Schema")
print("="*80)

# Tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
tables = cursor.fetchall()
print(f"\nTotal Tables: {len(tables)}")

for table in tables:
    table_name = table[0]
    print(f"\n[{table_name}]")
    
    cursor.execute(f'PRAGMA table_info({table_name});')
    columns = cursor.fetchall()
    
    cursor.execute(f'SELECT COUNT(*) FROM {table_name};')
    row_count = cursor.fetchone()[0]
    
    print(f"  Rows: {row_count}")
    print("  Columns:")
    for col in columns:
        cid, name, type_, notnull, default, pk = col
        info = f"    {name:25} {type_:15}"
        if pk: info += " [PK]"
        if notnull: info += " [NOT NULL]"
        print(info)

# Indices
print("\n" + "="*80)
print("Indices")
print("="*80)
cursor.execute("SELECT name, tbl_name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%';")
indices = cursor.fetchall()
print(f"Custom Indices: {len(indices)}")
for idx in indices:
    print(f"  {idx[0]} on {idx[1]}")

if len(indices) == 0:
    print("  WARNING: No custom indices found!")

conn.close()
