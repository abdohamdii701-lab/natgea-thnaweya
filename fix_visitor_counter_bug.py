import os
import re
import json

BASE_OFFSET = 1542890

# Fix visits.json if exists
with open('visits.json', 'w', encoding='utf-8') as f:
    json.dump({'count': 1}, f)

# Bulletproof visitor counter script with NO race condition & always adding BASE_OFFSET
robust_counter_script = f"""
<script>
    // Bulletproof Real Visitor Counter
    (function() {{
        const BASE_OFFSET = {BASE_OFFSET};

        function setUI(count) {{
            const formatted = Number(count).toLocaleString('ar-EG');
            const update = () => {{
                document.querySelectorAll('.visit-count-val').forEach(el => {{
                    el.textContent = formatted;
                }});
            }};
            if (document.readyState === 'loading') {{
                document.addEventListener('DOMContentLoaded', update);
            }} else {{
                update();
            }}
        }}

        async function initCounter() {{
            let deltaCount = 0;

            // 1. Try local Flask backend API
            try {{
                const res = await fetch('/api/visitor_count');
                if (res.ok) {{
                    const data = await res.json();
                    if (data && typeof data.count === 'number') {{
                        deltaCount = data.count;
                    }}
                }}
            }} catch (e) {{}}

            // 2. If online static host (Cloudflare/Vercel), try real public CounterAPI
            if (!deltaCount) {{
                try {{
                    const res = await fetch('https://api.counterapi.dev/v1/natgea-thnaweya-2026-egypt/visits/up');
                    if (res.ok) {{
                        const data = await res.json();
                        if (data && typeof data.count === 'number') {{
                            deltaCount = data.count;
                        }}
                    }}
                }} catch (e) {{}}
            }}

            // 3. Fallback to LocalStorage tracking
            if (!deltaCount) {{
                let localDelta = parseInt(localStorage.getItem('real_visit_delta') || "1");
                if (!sessionStorage.getItem('session_visited_flag')) {{
                    localDelta += 1;
                    localStorage.setItem('real_visit_delta', localDelta.toString());
                    sessionStorage.setItem('session_visited_flag', 'true');
                }}
                deltaCount = localDelta;
            }}

            const finalCount = BASE_OFFSET + deltaCount;
            setUI(finalCount);
        }}

        // Set initial baseline immediately
        setUI(BASE_OFFSET + 1);
        initCounter();
    }})();
</script>
"""

files = ['index.html', 'analytics.html', 'predictions.html', 'dist/index.html', 'dist/analytics.html', 'dist/predictions.html']

for f_path in files:
    if os.path.exists(f_path):
        with open(f_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Fix static HTML fallback from 1 to 1,542,891
        content = content.replace('1,284,950', '١,٥٤٢,٨٩١')
        content = content.replace('>1<', '>١,٥٤٢,٨٩١<')

        # Replace counter script
        content = re.sub(r'<script>\s*// Real Live Visitor Counter[\s\S]*?</script>', robust_counter_script, content)
        content = re.sub(r'<script>\s*// Bulletproof Real Visitor Counter[\s\S]*?</script>', robust_counter_script, content)
        content = re.sub(r'<script>\s*// 100% Real Live Visitor Counter[\s\S]*?</script>', robust_counter_script, content)
        content = re.sub(r'<script>\s*// Live Visitor Counter Logic[\s\S]*?</script>', robust_counter_script, content)

        with open(f_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed visitor counter script in {f_path}")

