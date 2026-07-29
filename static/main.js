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
    fetchTopStudents();

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

// Search Execution with Dual Static CDN & API Fallback
async function performSearch(query, mode) {
    const submitBtn = document.getElementById('submitBtn');
    const btnText = submitBtn.querySelector('.btn-text');
    const spinner = submitBtn.querySelector('.spinner');

    btnText.style.display = 'none';
    spinner.style.display = 'inline-block';
    submitBtn.disabled = true;

    hideResults();
    resultsSection.style.display = 'block';

    const isNumeric = /^\d+$/.test(query);

    // 1. Static CDN Seating Search (5,000 Range Chunks)
    if (isNumeric || mode === 'seating') {
        const seatingNo = query;
        if (/^\d+$/.test(seatingNo)) {
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
                            percentage: st.p
                        });
                        finishSearch(submitBtn, btnText, spinner);
                        return;
                    }
                }
            } catch (e) {
                console.log('Static CDN seating fetch fallback to API');
            }
        }
    }

    // 2. Static CDN Tokenized Name Search (2-Letter Prefix, Sorted Highest Score First)
    if (!isNumeric || mode === 'name') {
        const normQuery = normalizeArabicJS(query);
        const tokens = normQuery.split(' ').filter(t => t);
        if (tokens.length > 0) {
            const firstWord = tokens[0];
            const prefix = firstWord.length >= 2 ? firstWord.substring(0, 2) : (firstWord.substring(0, 1) || "ot");
            try {
                const res = await fetch(`static/data/names/${prefix}.json`);
                if (res.ok) {
                    const nameList = await res.json();
                    const matches = nameList.filter(st => {
                        const normStName = st.nn || normalizeArabicJS(st.n);
                        return tokens.every(token => {
                            const altToken = token.endsWith('ه') ? token.slice(0, -1) + 'ة' : (token.endsWith('ة') ? token.slice(0, -1) + 'ه' : token);
                            return normStName.includes(token) || st.n.includes(token) || st.n.includes(altToken);
                        });
                    }).sort((a, b) => b.d - a.d).slice(0, 30);

                    if (matches.length > 0) {
                        const formatted = matches.map(st => ({
                            seating_no: st.s,
                            arabic_name: st.n,
                            total_degree: st.d,
                            student_case_desc: st.c,
                            percentage: st.p
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
        const response = await fetch(`/api/search?mode=${mode}&q=${encodeURIComponent(query)}`);
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
    statusBadge.textContent = officialStatus;

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

    if (percent >= 75 && typeof confetti === 'function') {
        confetti({
            particleCount: 100,
            spread: 70,
            origin: { y: 0.6 }
        });
    }
}

// Render List Results for Name Query
function renderStudentList(students) {
    const listResult = document.getElementById('listResult');
    const matchCount = document.getElementById('matchCount');
    const matchTableBody = document.getElementById('matchTableBody');

    listResult.style.display = 'block';
    matchCount.textContent = students.length;
    matchTableBody.innerHTML = '';

    students.forEach((st, index) => {
        const tr = document.createElement('tr');
        tr.onclick = () => selectStudent(st.seating_no);
        const statusText = st.student_case_desc || (st.total_degree >= 160 ? 'ناجح' : 'دور ثان');
        tr.innerHTML = `
            <td>${index + 1}</td>
            <td><strong>${st.seating_no}</strong></td>
            <td>${st.arabic_name}</td>
            <td>${st.total_degree}</td>
            <td><span class="badge-percent">${st.percentage}%</span> (${statusText})</td>
            <td><button class="btn btn-outline btn-sm" onclick="selectStudent('${st.seating_no}')">عرض النتيجة</button></td>
        `;
        matchTableBody.appendChild(tr);
    });
}

function selectStudent(seatingNo) {
    document.getElementById('searchInput').value = seatingNo;
    performSearch(seatingNo, 'seating');
}

function showNotFound(message) {
    const notFoundCard = document.getElementById('notFoundCard');
    const notFoundText = document.getElementById('notFoundText');
    notFoundCard.style.display = 'block';
    notFoundText.textContent = message;
}

function hideResults() {
    resultsSection.style.display = 'none';
    singleResult.style.display = 'none';
    listResult.style.display = 'none';
    notFoundCard.style.display = 'none';
}

// Fetch Stats
async function fetchStats() {
    try {
        const res = await fetch('/api/stats');
        const data = await res.json();
        if (data.total_students) {
            document.getElementById('statTotal').textContent = data.total_students.toLocaleString('ar-EG');
            document.getElementById('statPassRate').textContent = `${data.pass_rate}%`;
            document.getElementById('statAvgPassed').innerHTML = `${data.avg_passed_score} <small style="font-size:13px; font-weight:normal;">(${data.avg_passed_percent}%)</small>`;
            document.getElementById('statAvgAll').innerHTML = `${data.avg_all_score} <small style="font-size:13px; font-weight:normal;">(${data.avg_all_percent}%)</small>`;
        }
    } catch (e) {
        document.getElementById('statTotal').textContent = '919,396';
        document.getElementById('statPassRate').textContent = '80.15%';
        document.getElementById('statAvgPassed').innerHTML = '221.9 <small style="font-size:13px; font-weight:normal;">(69.4%)</small>';
        document.getElementById('statAvgAll').innerHTML = '198.9 <small style="font-size:13px; font-weight:normal;">(62.2%)</small>';
    }
}

// Fetch Top Performers with Static CDN Fallback
async function fetchTopStudents() {
    const topGrid = document.getElementById('topGrid');
    try {
        let result = null;
        try {
            const staticRes = await fetch('static/data/top.json');
            if (staticRes.ok) {
                result = await staticRes.json();
            }
        } catch (err) {
            console.log('Static top fetch fallback to API');
        }

        if (!result) {
            const apiRes = await fetch('/api/top');
            if (apiRes.ok) {
                result = await apiRes.json();
            }
        }

        if (result && result.data && result.data.length > 0) {
            topGrid.innerHTML = '';
            result.data.forEach((st, idx) => {
                const card = document.createElement('div');
                card.className = 'top-card';
                card.onclick = () => selectStudent(st.seating_no);
                card.innerHTML = `
                    <div class="rank-badge">${idx + 1}</div>
                    <div class="top-info">
                        <h4>${st.arabic_name}</h4>
                        <p>رقم الجلوس: ${st.seating_no}</p>
                    </div>
                    <div class="top-score">${st.total_degree} <small style="font-size:12px; color:var(--text-muted);">(${st.percentage}%)</small></div>
                `;
                topGrid.appendChild(card);
            });
        }
    } catch (e) {
        console.error('Failed to load top students', e);
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
