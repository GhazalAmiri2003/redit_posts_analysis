import os
import json
import time
import praw

# تنظیمات Reddit در reddit_config.py یا از env بارگذاری شود
import reddit_config

DATA_FILE = "/app/sensor_data.json"

def write_safely(data):
    while os.path.exists(DATA_FILE + ".lock"):
        time.sleep(0.1)
    open(DATA_FILE + ".lock", "w").close()
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    finally:
        os.remove(DATA_FILE + ".lock")

def post_to_json(post):
    return {
        "type": "post",
        "id": post.id,
        "title": post.title,
        "score": post.score,
        "url": post.url,
        "created_utc": post.created_utc
    }

def comment_to_json(comment, post_id):
    return {
        "type": "comment",
        "comment_id": comment.id,
        "post_id": post_id,
        "text": comment.body,
        "created_utc": comment.created_utc
    }

reddit = praw.Reddit(
    client_id=reddit_config.REDDIT_CLIENT_ID,
    client_secret=reddit_config.REDDIT_SECRET,
    username=reddit_config.REDDIT_USERNAME,
    password=reddit_config.REDDIT_PASSWORD,
    user_agent=reddit_config.REDDIT_USER_AGENT
)

seen_posts = set()
subreddit = reddit.subreddit("technology")

print("[PUBLISHER] ✅ Publisher started…")

while True:
    try:
        for post in subreddit.new(limit=40):
            if post.id in seen_posts:
                continue

            write_safely(post_to_json(post))
            print(f"[PUBLISHER] Sent post: {post.title[:30]}…")
            time.sleep(2)

            post.comments.replace_more(limit=0)
            for comment in post.comments[:3]:
                write_safely(comment_to_json(comment, post.id))
                print(f"[PUBLISHER] Sent comment: {comment.body[:30]}…")
                time.sleep(2)

            seen_posts.add(post.id)

        time.sleep(10)

    except Exception as e:
        print(f"[PUBLISHER] خطای کلی: {e}")
        time.sleep(5)
