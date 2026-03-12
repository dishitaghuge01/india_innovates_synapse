import feedparser
import json
import os
from datetime import datetime
import time

RAW_DATA_PATH = "data/raw/articles.json"

RSS_FEEDS = [
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.reutersagency.com/feed/?best-topics=world",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "https://foreignpolicy.com/feed/",
    "https://www.defensenews.com/arc/outboundfeeds/rss/"
]


def fetch_rss_feed(feed_url):
    """
    Fetch and parse a single RSS feed
    """

    feed = feedparser.parse(feed_url)

    articles = []

    for entry in feed.entries:

        article = {
            "title": entry.get("title"),
            "content": entry.get("summary"),
            "description": entry.get("summary"),
            "source": feed.feed.get("title"),
            "url": entry.get("link"),
            "published_at": entry.get("published", str(datetime.utcnow()))
        }

        articles.append(article)

    return articles


def fetch_all_rss_feeds():
    """
    Fetch articles from all RSS feeds
    """

    all_articles = []

    for feed_url in RSS_FEEDS:

        print(f"Fetching RSS feed: {feed_url}")

        articles = fetch_rss_feed(feed_url)

        all_articles.extend(articles)

    return all_articles


def remove_duplicates(articles):
    """
    Remove duplicate articles using URL
    """

    seen_urls = set()
    unique_articles = []

    for article in articles:

        url = article.get("url")

        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_articles.append(article)

    return unique_articles


def save_raw_articles(articles):
    """
    Append articles to raw storage
    """

    os.makedirs("data/raw", exist_ok=True)

    with open(RAW_DATA_PATH, "a", encoding="utf-8") as f:

        for article in articles:
            f.write(json.dumps(article) + "\n")


def run_rss_ingestion_agent(interval=600):
    """
    Autonomous RSS ingestion agent
    """

    print("Starting RSS Ingestion Agent...")

    while True:

        print("\nFetching RSS intelligence feeds...")

        articles = fetch_all_rss_feeds()

        articles = remove_duplicates(articles)

        print(f"Collected {len(articles)} unique RSS articles")

        save_raw_articles(articles)

        print("Articles appended to data/raw/articles.json")

        print(f"Sleeping for {interval} seconds...\n")

        time.sleep(interval)

def fetch_articles():

    articles = fetch_all_rss_feeds()

    articles = remove_duplicates(articles)

    return articles

if __name__ == "__main__":

    run_rss_ingestion_agent(interval=300)
