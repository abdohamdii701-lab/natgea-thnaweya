import asyncio
import aiohttp
import sqlite3
import html as html_lib
import re
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = "Stage_New_Search.db"
WORKERS = 100  # 100 workers per site x 3 sites = 300 total workers for max stability & speed
BATCH = 500
SITES = [
    'https://natega.elwatannews.com',
    'https://natega.youm7.com',
    'https://natega.elfagr.org',
]
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36'

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
            async with session.post(site_url + '/Result/1', data=data, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as r:
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
    print(" 🚀🚀🚀 ULTRA TURBO SCRAPER (3 SITES x 100 WORKERS = 300 TOTAL)")
    print("=" * 75, flush=True)

    # DB setup
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    cur = conn.cursor()
    
    # Ensure columns
    cur.execute("PRAGMA table_info(stage_new_search)")
    cols = [c[1] for c in cur.fetchall()]
    for col in ['branch_name','arabic_deg','english_deg','second_lang_deg','physics_deg',
                'chemistry_deg','biology_deg','geology_deg','math1_deg','math2_deg',
                'history_deg','geography_deg','philosophy_deg','psychology_deg']:
        if col not in cols:
            t = 'TEXT' if col == 'branch_name' else 'REAL'
            cur.execute(f"ALTER TABLE stage_new_search ADD COLUMN {col} {t}")
    conn.commit()

    # Get remaining unpopulated seats
    print("📂 Loading remaining unpopulated students from database...", flush=True)
    cur.execute("SELECT seating_no FROM stage_new_search WHERE branch_name IS NULL OR branch_name = '' ORDER BY CAST(seating_no AS INT)")
    remaining = [r[0] for r in cur.fetchall()]
    
    cur.execute("SELECT COUNT(*) FROM stage_new_search WHERE branch_name IS NOT NULL AND branch_name != ''")
    done = cur.fetchone()[0]
    total = len(remaining)
    print(f"📊 Already Done: {done:,} | Remaining: {total:,} | Grand Total: {done+total:,}", flush=True)

    if total == 0:
        print("🎉 All students already scraped!")
        return

    # Split across sites round-robin
    chunks = {s: [] for s in SITES}
    for i, s in enumerate(remaining):
        chunks[SITES[i % len(SITES)]].append(s)
    for s in SITES:
        print(f"  📡 {s.split('//')[1]}: {len(chunks[s]):,} students assigned", flush=True)

    # Create sessions
    sessions = {}
    semaphores = {s: asyncio.Semaphore(WORKERS) for s in SITES}
    
    for site in SITES:
        jar = aiohttp.CookieJar(unsafe=True)
        c = aiohttp.TCPConnector(limit=WORKERS, ssl=False, ttl_dns_cache=300)
        sess = aiohttp.ClientSession(connector=c, cookie_jar=jar)
        # Acquire initial cookies
        try:
            async with sess.get(site + '/', headers={'User-Agent': UA}) as r:
                await r.text()
            print(f"  🔑 {site.split('//')[1]}: cookies ✅", flush=True)
        except Exception:
            print(f"  🔑 {site.split('//')[1]}: cookies ⚠️", flush=True)
        sessions[site] = sess

    # Quick test with seat 2001970 or first remaining seat
    test_seat = remaining[0]
    s0, d0 = await grab(sessions[SITES[0]], SITES[0], test_seat, semaphores[SITES[0]])
    if d0:
        print(f"\n🧪 Quick Test ✅ SUCCESS: seat={s0} | Branch={d0[0]} | Total={d0[1]}", flush=True)
    else:
        print(f"\n🧪 Quick Test ⚠️ Seat {s0} returned no result on {SITES[0]}", flush=True)

    # Build all tasks
    print(f"\n🚀 LAUNCHING {WORKERS * len(SITES)} CONCURRENT WORKERS!\n", flush=True)
    all_tasks = []
    for site in SITES:
        for seat in chunks[site]:
            all_tasks.append(grab(sessions[site], site, seat, semaphores[site]))

    checked = 0
    bc = done
    sc = done
    t0 = time.time()
    batch = []

    for fut in asyncio.as_completed(all_tasks):
        seat, data = await fut
        checked += 1
        if data:
            br, tot, hb, hs, mk = data
            if hb: bc += 1
            if hs: sc += 1
            batch.append((br, tot, mk['arabic_deg'], mk['english_deg'], mk['second_lang_deg'],
                          mk['physics_deg'], mk['chemistry_deg'], mk['biology_deg'],
                          mk['geology_deg'], mk['math1_deg'], mk['math2_deg'],
                          mk['history_deg'], mk['geography_deg'], mk['philosophy_deg'],
                          mk['psychology_deg'], seat))

        if len(batch) >= BATCH:
            cur.executemany("""UPDATE stage_new_search SET
                branch_name=COALESCE(?,branch_name),total_degree=COALESCE(?,total_degree),
                arabic_deg=COALESCE(?,arabic_deg),english_deg=COALESCE(?,english_deg),
                second_lang_deg=COALESCE(?,second_lang_deg),physics_deg=COALESCE(?,physics_deg),
                chemistry_deg=COALESCE(?,chemistry_deg),biology_deg=COALESCE(?,biology_deg),
                geology_deg=COALESCE(?,geology_deg),math1_deg=COALESCE(?,math1_deg),
                math2_deg=COALESCE(?,math2_deg),history_deg=COALESCE(?,history_deg),
                geography_deg=COALESCE(?,geography_deg),philosophy_deg=COALESCE(?,philosophy_deg),
                psychology_deg=COALESCE(?,psychology_deg) WHERE seating_no=?""", batch)
            conn.commit()
            batch.clear()

        if checked % 200 == 0 or checked == total:
            el = time.time() - t0
            rate = checked / el if el > 0 else 0
            pct = checked / total * 100
            eta = (total - checked) / rate / 60 if rate > 0 else 0
            eta_s = f"{eta/60:.1f}h" if eta > 60 else f"{eta:.0f}m"
            print(f"  ⚡ {checked:,}/{total:,} ({pct:.1f}%) | 🏷️{bc:,} | 📚{sc:,} | {rate:.0f}/s | ETA:{eta_s}", flush=True)

    if batch:
        cur.executemany("""UPDATE stage_new_search SET
            branch_name=COALESCE(?,branch_name),total_degree=COALESCE(?,total_degree),
            arabic_deg=COALESCE(?,arabic_deg),english_deg=COALESCE(?,english_deg),
            second_lang_deg=COALESCE(?,second_lang_deg),physics_deg=COALESCE(?,physics_deg),
            chemistry_deg=COALESCE(?,chemistry_deg),biology_deg=COALESCE(?,biology_deg),
            geology_deg=COALESCE(?,geology_deg),math1_deg=COALESCE(?,math1_deg),
            math2_deg=COALESCE(?,math2_deg),history_deg=COALESCE(?,history_deg),
            geography_deg=COALESCE(?,geography_deg),philosophy_deg=COALESCE(?,philosophy_deg),
            psychology_deg=COALESCE(?,psychology_deg) WHERE seating_no=?""", batch)
        conn.commit()

    for s in sessions.values(): await s.close()
    conn.close()
    el = time.time() - t0
    print(f"\n{'='*70}\n✅ DONE! {checked:,} | 🏷️{bc:,} | 📚{sc:,} | ⏱️{el/60:.1f}m\n{'='*70}")

if __name__ == "__main__":
    asyncio.run(main())
