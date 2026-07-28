import pyodbc
import csv
import time

def extract_access_to_csv():
    start_time = time.time()
    db_path = r"e:\natega\نسخة البحث الدور الأول 2026 - نظام حديث.accdb"
    output_csv = r"e:\natega\Stage_New_Search_Extracted.csv"

    conn_str = f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={db_path};"

    print("Connecting to Access database...")
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    query = "SELECT seating_no, arabic_name, total_degree FROM Stage_New_Search"
    print("Executing query...")
    cursor.execute(query)

    print("Writing to CSV file...")
    count = 0
    with open(output_csv, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['رقم الجلوس', 'الاسم', 'المجموع'])
        
        batch_size = 50000
        while True:
            rows = cursor.fetchmany(batch_size)
            if not rows:
                break
            writer.writerows(rows)
            count += len(rows)
            print(f"Extracted {count} rows...")

    conn.close()
    end_time = time.time()
    print(f"Done! Successfully extracted {count} rows in {end_time - start_time:.2f} seconds.")

if __name__ == '__main__':
    extract_access_to_csv()
