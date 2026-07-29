import sqlite3
import time
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

MAIN_DB = "Stage_New_Search.db"
COLAB_RESULTS_DB = "scraped_results.db"

def main():
    print("=" * 70)
    print(" 🔄 IMPORT COLAB RESULTS INTO LOCAL DATABASE")
    print("=" * 70)

    if not os.path.exists(COLAB_RESULTS_DB):
        print(f"❌ Error: Could not find '{COLAB_RESULTS_DB}' in current folder! Please download 'scraped_results.db' from Colab and place it in e:\\natega.")
        return

    conn_main = sqlite3.connect(MAIN_DB)
    cur_main = conn_main.cursor()

    conn_colab = sqlite3.connect(COLAB_RESULTS_DB)
    cur_colab = conn_colab.cursor()

    print(f"📂 Reading records from {COLAB_RESULTS_DB}...")
    cur_colab.execute("""
        SELECT seating_no, branch_name, total_degree, arabic_deg, english_deg, second_lang_deg,
               physics_deg, chemistry_deg, biology_deg, geology_deg, math1_deg, math2_deg,
               history_deg, geography_deg, philosophy_deg, psychology_deg
        FROM student_results
    """)
    records = cur_colab.fetchall()
    print(f"📊 Total records found to import: {len(records):,}")

    if not records:
        print("⚠️ No records found in scraped_results.db")
        return

    start = time.time()
    cur_main.executemany("""
        UPDATE stage_new_search SET
            branch_name = COALESCE(?, branch_name),
            total_degree = COALESCE(?, total_degree),
            arabic_deg = COALESCE(?, arabic_deg),
            english_deg = COALESCE(?, english_deg),
            second_lang_deg = COALESCE(?, second_lang_deg),
            physics_deg = COALESCE(?, physics_deg),
            chemistry_deg = COALESCE(?, chemistry_deg),
            biology_deg = COALESCE(?, biology_deg),
            geology_deg = COALESCE(?, geology_deg),
            math1_deg = COALESCE(?, math1_deg),
            math2_deg = COALESCE(?, math2_deg),
            history_deg = COALESCE(?, history_deg),
            geography_deg = COALESCE(?, geography_deg),
            philosophy_deg = COALESCE(?, philosophy_deg),
            psychology_deg = COALESCE(?, psychology_deg)
        WHERE seating_no = ?
    """, [(r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9], r[10], r[11], r[12], r[13], r[14], r[15], r[0]) for r in records])

    conn_main.commit()
    conn_main.close()
    conn_colab.close()

    elapsed = time.time() - start
    print(f"\n✅ SUCCESS! Imported {len(records):,} student results into {MAIN_DB} in {elapsed:.2f} seconds!")
    print("=" * 70)

if __name__ == "__main__":
    main()
