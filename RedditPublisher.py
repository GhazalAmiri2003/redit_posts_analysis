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

subreddit = reddit.subreddit("technology")
seen_posts = set()

while True:
    for post in subreddit.new(limit=40):
        if post.id in seen_posts:
            continue

        # ذخیره پست
        post_data = post_to_json(post)
        with open("sensor_data.json", "w", encoding="utf-8") as f:
            json.dump(post_data, f, indent=2, ensure_ascii=False)
        print(f"[PUBLISHER] ✅ Sent post: {post.title}")
        time.sleep(2)

        # ذخیره تا ۳ کامنت از همان پست
        post.comments.replace_more(limit=0)
        comments = post.comments[:3]  # تا ۳ کامنت اول
        for comment in comments:
            comment_data = comment_to_json(comment, post.id)
            with open("sensor_data.json", "w", encoding="utf-8") as f:
                json.dump(comment_data, f, indent=2, ensure_ascii=False)
            print(f"[PUBLISHER] 💬 Sent comment: {comment.body[:40]}...")
            time.sleep(2)

        seen_posts.add(post.id)

    time.sleep(10)
