import feedparser
import json
import os
from datetime import datetime
import time

from ingestion.ingestion_utils import (
    generate_article_id,
    normalize_published_at,
    validate_article
)
from ingestion.web_scraper import scrape_article
from utils import logger

RAW_DATA_PATH = "data/raw/articles.json"

RSS_FEEDS = [
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.reutersagency.com/feed/?best-topics=world",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "https://foreignpolicy.com/feed/",
    "https://www.defensenews.com/arc/outboundfeeds/rss/"
]

# =========================
# Domains where scraping is useless / blocked
# =========================
BLOCKED_DOMAINS = [
    "nytimes.com",   # blocks bots
]


def should_scrape(url):
    return not any(domain in url for domain in BLOCKED_DOMAINS)


# =========================
# SAFE scraping (non-blocking)
# =========================
def safe_scrape(url):
    try:
        return scrape_article(url)
    except Exception:
        return None


# =========================
# Extract published_at robustly
# =========================
def extract_published_at(entry, scraped):

    # RSS fields first
    published = entry.get("published") or entry.get("updated")

    if published:
        normalized = normalize_published_at(published)
        if normalized:
            return normalized

    # RSS parsed fallback (BBC fix)
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        try:
            return datetime(*entry.published_parsed[:6]).isoformat()
        except Exception:
            pass

    # Scraper fallback
    if scraped:
        return scraped.get("published_at")

    return None


# =========================
# Build article object
# =========================
def build_article(entry, source_name):

    source_url = entry.get("link")
    if not source_url:
        return None

    # 🟢 PRIMARY RSS DATA (always reliable)
    title = entry.get("title")
    summary = entry.get("summary")

    # 🟡 OPTIONAL scraping (only if allowed)
    scraped = None
    if should_scrape(source_url):
        scraped = safe_scrape(source_url)

    # 🟣 Extract published_at
    published_at = extract_published_at(entry, scraped)

    if not published_at:
        logger.debug(f"Missing published_at: {source_url}")

    # 🟣 Build text content
    if scraped:
        raw_text = scraped.get("raw_text") or summary
        author = scraped.get("author")
        scraped_title = scraped.get("source_title")

        if scraped_title:
            title = scraped_title
    else:
        raw_text = summary
        author = None

    # Ensure raw_text always exists
    if not raw_text:
        raw_text = ""

    # 🟣 Final article object
    article = {
        "article_id": generate_article_id(source_url),
        "source_url": source_url,
        "source_title": title,
        "source_name": source_name,
        "published_at": published_at,
        "raw_text": raw_text,
        "author": author,
    }

    # Soft validation
    if not validate_article(article):
        logger.warning(f"Validation failed: {source_url}")
        return None

    return article


# =========================
# Fetch single feed
# =========================
def fetch_rss_feed(feed_url):

    feed = feedparser.parse(feed_url)
    source_name = feed.feed.get("title", "Unknown Source")

    articles = []

    for entry in feed.entries:
        article = build_article(entry, source_name)
        if article:
            articles.append(article)

    logger.info(f"Fetched {len(articles)} articles from {feed_url}")
    return articles


# =========================
# Fetch all feeds
# =========================
def fetch_all_rss_feeds():

    all_articles = []

    for feed_url in RSS_FEEDS:
        logger.info(f"Fetching RSS feed: {feed_url}")
        articles = fetch_rss_feed(feed_url)
        all_articles.extend(articles)

    logger.info(f"Collected {len(all_articles)} articles from all feeds")
    return all_articles


# =========================
# Remove duplicates
# =========================
def remove_duplicates(articles):

    seen_urls = set()
    unique_articles = []

    for article in articles:
        url = article.get("source_url")

        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_articles.append(article)

    return unique_articles


# =========================
# Save
# =========================
def save_raw_articles(articles):

    os.makedirs("data/raw", exist_ok=True)

    with open(RAW_DATA_PATH, "a", encoding="utf-8") as f:
        for article in articles:
            f.write(json.dumps(article) + "\n")


# =========================
# Agent
# =========================
def run_rss_ingestion_agent(interval=600):

    logger.info("Starting RSS Ingestion Agent...")

    while True:

        logger.info("\nFetching RSS feeds...")

        articles = fetch_all_rss_feeds()
        articles = remove_duplicates(articles)

        logger.info(f"Collected {len(articles)} unique articles")

        save_raw_articles(articles)

        logger.info("Saved articles to data/raw/articles.json")
        logger.info(f"Sleeping for {interval} seconds...\n")

        time.sleep(interval)


# =========================
# Entry point
# =========================
def fetch_articles():

    articles = fetch_all_rss_feeds()
    articles = remove_duplicates(articles)

    return articles


if __name__ == "__main__":
    run_rss_ingestion_agent(interval=300)
