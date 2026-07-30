from flask import Flask, request, jsonify, render_template, send_from_directory
import sqlite3
import os
import zipfile
import re
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder='static', template_folder=BASE_DIR)

IS_VERCEL = os.environ.get('VERCEL') == '1' or 'VERCEL' in os.environ

if IS_VERCEL:
    DB_PATH = "/tmp/Stage_New_Search.db"
    VISITS_FILE = "/tmp/visits.json"
else:
    DB_PATH = os.path.join(BASE_DIR, "Stage_New_Search.db")
    VISITS_FILE = os.path.join(BASE_DIR, "visits.json")

ZIP_PATH = os.path.join(BASE_DIR, "Stage_New_Search_db.zip")

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
    return conn

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

@app.route('/api/visitor_count', methods=['GET', 'POST'])
def visitor_count():
    count = get_real_visits()
    return jsonify({'count': count})

@app.route('/api/search', methods=['GET'])
def search():
    query = request.args.get('q', '').strip()
    mode = request.args.get('mode', 'auto').strip()

    if not query:
        return jsonify({'error': 'يرجى كتابة رقم الجلوس أو اسم الطالب'}), 400

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
    app.run(host='0.0.0.0', port=5000, debug=False)
