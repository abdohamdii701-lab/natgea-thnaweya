import json
import os

paths = ['static/data/tansiq.json', 'dist/static/data/tansiq.json']

for p in paths:
    if os.path.exists(p):
        with open(p, 'r', encoding='utf-8') as f:
            data = json.load(f)

        data['stage1_limits'] = {
            "science_bio": {
                "name": "علمي علوم - المرحلة الأولى",
                "min_deg": 289.0,
                "min_pct": 90.31,
                "min_deg_2025": 293.0,
                "min_pct_2025": 91.56,
                "status": "المرحلة الأولى الرسمية",
                "student_count": 28000
            },
            "science_math": {
                "name": "علمي رياضة - المرحلة الأولى",
                "min_deg": 274.5,
                "min_pct": 85.78,
                "min_deg_2025": 283.0,
                "min_pct_2025": 88.44,
                "status": "المرحلة الأولى الرسمية",
                "student_count": 25500
            },
            "literary": {
                "name": "أدبي - المرحلة الأولى",
                "min_deg": 235.0,
                "min_pct": 73.44,
                "min_deg_2025": 233.0,
                "min_pct_2025": 72.81,
                "status": "المرحلة الأولى الرسمية",
                "student_count": 15000
            }
        }

        with open(p, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

print("Updated stage1_limits in tansiq.json files successfully.")
