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
CONCURRENCY = 25  # lowered from 250 — high concurrency is the likely trigger for site-side blocking
BATCH = 500
YOUM7_URL = 'https://natega.youm7.com'

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
        elif 'علمي علوم' in b: branch = 'علمي علوم'
        elif 'علمي رياضة' in b: branch = 'علمي رياضة'
        elif 'علمي' in b: branch = 'علمي'
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

FAIL_STATS = {'timeout': 0, 'conn_error': 0, 'bad_status': 0, 'no_marker': 0, 'other': 0}
_last_sample_texts = []  # keep a few raw bodies of "no_marker" failures for inspection

async def grab_seat(session, seat, sem, throttle):
    async with sem:
        # Cooperative throttle: if we're in a suspected block/rate-limit window, slow down
        if throttle['delay'] > 0:
            await asyncio.sleep(throttle['delay'])
        try:
            headers = {
                'User-Agent': UA,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'ar-EG,ar;q=0.9,en-US;q=0.8,en;q=0.7',
                'Origin': YOUM7_URL,
                'Referer': YOUM7_URL + '/'
            }
            data = {'seating_no': str(seat), 'system': '1'}
            timeout = aiohttp.ClientTimeout(total=6.0, connect=3.0, sock_read=3.0)
            async with session.post(YOUM7_URL + '/Result/1', data=data, headers=headers, timeout=timeout) as r:
                if r.status != 200:
                    FAIL_STATS['bad_status'] += 1
                    throttle['recent_fail'] += 1
                    return seat, None
                text = await r.text()
                parsed = parse(text)
                if parsed:
                    throttle['recent_fail'] = 0  # success resets the failure streak
                    return seat, parsed
                # Got HTTP 200 but no usable data — likely a block/CAPTCHA page, not a real "no result"
                FAIL_STATS['no_marker'] += 1
                throttle['recent_fail'] += 1
                if len(_last_sample_texts) < 3:
                    _last_sample_texts.append(text[:800])
        except asyncio.TimeoutError:
            FAIL_STATS['timeout'] += 1
            throttle['recent_fail'] += 1
        except aiohttp.ClientError:
            FAIL_STATS['conn_error'] += 1
            throttle['recent_fail'] += 1
        except Exception:
            FAIL_STATS['other'] += 1
            throttle['recent_fail'] += 1
        return seat, None

async def safe_grab(session, seat, sem, throttle):
    """Wrapper using asyncio.wait_for to prevent any task hanging forever on Colab."""
    try:
        return await asyncio.wait_for(grab_seat(session, seat, sem, throttle), timeout=7.0)
    except Exception:
        FAIL_STATS['other'] += 1
        return seat, None

async def main():
    print("=" * 75)
    print(" 🚀🚀🚀 YOUM7 STALL-FREE COLAB SCRAPER (250 WORKERS - 100% YOUM7 ONLY)")
    print("=" * 75, flush=True)

    if not os.path.exists(INPUT_FILE):
        print(f"❌ Error: Input file '{INPUT_FILE}' not found! Please upload 'unpopulated_seats.txt'.", flush=True)
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
    
    print(f"📊 Remaining to scrape: {total:,} | Already saved in results: {already_done_count:,} | Total in file: {len(seats):,}", flush=True)

    if total == 0:
        print("🎉 All seats in unpopulated_seats.txt have been scraped!")
        return

    jar = aiohttp.CookieJar(unsafe=True)
    c = aiohttp.TCPConnector(limit=CONCURRENCY, ssl=False, ttl_dns_cache=300)
    session = aiohttp.ClientSession(connector=c, cookie_jar=jar)

    # Acquire homepage cookie
    try:
        async with session.get(YOUM7_URL + '/', headers={'User-Agent': UA}) as r:
            await r.text()
        print(f"  🔑 {YOUM7_URL.split('//')[1]}: Youm7 Session Cookie OK ✅", flush=True)
    except Exception:
        print(f"  🔑 {YOUM7_URL.split('//')[1]}: Youm7 Warning ⚠️", flush=True)

    sem = asyncio.Semaphore(CONCURRENCY)
    throttle = {'delay': 0.0, 'recent_fail': 0}

    # Quick test
    test_seat = remaining[0]
    s0, d0 = await safe_grab(session, test_seat, sem, throttle)
    if d0:
        print(f"\n🧪 Quick Test ✅ SUCCESS: seat={s0} | Branch={d0[0]} | Total={d0[1]}", flush=True)
    else:
        print(f"\n🧪 Quick Test ⚠️ Seat {s0} returned no result on Youm7", flush=True)

    print(f"\n🚀 LAUNCHING SCRAPER FOR {total:,} SEATS...\n", flush=True)
    tasks = [safe_grab(session, seat, sem, throttle) for seat in remaining]

    checked = 0
    saved_count = already_done_count
    t0 = time.time()
    batch = []

    for fut in asyncio.as_completed(tasks):
        seat, data = await fut
        checked += 1

        # Adaptive backoff: a long unbroken streak of failures strongly suggests
        # the site is rate-limiting/blocking us, not that seats genuinely lack results.
        if throttle['recent_fail'] > 0 and throttle['recent_fail'] % 100 == 0:
            throttle['delay'] = min(throttle['delay'] + 0.2, 3.0)
            print(f"  ⏸️  {throttle['recent_fail']} consecutive failures — possible blocking, "
                  f"throttling to {throttle['delay']:.1f}s delay/request", flush=True)

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

        if checked % 200 == 0 or checked == total:
            el = time.time() - t0
            rate = checked / el if el > 0 else 0
            pct = checked / total * 100
            eta = (total - checked) / rate / 60 if rate > 0 else 0
            eta_str = f"{eta/60:.1f}h" if eta > 60 else f"{eta:.0f}m"
            print(f"  ⚡ [Youm7 Live] {checked:,}/{total:,} ({pct:.1f}%) | 📚 Scraped Results: {saved_count:,} | ⚡ {rate:.0f} req/sec | ETA: {eta_str} | "
                  f"❌ timeout={FAIL_STATS['timeout']} conn={FAIL_STATS['conn_error']} status={FAIL_STATS['bad_status']} no_marker={FAIL_STATS['no_marker']}", flush=True)

    if batch:
        cur.executemany("""INSERT OR REPLACE INTO student_results (
            seating_no, branch_name, total_degree, arabic_deg, english_deg, second_lang_deg,
            physics_deg, chemistry_deg, biology_deg, geology_deg, math1_deg, math2_deg,
            history_deg, geography_deg, philosophy_deg, psychology_deg
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", batch)
        conn.commit()

    await session.close()
    conn.close()
    el = time.time() - t0
    print(f"\n{'='*75}\n✅ ALL DONE ON YOUM7! Checked {checked:,} | Saved Results: {saved_count:,} | Time: {el/60:.1f}m\n{'='*75}")
    print(f"\n📊 Failure breakdown: {FAIL_STATS}")
    if FAIL_STATS['no_marker'] > 0 and _last_sample_texts:
        print("\n🔎 Sample of HTTP-200-but-no-result response bodies (check for CAPTCHA/block page):")
        for i, t in enumerate(_last_sample_texts, 1):
            print(f"--- sample {i} ---\n{t}\n")

if __name__ == "__main__":
    asyncio.run(main())
