import os
import json
import sqlite3
import time
import mysql.connector

DB_FILE = "subscriber_data.db"
DATA_FILE = "sensor_data.json"

# اتصال به SQLite و ساخت جدول
sqlite_conn = sqlite3.connect(DB_FILE)
sqlite_cursor = sqlite_conn.cursor()
sqlite_cursor.execute('''
    CREATE TABLE IF NOT EXISTS reddit_posts (
        id TEXT PRIMARY KEY,
        title TEXT,
        score INTEGER,
        url TEXT,
        created_utc REAL
    )
''')
sqlite_conn.commit()

# اتصال به MySQL با استفاده از ENV
mysql_conn = mysql.connector.connect(
    host=os.environ.get("MYSQL_HOST", "localhost"),
    user=os.environ.get("MYSQL_USER", "root"),
    password=os.environ.get("MYSQL_PASSWORD", "root"),
    database=os.environ.get("MYSQL_DATABASE", "reddit_data"),
    port=int(os.environ.get("MYSQL_PORT", 3308))
)
mysql_cursor = mysql_conn.cursor()

# ساخت جدول در MySQL اگر وجود نداشته باشد
mysql_cursor.execute('''
    CREATE TABLE IF NOT EXISTS reddit_posts (
        id VARCHAR(255) PRIMARY KEY,
        title TEXT,
        score INT,
        url TEXT,
        created_utc DOUBLE
    )
''')
mysql_conn.commit()

print("[SUBSCRIBER] Waiting for data...")
print("[DEBUG] Subscriber started running...")

while True:
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)

            # درج در SQLite
            sqlite_cursor.execute('''
                INSERT OR REPLACE INTO reddit_posts (id, title, score, url, created_utc)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                data["id"],
                data["title"],
                data["score"],
                data["url"],
                data["created_utc"]
            ))
            sqlite_conn.commit()
            print(f"[SUBSCRIBER] Saved to SQLite: {data['title']}")

            # درج در MySQL
            mysql_cursor.execute('''
                INSERT INTO reddit_posts (id, title, score, url, created_utc)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    title = VALUES(title),
                    score = VALUES(score),
                    url = VALUES(url),
                    created_utc = VALUES(created_utc)
            ''', (
                data["id"],
                data["title"],
                data["score"],
                data["url"],
                data["created_utc"]
            ))
            mysql_conn.commit()
            print(f"[SUBSCRIBER] Saved to MySQL: {data['title']}")

            os.remove(DATA_FILE)

        except Exception as e:
            print("[SUBSCRIBER] Error:", e)

    time.sleep(2)
