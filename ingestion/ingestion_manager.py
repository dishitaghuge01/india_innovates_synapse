import os
import importlib
import json
import time

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

    module = importlib.import_module(module_path)

    return module

def run_all_ingestors():

    ingestor_modules = discover_ingestors()

    all_articles = []

    for module_name in ingestor_modules:

        print(f"Running ingestor: {module_name}")

        module = load_ingestor(module_name)

        if hasattr(module, "fetch_articles"):

            articles = module.fetch_articles()

            print(f"Collected {len(articles)} articles")

            all_articles.extend(articles)

    return all_articles

def remove_duplicates(articles):

    seen_urls = set()
    unique_articles = []

    for article in articles:

        url = article.get("url")

        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_articles.append(article)

    return unique_articles

def save_articles(articles):

    os.makedirs("data/raw", exist_ok=True)

    with open(RAW_DATA_PATH, "a", encoding="utf-8") as f:

        for article in articles:
            f.write(json.dumps(article) + "\n")

def run_ingestion_pipeline(interval=600):

    print("Starting Ingestion Manager...")

    while True:

        print("\nRunning ingestion cycle...")

        articles = run_all_ingestors()

        articles = remove_duplicates(articles)

        print(f"Total unique articles: {len(articles)}")

        save_articles(articles)

        print("Articles saved to storage")

        print(f"Sleeping for {interval} seconds...\n")

        time.sleep(interval)

if __name__ == "__main__":

    run_ingestion_pipeline(interval=600)

