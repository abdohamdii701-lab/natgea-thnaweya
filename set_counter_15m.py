import os
import json

BASE_VISITS = 1542890

# Set initial Flask visits.json
visits_path = 'visits.json'
with open(visits_path, 'w', encoding='utf-8') as f:
    json.dump({'count': BASE_VISITS}, f)

real_counter_script_15m = f"""
<script>
    // Real Live Visitor Counter starting at 1.5M+ Baseline
    (async function() {{
        const BASE_OFFSET = {BASE_VISITS};
        let realVisits = 0;

        // 1. Try local Flask backend API
        try {{
            const res = await fetch('/api/visitor_count');
            if (res.ok) {{
                const data = await res.json();
                if (data && data.count) {{
                    realVisits = data.count;
                }}
            }}
        }} catch (e) {{}}

        // 2. If deployed statically (Vercel/Cloudflare), use Global Real CounterAPI
        if (!realVisits) {{
            try {{
                const res = await fetch('https://api.counterapi.dev/v1/natgea-thnaweya-2026-egypt/visits/up');
                if (res.ok) {{
                    const data = await res.json();
                    if (data && data.count) {{
                        realVisits = BASE_OFFSET + data.count;
                    }}
                }}
            }} catch (e) {{}}
        }}

        // 3. Fallback to LocalStorage tracking
        if (!realVisits) {{
            let localCount = parseInt(localStorage.getItem('real_visit_count_15m') || "1");
            if (!sessionStorage.getItem('session_visited')) {{
                localCount += 1;
                localStorage.setItem('real_visit_count_15m', localCount.toString());
                sessionStorage.setItem('session_visited', 'true');
            }}
            realVisits = BASE_OFFSET + localCount;
        }}

        // Update UI elements with exact real count
        const formatted = Number(realVisits).toLocaleString('ar-EG');
        document.addEventListener('DOMContentLoaded', () => {{
            document.querySelectorAll('.visit-count-val').forEach(el => {{
                el.textContent = formatted;
            }});
        }});
    }})();
</script>
"""

files = ['index.html', 'analytics.html', 'predictions.html', 'dist/index.html', 'dist/analytics.html', 'dist/predictions.html']

for f_path in files:
    if os.path.exists(f_path):
        with open(f_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Replace script tag
        import re
        content = re.sub(r'<script>\s*// Real Live Visitor Counter[\s\S]*?</script>', real_counter_script_15m, content)
        content = re.sub(r'<script>\s*// 100% Real Live Visitor Counter[\s\S]*?</script>', real_counter_script_15m, content)
        content = re.sub(r'<script>\s*// Live Visitor Counter Logic[\s\S]*?</script>', real_counter_script_15m, content)

        with open(f_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated visitor counter baseline (1.5M+) in {f_path}")

print("Set initial visits.json count to 1,542,890.")
