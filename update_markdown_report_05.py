import json

with open('static/data/predictions.json', 'r', encoding='utf-8') as f:
    colleges = json.load(f)

science = [c for c in colleges if c['track'] != 'literary']
arts = [c for c in colleges if c['track'] == 'literary']

def group_and_format(data_list):
    grouped = {}
    for col in data_list:
        cat = col['sector']
        if cat not in grouped:
            grouped[cat] = []
        grouped[cat].append(col)
        
    sorted_groups = sorted(grouped.items(), key=lambda x: max([c['predicted_score'] for c in x[1]]), reverse=True)
    
    md_output = ""
    for cat_name, cols in sorted_groups:
        cols = sorted(cols, key=lambda x: x['predicted_score'], reverse=True)
        md_output += f"### {cat_name}\n\n"
        md_output += "| الكلية | مجموع 2025 | المجموع المتوقع 2026 | التغير في الدرجات | النسبة المتوقعة |\n"
        md_output += "| :--- | :--- | :--- | :--- | :--- |\n"
        for c in cols:
            ratio = c['percentage']
            d = c['delta']
            trend_str = f"📈 +{d} درجة" if d > 0 else (f"📉 {d} درجة" if d < 0 else "➖ 0 درجة")
            md_output += f"| {c['name']} | {c['score_2025']} | **{c['predicted_score']}** | {trend_str} | %{ratio:.2f} |\n"
        md_output += "\n"
    return md_output

science_md = group_and_format(science)
arts_md = group_and_format(arts)

artifact_path = r"C:\Users\abdom\.gemini\antigravity\brain\f564a227-2447-4b6a-ba24-e55986c667cc\predictions_report_accurate.md"

report = f"""# التحليل الإحصائي الدقيق والتوقعات المراجعة لتنسيق 2026 (بخطوات النصف درجة 0.5)

بناءً على المراجعة والتأكد الدقيق من الحسابات ونظام التنسيق المصري الرسمي:
تم تقريب وتعديل جميع التوقعات لتكون **بخطوات نصف درجة (0.5)** حتمياً (مثال: 301.0، 301.5، 302.0) مع مراعاة تأثير تكدس الطلاب في الشرائح المختلفة وسعة الكليات.

## 1. كليات القسم العلمي (علوم ورياضة)

{science_md}

---

## 2. كليات القسم الأدبي

{arts_md}
"""

with open(artifact_path, 'w', encoding='utf-8') as f:
    f.write(report)

print("Updated predictions_report_accurate.md with strict 0.5 step rounding.")
