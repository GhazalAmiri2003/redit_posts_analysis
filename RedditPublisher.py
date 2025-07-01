import praw
import reddit_config
import json
import time

# اتصال به Reddit
reddit = praw.Reddit(
    client_id=reddit_config.REDDIT_CLIENT_ID,
    client_secret=reddit_config.REDDIT_SECRET,
    username=reddit_config.REDDIT_USERNAME,
    password=reddit_config.REDDIT_PASSWORD,
    user_agent=reddit_config.REDDIT_USER_AGENT
)

# تابع برای تبدیل پست به فرمت JSON ساده
def post_to_json(post):
    return {
        "id": post.id,
        "title": post.title,
        "score": post.score,
        "url": post.url,
        "created_utc": post.created_utc
    }

# حلقه اصلی: هر 5 ثانیه یک پست جدید
seen_ids = set()

while True:
    subreddit = reddit.subreddit("technology")
    for post in subreddit.new(limit=5):
        if post.id not in seen_ids:
            data = post_to_json(post)
            with open("sensor_data.json", "w") as f:
                json.dump(data, f, indent=2)
            print(f"[PUBLISHER] Sent post: {post.title}")
            seen_ids.add(post.id)
            break  # فقط یکی در هر بار

    time.sleep(5)
