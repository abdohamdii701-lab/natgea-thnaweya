import json
import os

# Load 2025 limits
with open('limits.json', 'r', encoding='utf-8') as f:
    limits_data = json.load(f)

science = limits_data['science']
arts = limits_data['arts']

# Define true sector minimums for 2025 and 2026 projections + top college shift
sector_configs = {
    'الطب البشري': (298.0, 301.0, 1.5),              # Cairo Medicine 303.5 -> 305.0 (+1.5)
    'طب الأسنان': (296.5, 298.5, 1.0),              # Top Dentistry -> +1.0
    'العلاج الطبيعي': (294.5, 296.0, 1.0),          # Top Physio -> +1.0
    'الصيدلة': (294.0, 291.0, -1.5),                 # Top Pharmacy -> -1.5
    'الطب البيطري': (277.5, 285.5, 2.5),            # Top Vet -> +2.5
    'الهندسة': (287.5, 279.0, -3.0),                 # Cairo Eng 296.0 -> 293.0 (-3.0)
    'حاسبات ومعلومات (رياضة)': (269.5, 266.0, -1.5),
    'حاسبات ومعلومات (علوم)': (283.5, 283.0, -0.5),
    'الملاحة وتكنولوجيا الفضاء': (260.0, 264.5, 2.0),
    'الفنون الجميلة (عمارة)': (251.0, 262.5, 3.0),
    'الفنون التطبيقية': (242.5, 258.5, 4.0),
    'العلوم الصحية والتطبيقية': (282.0, 278.5, -1.5),
    'العلوم (علمي علوم)': (250.5, 277.0, 2.5),
    'العلوم (علمي رياضة)': (233.5, 248.0, 2.0),
    'كلية التمريض': (273.0, 268.5, -2.0),
    'معاهد التمريض والصحة': (246.0, 252.0, 2.0),
    'كليات علمية أخرى': (200.0, 200.0, 0.0),
    
    # Literary
    'الاقتصاد والعلوم السياسية': (287.5, 297.0, 2.0),  # Cairo Econ 299.5 -> 301.5 (+2.0)!
    'الألسن': (280.5, 282.5, 1.5),                    # Kafr El-Sheikh Alsun 297.0 -> 298.5 (+1.5)
    'الإعلام': (277.5, 278.0, 1.0),                    # Cairo Mass Comm 288.5 -> 289.5 (+1.0)
    'الآثار': (263.5, 271.5, 2.0),                    # Cairo Archaeology 274.5 -> 276.5 (+2.0)
    'الفنون الجميلة (فنون)': (231.0, 267.0, 4.0),
    'التربية': (232.5, 248.0, 3.0),
    'التجارة': (231.0, 229.0, -1.0),
    'الآداب والحقوق': (201.5, 198.5, -1.0),
    'كليات أدبية أخرى': (180.0, 180.0, 0.0)
}

all_colleges = []

def process_track(data, track_code):
    for col in data:
        name = col['name']
        name_lower = name.lower()
        score_2025 = col['score']
        
        sector = 'كليات أخرى'
        
        if track_code != 'literary':
            if 'طب' in name_lower and 'أسنان' not in name_lower and 'بيطري' not in name_lower and 'فم' not in name_lower:
                sector = 'الطب البشري'
            elif 'أسنان' in name_lower or 'فم' in name_lower:
                sector = 'طب الأسنان'
            elif 'علاج طبيعي' in name_lower:
                sector = 'العلاج الطبيعي'
            elif 'صيدلة' in name_lower:
                sector = 'الصيدلة'
            elif 'بيطري' in name_lower:
                sector = 'الطب البيطري'
            elif 'هندسة' in name_lower and 'عمارة' not in name_lower:
                sector = 'الهندسة'
            elif 'حاسبات' in name_lower or 'ذكاء' in name_lower:
                if 'رياضة' in name_lower:
                    sector = 'حاسبات ومعلومات (رياضة)'
                else:
                    sector = 'حاسبات ومعلومات (علوم)'
            elif 'ملاحة' in name_lower:
                sector = 'الملاحة وتكنولوجيا الفضاء'
            elif 'فنون جميلة' in name_lower and 'عمارة' in name_lower:
                sector = 'الفنون الجميلة (عمارة)'
            elif 'فنون تطبيقية' in name_lower:
                sector = 'الفنون التطبيقية'
            elif 'علوم صحية' in name_lower or 'علوم تطبيقية' in name_lower:
                sector = 'العلوم الصحية والتطبيقية'
            elif 'تمريض' in name_lower and 'معهد' not in name_lower and 'فنى' not in name_lower and 'فني' not in name_lower:
                sector = 'كلية التمريض'
            elif 'تمريض' in name_lower or 'صحى' in name_lower or 'صحي' in name_lower:
                sector = 'معاهد التمريض والصحة'
            elif 'علوم' in name_lower and 'رياضة' in name_lower:
                sector = 'العلوم (علمي رياضة)'
            elif 'علوم' in name_lower and 'سياسية' not in name_lower and 'بترول' not in name_lower:
                sector = 'العلوم (علمي علوم)'
            else:
                sector = 'كليات علمية أخرى'
        else:
            if 'اقتصاد' in name_lower and ('سياسية' in name_lower or 'سياسة' in name_lower):
                sector = 'الاقتصاد والعلوم السياسية'
            elif 'ألسن' in name_lower:
                sector = 'الألسن'
            elif 'إعلام' in name_lower:
                sector = 'الإعلام'
            elif 'آثار' in name_lower:
                sector = 'الآثار'
            elif 'فنون جميلة' in name_lower and 'فنون' in name_lower:
                sector = 'الفنون الجميلة (فنون)'
            elif 'تربية' in name_lower:
                sector = 'التربية'
            elif 'تجارة' in name_lower:
                sector = 'التجارة'
            elif 'آداب' in name_lower or 'حقوق' in name_lower:
                sector = 'الآداب والحقوق'
            else:
                sector = 'كليات أدبية أخرى'

        min_2025, proj_min_2026, top_shift = sector_configs.get(sector, (score_2025, score_2025, 0.0))
        min_shift = proj_min_2026 - min_2025
        
        max_sector_score = 305.0
        
        if score_2025 <= min_2025:
            delta = min_shift
        elif score_2025 >= max_sector_score:
            delta = top_shift
        else:
            t = (score_2025 - min_2025) / (max_sector_score - min_2025)
            delta = min_shift + t * (top_shift - min_shift)

        actual_track = track_code
        if track_code == 'science':
            if 'رياضة' in name_lower or sector in ['الهندسة', 'حاسبات ومعلومات (رياضة)', 'الملاحة وتكنولوجيا الفضاء', 'الفنون الجميلة (عمارة)', 'العلوم (علمي رياضة)']:
                actual_track = 'science_math'
            else:
                actual_track = 'science_bio'

        predicted_score = min(round(score_2025 + delta, 1), 320.0)
        percentage = round((predicted_score / 320.0) * 100, 2)

        all_colleges.append({
            'name': name,
            'score_2025': score_2025,
            'predicted_score': predicted_score,
            'percentage': percentage,
            'delta': round(delta, 1),
            'sector': sector,
            'track': actual_track,
            'track_name': 'علمي علوم' if actual_track == 'science_bio' else ('علمي رياضة' if actual_track == 'science_math' else 'أدبي')
        })

process_track(science, 'science')
process_track(arts, 'literary')

# Write to static/data/predictions.json and dist/static/data/predictions.json
dirs = ['static/data', 'dist/static/data']
for d in dirs:
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, 'predictions.json'), 'w', encoding='utf-8') as f:
        json.dump(all_colleges, f, ensure_ascii=False, indent=2)

print("Updated predictions.json with smooth non-linear ceiling curve model.")
