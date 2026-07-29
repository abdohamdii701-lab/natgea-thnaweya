// Natega 2026 Interactive Script - Dual Static CDN & API Engine

document.addEventListener('DOMContentLoaded', () => {
    const searchForm = document.getElementById('searchForm');
    const searchInput = document.getElementById('searchInput');
    const clearBtn = document.getElementById('clearBtn');
    const submitBtn = document.getElementById('submitBtn');
    const themeToggle = document.getElementById('themeToggle');
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabTipText = document.getElementById('tabTipText');
    
    let currentMode = 'seating';

    // UI Elements
    const resultsSection = document.getElementById('resultsSection');
    const singleResult = document.getElementById('singleResult');
    const listResult = document.getElementById('listResult');
    const notFoundCard = document.getElementById('notFoundCard');
    
    // Student Single Card Elements
    const resName = document.getElementById('resName');
    const resSeatingNo = document.getElementById('resSeatingNo');
    const resTotal = document.getElementById('resTotal');
    const resPercent = document.getElementById('resPercent');
    const resProgressBar = document.getElementById('resProgressBar');
    const resGrade = document.getElementById('resGrade');
    const statusBadge = document.getElementById('statusBadge');
    
    // Load Stats and Top Students on launch
    fetchStats();
    fetchTopStudents('all');

    // Top Performers Track Tabs Switcher
    const topTabBtns = document.querySelectorAll('.top-tab-btn');
    topTabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            topTabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            fetchTopStudents(btn.dataset.track);
        });
    });

    // Tab Switch Handlers
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentMode = btn.dataset.mode;

            if (currentMode === 'seating') {
                searchInput.placeholder = 'أدخل رقم الجلوس (مثال: 2001970)...';
                tabTipText.innerHTML = '<i class="fa-solid fa-lightbulb"></i> يتم استعلام رقم الجلوس بدقة عالية وعرض بطاقة النتيجة فورياً.';
            } else {
                searchInput.placeholder = 'أدخل اسم الطالب ثلاثي أو رباعي (مثال: احمد محمود)...';
                tabTipText.innerHTML = '<i class="fa-solid fa-lightbulb"></i> يتيح البحث بالاسم استعراض جميع الأسماء المطابقة مع ترتيب المجموع بالدرجات.';
            }
            searchInput.focus();
        });
    });

    // Input handlers
    searchInput.addEventListener('input', () => {
        clearBtn.style.display = searchInput.value ? 'block' : 'none';
    });

    clearBtn.addEventListener('click', () => {
        searchInput.value = '';
        clearBtn.style.display = 'none';
        searchInput.focus();
        hideResults();
    });

    // Form Submit
    searchForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const query = searchInput.value.trim();
        if (query) {
            performSearch(query, currentMode);
        }
    });

    // Theme Toggle
    themeToggle.addEventListener('click', () => {
        document.body.classList.toggle('light-theme');
        const isLight = document.body.classList.contains('light-theme');
        themeToggle.innerHTML = isLight ? '<i class="fa-solid fa-sun"></i>' : '<i class="fa-solid fa-moon"></i>';
        localStorage.setItem('natega_theme', isLight ? 'light' : 'dark');
    });

    if (localStorage.getItem('natega_theme') === 'light') {
        document.body.classList.add('light-theme');
        themeToggle.innerHTML = '<i class="fa-solid fa-sun"></i>';
    }

    // Share Button Listener
    document.getElementById('shareBtn')?.addEventListener('click', shareResult);
});

// Arabic normalization helper in JS
function normalizeArabicJS(text) {
    if (!text) return "";
    let str = String(text);
    str = str.replace(/[\u0617-\u061A\u064B-\u0652]/g, '');
    str = str.replace(/[أإآٱ]/g, 'ا');
    str = str.replace(/ى/g, 'ي');
    str = str.replace(/ة/g, 'ه');
    str = str.replace(/ؤ/g, 'و');
    str = str.replace(/ئ/g, 'ي');
    return str.replace(/\s+/g, ' ').trim();
}

// Smart Hybrid Search Execution with Auto-Detecting CDN & API Fallback
async function performSearch(query, mode) {
    const submitBtn = document.getElementById('submitBtn');
    const btnText = submitBtn.querySelector('.btn-text');
    const spinner = submitBtn.querySelector('.spinner');

    btnText.style.display = 'none';
    spinner.style.display = 'inline-block';
    submitBtn.disabled = true;

    hideResults();
    resultsSection.style.display = 'block';

    // Smart Auto-Detect Query Type (Seating vs Name)
    const isNumeric = /^\d+$/.test(query);
    const searchMode = isNumeric ? 'seating' : 'name';

    // 1. Static CDN Seating Search
    if (searchMode === 'seating') {
        const seatingNo = query;
        const chunkKey = Math.floor(parseInt(seatingNo) / 5000) * 5000;
        try {
            const res = await fetch(`static/data/seating/${chunkKey}.json`);
            if (res.ok) {
                const chunkData = await res.json();
                if (chunkData[seatingNo]) {
                    const st = chunkData[seatingNo];
                    renderSingleStudent({
                        seating_no: seatingNo,
                        arabic_name: st.n,
                        total_degree: st.d,
                        student_case_desc: st.c,
                        percentage: st.p,
                        branch_name: st.b,
                        subjects: st.subj || {},
                        branch_rank: st.brk,
                        branch_total: st.btot
                    });
                    finishSearch(submitBtn, btnText, spinner);
                    return;
                }
            }
        } catch (e) {
            console.log('Static CDN seating fetch fallback to API');
        }
    }

    // 2. Static CDN Tokenized Name Search (URL Encoded Prefix, Sorted Highest Score First)
    if (searchMode === 'name') {
        const normQuery = normalizeArabicJS(query);
        const tokens = normQuery.split(' ').filter(t => t);
        if (tokens.length > 0) {
            const firstWord = tokens[0];
            const prefix = (firstWord.startsWith('مح') && firstWord.length >= 3) ? firstWord.substring(0, 3) : (firstWord.length >= 2 ? firstWord.substring(0, 2) : (firstWord.substring(0, 1) || "ot"));
            
            try {
                let res = await fetch(`static/data/names/${encodeURIComponent(prefix)}.json`);
                if (!res.ok) {
                    res = await fetch(`static/data/names/${prefix}.json`);
                }

                if (res.ok) {
                    const nameList = await res.json();
                    const matches = nameList.filter(st => {
                        const normStName = st.nn || normalizeArabicJS(st.n);
                        const rawStName = st.n;
                        return tokens.every(token => {
                            const normToken = normalizeArabicJS(token);
                            const altToken = token.endsWith('ه') ? token.slice(0, -1) + 'ة' : (token.endsWith('ة') ? token.slice(0, -1) + 'ه' : token);
                            return normStName.includes(normToken) || rawStName.includes(token) || rawStName.includes(altToken);
                        });
                    }).sort((a, b) => b.d - a.d).slice(0, 30);

                    if (matches.length > 0) {
                        const formatted = matches.map(st => ({
                            seating_no: st.s,
                            arabic_name: st.n,
                            total_degree: st.d,
                            student_case_desc: st.c,
                            percentage: st.p,
                            branch_name: st.b,
                            subjects: st.subj || {},
                            branch_rank: st.brk,
                            branch_total: st.btot
                        }));
                        if (formatted.length === 1) {
                            renderSingleStudent(formatted[0]);
                        } else {
                            renderStudentList(formatted);
                        }
                        finishSearch(submitBtn, btnText, spinner);
                        return;
                    }
                }
            } catch (e) {
                console.log('Static CDN name fetch fallback to API');
            }
        }
    }

    // 3. Dynamic API Server Fallback
    try {
        const response = await fetch(`/api/search?mode=${searchMode}&q=${encodeURIComponent(query)}`);
        const result = await response.json();

        if (result.type === 'single' && result.data) {
            renderSingleStudent(result.data);
        } else if (result.type === 'list' && result.data && result.data.length > 0) {
            renderStudentList(result.data);
        } else {
            showNotFound(result.message || `لم نتمكن من العثور على أية نتائج مطابقة للبحث: "${query}"`);
        }
    } catch (err) {
        showNotFound(`لم نتمكن من العثور على أية نتائج مطابقة للبحث: "${query}"`);
    } finally {
        finishSearch(submitBtn, btnText, spinner);
    }
}

function finishSearch(submitBtn, btnText, spinner) {
    btnText.style.display = 'inline';
    spinner.style.display = 'none';
    submitBtn.disabled = false;
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Render Single Student Result
function renderSingleStudent(student) {
    document.getElementById('singleResult').style.display = 'block';

    resName.textContent = student.arabic_name;
    resSeatingNo.textContent = student.seating_no;
    resTotal.textContent = student.total_degree;
    resPercent.textContent = `${student.percentage}%`;
    resProgressBar.style.width = `${Math.min(student.percentage, 100)}%`;

    const officialStatus = student.student_case_desc || (student.total_degree >= 160 ? 'ناجح دور أول' : 'له دور ثاني');
    const branchName = student.branch_name || student.b || '';
    
    statusBadge.textContent = branchName ? `${officialStatus} • ${branchName}` : officialStatus;

    if (officialStatus.includes('ناجح')) {
        statusBadge.style.background = 'rgba(16, 185, 129, 0.2)';
        statusBadge.style.color = '#10b981';
        statusBadge.style.borderColor = '#10b981';
    } else if (officialStatus.includes('غياب')) {
        statusBadge.style.background = 'rgba(100, 116, 139, 0.2)';
        statusBadge.style.color = '#94a3b8';
        statusBadge.style.borderColor = '#94a3b8';
    } else {
        statusBadge.style.background = 'rgba(239, 68, 68, 0.2)';
        statusBadge.style.color = '#ef4444';
        statusBadge.style.borderColor = '#ef4444';
    }

    const percent = student.percentage;
    let gradeText = 'مقبول';

    if (officialStatus.includes('ناجح') && student.total_degree === 0) {
        gradeText = 'ناجح / معفى من المجموع';
    } else if (percent >= 85) {
        gradeText = 'ممتاز 🌟';
    } else if (percent >= 75) {
        gradeText = 'جيد جداً ✨';
    } else if (percent >= 65) {
        gradeText = 'جيد 👍';
    } else if (percent >= 50) {
        gradeText = 'مقبول';
    } else {
        gradeText = 'دور ثاني / غير مستكمل';
    }

    resGrade.textContent = gradeText;

    // Render Subjects Breakdown Table
    renderSubjectBreakdownTable(student);

    // Render Branch Rank & Bell Curve Visualization
    renderBranchRankAndBellCurve(student);

    // Render Tansiq Predictor & Probability Engine
    renderTansiqPredictor(student);

    if (percent >= 75 && typeof confetti === 'function') {
        confetti({
            particleCount: 100,
            spread: 70,
            origin: { y: 0.6 }
        });
    }
}

// Subject Max Score Definition Dictionary
const SUBJECT_CONFIG = [
    { key: 'arabic_deg', name: 'اللغة العربية', max: 80 },
    { key: 'english_deg', name: 'اللغة الأجنبية الأولى', max: 60 },
    { key: 'second_lang_deg', name: 'اللغة الأجنبية الثانية', max: 40 },
    { key: 'physics_deg', name: 'الفيزياء', max: 60 },
    { key: 'chemistry_deg', name: 'الكيمياء', max: 60 },
    { key: 'biology_deg', name: 'الأحياء', max: 60 },
    { key: 'geology_deg', name: 'الجيولوجيا والعلوم البيئية', max: 60 },
    { key: 'math1_deg', name: 'الرياضيات البحتة', max: 60 },
    { key: 'math2_deg', name: 'الرياضيات التطبيقية', max: 60 },
    { key: 'history_deg', name: 'التاريخ', max: 60 },
    { key: 'geography_deg', name: 'الجغرافيا', max: 60 },
    { key: 'philosophy_deg', name: 'الفلسفة والمنطق', max: 60 },
    { key: 'psychology_deg', name: 'علم النفس والاجتماع', max: 60 }
];

function renderSubjectBreakdownTable(student) {
    const container = document.getElementById('subjectBreakdownContainer');
    const tbody = document.getElementById('subjectTableBody');
    tbody.innerHTML = '';

    const subjData = student.subjects || student;
    const branchName = student.branch_name || student.b || 'عام';
    const branchTotal = student.branch_total || (branchName.includes('علوم') ? 350000 : (branchName.includes('رياضة') ? 120000 : 410000));
    const nationwideTotal = 919396;

    let hasSubj = false;

    SUBJECT_CONFIG.forEach(cfg => {
        const val = subjData[cfg.key];
        if (val !== undefined && val !== null) {
            hasSubj = true;
            const numVal = parseFloat(val);
            const subjPercentRatio = numVal / cfg.max;
            const subjPercent = (subjPercentRatio * 100).toFixed(1);
            
            // Calculate statistical subject ranks if explicit ranks are absent
            const pRatio = Math.max(0, 1 - subjPercentRatio);
            const branchSubjRank = subjData[`${cfg.key}_brk`] || Math.max(1, Math.round(Math.pow(pRatio, 1.5) * branchTotal * 0.65));
            const nationSubjRank = subjData[`${cfg.key}_nat`] || Math.max(1, Math.round(Math.pow(pRatio, 1.5) * nationwideTotal * 0.65));

            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><strong>${cfg.name}</strong></td>
                <td><span class="subj-score-badge">${numVal}</span></td>
                <td>${cfg.max}</td>
                <td><strong style="color: var(--primary);">${subjPercent}%</strong></td>
                <td><span class="rank-badge-pill branch-pill"><i class="fa-solid fa-ranking-star"></i> #${branchSubjRank.toLocaleString('ar-EG')}</span></td>
                <td><span class="rank-badge-pill nation-pill"><i class="fa-solid fa-earth-africa"></i> #${nationSubjRank.toLocaleString('ar-EG')}</span></td>
            `;
            tbody.appendChild(tr);
        }
    });

    container.style.display = hasSubj ? 'block' : 'none';
}

// Render Branch Ranking & Interactive Bell Curve Chart
function renderBranchRankAndBellCurve(student) {
    const container = document.getElementById('analyticsSection');
    const rankEl = document.getElementById('resBranchRank');
    const countEl = document.getElementById('resBranchTotalCount');
    const pctTextEl = document.getElementById('resPercentileText');
    const pctDescEl = document.getElementById('resPercentileDesc');

    container.style.display = 'block';

    const branchName = student.branch_name || student.b || 'عام';
    const totalScore = parseFloat(student.total_degree) || 0;
    const pct = parseFloat(student.percentage) || 0;

    // Estimate or load branch rank
    let branchTotal = student.branch_total || (branchName.includes('علوم') ? 350000 : (branchName.includes('رياضة') ? 120000 : 410000));
    let estimatedRank = student.branch_rank;

    if (!estimatedRank) {
        // Calculate statistical rank based on normal distribution CDF percentile
        const percentileRank = (100 - pct) / 100;
        estimatedRank = Math.max(1, Math.round(percentileRank * branchTotal * 0.85));
    }

    rankEl.textContent = `المركز #${estimatedRank.toLocaleString('ar-EG')}`;
    countEl.textContent = `من أصل ${branchTotal.toLocaleString('ar-EG')} طالب في شعبة ${branchName}`;

    // Top Percentile Calculation (e.g. "أنت من أعلى 4.5% في الشعبة")
    const topPercentile = Math.max(0.1, ((estimatedRank / branchTotal) * 100)).toFixed(1);
    pctTextEl.textContent = `من أعلى ${topPercentile}% في الجمهورية`;

    if (topPercentile <= 5) {
        pctDescEl.textContent = 'أداء أسطوري ينتمي إلى قائمة الصفوة والأوائل 🏆';
    } else if (topPercentile <= 15) {
        pctDescEl.textContent = 'أداء ممتاز جداً أعلى بكثير من متوسط الشعبة 🌟';
    } else if (topPercentile <= 30) {
        pctDescEl.textContent = 'أداء جيد جداً أعلى من متوسط الشعبة 👍';
    } else {
        pctDescEl.textContent = 'أداء متكافئ ضمن نطاق متوسط الشعبة';
    }

    // Draw Bell Curve Canvas
    drawBellCurve(pct);
}

// Draw Bell Curve Canvas Chart
function drawBellCurve(studentPercent) {
    const canvas = document.getElementById('bellCurveCanvas');
    if (!canvas || !canvas.getContext) return;

    const ctx = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;

    ctx.clearRect(0, 0, w, h);

    const padding = 30;
    const chartW = w - padding * 2;
    const chartH = h - padding * 2;
    const baseline = h - padding;

    // Normal Distribution formula (Mean = 62.5%, StdDev = 15%)
    const mean = 62.5;
    const stdDev = 15;

    function gaussian(x) {
        return Math.exp(-0.5 * Math.pow((x - mean) / stdDev, 2));
    }

    // Draw Grid Lines & X-Axis
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
    ctx.lineWidth = 1;

    ctx.beginPath();
    ctx.moveTo(padding, baseline);
    ctx.lineTo(w - padding, baseline);
    ctx.stroke();

    // Draw Curve Fill Gradient
    const grad = ctx.createLinearGradient(0, padding, 0, baseline);
    grad.addColorStop(0, 'rgba(99, 102, 241, 0.4)');
    grad.addColorStop(1, 'rgba(99, 102, 241, 0.0)');

    ctx.beginPath();
    ctx.moveTo(padding, baseline);

    for (let px = 0; px <= chartW; px += 2) {
        const percentX = (px / chartW) * 100;
        const yVal = gaussian(percentX);
        const py = baseline - (yVal * (chartH - 20));
        ctx.lineTo(padding + px, py);
    }

    ctx.lineTo(w - padding, baseline);
    ctx.closePath();
    ctx.fillStyle = grad;
    ctx.fill();

    // Draw Curve Line
    ctx.strokeStyle = '#6366f1';
    ctx.lineWidth = 3;
    ctx.beginPath();

    for (let px = 0; px <= chartW; px += 2) {
        const percentX = (px / chartW) * 100;
        const yVal = gaussian(percentX);
        const py = baseline - (yVal * (chartH - 20));
        if (px === 0) ctx.moveTo(padding + px, py);
        else ctx.lineTo(padding + px, py);
    }
    ctx.stroke();

    // Plot Student Highlight Dot
    const studentPx = (Math.min(100, Math.max(0, studentPercent)) / 100) * chartW;
    const studentYVal = gaussian(studentPercent);
    const studentPy = baseline - (studentYVal * (chartH - 20));

    // Vertical dashed line to student position
    ctx.setLineDash([4, 4]);
    ctx.strokeStyle = '#10b981';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(padding + studentPx, baseline);
    ctx.lineTo(padding + studentPx, studentPy);
    ctx.stroke();
    ctx.setLineDash([]);

    # Outer Glowing Dot
    ctx.beginPath();
    ctx.arc(padding + studentPx, studentPy, 10, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(16, 185, 129, 0.3)';
    ctx.fill();

    // Inner Glowing Dot
    ctx.beginPath();
    ctx.arc(padding + studentPx, studentPy, 5, 0, Math.PI * 2);
    ctx.fillStyle = '#10b981';
    ctx.fill();

    // Student Score Tooltip Bubble above dot
    ctx.fillStyle = '#10b981';
    ctx.font = 'bold 12px Cairo, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(`${studentPercent}% (موقعك)`, padding + studentPx, studentPy - 14);
}

// Fetch Top Performers with Static CDN Fallback and Branch Separation
async function fetchTopStudents(trackMode = 'all') {
    const topGrid = document.getElementById('topGrid');
    topGrid.innerHTML = '<div style="grid-column: 1/-1; text-align:center; padding: 20px; color:var(--text-muted);"><i class="fa-solid fa-spinner fa-spin"></i> جاري تحميل أوائل الشعبة...</div>';

    let fileMap = {
        'all': 'static/data/top.json',
        'science_bio': 'static/data/top_science_bio.json',
        'science_math': 'static/data/top_science_math.json',
        'literary': 'static/data/top_literary.json'
    };

    let targetFile = fileMap[trackMode] || 'static/data/top.json';

    try {
        let result = null;
        try {
            const staticRes = await fetch(targetFile);
            if (staticRes.ok) {
                result = await staticRes.json();
            }
        } catch (err) {
            console.log('Static top fetch fallback');
        }

        if (!result) {
            const apiRes = await fetch(`/api/top?track=${trackMode}`);
            if (apiRes.ok) {
                result = await apiRes.json();
            }
        }

        if (result && (result.data || Array.isArray(result))) {
            const list = result.data || result;
            topGrid.innerHTML = '';
            list.forEach((st, idx) => {
                const card = document.createElement('div');
                card.className = 'top-card';
                card.onclick = () => selectStudent(st.seating_no);
                const bName = st.branch_name || st.b || '';
                card.innerHTML = `
                    <div class="rank-badge">${idx + 1}</div>
                    <div class="top-info">
                        <h4>${st.arabic_name || st.n}</h4>
                        <p>رقم الجلوس: ${st.seating_no || st.s} ${bName ? '• ' + bName : ''}</p>
                    </div>
                    <div class="top-score">${st.total_degree || st.d} <small style="font-size:12px; color:var(--text-muted);">(${st.percentage || st.p}%)</small></div>
                `;
                topGrid.appendChild(card);
            });
        } else {
            topGrid.innerHTML = '<div style="grid-column: 1/-1; text-align:center; padding: 20px; color:var(--text-muted);">سيتم إعلان القائمة الرسمية للأوائل فور اعتمادها رسمياً.</div>';
        }
    } catch (e) {
        console.error('Failed to load top students', e);
        topGrid.innerHTML = '<div style="grid-column: 1/-1; text-align:center; padding: 20px; color:var(--text-muted);">سيتم إعلان القائمة الرسمية للأوائل فور اعتمادها رسمياً.</div>';
    }
}


// Tansiq Predictor & Probability Engine Renderer
let cachedTansiqData = null;

async function renderTansiqPredictor(student) {
    const container = document.getElementById('tansiqPredictorContainer');
    const grid = document.getElementById('tansiqGrid');
    grid.innerHTML = '';

    const stPct = parseFloat(student.percentage) || 0;
    const branchName = student.branch_name || student.b || '';

    // Determine target track for Tansiq
    let targetTrack = 'science_bio';
    if (branchName.includes('رياض')) {
        targetTrack = 'science_math';
    } else if (branchName.includes('أدب') || branchName.includes('ادب')) {
        targetTrack = 'literary';
    }

    try {
        if (!cachedTansiqData) {
            const res = await fetch('static/data/tansiq.json');
            if (res.ok) {
                cachedTansiqData = await res.json();
            }
        }

        if (cachedTansiqData && cachedTansiqData.sectors) {
            const trackSectors = cachedTansiqData.sectors.filter(s => s.track === targetTrack);

            if (trackSectors.length > 0) {
                container.style.display = 'block';

                trackSectors.forEach(sec => {
                    // Probability calculation algorithm
                    let prob = 50;
                    let probLabel = '🟡 فرصة محتملة';
                    let badgeClass = 'prob-med';
                    let barColor = 'linear-gradient(90deg, #f59e0b, #eab308)';

                    if (stPct >= sec.max_pct) {
                        prob = Math.min(99, 95 + (stPct - sec.max_pct) * 2);
                        probLabel = '🟢 فرصة مؤكدة جداً';
                        badgeClass = 'prob-high';
                        barColor = 'linear-gradient(90deg, #10b981, #34d399)';
                    } else if (stPct >= sec.avg_pct) {
                        const ratio = (stPct - sec.avg_pct) / (sec.max_pct - sec.avg_pct || 1);
                        prob = 80 + ratio * 15;
                        probLabel = '🟢 فرصة قوية جداً';
                        badgeClass = 'prob-high';
                        barColor = 'linear-gradient(90deg, #10b981, #34d399)';
                    } else if (stPct >= sec.min_pct - 1.5) {
                        const ratio = (stPct - (sec.min_pct - 1.5)) / (sec.avg_pct - (sec.min_pct - 1.5) || 1);
                        prob = 50 + ratio * 30;
                        probLabel = '🟡 فرصة محتملة';
                        badgeClass = 'prob-med';
                        barColor = 'linear-gradient(90deg, #f59e0b, #eab308)';
                    } else {
                        const ratio = Math.max(0, stPct / (sec.min_pct - 1.5 || 1));
                        prob = Math.max(10, Math.round(ratio * 45));
                        probLabel = '🔴 فرصة ضئيلة';
                        badgeClass = 'prob-low';
                        barColor = 'linear-gradient(90deg, #ef4444, #f87171)';
                    }

                    prob = Math.round(prob);

                    const card = document.createElement('div');
                    card.className = 'tansiq-card';
                    card.innerHTML = `
                        <div class="tcard-top">
                            <span class="tcard-name">${sec.name}</span>
                            <span class="prob-badge ${badgeClass}">${probLabel} (${prob}%)</span>
                        </div>
                        <div class="tcard-meta">
                            <span>متوسط التنسيق (آخر 3 سنوات): <strong>${sec.avg_pct}%</strong> | الحد الأدنى: <strong>${sec.min_pct}%</strong></span>
                        </div>
                        <div class="prob-bar-bg">
                            <div class="prob-bar-fill" style="width: ${prob}%; background: ${barColor};"></div>
                        </div>
                    `;
                    grid.appendChild(card);
                });
            } else {
                container.style.display = 'none';
            }
        }
    } catch (e) {
        console.error('Failed to render Tansiq predictor', e);
        container.style.display = 'none';
    }
}

// Share Result
function shareResult() {
    const name = resName.textContent;
    const seating = resSeatingNo.textContent;
    const score = resTotal.textContent;
    const percent = resPercent.textContent;

    const shareText = `🎓 نتيجة الثانوية العامة 2026 🎓\nاسم الطالب: ${name}\nرقم الجلوس: ${seating}\nالمجموع: ${score} من 320\nالنسبة المئوية: ${percent}`;

    if (navigator.share) {
        navigator.share({
            title: 'نتيجة الثانوية العامة 2026',
            text: shareText,
            url: window.location.href
        }).catch(() => {});
    } else {
        navigator.clipboard.writeText(shareText).then(() => {
            alert('تم نسخ تفاصيل النتيجة إلى الحافظة بنجاح!');
        });
    }
}
