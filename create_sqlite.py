import sqlite3
import pyodbc
import os
import time

def build_sqlite_db():
    start_time = time.time()
    db_path = r"e:\natega\نسخة البحث الدور الأول 2026 - نظام حديث.accdb"
    sqlite_db_path = r"e:\natega\Stage_New_Search.db"

    conn_str = f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={db_path};"

    print("Connecting to Access database...")
    conn_access = pyodbc.connect(conn_str)
    cursor_access = conn_access.cursor()

    print("Creating SQLite database...")
    conn_sqlite = sqlite3.connect(sqlite_db_path)
    cursor_sqlite = conn_sqlite.cursor()

    cursor_sqlite.execute("DROP TABLE IF EXISTS stage_new_search")
    cursor_sqlite.execute("""
    CREATE TABLE stage_new_search (
        seating_no TEXT PRIMARY KEY,
        arabic_name TEXT,
        total_degree REAL,
        student_case_desc TEXT
    )
    """)

    print("Fetching data from Access and inserting into SQLite...")
    cursor_access.execute("SELECT seating_no, arabic_name, total_degree, student_case_desc FROM Stage_New_Search")

    batch_size = 50000
    count = 0

    while True:
        rows = cursor_access.fetchmany(batch_size)
        if not rows:
            break
        cursor_sqlite.executemany("INSERT INTO stage_new_search VALUES (?, ?, ?, ?)", rows)
        conn_sqlite.commit()
        count += len(rows)
        print(f"Inserted {count} rows into SQLite...")

    print("Creating index on arabic_name...")
    cursor_sqlite.execute("CREATE INDEX idx_arabic_name ON stage_new_search(arabic_name)")
    conn_sqlite.commit()

    conn_access.close()
    conn_sqlite.close()

    end_time = time.time()
    print(f"Done! SQLite database created in {end_time - start_time:.2f} seconds at: {sqlite_db_path}")

if __name__ == '__main__':
    build_sqlite_db()
