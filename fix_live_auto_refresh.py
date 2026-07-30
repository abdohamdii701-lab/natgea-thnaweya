import os
import re

# 1. Add CORS to app.py
with open('app.py', 'r', encoding='utf-8') as f:
    app_code = f.read()

if 'Access-Control-Allow-Origin' not in app_code:
    cors_code = """
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = '*'
    response.headers['Access-Control-Allow-Methods'] = '*'
    return response
"""
    app_code = app_code.replace("app = Flask(__name__, static_folder='static', template_folder=BASE_DIR)", "app = Flask(__name__, static_folder='static', template_folder=BASE_DIR)\n" + cors_code)
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(app_code)
    print("Added CORS headers to app.py")

# 2. Update static/main.js to send search_ping to http://localhost:5000 when on github.io
js_files = ['static/main.js', 'dist/static/main.js']

smart_ping_code = """
    // Smart Cross-Origin & Local Search Tracking Ping
    try {
        let pingUrl = '/api/search_ping';
        if (window.location.hostname.includes('github.io')) {
            pingUrl = 'http://localhost:5000/api/search_ping';
        }
        fetch(`${pingUrl}?q=${encodeURIComponent(query)}&mode=${searchMode}&_t=${Date.now()}`).catch(() => {});
    } catch(e) {}
"""

for js_path in js_files:
    if os.path.exists(js_path):
        with open(js_path, 'r', encoding='utf-8') as f:
            js_content = f.read()

        # Replace search_ping block
        import re
        js_content = re.sub(r'// Background Ping to Admin Dashboard[\s\S]*?\}/api/search_ping[\s\S]*?\}\s*\} catch\(e\) \{\}', smart_ping_code, js_content)
        js_content = re.sub(r'// Smart Cross-Origin & Local Search Tracking Ping[\s\S]*?\}\s*\} catch\(e\) \{\}', smart_ping_code, js_content)

        with open(js_path, 'w', encoding='utf-8') as f:
            f.write(js_content)
        print(f"Updated smart search tracking in {js_path}")

print("Cross-origin search tracking setup completed.")
