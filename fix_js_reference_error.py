import os

js_files = ['static/main.js', 'dist/static/main.js']

for js_path in js_files:
    if os.path.exists(js_path):
        with open(js_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Fix ReferenceError by moving searchMode definition above fetch
        old_block = """    // Background Ping to Admin Dashboard Logging System
    try {
        fetch(`/api/search_ping?q=${encodeURIComponent(query)}&mode=${searchMode}`).catch(() => {});
    } catch(e) {}

    // Smart Auto-Detect Query Type (Seating vs Name)
    const isNumeric = /^\\d+$/.test(query);
    const searchMode = isNumeric ? 'seating' : 'name';"""

        new_block = """    // Smart Auto-Detect Query Type (Seating vs Name)
    const isNumeric = /^\\d+$/.test(query);
    const searchMode = isNumeric ? 'seating' : 'name';

    // Smart Search Ping for Admin Logging
    try {
        let pingUrl = '/api/search_ping';
        if (window.location.hostname.includes('github.io')) {
            pingUrl = 'http://localhost:5000/api/search_ping';
        }
        fetch(`${pingUrl}?q=${encodeURIComponent(query)}&mode=${searchMode}&_t=${Date.now()}`).catch(() => {});
    } catch(e) {}"""

        # Perform replacement
        if "fetch(`/api/search_ping?q=${encodeURIComponent(query)}&mode=${searchMode}`)" in content:
            # Replace lines 218 to 226
            lines = content.split('\n')
            new_lines = []
            skip = False
            for line in lines:
                if '// Background Ping to Admin Dashboard Logging System' in line:
                    skip = True
                    continue
                if skip and "const searchMode = isNumeric ? 'seating' : 'name';" in line:
                    skip = False
                    new_lines.append(new_block)
                    continue
                if not skip:
                    new_lines.append(line)
            content = '\n'.join(new_lines)
            with open(js_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Successfully fixed ReferenceError in {js_path}")

