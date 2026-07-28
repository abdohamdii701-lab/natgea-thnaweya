import sqlite3
import pyodbc
import re
import os
import time

def normalize_arabic(text):
    if not text:
        return ""
    text = str(text)
    tashkeel = re.compile(r'[\u0617-\u061A\u064B-\u0652]')
    text = re.sub(tashkeel, '', text)
    text = re.sub(r'[أإآٱ]', 'ا', text)
    text = re.sub(r'ى', 'ي', text)
    text = re.sub(r'ة', 'ه', text)
    text = re.sub(r'ؤ', 'و', text)
    text = re.sub(r'ئ', 'ي', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def build_sqlite_db():
    start_time = time.time()
    db_path = r"e:\natega\نسخة البحث الدور الأول 2026 - نظام حديث.accdb"
    sqlite_db_path = r"e:\natega\Stage_New_Search.db"

    conn_str = f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={db_path};"

    print("Connecting to Access database...")
    conn_access = pyodbc.connect(conn_str)
    cursor_access = conn_access.cursor()

    print("Creating SQLite database with normalized_name...")
    conn_sqlite = sqlite3.connect(sqlite_db_path)
    cursor_sqlite = conn_sqlite.cursor()

    cursor_sqlite.execute("DROP TABLE IF EXISTS stage_new_search")
    cursor_sqlite.execute("""
    CREATE TABLE stage_new_search (
        seating_no TEXT PRIMARY KEY,
        arabic_name TEXT,
        total_degree REAL,
        student_case_desc TEXT,
        normalized_name TEXT
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
        inserted_rows = [(r[0], r[1], r[2], r[3], normalize_arabic(r[1])) for r in rows]
        cursor_sqlite.executemany("INSERT INTO stage_new_search VALUES (?, ?, ?, ?, ?)", inserted_rows)
        conn_sqlite.commit()
        count += len(rows)
        print(f"Inserted {count} rows into SQLite...")

    print("Creating indexes on seating_no, arabic_name, and normalized_name...")
    cursor_sqlite.execute("CREATE INDEX idx_arabic_name ON stage_new_search(arabic_name)")
    cursor_sqlite.execute("CREATE INDEX idx_norm_name ON stage_new_search(normalized_name)")
    conn_sqlite.commit()

    conn_access.close()
    conn_sqlite.close()

    end_time = time.time()
    print(f"Done! SQLite database created in {end_time - start_time:.2f} seconds at: {sqlite_db_path}")

if __name__ == '__main__':
    build_sqlite_db()
