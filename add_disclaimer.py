import os

disclaimer_html = """
            <p class="disclaimer-note" style="margin-top: 0.8rem; font-size: 0.78rem; opacity: 0.75; line-height: 1.5; max-width: 800px; margin-left: auto; margin-right: auto;">
                ⚠️ <strong>إخلاء مسؤولية:</strong> هذا الموقع هو تطبيق تحليلي استرشادي غير رسمي يهدف لمساعدة الطلاب، وجميع النتائج ومؤشرات التنسيق استرشادية فقط. البيانات والحدود الدنيا الرسمية تُعلن حصراً عبر بوابة التنسيق الإلكتروني لوزارة التعليم العالي والبحث العلمي.
            </p>"""

files = ['index.html', 'analytics.html', 'predictions.html', 'dist/index.html', 'dist/analytics.html', 'dist/predictions.html']

for f_path in files:
    if os.path.exists(f_path):
        with open(f_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'disclaimer-note' not in content:
            # Insert into footer
            if '</footer>' in content:
                content = content.replace('</footer>', f'{disclaimer_html}\n    </footer>')
            else:
                # Add footer before </body> if no footer
                footer_block = f"""
    <footer style="padding: 2rem 0; text-align: center; border-top: 1px solid var(--bg-card-border);">
        <div class="container">
            <p>جميع الحقوق محفوظة &copy; 2026 - نظام استعلام وتوقعات نتيجة الثانوية العامة</p>
            {disclaimer_html}
        </div>
    </footer>"""
                content = content.replace('</body>', f'{footer_block}\n</body>')
                
            with open(f_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Added disclaimer to {f_path}")

