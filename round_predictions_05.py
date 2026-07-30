import json
import os

def round_half(val):
    # Round to nearest 0.5 degree step
    return round(float(val) * 2.0) / 2.0

paths = ['static/data/predictions.json', 'dist/static/data/predictions.json']

for p in paths:
    if os.path.exists(p):
        with open(p, 'r', encoding='utf-8') as f:
            colleges = json.load(f)
            
        for col in colleges:
            raw_pred = col['predicted_score']
            rounded_pred = min(round_half(raw_pred), 320.0)
            col['predicted_score'] = rounded_pred
            col['percentage'] = round((rounded_pred / 320.0) * 100, 2)
            col['delta'] = round(rounded_pred - col['score_2025'], 1)

        with open(p, 'w', encoding='utf-8') as f:
            json.dump(colleges, f, ensure_ascii=False, indent=2)

print("Updated predictions.json with strict 0.5-degree step rounding.")

# Also update tansiq.json stage1 limits and sectors
tansiq_paths = ['static/data/tansiq.json', 'dist/static/data/tansiq.json']

for p in tansiq_paths:
    if os.path.exists(p):
        with open(p, 'r', encoding='utf-8') as f:
            tdata = json.load(f)
            
        for key, s1 in tdata.get('stage1_limits', {}).items():
            r_deg = round_half(s1['min_deg'])
            s1['min_deg'] = r_deg
            s1['min_pct'] = round((r_deg / 320.0) * 100, 2)
            
        for sector in tdata.get('sectors', []):
            r_deg = round_half(sector['proj_min_deg'])
            sector['proj_min_deg'] = r_deg
            sector['proj_min_pct'] = round((r_deg / 320.0) * 100, 2)
            sector['shift'] = round(sector['proj_min_pct'] - sector['prev_min_pct'], 2)

        with open(p, 'w', encoding='utf-8') as f:
            json.dump(tdata, f, ensure_ascii=False, indent=2)

print("Updated tansiq.json with strict 0.5-degree step rounding.")
