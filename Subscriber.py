import os
import json
import time
import mysql.connector
from pymongo import MongoClient
from textblob import TextBlob

DATA_FILE = "sensor_data.json"

# اتصال به MySQL
mysql_conn = mysql.connector.connect(
    host=os.environ.get("MYSQL_HOST", "localhost"),
    user=os.environ.get("MYSQL_USER", "root"),
    password=os.environ.get("MYSQL_PASSWORD", "root"),
    database=os.environ.get("MYSQL_DATABASE", "reddit_data"),
    port=int(os.environ.get("MYSQL_PORT", 3306))
)
mysql_cursor = mysql_conn.cursor()

# ساخت جدول پست‌ها اگر وجود نداشت
mysql_cursor.execute('''
    CREATE TABLE IF NOT EXISTS reddit_posts (
        id VARCHAR(255) PRIMARY KEY,
        title TEXT,
        score INT,
        url TEXT,
        created_utc DOUBLE,
        polarity FLOAT
    )
''')
mysql_conn.commit()

# اتصال به MongoDB
mongo_client = MongoClient("mongodb://mongo:27017/")
mongo_db = mongo_client["reddit_data"]
mongo_comments = mongo_db["reddit_comments"]

print("[SUBSCRIBER] ✅ Subscriber started...")

while True:
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            if data.get("type") == "post":
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
                print(f"[SUBSCRIBER] ✅ Saved post to MySQL: {data['title'][:40]}...")

            elif data.get("type") == "comment":
                polarity = TextBlob(data["text"]).sentiment.polarity

                mongo_comments.update_one(
                    {"comment_id": data["comment_id"]},
                    {"$set": {
                        "post_id": data["post_id"],
                        "text": data["text"],
                        "created_utc": data["created_utc"],
                        "polarity": polarity
                    }},
                    upsert=True
                )
                print(f"[SUBSCRIBER] 💬 Saved comment with polarity={polarity:.2f}")

                # محاسبه و ثبت polarity نهایی در MySQL
                comments = list(mongo_comments.find({"post_id": data["post_id"]}))
                if comments:
                    avg_polarity = sum(c.get("polarity", 0) for c in comments) / len(comments)
                    mysql_cursor.execute("""
                        UPDATE reddit_posts
                        SET polarity = %s
                        WHERE id = %s
                    """, (
                        avg_polarity,
                        data["post_id"]
                    ))
                    mysql_conn.commit()
                    print(f"[SUBSCRIBER] ✅ Updated final polarity for post {data['post_id']}: {avg_polarity:.2f}")

            else:
                print("[SUBSCRIBER] ⚠️ Unknown data type")

            os.remove(DATA_FILE)
            continue

        except Exception as e:
            print("[SUBSCRIBER] ❌ Error while processing data:", e)

    time.sleep(1)
