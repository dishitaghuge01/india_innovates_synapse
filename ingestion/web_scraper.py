import requests
from bs4 import BeautifulSoup
from newspaper import Article
from urllib.parse import urlparse

from utils import logger


# =========================
# Headers (VERY IMPORTANT)
# =========================
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


# =========================
# Helper
# =========================
def get_source_name_from_url(url):
    if not url:
        return None
    return urlparse(url).hostname


# =========================
# Method 1: BeautifulSoup
# =========================
def scrape_with_bs4(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=5)

        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        # Extract paragraphs
        paragraphs = soup.find_all("p")
        text = " ".join([p.get_text() for p in paragraphs])

        title = soup.title.string if soup.title else None

        if not text or len(text) < 200:
            return None

        return {
            "raw_text": text,
            "source_title": title,
            "author": None,
            "published_at": None,
        }

    except Exception as e:
        logger.debug(f"BS4 scrape failed: {url} | {e}")
        return None


# =========================
# Method 2: newspaper3k (fallback)
# =========================
def scrape_with_newspaper(url):
    try:
        article = Article(url)
        article.download()
        article.parse()

        return {
            "raw_text": article.text,
            "source_title": article.title,
            "author": article.authors[0] if article.authors else None,
            "published_at": article.publish_date.isoformat() if article.publish_date else None,
        }

    except Exception as e:
        logger.debug(f"Newspaper scrape failed: {url} | {e}")
        return None


# =========================
# Main scraper
# =========================
def scrape_article(url):
    # 1️⃣ Try BeautifulSoup first
    data = scrape_with_bs4(url)

    if data:
        return data

    # 2️⃣ Fallback to newspaper3k
    data = scrape_with_newspaper(url)

    if data:
        return data

    # ❌ Final failure
    logger.debug(f"All scraping methods failed: {url}")
    return None
