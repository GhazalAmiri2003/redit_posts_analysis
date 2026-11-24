"""Reddit credentials are supplied by the local environment, never Git."""
import os

REDDIT_CLIENT_ID = os.environ["REDDIT_CLIENT_ID"]
REDDIT_SECRET = os.environ["REDDIT_SECRET"]
REDDIT_USERNAME = os.getenv("REDDIT_USERNAME") or None
REDDIT_PASSWORD = os.getenv("REDDIT_PASSWORD") or None
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "python:reddit-data-analysis:1.0")

if bool(REDDIT_USERNAME) != bool(REDDIT_PASSWORD):
    raise ValueError("Set both REDDIT_USERNAME and REDDIT_PASSWORD, or neither.")
