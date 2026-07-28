// Natega 2026 Interactive Script

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

// Search Execution
async function performSearch(query, mode) {
    const submitBtn = document.getElementById('submitBtn');
    const btnText = submitBtn.querySelector('.btn-text');
    const spinner = submitBtn.querySelector('.spinner');

    btnText.style.display = 'none';
    spinner.style.display = 'inline-block';
    submitBtn.disabled = true;

    try {
        const response = await fetch(`/api/search?mode=${mode}&q=${encodeURIComponent(query)}`);
        const result = await response.json();

        hideResults();
        resultsSection.style.display = 'block';

        if (result.type === 'single' && result.data) {
            renderSingleStudent(result.data);
        } else if (result.type === 'list' && result.data && result.data.length > 0) {
            renderStudentList(result.data);
        } else {
            showNotFound(result.message || `لم نتمكن من العثور على أية نتائج مطابقة للبحث: "${query}"`);
        }
    } catch (err) {
        showNotFound('تعذر الاتصال بالسيرفر. تأكد من تشغيل الموقع والاتصال بالشبكة.');
    } finally {
        btnText.style.display = 'inline';
        spinner.style.display = 'none';
        submitBtn.disabled = false;

        // Smooth scroll to results
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

// Render Single Student Result
function renderSingleStudent(student) {
    document.getElementById('singleResult').style.display = 'block';

    resName.textContent = student.arabic_name;
    resSeatingNo.textContent = student.seating_no;
    resTotal.textContent = student.total_degree;
    resPercent.textContent = `${student.percentage}%`;
    resProgressBar.style.width = `${Math.min(student.percentage, 100)}%`;

    // Official status description from database
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

    // Grade Calculation
    const percent = student.percentage;
    let gradeText = 'مقبول';

    if (percent >= 85) {
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

    // Trigger Confetti for high performers
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
            document.getElementById('statAvgPassed').innerHTML = `${data.avg_passed_score} <small style="font-size:13px; font-weight:normal; color:var(--text-muted);">(${data.avg_passed_percent}%)</small>`;
            document.getElementById('statAvgAll').innerHTML = `${data.avg_all_score} <small style="font-size:13px; font-weight:normal; color:var(--text-muted);">(${data.avg_all_percent}%)</small>`;
        }
    } catch (e) {
        console.error('Failed to load stats', e);
    }
}

// Fetch Top Performers
async function fetchTopStudents() {
    const topGrid = document.getElementById('topGrid');
    try {
        const res = await fetch('/api/top');
        const result = await res.json();
        if (result.data && result.data.length > 0) {
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
