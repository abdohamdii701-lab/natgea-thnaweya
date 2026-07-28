from flask import Flask, request, jsonify, render_template
import sqlite3
import os
import zipfile

app = Flask(__name__, static_folder='static', template_folder='templates')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

IS_VERCEL = os.environ.get('VERCEL') == '1' or 'VERCEL' in os.environ

if IS_VERCEL:
    DB_PATH = "/tmp/Stage_New_Search.db"
else:
    DB_PATH = os.path.join(BASE_DIR, "Stage_New_Search.db")

ZIP_PATH = os.path.join(BASE_DIR, "Stage_New_Search_db.zip")

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
    return render_template('index.html')

@app.route('/api/search', methods=['GET'])
def search():
    query = request.args.get('q', '').strip()
    mode = request.args.get('mode', 'auto').strip()

    if not query:
        return jsonify({'error': 'يرجى كتابة رقم الجلوس أو اسم الطالب'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    is_seating_search = (mode == 'seating') or (mode == 'auto' and query.isdigit())

    if is_seating_search:
        cursor.execute("""
            SELECT seating_no, arabic_name, total_degree, student_case_desc 
            FROM stage_new_search 
            WHERE seating_no = ?
        """, (query,))
        row = cursor.fetchone()
        conn.close()

        if row:
            student = dict(row)
            student['percentage'] = round((student['total_degree'] / 320.0) * 100, 2)
            return jsonify({'type': 'single', 'data': student})
        else:
            return jsonify({'type': 'single', 'data': None, 'message': f'لم يتم العثور على طالب برقم الجلوس: {query}'}), 404
    else:
        name_query = f"%{query}%"
        cursor.execute("""
            SELECT seating_no, arabic_name, total_degree, student_case_desc 
            FROM stage_new_search 
            WHERE arabic_name LIKE ? 
            ORDER BY total_degree DESC 
            LIMIT 30
        """, (name_query,))
        rows = cursor.fetchall()
        conn.close()

        results = []
        for r in rows:
            st = dict(r)
            st['percentage'] = round((st['total_degree'] / 320.0) * 100, 2)
            results.append(st)

        return jsonify({'type': 'list', 'data': results, 'count': len(results)})

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
    total, avg_score, max_score = cursor.fetchone()
    
    cursor.execute("SELECT COUNT(*) FROM stage_new_search WHERE total_degree >= 160")
    passed = cursor.fetchone()[0]
    conn.close()

    pass_rate = round((passed / total) * 100, 2) if total > 0 else 0
    avg_score_rounded = round(avg_score, 1) if avg_score else 0

    return jsonify({
        'total_students': total,
        'passed_students': passed,
        'pass_rate': pass_rate,
        'avg_score': avg_score_rounded,
        'avg_percent': round((avg_score_rounded / 320.0) * 100, 1),
        'max_score': max_score or 320
    })

if __name__ == '__main__':
    print("Starting Natega Web Server on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
