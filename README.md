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

## Status
Educational prototype. Before running or deploying it, replace committed credentials with environment-based configuration, revoke any previously exposed credentials, review the Git history and verify the local database settings. The file-based handoff is a prototype rather than a durable message broker. No independent runtime verification is claimed.
