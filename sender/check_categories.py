import sqlite3

conn = sqlite3.connect("worker_data.db")
cur = conn.cursor()
cur.execute("SELECT value FROM platform_settings WHERE platform = 'krisha' AND key = 'categories'")
row = cur.fetchone()
conn.close()

if row:
    print("Raw value from DB:", row[0])
    try:
        import json
        cats = json.loads(row[0])
        print("Parsed categories as list:", cats)
        print("Count:", len(cats))
    except Exception as e:
        print("Ошибка при обработке как JSON:", e)
else:
    print("Нет категорий для krisha")