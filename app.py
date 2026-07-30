from flask import Flask, request, jsonify, render_template, send_from_directory
import sqlite3
import os
import zipfile
import re
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder='static', template_folder=BASE_DIR)

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = '*'
    response.headers['Access-Control-Allow-Methods'] = '*'
    return response


IS_VERCEL = os.environ.get('VERCEL') == '1' or 'VERCEL' in os.environ
ADMIN_SECRET_KEY = os.environ.get('ADMIN_KEY', 'admin123')

if IS_VERCEL:
    DB_PATH = "/tmp/Stage_New_Search.db"
    VISITS_FILE = "/tmp/visits.json"
else:
    DB_PATH = os.path.join(BASE_DIR, "Stage_New_Search.db")
    VISITS_FILE = os.path.join(BASE_DIR, "visits.json")

ZIP_PATH = os.path.join(BASE_DIR, "Stage_New_Search_db.zip")

def init_logs_db(conn):
    try:
        cursor = conn.cursor()
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
        conn.commit()
    except Exception as e:
        print("Error initializing search_logs table:", e)

def get_real_visits():
    count = 1
    if os.path.exists(VISITS_FILE):
        try:
            with open(VISITS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                count = data.get('count', 0) + 1
        except:
            count = 1
    with open(VISITS_FILE, 'w', encoding='utf-8') as f:
        json.dump({'count': count}, f)
    return count

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

def check_and_extract_db():
    if not os.path.exists(DB_PATH) and os.path.exists(ZIP_PATH):
        print(f"Extracting Stage_New_Search.db to {DB_PATH}...")
        extract_dir = "/tmp" if IS_VERCEL else BASE_DIR
        with zipfile.ZipFile(ZIP_PATH, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        print("Database extracted successfully!")

def get_db_connection():
    check_and_extract_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    init_logs_db(conn)
    return conn

def log_search_event(ip, query, mode, user_agent):
    if not query:
        return
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute(
            "INSERT INTO search_logs (ip, query, mode, user_agent, timestamp) VALUES (?, ?, ?, ?, ?)",
            (ip, query, mode, user_agent, now_str)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print("Error logging search:", e)

@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/index.html')
def index_file():
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/analytics.html')
def analytics():
    return send_from_directory(BASE_DIR, 'analytics.html')

@app.route('/predictions.html')
def predictions():
    return send_from_directory(BASE_DIR, 'predictions.html')

@app.route('/admin.html')
@app.route('/admin')
def admin_page():
    return send_from_directory(BASE_DIR, 'admin.html')

@app.route('/api/visitor_count', methods=['GET', 'POST'])
def visitor_count():
    count = get_real_visits()
    return jsonify({'count': count})


@app.route('/api/search_ping', methods=['GET', 'POST'])
def search_ping():
    query = request.args.get('q', '').strip()
    mode = request.args.get('mode', 'auto').strip()

    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if client_ip and ',' in client_ip:
        client_ip = client_ip.split(',')[0].strip()
    user_agent = request.headers.get('User-Agent', '')

    if query:
        log_search_event(client_ip, query, mode, user_agent)
    return jsonify({'status': 'logged'})

@app.route('/api/search', methods=['GET'])
def search():
    query = request.args.get('q', '').strip()
    mode = request.args.get('mode', 'auto').strip()

    # Capture Visitor IP & User Agent
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if client_ip and ',' in client_ip:
        client_ip = client_ip.split(',')[0].strip()
    user_agent = request.headers.get('User-Agent', '')

    if not query:
        return jsonify({'error': 'يرجى كتابة رقم الجلوس أو اسم الطالب'}), 400

    # Log the search event
    log_search_event(client_ip, query, mode, user_agent)

    conn = get_db_connection()
    cursor = conn.cursor()

    if query.isdigit():
        cursor.execute("""
            SELECT seating_no, arabic_name, total_degree, student_case_desc 
            FROM stage_new_search 
            WHERE seating_no = ?
        """, (query,))
        row = cursor.fetchone()

        if row:
            student = dict(row)
            student['percentage'] = round((student['total_degree'] / 320.0) * 100, 2)
            conn.close()
            return jsonify({'type': 'single', 'data': student})

    raw_tokens = [t for t in query.split() if t]
    if not raw_tokens:
        conn.close()
        return jsonify({'type': 'list', 'data': [], 'count': 0})

    where_clauses = ["(normalized_name LIKE ? OR arabic_name LIKE ?)" for _ in raw_tokens]
    sql = f"""
        SELECT seating_no, arabic_name, total_degree, student_case_desc 
        FROM stage_new_search 
        WHERE {" AND ".join(where_clauses)}
        ORDER BY total_degree DESC 
        LIMIT 30
    """
    
    params = []
    for t in raw_tokens:
        norm_t = normalize_arabic(t)
        params.extend([f"%{norm_t}%", f"%{t}%"])

    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()

    results = []
    for r in rows:
        st = dict(r)
        st['percentage'] = round((st['total_degree'] / 320.0) * 100, 2)
        results.append(st)

    if len(results) == 1:
        return jsonify({'type': 'single', 'data': results[0]})
    elif len(results) > 1:
        return jsonify({'type': 'list', 'data': results, 'count': len(results)})
    else:
        return jsonify({'type': 'none', 'data': [], 'message': f'لم نتمكن من العثور على أية نتائج مطابقة للبحث: "{query}"'})

@app.route('/api/admin/logs', methods=['GET'])
def admin_logs():
    key = request.args.get('key', '').strip()
    if key != ADMIN_SECRET_KEY:
        return jsonify({'error': 'غير مصرح للوصول - كلمة السر خاطئة'}), 401

    conn = get_db_connection()
    cursor = conn.cursor()

    # Total searches count
    cursor.execute("SELECT COUNT(*) FROM search_logs")
    total_searches = cursor.fetchone()[0]

    # Unique IPs count
    cursor.execute("SELECT COUNT(DISTINCT ip) FROM search_logs")
    unique_ips = cursor.fetchone()[0]

    # Today's searches
    today_str = datetime.now().strftime('%Y-%m-%d')
    cursor.execute("SELECT COUNT(*) FROM search_logs WHERE timestamp LIKE ?", (f"{today_str}%",))
    today_searches = cursor.fetchone()[0]

    # Top searched queries
    cursor.execute("""
        SELECT query, COUNT(*) as cnt, MAX(timestamp) as last_time 
        FROM search_logs 
        GROUP BY query 
        ORDER BY cnt DESC 
        LIMIT 10
    """)
    top_queries = [{'query': r[0], 'count': r[1], 'last_time': r[2]} for r in cursor.fetchall()]
    top_query_name = top_queries[0]['query'] if top_queries else '—'

    # Live 100 recent logs
    cursor.execute("""
        SELECT ip, query, mode, user_agent, timestamp 
        FROM search_logs 
        ORDER BY id DESC 
        LIMIT 100
    """)
    logs = [{
        'ip': r[0],
        'query': r[1],
        'mode': r[2],
        'user_agent': r[3],
        'timestamp': r[4]
    } for r in cursor.fetchall()]

    conn.close()

    return jsonify({
        'total_searches': total_searches,
        'unique_ips': unique_ips,
        'today_searches': today_searches,
        'top_query': top_query_name,
        'top_queries': top_queries,
        'logs': logs
    })

@app.route('/api/top', methods=['GET'])
def top_students():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT seating_no, arabic_name, total_degree, student_case_desc 
        FROM stage_new_search 
        ORDER BY total_degree DESC 
        LIMIT 15
    """)
    rows = cursor.fetchall()
    conn.close()

    results = []
    for r in rows:
        st = dict(r)
        st['percentage'] = round((st['total_degree'] / 320.0) * 100, 2)
        results.append(st)

    return jsonify({'data': results})

@app.route('/api/stats', methods=['GET'])
def stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*), AVG(total_degree), MAX(total_degree) FROM stage_new_search")
    total, avg_all, max_score = cursor.fetchone()
    
    cursor.execute("SELECT COUNT(*), AVG(total_degree) FROM stage_new_search WHERE total_degree >= 160")
    passed_cnt, avg_passed = cursor.fetchone()
    conn.close()

    pass_rate = round((passed_cnt / total) * 100, 2) if total > 0 else 0
    avg_passed_rounded = round(avg_passed, 1) if avg_passed else 0
    avg_all_rounded = round(avg_all, 1) if avg_all else 0

    return jsonify({
        'total_students': total,
        'passed_students': passed_cnt,
        'pass_rate': pass_rate,
        'avg_passed_score': avg_passed_rounded,
        'avg_passed_percent': round((avg_passed_rounded / 320.0) * 100, 1),
        'avg_all_score': avg_all_rounded,
        'avg_all_percent': round((avg_all_rounded / 320.0) * 100, 1),
        'max_score': max_score or 320
    })

if __name__ == '__main__':
    print("Starting Natega Web Server on http://localhost:5000")
    print("Admin dashboard available at http://localhost:5000/admin.html")
    app.run(host='0.0.0.0', port=5000, debug=False)
