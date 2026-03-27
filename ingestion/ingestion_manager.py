import os
import importlib
import json
import time
import hashlib
import argparse

from ingestion.ingestion_utils import validate_article
from utils import logger

INGESTION_FOLDER = "ingestion"
RAW_DATA_PATH = "data/raw/articles.json"

CACHE_DIR = "data/cache"
PROCESSED_ARTICLES_PATH = os.path.join(CACHE_DIR, "processed_articles.json")


def discover_ingestors():
    ingestors = []
    for file in os.listdir(INGESTION_FOLDER):
        if file.endswith("_ingestor.py") or file == "web_scraper.py":
            module_name = file.replace(".py", "")
            ingestors.append(module_name)
    return ingestors


def load_ingestor(module_name):
    module_path = f"{INGESTION_FOLDER}.{module_name}"
    return importlib.import_module(module_path)


def run_all_ingestors():
    ingestor_modules = discover_ingestors()
    all_articles = []

    for module_name in ingestor_modules:
        logger.info(f"Running ingestor: {module_name}")
        module = load_ingestor(module_name)

        if hasattr(module, "fetch_articles"):
            articles = module.fetch_articles() or []
            logger.info(f"Collected {len(articles)} articles from {module_name}")
            all_articles.extend(articles)

    return all_articles


def drop_invalid_articles(articles):
    valid_articles = []

    for article in articles:
        if validate_article(article):
            valid_articles.append(article)
        else:
            logger.warning(f"Dropping invalid article URL {article.get('source_url')}")

    return valid_articles


def run_ingestion():
    logger.info("Starting ingestion run...")
    articles = run_all_ingestors()

    logger.info(f"Total raw articles collected: {len(articles)}")

    articles = drop_invalid_articles(articles)
    logger.info(f"Total valid articles after validation: {len(articles)}")

    return articles


def save_articles(articles):
    os.makedirs("data/raw", exist_ok=True)
    os.makedirs(CACHE_DIR, exist_ok=True)

    # Load processed articles
    processed_articles = {}
    if os.path.exists(PROCESSED_ARTICLES_PATH):
        with open(PROCESSED_ARTICLES_PATH, "r", encoding="utf-8") as f:
            processed_articles = json.load(f)

    new_articles = []
    for article in articles:
        # Compute hash
        if article.get("article_id"):
            article_hash = hashlib.md5(article["article_id"].encode()).hexdigest()
        else:
            content = f"{article.get('source_title', '')} {article.get('raw_text', '')}"
            article_hash = hashlib.md5(content.encode()).hexdigest()

        if article_hash not in processed_articles:
            new_articles.append(article)
            processed_articles[article_hash] = article.get("published_at") or ""

    # Save new articles
    with open(RAW_DATA_PATH, "a", encoding="utf-8") as f:
        for article in new_articles:
            f.write(json.dumps(article) + "\n")

    # Save updated processed articles
    with open(PROCESSED_ARTICLES_PATH, "w", encoding="utf-8") as f:
        json.dump(processed_articles, f, indent=2)

    logger.info(f"Saved {len(new_articles)} new articles")


def run_ingestion_pipeline(interval=600):
    logger.info("Starting Ingestion Manager...")

    while True:
        logger.info("\nRunning ingestion cycle...")

        articles = run_ingestion()

        save_articles(articles)

        logger.info(f"Articles saved to storage ({len(articles)})")
        logger.info(f"Sleeping for {interval} seconds...\n")

        time.sleep(interval)


def run_ingestion_once():
    logger.info("Running single ingestion cycle...")
    articles = run_ingestion()
    save_articles(articles)
    logger.info(f"Single ingestion cycle completed ({len(articles)} articles)")


def parse_args():
    parser = argparse.ArgumentParser(description="Run ingestion manager")
    parser.add_argument(
        "--loop", action="store_true", help="Run continuously with sleep interval"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=600,
        help="Polling interval in seconds for loop mode",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if args.loop:
        run_ingestion_pipeline(interval=args.interval)
    else:
        run_ingestion_once()
