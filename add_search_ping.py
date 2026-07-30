import os
import re

# 1. Update app.py to add /api/search_ping route
with open('app.py', 'r', encoding='utf-8') as f:
    app_content = f.read()

if '/api/search_ping' not in app_content:
    search_ping_route = """
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
"""
    app_content = app_content.replace("@app.route('/api/search', methods=['GET'])", search_ping_route + "\n@app.route('/api/search', methods=['GET'])")
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(app_content)
    print("Added /api/search_ping route to app.py")

# 2. Update static/main.js and dist/static/main.js
js_files = ['static/main.js', 'dist/static/main.js']

ping_code = """
    // Background Ping to Admin Dashboard Logging System
    try {
        fetch(`/api/search_ping?q=${encodeURIComponent(query)}&mode=${searchMode}`).catch(() => {});
    } catch(e) {}
"""

for js_path in js_files:
    if os.path.exists(js_path):
        with open(js_path, 'r', encoding='utf-8') as f:
            js_content = f.read()

        if '/api/search_ping' not in js_content:
            js_content = js_content.replace(
                "// Smart Auto-Detect Query Type (Seating vs Name)",
                ping_code + "\n    // Smart Auto-Detect Query Type (Seating vs Name)"
            )
            with open(js_path, 'w', encoding='utf-8') as f:
                f.write(js_content)
            print(f"Added search_ping tracking to {js_path}")

