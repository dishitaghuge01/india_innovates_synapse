from newspaper import Article
import json
import os
from datetime import datetime
import time
RAW_DATA_PATH = "data/raw/articles.json"
SCRAPE_URLS = [

    "https://www.brookings.edu/articles/",
    "https://carnegieendowment.org/publications",
    "https://www.csis.org/analysis",
    "https://www.atlanticcouncil.org/blogs/",
    "https://www.rand.org/pubs.html"

]
def scrape_article(url):

    try:

        article = Article(url)

        article.download()
        article.parse()

        data = {
            "title": article.title,
            "content": article.text,
            "description": article.meta_description,
            "source": url,
            "url": url,
            "published_at": str(article.publish_date or datetime.utcnow())
        }

        return data

    except Exception as e:

        print(f"Failed to scrape {url}: {e}")
        return None
def scrape_all_sources():

    articles = []

    for url in SCRAPE_URLS:

        print(f"Scraping: {url}")

        article = scrape_article(url)

        if article:
            articles.append(article)

    return articles
def remove_duplicates(articles):

    seen_urls = set()
    unique_articles = []

    for article in articles:

        url = article.get("url")

        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_articles.append(article)

    return unique_articles
def save_raw_articles(articles):

    os.makedirs("data/raw", exist_ok=True)

    with open(RAW_DATA_PATH, "a", encoding="utf-8") as f:

        for article in articles:
            f.write(json.dumps(article) + "\n")
def run_web_scraper_agent(interval=1800):

    print("Starting Web Scraper Agent...")

    while True:

        print("\nScraping intelligence sources...")

        articles = scrape_all_sources()

        articles = remove_duplicates(articles)

        print(f"Collected {len(articles)} articles")

        save_raw_articles(articles)

        print("Articles appended to storage")

        print(f"Sleeping for {interval} seconds...")

        time.sleep(interval)
if __name__ == "__main__":

    run_web_scraper_agent(interval=1800)
