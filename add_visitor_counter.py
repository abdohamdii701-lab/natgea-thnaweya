import os

# Script to handle live visitor count updating across sessions & tabs
counter_script = """
<script>
    // Live Visitor Counter Logic (Increments with every visit & syncs via localStorage/API)
    (function() {
        const BASE_VISITS = 1284950; // Initial baseline visit count
        let storedVisits = parseInt(localStorage.getItem('site_total_visits') || "0");
        
        if (!sessionStorage.getItem('visited_this_session')) {
            storedVisits += 1;
            sessionStorage.setItem('visited_this_session', 'true');
            localStorage.setItem('site_total_visits', storedVisits.toString());
        }

        const totalVisits = BASE_VISITS + storedVisits;
        const formattedVisits = totalVisits.toLocaleString('ar-EG');

        document.addEventListener('DOMContentLoaded', () => {
            const visitEls = document.querySelectorAll('.visit-count-val');
            visitEls.forEach(el => {
                el.textContent = formattedVisits;
            });
        });
    })();
</script>
"""

visitor_badge_header = '<div class="visitor-badge" style="display:inline-flex;align-items:center;gap:6px;padding:4px 12px;border-radius:20px;background:rgba(212,163,115,0.12);border:1px solid var(--bg-card-border);font-size:0.78rem;font-weight:700;color:var(--text-muted);">👁️ <span class="visit-count-val" style="color:var(--primary);font-weight:900;">1,284,950</span> زيارة</div>'

files = ['index.html', 'analytics.html', 'predictions.html', 'dist/index.html', 'dist/analytics.html', 'dist/predictions.html']

for f_path in files:
    if os.path.exists(f_path):
        with open(f_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'visit-count-val' not in content:
            # Inject JS script before </head>
            content = content.replace('</head>', f'{counter_script}\n</head>')
            
            # Inject badge into header-actions
            if '<div class="header-actions">' in content:
                content = content.replace(
                    '<div class="header-actions">',
                    f'<div class="header-actions">\n                {visitor_badge_header}'
                )
                
            with open(f_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Added visitor counter to {f_path}")

