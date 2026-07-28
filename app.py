from flask import Flask, request, jsonify, render_template, send_from_directory
import sqlite3
import os

app = Flask(__name__, static_folder='static', template_folder='templates')
DB_PATH = r"e:\natega\Stage_New_Search.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/search', methods=['GET'])
def search():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'error': 'يرجى كتابة رقم الجلوس أو اسم الطالب'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    if query.isdigit():
        # Search by seating number (exact indexed query)
        cursor.execute("""
            SELECT seating_no, arabic_name, total_degree 
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
            return jsonify({'type': 'single', 'data': None, 'message': 'لم يتم العثور على طالب بهرقم الجلوس المكتوب'}), 404
    else:
        # Search by name (LIKE pattern)
        name_query = f"%{query}%"
        cursor.execute("""
            SELECT seating_no, arabic_name, total_degree 
            FROM stage_new_search 
            WHERE arabic_name LIKE ? 
            ORDER BY total_degree DESC 
            LIMIT 20
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
        SELECT seating_no, arabic_name, total_degree 
        FROM stage_new_search 
        ORDER BY total_degree DESC 
        LIMIT 10
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
    cursor.execute("SELECT COUNT(*) as total FROM stage_new_search")
    total = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as passed FROM stage_new_search WHERE total_degree >= 160")
    passed = cursor.fetchone()['passed']
    conn.close()

    return jsonify({
        'total_students': total,
        'passed_students': passed,
        'pass_rate': round((passed / total) * 100, 1) if total > 0 else 0,
        'max_degree': 320
    })

if __name__ == '__main__':
    print("Starting Natega Web Server on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
