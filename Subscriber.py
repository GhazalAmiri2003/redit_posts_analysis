import os
import json
import time
import mysql.connector
from mysql.connector import Error
from pymongo import MongoClient
from textblob import TextBlob
from neo4j import GraphDatabase, exceptions as neo4j_exc

DATA_FILE = "/app/sensor_data.json"
FAKE_USER_COUNT = 10
user_index = 0

def wait_for_mysql():
    while True:
        try:
            conn = mysql.connector.connect(
                host=os.environ["MYSQL_HOST"],
                port=int(os.environ["MYSQL_PORT"]),
                user=os.environ["MYSQL_USER"],
                password=os.environ["MYSQL_ROOT_PASSWORD"],  # ← اینجا تغییر کرد
                database=os.environ["MYSQL_DATABASE"],
                charset="utf8mb4",
                use_unicode=True
            )
            conn.close()
            break
        except Error:
            print("[WAIT] منتظر MySQL …")
            time.sleep(2)

def wait_for_mongo():
    while True:
        try:
            client = MongoClient(
                f"mongodb://{os.environ['MONGO_HOST']}:{os.environ['MONGO_PORT']}/",
                serverSelectionTimeoutMS=2000
            )
            client.admin.command('ping')
            client.close()
            break
        except Exception:
            print("[WAIT] منتظر MongoDB …")
            time.sleep(2)

def wait_for_neo4j():
    uri = os.environ["NEO4J_URI"]
    auth = (os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"])
    while True:
        try:
            driver = GraphDatabase.driver(uri, auth=auth)
            with driver.session() as session:
                session.run("RETURN 1").single()
            driver.close()
            break
        except neo4j_exc.ServiceUnavailable:
            print("[WAIT] منتظر Neo4j …")
            time.sleep(2)

# صبر می‌کنیم تا همهٔ سرویس‌ها آماده شوند
wait_for_mysql()
wait_for_mongo()
wait_for_neo4j()

# اتصال به MySQL (utf8mb4)
mysql_conn = mysql.connector.connect(
    host=os.environ["MYSQL_HOST"],
    port=int(os.environ["MYSQL_PORT"]),
    user=os.environ["MYSQL_USER"],
    password=os.environ["MYSQL_ROOT_PASSWORD"],  # ← اینجا هم تغییر دادیم
    database=os.environ["MYSQL_DATABASE"],
    charset="utf8mb4",
    use_unicode=True
)
mysql_cursor = mysql_conn.cursor()

# اطمینان از charset دیتابیس/جدول
mysql_cursor.execute(f"ALTER DATABASE `{os.environ['MYSQL_DATABASE']}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
mysql_cursor.execute('''
    CREATE TABLE IF NOT EXISTS reddit_posts (
        id VARCHAR(255) PRIMARY KEY,
        title TEXT,
        score INT,
        url TEXT,
        created_utc DOUBLE,
        polarity FLOAT
    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
''')
mysql_conn.commit()

# اتصال به MongoDB
mongo_client = MongoClient(f"mongodb://{os.environ['MONGO_HOST']}:{os.environ['MONGO_PORT']}/")
mongo_db = mongo_client["reddit_data"]
mongo_comments = mongo_db["reddit_comments"]

# اتصال به Neo4j
neo4j_driver = GraphDatabase.driver(
    os.environ["NEO4J_URI"],
    auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"])
)

# ساخت کاربران فیک
def create_fake_users(tx):
    for i in range(1, FAKE_USER_COUNT + 1):
        tx.run("MERGE (:User {id: $id})", id=f"user_{i}")

with neo4j_driver.session() as session:
    session.execute_write(create_fake_users)

print("[SUBSCRIBER] ✅ Subscriber started…")

while True:
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            print(f"[DEBUG] دریافت داده: {data.get('type')}")

            if data["type"] == "post":
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
                print(f"[SUBSCRIBER] ذخیره پست در MySQL: {data['title'][:30]}…")

            elif data["type"] == "comment":
                polarity = TextBlob(data["text"]).sentiment.polarity
                mongo_comments.update_one(
                    {"comment_id": data["comment_id"]},
                    {"$set":{
                        "post_id": str(data["post_id"]),
                        "text": data["text"],
                        "created_utc": data["created_utc"],
                        "polarity": polarity
                    }},
                    upsert=True
                )
                print(f"[SUBSCRIBER] ذخیره کامنت در MongoDB (polarity={polarity:.2f})")

                # میانگین polarity
                comments = list(mongo_comments.find({"post_id": str(data["post_id"])}))
                if comments:
                    avg_polarity = sum(c["polarity"] for c in comments) / len(comments)
                    mysql_cursor.execute(
                        "UPDATE reddit_posts SET polarity=%s WHERE id=%s",
                        (avg_polarity, data["post_id"])
                    )
                    mysql_conn.commit()
                    print(f"[SUBSCRIBER] بروزرسانی polarity در MySQL: {avg_polarity:.2f}")

                # ذخیره در Neo4j
                user_id = f"user_{(user_index % FAKE_USER_COUNT) + 1}"
                post_id = str(data["post_id"])
                def save_rel(tx, user_id, post_id, polarity):
                    tx.run("""
                        MERGE (p:Post {id: $post_id})
                        MERGE (u:User {id: $user_id})
                        MERGE (u)-[r:COMMENTED_ON]->(p)
                        SET r.polarity = $polarity
                    """, user_id=user_id, post_id=post_id, polarity=polarity)
                with neo4j_driver.session() as session:
                    session.execute_write(save_rel, user_id, post_id, polarity)
                print(f"[SUBSCRIBER] ثبت رابطه Neo4j: {user_id}→{post_id}")
                user_index += 1

            os.remove(DATA_FILE)

        except Exception as e:
            print(f"[SUBSCRIBER] خطا هنگام پردازش: {e}")

    time.sleep(1)
