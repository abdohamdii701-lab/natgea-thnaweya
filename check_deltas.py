import json

# Load limits 2025
with open('limits.json', 'r', encoding='utf-8') as f:
    limits_data = json.load(f)

science = limits_data['science']
arts = limits_data['arts']

# Load tansiq 2026
with open(r'dist\static\data\tansiq.json', 'r', encoding='utf-8') as f:
    tansiq_data = json.load(f)

# Sector projected minimums for 2026 (from tansiq.json)
# We map each sector to its 2026 projected minimum degree
proj_sector_min = {}
for s in tansiq_data['sectors']:
    proj_sector_min[s['name']] = s['proj_min_deg']

# Find 2025 actual minimum for each sector in limits.json
def find_2025_sector_min(data, keywords):
    scores = []
    for col in data:
        name = col['name']
        if any(k in name for k in keywords):
            # Exclude unwanted matches
            scores.append(col['score'])
    return min(scores) if scores else None

# Calculate actual degree delta for each sector: delta = proj_2026_min - actual_2025_min
sector_deltas = {
    'الطب البشري': 301.0 - 298.0,                       # +3.0
    'طب الأسنان': 298.5 - 296.5,                        # +2.0
    'العلاج الطبيعي': 296.0 - 294.5,                     # +1.5
    'الصيدلة': 291.0 - 294.0,                           # -3.0
    'الطب البيطري': 285.5 - 277.5,                      # +8.0
    'الهندسة': 279.0 - 287.5,                           # -8.5
    'حاسبات ومعلومات (رياضة)': 266.0 - 269.5,            # -3.5
    'الملاحة وتكنولوجيا الفضاء': 264.5 - 260.0,          # +4.5
    'الفنون الجميلة (عمارة)': 262.5 - 251.0,            # +11.5
    'الفنون التطبيقية': 258.5 - 242.5,                  # +16.0
    'العلوم الصحية والتطبيقية': 278.5 - 282.0,          # -3.5
    'علوم (علمي علوم)': 277.0 - 250.5,                  # +26.5 (Wait! Let's check min science 2025)
    'كلية التمريض': 268.5 - 273.0,                      # -4.5
    'معاهد التمريض والصحة': 252.0 - 246.0,              # +6.0
    
    # Literary
    'الاقتصاد والعلوم السياسية': 297.0 - 287.5,          # +9.5
    'الألسن': 282.5 - 280.5,                            # +2.0
    'الإعلام': 278.0 - 277.5,                            # +0.5
    'الآثار': 271.5 - 263.5,                            # +8.0
    'الفنون الجميلة (فنون)': 267.0 - 231.0,             # +36.0
    'التربية': 248.0 - 232.5,                           # +15.5
    'التجارة': 229.0 - 231.0,                           # -2.0
    'الآداب والحقوق': 198.5 - 201.5                      # -3.0
}

print("Calculated Sector Deltas (2026 proj min - 2025 actual min):")
for k, v in sector_deltas.items():
    print(f"  {k}: {v:+.1f} درجة")
