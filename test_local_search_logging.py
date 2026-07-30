import urllib.request
import json

# Send local search ping
try:
    url = "http://127.0.0.1:5000/api/search_ping?q=%D8%A7%D8%AE%D8%AA%D8%A8%D8%A7%D8%B1_%D9%85%D8%AD%D9%84%D9%8A_%D8%AA%D8%A3%D9%83%D9%8A%D8%AF%D9%8A&mode=name"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 TestLocalBrowser'})
    with urllib.request.urlopen(req) as response:
        print("Ping Response:", response.read().decode('utf-8'))

    # Fetch admin logs from local server
    admin_url = "http://127.0.0.1:5000/api/admin/logs?key=admin123"
    with urllib.request.urlopen(admin_url) as res:
        logs_data = json.loads(res.read().decode('utf-8'))
        print("Total Searches in Local DB:", logs_data.get('total_searches'))
        print("Latest 3 Log Entries:")
        for log in logs_data.get('logs', [])[:3]:
            print(f" - [{log['timestamp']}] IP: {log['ip']} | Query: {log['query']}")
except Exception as e:
    print("Error:", e)
