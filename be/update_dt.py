import sqlite3

conn = sqlite3.connect(r"C:\01_Projects\sunflower87\db\sunflower87.db")
conn.execute("UPDATE account SET dt_opened = '2024-05-01'")
conn.commit()
conn.close()
print("Updated successfully")
