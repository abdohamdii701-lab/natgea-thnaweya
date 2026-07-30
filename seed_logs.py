import sqlite3
import os
from datetime import datetime

DB_PATH = "e:/natega/Stage_New_Search.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Ensure table exists
cursor.execute("""
    CREATE TABLE IF NOT EXISTS search_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ip TEXT,
        query TEXT,
        mode TEXT,
        user_agent TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
""")

# Insert initial test logs to verify dashboard rendering
sample_logs = [
    ('127.0.0.1', '2001970', 'seating', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0'),
    ('127.0.0.1', 'احمد محمود', 'name', 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) Mobile'),
    ('192.168.1.3', '2005432', 'seating', 'Mozilla/5.0 (Linux; Android 14; SM-S928B) Chrome/125.0'),
    ('41.234.12.89', 'محمد علي', 'name', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0'),
    ('156.204.88.12', '2019888', 'seating', 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X)')
]

now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
for ip, query, mode, ua in sample_logs:
    cursor.execute(
        "INSERT INTO search_logs (ip, query, mode, user_agent, timestamp) VALUES (?, ?, ?, ?, ?)",
        (ip, query, mode, ua, now_str)
    )

conn.commit()

# Verify count
cursor.execute("SELECT COUNT(*) FROM search_logs")
count = cursor.fetchone()[0]
conn.close()

print(f"Successfully seeded search_logs table. Total log entries: {count}")
