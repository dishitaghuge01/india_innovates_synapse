import requests
import time
import json
import os

from utils.config import NEWS_API_KEY

# NewsAPI endpoint
NEWS_URL = "https://newsapi.org/v2/everything"

# Path to store raw articles
RAW_DATA_PATH = "data/raw/articles.json"


def fetch_news(query="geopolitics", page_size=10):
    """
    Fetch news articles from NewsAPI for a specific query
    """

    params = {
        "q": query,
        "language": "en",
        "pageSize": page_size,
        "apiKey": NEWS_API_KEY
    }

    try:
        response = requests.get(NEWS_URL, params=params)

        if response.status_code != 200:
            print("Error fetching news:", response.text)
            return []

        data = response.json()

        articles = []

        for article in data.get("articles", []):

            articles.append({
                "title": article.get("title"),
                "content": article.get("content"),
                "description": article.get("description"),
                "source": article.get("source", {}).get("name"),
                "url": article.get("url"),
                "published_at": article.get("publishedAt")
            })

        return articles

    except Exception as e:
        print("Exception while fetching news:", e)
        return []


def fetch_multiple_topics():
    """
    Fetch news from multiple intelligence-related domains
    """

    topics = [
        "geopolitics",
        "semiconductor supply chain",
        "defense technology",
        "energy markets",
        "international trade"
    ]

    all_articles = []

    for topic in topics:

        print(f"Fetching topic: {topic}")

        articles = fetch_news(query=topic)

        all_articles.extend(articles)

    return all_articles


def save_raw_articles(articles):
    """
    Save raw articles to disk for later processing
    """

    os.makedirs("data/raw", exist_ok=True)

    with open(RAW_DATA_PATH, "a", encoding="utf-8") as f:

        for article in articles:
            f.write(json.dumps(article) + "\n")


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


def run_ingestion_agent(interval=600):
    """
    Autonomous ingestion agent

    interval = seconds between ingestion runs
    default = 10 minutes
    """

    print("Starting News Ingestion Agent...")

    while True:

        print("\nFetching latest intelligence data...")

        articles = fetch_multiple_topics()

        articles = remove_duplicates(articles)

        print(f"Collected {len(articles)} unique articles")

        save_raw_articles(articles)

        print("Articles saved to data/raw/articles.json")

        print(f"Sleeping for {interval} seconds...")

        time.sleep(interval)

def fetch_articles():

    articles = fetch_news()

    articles = remove_duplicates(articles)

    return articles


if __name__ == "__main__":

    run_ingestion_agent(interval=300)
