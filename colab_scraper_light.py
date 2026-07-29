import asyncio
import aiohttp
import sqlite3
import html as html_lib
import re
import sys
import time
import os

sys.stdout.reconfigure(encoding='utf-8')

INPUT_FILE = "unpopulated_seats.txt"
OUTPUT_DB = "scraped_results.db"
WORKERS_PER_SITE = 150  # 150 x 3 = 450 concurrent cloud workers on Google Colab
BATCH = 1000
SITES = [
    'https://natega.elwatannews.com',
    'https://natega.youm7.com',
    'https://natega.elfagr.org',
]
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36'

def init_output_db():
    conn = sqlite3.connect(OUTPUT_DB)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS student_results (
            seating_no TEXT PRIMARY KEY,
            branch_name TEXT,
            total_degree REAL,
            arabic_deg REAL,
            english_deg REAL,
            second_lang_deg REAL,
            physics_deg REAL,
            chemistry_deg REAL,
            biology_deg REAL,
            geology_deg REAL,
            math1_deg REAL,
            math2_deg REAL,
            history_deg REAL,
            geography_deg REAL,
            philosophy_deg REAL,
            psychology_deg REAL
        )
    """)
    conn.commit()
    conn.close()

def parse(raw):
    if not raw or 'student-result' not in raw:
        return None
    h = html_lib.unescape(raw)
    
    # Branch
    branch = None
    m = re.search(r'الشعبة:\s*\n?\s*(\S+)', h)
    if m:
        b = m.group(1)
        if 'أدبي' in b or 'ادبي' in b: branch = 'أدبي'
        elif 'علمي' in b: branch = b
    if not branch:
        if 'أدبي' in h and 'الشعبة' in h: branch = 'أدبي'
        elif 'علمي علوم' in h: branch = 'علمي علوم'
        elif 'علمي رياضة' in h: branch = 'علمي رياضة'
        
    # Total
    total = None
    tm = re.search(r'مجموع الدرجات.*?(\d+(?:\.\d+)?)\s*/', h, re.DOTALL)
    if tm: total = float(tm.group(1))
    
    # Subjects
    smap = {
        'اللغة العربية': 'arabic_deg',
        'اللغة الأجنبية الأولى': 'english_deg',
        'اللغة الأجنبية الثانية': 'second_lang_deg',
        'الفيزياء': 'physics_deg',
        'الكيمياء': 'chemistry_deg',
        'الأحياء': 'biology_deg',
        'الجيولوجيا': 'geology_deg',
        'مجموع الرياضيات البحتة': 'math1_deg',
        'الرياضيات البحتة': 'math1_deg',
        'مجموع الرياضيات التطبيقية': 'math2_deg',
        'الرياضيات التطبيقية': 'math2_deg',
        'التاريخ': 'history_deg',
        'الجغرافيا': 'geography_deg',
        'الفلسفة والمنطق': 'philosophy_deg',
        'الفلسفة': 'philosophy_deg',
        'علم النفس والاجتماع': 'psychology_deg',
        'علم النفس': 'psychology_deg',
        'الإحصاء': 'math2_deg'
    }
    mk = {k: None for k in ['arabic_deg','english_deg','second_lang_deg','physics_deg',
          'chemistry_deg','biology_deg','geology_deg','math1_deg','math2_deg',
          'history_deg','geography_deg','philosophy_deg','psychology_deg']}
          
    for sn, sc, _ in re.findall(r'<td>(.*?)</td>\s*<td>(.*?)</td>\s*<td>(.*?)</td>', h):
        for p, k in smap.items():
            if p in sn.strip():
                sm = re.match(r'(\d+(?:\.\d+)?)\s*/', sc)
                if sm: mk[k] = float(sm.group(1))
                break
                
    hs = any(v is not None for v in mk.values())
    if branch or total or hs:
        return (branch, total, bool(branch), hs, mk)
    return None

async def grab(session, site_url, seat, sem):
    async with sem:
        try:
            headers = {
                'User-Agent': UA,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'ar-EG,ar;q=0.9,en-US;q=0.8,en;q=0.7',
                'Origin': site_url,
                'Referer': site_url + '/'
            }
            data = {'seating_no': str(seat), 'system': '1'}
            async with session.post(site_url + '/Result/1', data=data, headers=headers, timeout=aiohttp.ClientTimeout(total=4)) as r:
                if r.status == 200:
                    text = await r.text()
                    parsed = parse(text)
                    if parsed:
                        return seat, parsed
        except Exception:
            pass
        return seat, None

async def main():
    print("=" * 75)
    print(" ☁️☁️☁️ LIGHTWEIGHT GOOGLE COLAB SCRAPER (450 CONCURRENT CLOUD WORKERS)")
    print("=" * 75, flush=True)

    if not os.path.exists(INPUT_FILE):
        print(f"❌ Error: Input file '{INPUT_FILE}' not found! Please upload 'unpopulated_seats.txt' to Colab.", flush=True)
        return

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        seats = [line.strip() for line in f if line.strip()]

    init_output_db()
    
    conn = sqlite3.connect(OUTPUT_DB)
    cur = conn.cursor()
    
    # Check already scraped in output db
    cur.execute("SELECT seating_no FROM student_results")
    already_scraped = set(r[0] for r in cur.fetchall())
    
    remaining = [s for s in seats if s not in already_scraped]
    total = len(remaining)
    already_done_count = len(already_scraped)
    
    print(f"📊 Seats to scrape: {total:,} | Already saved in results: {already_done_count:,} | Total: {len(seats):,}", flush=True)

    if total == 0:
        print("🎉 All seats in unpopulated_seats.txt have been scraped!")
        return

    # Split remaining seats across 3 sites
    chunks = {s: [] for s in SITES}
    for i, s in enumerate(remaining):
        chunks[SITES[i % len(SITES)]].append(s)

    sessions = {}
    semaphores = {s: asyncio.Semaphore(WORKERS_PER_SITE) for s in SITES}
    
    for site in SITES:
        jar = aiohttp.CookieJar(unsafe=True)
        c = aiohttp.TCPConnector(limit=WORKERS_PER_SITE, ssl=False, ttl_dns_cache=300)
        sess = aiohttp.ClientSession(connector=c, cookie_jar=jar)
        try:
            async with sess.get(site + '/', headers={'User-Agent': UA}) as r:
                await r.text()
            print(f"  🔑 {site.split('//')[1]}: Cookies OK ✅", flush=True)
        except Exception:
            print(f"  🔑 {site.split('//')[1]}: Cookies Warning ⚠️", flush=True)
        sessions[site] = sess

    test_seat = remaining[0]
    s0, d0 = await grab(sessions[SITES[0]], SITES[0], test_seat, semaphores[SITES[0]])
    if d0:
        print(f"\n🧪 Quick Test ✅ SUCCESS: seat={s0} | Branch={d0[0]} | Total={d0[1]}", flush=True)
    else:
        print(f"\n🧪 Quick Test ⚠️ Seat {s0} on {SITES[0]} returned no result", flush=True)

    print(f"\n🚀 LAUNCHING COLAB LIGHT SCRAPER (450 Concurrent Workers)...\n", flush=True)
    all_tasks = []
    for site in SITES:
        for seat in chunks[site]:
            all_tasks.append(grab(sessions[site], site, seat, semaphores[site]))

    checked = 0
    saved_count = already_done_count
    t0 = time.time()
    batch = []

    for fut in asyncio.as_completed(all_tasks):
        seat, data = await fut
        checked += 1
        if data:
            br, tot, hb, hs, mk = data
            saved_count += 1
            batch.append((seat, br, tot, mk['arabic_deg'], mk['english_deg'], mk['second_lang_deg'],
                          mk['physics_deg'], mk['chemistry_deg'], mk['biology_deg'],
                          mk['geology_deg'], mk['math1_deg'], mk['math2_deg'],
                          mk['history_deg'], mk['geography_deg'], mk['philosophy_deg'],
                          mk['psychology_deg']))

        if len(batch) >= BATCH:
            cur.executemany("""INSERT OR REPLACE INTO student_results (
                seating_no, branch_name, total_degree, arabic_deg, english_deg, second_lang_deg,
                physics_deg, chemistry_deg, biology_deg, geology_deg, math1_deg, math2_deg,
                history_deg, geography_deg, philosophy_deg, psychology_deg
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", batch)
            conn.commit()
            batch.clear()

        if checked % 500 == 0 or checked == total:
            el = time.time() - t0
            rate = checked / el if el > 0 else 0
            pct = checked / total * 100
            eta = (total - checked) / rate / 60 if rate > 0 else 0
            eta_str = f"{eta/60:.1f}h" if eta > 60 else f"{eta:.0f}m"
            print(f"  ☁️ [Colab Live] {checked:,}/{total:,} ({pct:.1f}%) | 📚 Scraped Results: {saved_count:,} | ⚡ {rate:.0f} req/sec | ETA: {eta_str}", flush=True)

    if batch:
        cur.executemany("""INSERT OR REPLACE INTO student_results (
            seating_no, branch_name, total_degree, arabic_deg, english_deg, second_lang_deg,
            physics_deg, chemistry_deg, biology_deg, geology_deg, math1_deg, math2_deg,
            history_deg, geography_deg, philosophy_deg, psychology_deg
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", batch)
        conn.commit()

    for s in sessions.values(): await s.close()
    conn.close()
    el = time.time() - t0
    print(f"\n{'='*75}\n✅ ALL DONE ON GOOGLE COLAB! Checked {checked:,} | Saved Results: {saved_count:,} | Time: {el/60:.1f}m\n{'='*75}")

if __name__ == "__main__":
    asyncio.run(main())
