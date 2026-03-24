import os
import importlib
import json
import time

from ingestion.ingestion_utils import validate_article
from utils import logger

INGESTION_FOLDER = "ingestion"
RAW_DATA_PATH = "data/raw/articles.json"


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

    with open(RAW_DATA_PATH, "a", encoding="utf-8") as f:
        for article in articles:
            f.write(json.dumps(article) + "\n")


def run_ingestion_pipeline(interval=600):
    logger.info("Starting Ingestion Manager...")

    while True:
        logger.info("\nRunning ingestion cycle...")

        articles = run_ingestion()

        save_articles(articles)

        logger.info(f"Articles saved to storage ({len(articles)})")
        logger.info(f"Sleeping for {interval} seconds...\n")

        time.sleep(interval)


if __name__ == "__main__":
    run_ingestion_pipeline(interval=600)
