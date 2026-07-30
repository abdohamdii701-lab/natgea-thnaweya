import os

admin_html_updated = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>لوحة إدارية وسجل البحث المباشر | Admin Dashboard</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800;900&family=Outfit:wght@400;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="static/style.css">

    <style>
        .admin-main { padding-bottom: 4rem; }
        
        .admin-hero {
            padding: 2rem 0 1rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 1rem;
        }

        .admin-title {
            display: flex;
            align-items: center;
            gap: 0.8rem;
        }
        .admin-title h2 { font-size: 1.6rem; font-weight: 900; }

        .auth-card {
            max-width: 480px;
            margin: 3rem auto;
            background: var(--bg-card);
            border: 1px solid var(--bg-card-border);
            backdrop-filter: var(--glass-blur);
            border-radius: var(--radius-lg);
            padding: 2rem;
            text-align: center;
            box-shadow: var(--shadow-subtle);
        }
        .auth-card h3 { font-size: 1.3rem; font-weight: 800; margin-bottom: 0.6rem; }
        .auth-card p { font-size: 0.85rem; color: var(--text-muted); margin-bottom: 1.5rem; }

        /* Server Notice Banner */
        .server-notice {
            margin-top: 1rem;
            padding: 0.9rem;
            border-radius: var(--radius-md);
            background: rgba(245, 158, 11, 0.12);
            border: 1px solid rgba(245, 158, 11, 0.3);
            color: var(--gold);
            font-size: 0.82rem;
            text-align: right;
            line-height: 1.5;
        }

        /* Overview Grid */
        .admin-stats-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1rem;
            margin-bottom: 2rem;
        }
        @media (max-width: 800px) { .admin-stats-grid { grid-template-columns: repeat(2, 1fr); } }

        .admin-stat-card {
            background: var(--bg-card);
            border: 1px solid var(--bg-card-border);
            backdrop-filter: var(--glass-blur);
            border-radius: var(--radius-md);
            padding: 1.2rem;
            box-shadow: var(--shadow-subtle);
        }
        .admin-stat-card .val { font-size: 1.8rem; font-weight: 900; color: var(--primary); margin-top: 0.2rem; }
        .admin-stat-card .lbl { font-size: 0.8rem; color: var(--text-muted); }

        /* Tables */
        .admin-section {
            background: var(--bg-card);
            border: 1px solid var(--bg-card-border);
            backdrop-filter: var(--glass-blur);
            border-radius: var(--radius-lg);
            padding: 1.5rem;
            margin-bottom: 2rem;
            box-shadow: var(--shadow-subtle);
        }
        .admin-section-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 1.2rem;
            flex-wrap: wrap;
            gap: 0.8rem;
        }
        .admin-section-title { font-size: 1.1rem; font-weight: 800; display: flex; align-items: center; gap: 8px; }

        .logs-table {
            width: 100%;
            border-collapse: collapse;
            text-align: right;
        }
        .logs-table th {
            background: rgba(0,0,0,0.25);
            padding: 12px 14px;
            font-size: 0.82rem;
            font-weight: 800;
            color: var(--text-muted);
            border-bottom: 1px solid var(--bg-card-border);
        }
        .logs-table td {
            padding: 12px 14px;
            font-size: 0.88rem;
            border-bottom: 1px solid rgba(255,255,255,0.04);
            color: var(--text-main);
        }
        .logs-table tr:hover { background: rgba(255,255,255,0.03); }

        .ip-badge {
            font-family: var(--font-numeric);
            font-size: 0.82rem;
            font-weight: 800;
            padding: 3px 8px;
            border-radius: 6px;
            background: rgba(6, 182, 212, 0.15);
            color: var(--blue);
            border: 1px solid rgba(6, 182, 212, 0.3);
            direction: ltr;
            display: inline-block;
        }
        .query-badge {
            font-weight: 800;
            color: var(--gold);
        }

        .refresh-btn {
            padding: 6px 14px;
            border-radius: 20px;
            border: 1px solid var(--bg-card-border);
            background: var(--bg-card);
            color: var(--primary);
            font-size: 0.8rem;
            font-weight: 700;
            cursor: pointer;
            transition: var(--transition);
        }
        .refresh-btn:hover { background: rgba(212,163,115,0.15); }

        body { background-color: var(--bg-dark); }
    </style>
</head>
<body class="light-theme">
    <div class="glow-bg">
        <div class="blob blob-1"></div>
        <div class="blob blob-2"></div>
        <div class="blob blob-3"></div>
    </div>

    <!-- Header Navigation -->
    <header class="main-header">
        <div class="container header-content">
            <div class="logo">
                <div class="logo-icon">🔒</div>
                <div class="logo-text">
                    <h1>لوحة الإدارة <span>Admin</span></h1>
                    <p class="subtitle">سجل البحث المباشر ومراقبة الزوار</p>
                </div>
            </div>
            <div class="header-actions">
                <button id="themeToggle" class="icon-btn" title="تبديل المظهر">🌙</button>
                <a href="index.html" class="btn btn-outline" style="font-size:0.85rem;">🔍 العودة للموقع</a>
            </div>
        </div>
    </header>

    <main class="container admin-main">

        <!-- Password Auth Section -->
        <div id="authSection" class="auth-card">
            <div style="font-size:3rem; margin-bottom:0.5rem;">🔐</div>
            <h3>تسجيل دخول لوحة الإدارة</h3>
            <p>أدخل كلمة سر الإدارة للوصول لسجل عمليات البحث وعناوين الـ IP للزوار</p>

            <form id="authForm" style="display:flex; flex-direction:column; gap:1rem;">
                <div>
                    <label style="display:block; font-size:0.8rem; text-align:right; color:var(--text-muted); margin-bottom:4px; font-weight:700;">كلمة سر الإدارة (Default: admin123)</label>
                    <input type="password" id="adminKeyInput" class="styled-input" placeholder="أدخل كلمة السر (admin123)..." required autofocus>
                </div>

                <div>
                    <label style="display:block; font-size:0.8rem; text-align:right; color:var(--text-muted); margin-bottom:4px; font-weight:700;">رابط سيرفر البايثون (اتركه كما هو إذا كنت تعمل محلياً)</label>
                    <input type="text" id="serverUrlInput" class="styled-input" placeholder="مثال: http://localhost:5000 أو رابط Render/Vercel">
                </div>

                <button type="submit" class="btn btn-primary" style="justify-content:center;">🔓 دخول اللوحة</button>
            </form>

            <div id="githubPagesNotice" class="server-notice" style="display: none;">
                💡 <strong>ملاحظة هامة (GitHub Pages):</strong> استضافة GitHub Pages تقوم باستضافة ملفات التصميم فقط ولا تملك سيرفر بايثون لملف <code>app.py</code>.<br>
                • للوصول للوحة على جهازك: افتح الرابط المحلـي <a href="http://localhost:5000/admin.html" target="_blank" style="color:var(--primary); font-weight:800;">http://localhost:5000/admin.html</a>.<br>
                • أو أدخل رابط سيرفر البايثون الخاص بك في الخانة أعلاه.
            </div>
        </div>

        <!-- Dashboard Content Section -->
        <div id="dashboardSection" style="display: none;">
            <div class="admin-hero">
                <div class="admin-title">
                    <span style="font-size:2rem;">📊</span>
                    <div>
                        <h2>مراقبة عمليات البحث المباشرة</h2>
                        <p style="font-size:0.85rem; color:var(--text-muted);">سجل لحظي بالـ IP والأسماء المبحوث عنها وأوقات الزيارة</p>
                    </div>
                </div>
                <div style="display:flex; gap:0.5rem; align-items:center;">
                    <button id="autoRefreshBtn" class="refresh-btn">🔄 تحديث تلقائي: مفعّل (5ث)</button>
                    <button id="manualRefreshBtn" class="refresh-btn">⚡ تحديث الآن</button>
                </div>
            </div>

            <!-- Stats Overview Grid -->
            <div class="admin-stats-grid">
                <div class="admin-stat-card">
                    <div class="lbl">🔍 إجمالي عمليات البحث الموثقة</div>
                    <div class="val" id="statTotalSearches">0</div>
                </div>
                <div class="admin-stat-card">
                    <div class="lbl">🌐 عدد عناوين الـ IP الفريدة</div>
                    <div class="val" id="statUniqueIPs">0</div>
                </div>
                <div class="admin-stat-card">
                    <div class="lbl">⚡ عمليات البحث اليوم</div>
                    <div class="val" id="statTodaySearches">0</div>
                </div>
                <div class="admin-stat-card">
                    <div class="lbl">🏆 أكثر الاستعلامات تكراراً</div>
                    <div class="val" id="statTopQuery">—</div>
                </div>
            </div>

            <!-- Top Searched Queries -->
            <div class="admin-section">
                <div class="admin-section-header">
                    <div class="admin-section-title">🔥 الأكثر بحثاً واستعلاماً على الموقع</div>
                </div>
                <div class="table-responsive">
                    <table class="logs-table">
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>نص / رقم البحث</th>
                                <th>عدد مرات الاستعلام</th>
                                <th>آخر استعلام</th>
                            </tr>
                        </thead>
                        <tbody id="topQueriesBody">
                            <!-- Populated by JS -->
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Live Search Logs Feed -->
            <div class="admin-section">
                <div class="admin-section-header">
                    <div class="admin-section-title">📋 السجل اللحظي المباشر لعمليات البحث (Live Feed)</div>
                    <span style="font-size:0.8rem; color:var(--text-muted);">عرض أحدث 100 عملية بحث</span>
                </div>

                <div class="table-responsive">
                    <table class="logs-table">
                        <thead>
                            <tr>
                                <th>الوقت والتاريخ</th>
                                <th>عنوان الـ IP الخاص بالزائر</th>
                                <th>نص البحث (الاسم / رقم الجلوس)</th>
                                <th>نمط البحث</th>
                                <th>الجهاز / المتصفح</th>
                            </tr>
                        </thead>
                        <tbody id="liveLogsBody">
                            <!-- Populated by JS -->
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

    </main>

    <script>
        let adminKey = localStorage.getItem('admin_secret_key') || '';
        let serverUrl = localStorage.getItem('admin_server_url') || '';
        let autoRefreshInterval = null;
        let isAutoRefresh = true;

        // Auto detect GitHub Pages
        if (window.location.hostname.includes('github.io')) {
            document.getElementById('githubPagesNotice').style.display = 'block';
            if (!serverUrl) {
                serverUrl = 'http://localhost:5000'; // Default fallback for GitHub Pages users
            }
        }

        document.getElementById('adminKeyInput').value = adminKey;
        document.getElementById('serverUrlInput').value = serverUrl;

        // Theme toggle
        function applyTheme(dark) {
            document.body.classList.toggle('light-theme', !dark);
            document.getElementById('themeToggle').textContent = dark ? '☀️' : '🌙';
        }
        document.getElementById('themeToggle').addEventListener('click', () => {
            const isLight = document.body.classList.contains('light-theme');
            applyTheme(isLight);
            localStorage.setItem('theme', isLight ? 'dark' : 'light');
        });
        (function() {
            const saved = localStorage.getItem('theme');
            applyTheme(saved === 'dark');
        })();

        // Handle Auth Form
        document.getElementById('authForm').addEventListener('submit', (e) => {
            e.preventDefault();
            adminKey = document.getElementById('adminKeyInput').value.trim();
            serverUrl = document.getElementById('serverUrlInput').value.trim();
            
            localStorage.setItem('admin_secret_key', adminKey);
            localStorage.setItem('admin_server_url', serverUrl);

            fetchDashboardData();
        });

        if (adminKey) {
            fetchDashboardData();
        }

        async function fetchDashboardData() {
            let baseUrl = serverUrl.replace(/\/$/, '');
            let endpoint = `${baseUrl}/api/admin/logs?key=${encodeURIComponent(adminKey)}`;
            if (!baseUrl && !window.location.hostname.includes('github.io')) {
                endpoint = `/api/admin/logs?key=${encodeURIComponent(adminKey)}`;
            }

            try {
                const res = await fetch(endpoint);
                if (res.status === 401 || res.status === 403) {
                    document.getElementById('authSection').style.display = 'block';
                    document.getElementById('dashboardSection').style.display = 'none';
                    alert('كلمة السر غير صحيحة!');
                    return;
                }

                if (res.ok) {
                    const data = await res.json();
                    document.getElementById('authSection').style.display = 'none';
                    document.getElementById('dashboardSection').style.display = 'block';
                    renderDashboard(data);
                    
                    if (isAutoRefresh && !autoRefreshInterval) {
                        autoRefreshInterval = setInterval(fetchDashboardData, 5000);
                    }
                } else if (res.status === 404) {
                    document.getElementById('authSection').style.display = 'block';
                    document.getElementById('dashboardSection').style.display = 'none';
                    document.getElementById('githubPagesNotice').style.display = 'block';
                }
            } catch (e) {
                console.error("Dashboard fetch error", e);
                document.getElementById('authSection').style.display = 'block';
                document.getElementById('dashboardSection').style.display = 'none';
                document.getElementById('githubPagesNotice').style.display = 'block';
            }
        }

        function renderDashboard(data) {
            // Stats
            document.getElementById('statTotalSearches').textContent = (data.total_searches || 0).toLocaleString('ar-EG');
            document.getElementById('statUniqueIPs').textContent = (data.unique_ips || 0).toLocaleString('ar-EG');
            document.getElementById('statTodaySearches').textContent = (data.today_searches || 0).toLocaleString('ar-EG');
            document.getElementById('statTopQuery').textContent = data.top_query || '—';

            // Top Queries Table
            const topBody = document.getElementById('topQueriesBody');
            topBody.innerHTML = '';
            (data.top_queries || []).forEach((q, idx) => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${idx + 1}</td>
                    <td><span class="query-badge">${q.query}</span></td>
                    <td><strong>${q.count.toLocaleString('ar-EG')}</strong> مرة</td>
                    <td style="font-size:0.8rem; color:var(--text-muted);">${q.last_time || '—'}</td>
                `;
                topBody.appendChild(tr);
            });

            // Live Logs Table
            const liveBody = document.getElementById('liveLogsBody');
            liveBody.innerHTML = '';
            (data.logs || []).forEach(log => {
                const tr = document.createElement('tr');
                const modeText = log.mode === 'seating' ? '💳 رقم جلوس' : '👤 اسم طالب';

                tr.innerHTML = `
                    <td style="direction:ltr; text-align:right; font-family:var(--font-numeric); font-size:0.8rem;">${log.timestamp}</td>
                    <td><span class="ip-badge">${log.ip}</span></td>
                    <td><strong class="query-badge">${log.query}</strong></td>
                    <td><span style="font-size:0.78rem;">${modeText}</span></td>
                    <td style="font-size:0.75rem; color:var(--text-muted); max-width:250px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;" title="${log.user_agent}">${log.user_agent}</td>
                `;
                liveBody.appendChild(tr);
            });
        }

        document.getElementById('manualRefreshBtn').addEventListener('click', fetchDashboardData);
        document.getElementById('autoRefreshBtn').addEventListener('click', () => {
            isAutoRefresh = !isAutoRefresh;
            const btn = document.getElementById('autoRefreshBtn');
            if (isAutoRefresh) {
                btn.textContent = "🔄 تحديث تلقائي: مفعّل (5ث)";
                autoRefreshInterval = setInterval(fetchDashboardData, 5000);
            } else {
                btn.textContent = "⏸️ تحديث تلقائي: متوقف";
                clearInterval(autoRefreshInterval);
                autoRefreshInterval = null;
            }
        });
    </script>
</body>
</html>
"""

locations = ['admin.html', 'dist/admin.html']
for loc in locations:
    with open(loc, 'w', encoding='utf-8') as f:
        f.write(admin_html_updated)

print("Updated admin.html in root and dist with GitHub Pages handling.")
