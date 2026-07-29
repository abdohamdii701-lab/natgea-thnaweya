import asyncio
import aiohttp
import sqlite3
import html as html_lib
import re
import sys
import time
import os

sys.stdout.reconfigure(encoding='utf-8')

INPUT_FILE = "seats_900k.txt"   # rename to match whatever file you upload with the 900k seat numbers
OUTPUT_DB = "scraped_results.db"

# ⚠️ These numbers are PUSHED PAST what we've actually verified (200 req/sec ran clean with
# zero errors on 19,807 seats). At 900k scale we need more speed to land in 25-60 min, so this
# is an extrapolation, not a proven-safe value. The adaptive backoff below is the safety net —
# watch the first progress lines; if timeout/other climb, it'll self-correct automatically.
WORKERS = 500
MAX_REQUESTS_PER_SECOND = 500   # → ~30 min ETA for 900k if it holds; auto-throttles down if the site pushes back
BATCH = 1000
SITE_URL = 'https://natega.elwatannews.com'
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
            psychology_deg REAL,
            branch_conflict TEXT
        )
    """)
    conn.commit()
    conn.close()


def parse(raw):
    if not raw or 'student-result' not in raw:
        return None
    h = html_lib.unescape(raw)

    # Branch — captures two words so "علمي علوم" / "علمي رياضة" aren't truncated to "علمي"
    branch = None
    m = re.search(r'الشعبة:\s*\n?\s*(\S+(?:\s+\S+)?)', h)
    if m:
        b = m.group(1).strip()
        if 'أدبي' in b or 'ادبي' in b:
            branch = 'أدبي'
        elif 'علمي' in b:
            if 'علوم' in b: branch = 'علمي علوم'
            elif 'رياضة' in b: branch = 'علمي رياضة'
            else: branch = 'علمي'
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
    mk = {k: None for k in ['arabic_deg', 'english_deg', 'second_lang_deg', 'physics_deg',
          'chemistry_deg', 'biology_deg', 'geology_deg', 'math1_deg', 'math2_deg',
          'history_deg', 'geography_deg', 'philosophy_deg', 'psychology_deg']}

    for sn, sc, _ in re.findall(r'<td>(.*?)</td>\s*<td>(.*?)</td>\s*<td>(.*?)</td>', h):
        for p, k in smap.items():
            if p in sn.strip():
                sm = re.match(r'(\d+(?:\.\d+)?)\s*/', sc)
                if sm: mk[k] = float(sm.group(1))
                break

    hs = any(v is not None for v in mk.values())

    # Cross-check branch against subject signature: الأحياء/الجيولوجيا حصريين لعلمي علوم،
    # والرياضة البحتة/التطبيقية حصريين لعلمي رياضة. يُستخدم كـ fallback فقط عند غموض النص،
    # أو كعلم تعارض للمراجعة اليدوية — مش حسم أوتوماتيكي أعمى.
    subject_branch = None
    has_science_subjects = mk['biology_deg'] is not None or mk['geology_deg'] is not None
    has_math_subjects = mk['math1_deg'] is not None or mk['math2_deg'] is not None
    if has_science_subjects and not has_math_subjects:
        subject_branch = 'علمي علوم'
    elif has_math_subjects and not has_science_subjects:
        subject_branch = 'علمي رياضة'

    branch_conflict = None
    if branch in (None, 'علمي') and subject_branch:
        branch = subject_branch
    elif branch in ('علمي علوم', 'علمي رياضة') and subject_branch and subject_branch != branch:
        branch_conflict = f"text={branch} vs subjects={subject_branch}"

    if branch or total or hs:
        return (branch, total, bool(branch), hs, mk, branch_conflict)
    return None


class RateLimiter:
    """Paces the total request RATE, independent of concurrency. Targets a
    suspected per-IP/per-session request-count limit on the server side,
    which concurrency tuning alone can't fix."""
    def __init__(self, per_second):
        self.min_interval = 1.0 / per_second
        self.lock = asyncio.Lock()
        self.next_time = 0.0

    async def wait(self):
        async with self.lock:
            now = time.time()
            if now < self.next_time:
                await asyncio.sleep(self.next_time - now)
            self.next_time = max(now, self.next_time) + self.min_interval


FAIL_STATS = {'timeout': 0, 'conn_error': 0, 'bad_status': 0, 'no_marker': 0, 'other': 0}
_last_sample_texts = []


async def grab(session, site_url, seat, sem, throttle, limiter):
    async with sem:
        await limiter.wait()
        if throttle['delay'] > 0:
            await asyncio.sleep(throttle['delay'])
        try:
            headers = {
                'User-Agent': UA,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'ar-EG,ar;q=0.9,en-US;q=0.8,en;q=0.7',
                'Origin': site_url,
                'Referer': site_url + '/'
            }
            data = {'seating_no': str(seat), 'system': '1'}
            timeout = aiohttp.ClientTimeout(total=8.0, connect=4.0, sock_read=4.0)

            async def do_request():
                async with session.post(site_url + '/Result/1', data=data, headers=headers, timeout=timeout) as r:
                    if r.status != 200:
                        FAIL_STATS['bad_status'] += 1
                        throttle['recent_fail'] += 1
                        return None
                    text = await r.text()
                    parsed = parse(text)
                    if parsed:
                        throttle['recent_fail'] = 0
                        return parsed
                    FAIL_STATS['no_marker'] += 1
                    throttle['recent_fail'] += 1
                    if len(_last_sample_texts) < 3:
                        _last_sample_texts.append(text[:800])
                    return None

            result = await asyncio.wait_for(do_request(), timeout=9.0)
            return seat, result
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


async def main():
    print("=" * 75)
    print(" ☁️☁️☁️ ELWATANNEWS 900K FAST SCRAPER")
    print("=" * 75, flush=True)

    if not os.path.exists(INPUT_FILE):
        print(f"❌ Error: Input file '{INPUT_FILE}' not found! Please upload it to Colab first.", flush=True)
        return

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        seats = [line.strip() for line in f if line.strip()]

    init_output_db()

    conn = sqlite3.connect(OUTPUT_DB)
    cur = conn.cursor()

    cur.execute("SELECT seating_no FROM student_results")
    already_scraped = set(r[0] for r in cur.fetchall())

    remaining = [s for s in seats if s not in already_scraped]
    total = len(remaining)
    already_done_count = len(already_scraped)

    print(f"📊 Seats to scrape: {total:,} | Already saved in results: {already_done_count:,} | Total in file: {len(seats):,}", flush=True)

    if total == 0:
        print("🎉 All seats have already been scraped!")
        return

    jar = aiohttp.CookieJar(unsafe=True)
    c = aiohttp.TCPConnector(limit=WORKERS, ssl=False, ttl_dns_cache=300)
    session = aiohttp.ClientSession(connector=c, cookie_jar=jar)
    try:
        async with session.get(SITE_URL + '/', headers={'User-Agent': UA}) as r:
            await r.text()
        print(f"  🔑 {SITE_URL.split('//')[1]}: Cookies OK ✅", flush=True)
    except Exception:
        print(f"  🔑 {SITE_URL.split('//')[1]}: Cookies Warning ⚠️", flush=True)

    sem = asyncio.Semaphore(WORKERS)
    throttle = {'delay': 0.0, 'recent_fail': 0, 'last_notified': 0}
    limiter = RateLimiter(MAX_REQUESTS_PER_SECOND)

    test_seat = remaining[0]
    s0, d0 = await grab(session, SITE_URL, test_seat, sem, throttle, limiter)
    if d0:
        print(f"\n🧪 Quick Test ✅ SUCCESS: seat={s0} | Branch={d0[0]} | Total={d0[1]}", flush=True)
    else:
        print(f"\n🧪 Quick Test ⚠️ Seat {s0} returned no result", flush=True)

    eta_estimate = total / MAX_REQUESTS_PER_SECOND / 60
    print(f"\n🚀 LAUNCHING ({WORKERS} workers, {MAX_REQUESTS_PER_SECOND} req/sec cap) | "
          f"Theoretical ETA: ~{eta_estimate:.0f}m if this rate holds...\n", flush=True)
    all_tasks = [grab(session, SITE_URL, seat, sem, throttle, limiter) for seat in remaining]

    checked = 0
    saved_count = already_done_count
    conflict_count = 0
    t0 = time.time()
    batch = []

    for fut in asyncio.as_completed(all_tasks):
        seat, data = await fut
        checked += 1

        if throttle['recent_fail'] > 0 and throttle['recent_fail'] - throttle['last_notified'] >= 30:
            throttle['delay'] = min(throttle['delay'] + 0.2, 3.0)
            throttle['last_notified'] = throttle['recent_fail']
            print(f"  ⏸️  {throttle['recent_fail']} consecutive failures — possible blocking, "
                  f"throttling to {throttle['delay']:.1f}s delay/request", flush=True)

        if data:
            br, tot, hb, hs, mk, conflict = data
            saved_count += 1
            if conflict:
                conflict_count += 1
            batch.append((seat, br, tot, mk['arabic_deg'], mk['english_deg'], mk['second_lang_deg'],
                          mk['physics_deg'], mk['chemistry_deg'], mk['biology_deg'],
                          mk['geology_deg'], mk['math1_deg'], mk['math2_deg'],
                          mk['history_deg'], mk['geography_deg'], mk['philosophy_deg'],
                          mk['psychology_deg'], conflict))

        if len(batch) >= BATCH:
            cur.executemany("""INSERT OR REPLACE INTO student_results (
                seating_no, branch_name, total_degree, arabic_deg, english_deg, second_lang_deg,
                physics_deg, chemistry_deg, biology_deg, geology_deg, math1_deg, math2_deg,
                history_deg, geography_deg, philosophy_deg, psychology_deg, branch_conflict
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", batch)
            conn.commit()
            batch.clear()

        if checked % 5000 == 0 or checked == total:
            el = time.time() - t0
            rate = checked / el if el > 0 else 0
            pct = checked / total * 100
            eta = (total - checked) / rate / 60 if rate > 0 else 0
            eta_str = f"{eta/60:.1f}h" if eta > 60 else f"{eta:.0f}m"
            print(f"  ☁️ [Watan Live] {checked:,}/{total:,} ({pct:.1f}%) | 📚 Scraped: {saved_count:,} | ⚡ {rate:.0f} req/sec | ETA: {eta_str} | "
                  f"❌ t={FAIL_STATS['timeout']} c={FAIL_STATS['conn_error']} s={FAIL_STATS['bad_status']} nm={FAIL_STATS['no_marker']} o={FAIL_STATS['other']} | "
                  f"⚠️ branch_conflicts={conflict_count}", flush=True)

    if batch:
        cur.executemany("""INSERT OR REPLACE INTO student_results (
            seating_no, branch_name, total_degree, arabic_deg, english_deg, second_lang_deg,
            physics_deg, chemistry_deg, biology_deg, geology_deg, math1_deg, math2_deg,
            history_deg, geography_deg, philosophy_deg, psychology_deg, branch_conflict
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", batch)
        conn.commit()

    await session.close()
    conn.close()
    el = time.time() - t0
    print(f"\n{'='*75}\n✅ ALL DONE! Checked {checked:,} | Saved Results: {saved_count:,} | Branch Conflicts: {conflict_count:,} | Time: {el/60:.1f}m\n{'='*75}")
    print(f"\n📊 Failure breakdown: {FAIL_STATS}")
    if FAIL_STATS['no_marker'] > 0 and _last_sample_texts:
        print("\n🔎 Sample of HTTP-200-but-no-result response bodies:")
        for i, t in enumerate(_last_sample_texts, 1):
            print(f"--- sample {i} ---\n{t}\n")
    if conflict_count > 0:
        print(f"\n⚠️  {conflict_count:,} records had text-branch vs subject-branch disagreement — "
              f"review rows where branch_conflict IS NOT NULL in the database.")

if __name__ == "__main__":
    asyncio.run(main())
