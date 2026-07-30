import os
import re
import urllib.request

# 1. Force cache busting on main.js in all HTML files
html_files = ['index.html', 'analytics.html', 'predictions.html', 'admin.html',
              'dist/index.html', 'dist/analytics.html', 'dist/predictions.html', 'dist/admin.html']

for h_path in html_files:
    if os.path.exists(h_path):
        with open(h_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Update script tags to use ?v=2.0 cache buster
        content = content.replace('src="static/main.js"', 'src="static/main.js?v=2.0"')
        content = content.replace('src="static/main.js?v=1.0"', 'src="static/main.js?v=2.0"')
        
        with open(h_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated cache buster in {h_path}")

# 2. Trigger a live search ping directly to Flask to verify logging
try:
    url = "http://127.0.0.1:5000/api/search_ping?q=%D8%A7%D8%AE%D8%AA%D8%A8%D8%A7%D8%B1_%D8%A7%D9%84%D8%AA%D8%AD%D8%AF%D9%8A%D8%AB_%D8%A7%D9%84%D9%84%D8%AD%D8%B8%D9%8A&mode=name"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) TestBrowser/1.0'})
    with urllib.request.urlopen(req) as response:
        res_data = response.read().decode('utf-8')
        print("Live Search Ping Test Result:", res_data)
except Exception as e:
    print("Error sending test search ping:", e)
