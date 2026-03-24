import requests
import json
import os

from ingestion.ingestion_utils import generate_article_id, normalize_published_at, validate_article
from utils import logger

RAW_DATA_PATH = "data/raw/articles.json"
NEWS_URL = "https://newsapi.org/v2/everything"

try:
    from utils.config import NEWS_API_KEY
except ImportError:
    NEWS_API_KEY = None


def build_article_object(article):
    source_url = article.get("url")
    raw_text = article.get("content") or article.get("description") or ""

    obj = {
        "article_id": generate_article_id(source_url) if source_url else None,
        "source_url": source_url,
        "source_title": article.get("title"),
        "source_name": article.get("source", {}).get("name") or article.get("source"),
        "published_at": normalize_published_at(article.get("publishedAt")),
        "raw_text": raw_text,
        "author": article.get("author"),
    }

    if not validate_article(obj):
        return None

    return obj


def fetch_news(query="geopolitics", page_size=10):
    params = {
        "q": query,
        "language": "en",
        "pageSize": page_size,
        "apiKey": NEWS_API_KEY,
    }

    try:
        if not NEWS_API_KEY:
            logger.warning("NEWS_API_KEY is missing; fetch_news cannot run")
            return []

        response = requests.get(NEWS_URL, params=params, timeout=30)

        if response.status_code != 200:
            logger.warning(f"Error fetching news: {response.status_code} {response.text}")
            return []

        data = response.json()

        articles = []

        for article in data.get("articles", []):
            normalized = build_article_object(article)
            if normalized:
                articles.append(normalized)

        logger.info(f"Fetched {len(articles)} valid news articles for query '{query}'")
        return articles

    except Exception as e:
        logger.error(f"Exception while fetching news: {e}")
        return []


def fetch_multiple_topics():
    topics = [
        "geopolitics",
        "semiconductor supply chain",
        "defense technology",
        "energy markets",
        "international trade",
    ]

    all_articles = []

    for topic in topics:
        logger.info(f"Fetching topic: {topic}")
        articles = fetch_news(query=topic)
        all_articles.extend(articles)

    logger.info(f"Collected {len(all_articles)} articles from news topics")
    return all_articles


if __name__ == "__main__":
    fetched = fetch_multiple_topics()
    logger.info(f"Total results: {len(fetched)}")
