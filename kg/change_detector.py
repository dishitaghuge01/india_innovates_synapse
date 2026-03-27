import json
import hashlib
from pathlib import Path

HASH_DB = Path("data/processed/article_hashes.json")

def load_hashes():
    if HASH_DB.exists():
        with open(HASH_DB, "r") as f:
            return set(json.load(f))
    return set()

def save_hashes(hashes):
    with open(HASH_DB, "w") as f:
        json.dump(list(hashes), f)

def hash_article(article_text):
    return hashlib.md5(article_text.encode()).hexdigest()

def filter_new_articles(articles):

    existing_hashes = load_hashes()
    new_articles = []
    new_hashes = set()

    for article in articles:

        content = article.get("content", "")
        h = hash_article(content)

        if h not in existing_hashes:
            new_articles.append(article)
            new_hashes.add(h)

    # update DB
    existing_hashes.update(new_hashes)
    save_hashes(existing_hashes)

    return new_articles
