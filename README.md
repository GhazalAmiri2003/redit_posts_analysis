# Reddit Data Collection and Sentiment Analysis

A Python data-engineering prototype that collects Reddit posts and comments, calculates sentiment scores and stores results across relational, document and graph databases.

## Data flow

1. A publisher collects recent posts and comments using PRAW.
2. A shared JSON file transfers records to a subscriber process.
3. Posts are stored in MySQL; comments and TextBlob sentiment polarity are stored in MongoDB.
4. Mean comment polarity is aggregated back into MySQL.
5. Neo4j stores post relationships with simulated user nodes and sentiment properties.

The repository also includes a standalone SQLite-based collection script.

## Technologies
Python · PRAW · TextBlob · MySQL · MongoDB · Neo4j · SQLite · Docker Compose

## Repository structure
| File | Purpose |
| --- | --- |
| `RedditPublisher.py` | Collection and serialization |
| `Subscriber.py` | Processing, sentiment analysis and persistence |
| `main.py` | Standalone data collection and analysis |
| `docker-compose.yml` | Local multi-service environment |

## Local setup

Copy `.env.example` to `.env` and supply newly generated credentials locally. Do not commit the actual file. For public-data read-only access, Reddit username and password are optional. Set strong local MySQL and Neo4j passwords.

```bash
docker compose config --quiet
docker compose up --build
```

Existing database volumes may require a separate password migration; do not delete data volumes without a backup. Host ports are bound to localhost. For a standalone Python run, export the Reddit environment variables into the Python process first.

## Status

Educational prototype. The current configuration no longer contains literal Reddit, MySQL or Neo4j credentials. Previously committed credentials must be revoked or rotated; the existing Git history has not been rewritten. The file-based handoff is a prototype rather than a durable message broker. Runtime verification is pending.
