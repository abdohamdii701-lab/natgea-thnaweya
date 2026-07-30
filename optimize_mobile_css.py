import os

mobile_optimization_css = """

/* ==========================================================================
   Mobile Performance & Lightweight Responsive Optimization (60 FPS Mobile)
   ========================================================================== */

/* Remove GPU-heavy backdrop-blur and keyframe animations on mobile screens for instant scrolling */
@media (max-width: 768px) {
    :root {
        --glass-blur: none !important;
    }

    /* Disable heavy blurred background blobs on mobile */
    .glow-bg, .blob {
        display: none !important;
    }

    /* Use crisp, fast solid-opaque backgrounds for cards */
    .bg-card, .search-card, .result-card, .total-card, .pf-card, 
    .band-card, .compare-card, .tansiq-card, .calc-card, .dir-controls, 
    .table-wrap, .main-header, .rank-box, .percentile-box, .chart-box {
        backdrop-filter: none !important;
        -webkit-backdrop-filter: none !important;
    }

    body {
        background-color: var(--bg-dark);
        /* Simple lightweight static gradient fallback */
        background-image: radial-gradient(circle at top right, rgba(212, 163, 115, 0.08), transparent 60%);
    }

    /* Prevent iOS auto-zoom on input focus by enforcing 16px font-size */
    input[type="text"], input[type="number"], select, .styled-input, .styled-select {
        font-size: 16px !important;
    }

    /* Touch-friendly header & compact navigation */
    .main-header {
        padding: 10px 0;
    }

    .header-content {
        gap: 8px;
    }

    .logo-icon {
        width: 36px;
        height: 36px;
        font-size: 16px;
    }

    .logo-text h1 {
        font-size: 15px;
    }

    .logo-text .subtitle {
        font-size: 9px;
    }

    .header-actions {
        gap: 6px;
        flex-wrap: wrap;
        justify-content: flex-end;
    }

    .header-actions .btn {
        padding: 6px 10px;
        font-size: 11px !important;
        border-radius: 20px;
    }

    .visitor-badge {
        font-size: 10px !important;
        padding: 3px 8px !important;
    }

    /* Search & Calc Hero Tweaks */
    .pred-hero, .analytics-hero, .search-section {
        padding: 1.2rem 0 1rem;
    }

    .pred-hero h2, .analytics-hero h2, .search-card h2 {
        font-size: 1.35rem;
    }

    .pred-hero p, .analytics-hero p, .search-desc {
        font-size: 0.82rem;
    }

    /* Calculator & Form Controls */
    .calc-card {
        padding: 1.2rem;
        margin: 1rem 0 1.5rem;
    }

    .calc-header {
        margin-bottom: 0.8rem;
    }

    .calc-icon {
        font-size: 1.5rem;
    }

    .calc-title {
        font-size: 1rem;
    }

    .mode-toggle-btn {
        font-size: 0.72rem;
        padding: 4px 10px;
        width: 100%;
        text-align: center;
    }

    .calc-form {
        grid-template-columns: 1fr !important;
        gap: 0.6rem;
    }

    .calc-btn {
        height: 42px;
        font-size: 0.88rem;
    }

    /* Responsive Directory Controls */
    .dir-controls {
        padding: 0.9rem;
    }

    .dir-search-row {
        grid-template-columns: 1fr !important;
        gap: 0.6rem;
    }

    .track-pills {
        gap: 0.35rem;
    }

    .pill-btn {
        padding: 5px 12px;
        font-size: 0.75rem;
    }

    /* Table Mobile Optimizations */
    .pred-table th, .pred-table td {
        padding: 10px 8px;
        font-size: 0.78rem;
    }

    .score-val {
        font-size: 0.88rem;
    }

    .trend-badge {
        font-size: 0.68rem;
        padding: 1px 5px;
    }

    /* Pagination Mobile */
    .pagination-wrap {
        font-size: 0.78rem;
        justify-content: center;
        text-align: center;
    }

    /* Disclaimer Note Mobile */
    .disclaimer-note {
        font-size: 0.72rem !important;
        padding: 0 10px;
    }
}

/* Fast hardware rendering hints for smooth scrolling */
.result-card, .top-card, .tansiq-card, .total-card, .pf-card, .band-card {
    content-visibility: auto;
    contain-intrinsic-size: 100px;
}
"""

css_paths = ['static/style.css', 'dist/static/style.css']

for p in css_paths:
    if os.path.exists(p):
        with open(p, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'Mobile Performance & Lightweight Responsive Optimization' not in content:
            content += mobile_optimization_css
            with open(p, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Appended mobile performance optimizations to {p}")

