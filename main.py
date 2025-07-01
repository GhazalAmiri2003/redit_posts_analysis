import praw
import reddit_config  # فایل تنظیماتی که ساختی
from textblob import TextBlob

# اتصال به Reddit
reddit = praw.Reddit(
    client_id=reddit_config.REDDIT_CLIENT_ID,
    client_secret=reddit_config.REDDIT_SECRET,
    username=reddit_config.REDDIT_USERNAME,
    password=reddit_config.REDDIT_PASSWORD,
    user_agent=reddit_config.REDDIT_USER_AGENT
)

# انتخاب یک subreddit، مثلا r/technology
subreddit = reddit.subreddit("technology")

# گرفتن 5 پست جدید
for post in subreddit.new(limit=5):
    print("Title:", post.title)
    # تحلیل احساسات
    blob = TextBlob(post.title)
    polarity = blob.sentiment.polarity  # بین -1 و +1

    if polarity > 0:
        sentiment = "positive"
    elif polarity < 0:
        sentiment = "negative"
    else:
        sentiment = "neutral"

    print("Sentiment:", sentiment)
    print("Polarity Score:", polarity)
    print("-" * 50)

    print("Score:", post.score)
    print("Created:", post.created_utc)
    print("URL:", post.url)
    print("-" * 50)
import sqlite3

# اتصال به دیتابیس (اگر وجود نداشته باشه، می‌سازه)
conn = sqlite3.connect("reddit_posts.db")
cursor = conn.cursor()

# ساخت جدول اگر وجود نداشت
cursor.execute('''
CREATE TABLE IF NOT EXISTS posts (
    id TEXT PRIMARY KEY,
    title TEXT,
    score INTEGER,
    url TEXT
)
''')

# ذخیره پست‌ها
for post in subreddit.new(limit=5):
    print("Title:", post.title)
    print("Score:", post.score)
    print("URL:", post.url)
    print("-" * 50)

    cursor.execute('''
        INSERT OR REPLACE INTO posts (id, title, score, url)
        VALUES (?, ?, ?, ?)
    ''', (post.id, post.title, post.score, post.url))

# ذخیره تغییرات
conn.commit()
conn.close()
