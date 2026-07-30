import os

# Update admin.html and dist/admin.html to support Cloudflare Workers / Pages
cf_worker_url = "https://natgea-thnaweya.abdohamdii701.workers.dev"

admin_files = ['admin.html', 'dist/admin.html']

for a_path in admin_files:
    if os.path.exists(a_path):
        with open(a_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Add Cloudflare Worker fallback to default server URL if empty
        content = content.replace(
            "let serverUrl = localStorage.getItem('admin_server_url') || '';",
            f"let serverUrl = localStorage.getItem('admin_server_url') || '{cf_worker_url}';"
        )
        content = content.replace(
            "placeholder=\"مثال: http://localhost:5000 أو اتركه فارغاً للوضع المباشر\"",
            f"placeholder=\"مثال: {cf_worker_url} أو Vercel أو Localhost\""
        )

        with open(a_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Optimized Cloudflare settings in {a_path}")

# Update static/main.js and dist/static/main.js
js_files = ['static/main.js', 'dist/static/main.js']

smart_cf_ping = f"""    // Smart Search Ping for Cloudflare, Vercel & Local Logging
    try {{
        let pingUrl = '/api/search_ping';
        if (window.location.hostname.includes('github.io') || window.location.hostname.includes('pages.dev')) {{
            pingUrl = localStorage.getItem('admin_server_url') || '{cf_worker_url}/api/search_ping';
        }}
        fetch(`${{pingUrl}}?q=${{encodeURIComponent(query)}}&mode=${{searchMode}}&_t=${{Date.now()}}`).catch(() => {{}});
    }} catch(e) {{}}"""

for js_path in js_files:
    if os.path.exists(js_path):
        with open(js_path, 'r', encoding='utf-8') as f:
            content = f.read()

        import re
        content = re.sub(r'// Smart Search Ping for Admin Logging[\s\S]*?\}\s*\} catch\(e\) \{\}', smart_cf_ping, content)

        with open(js_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Optimized Cloudflare ping tracking in {js_path}")

