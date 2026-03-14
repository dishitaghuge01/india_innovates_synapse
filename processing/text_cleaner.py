import re
import json
import os


RAW_DATA_PATH = "data/raw/articles.json"
CLEAN_DATA_PATH = "data/processed/clean_articles.json"

MAX_ARTICLE_LENGTH = 2000


def remove_urls(text):
    return re.sub(r"http\S+|www\S+|https\S+", "", text)


def remove_html(text):
    return re.sub(r"<.*?>", "", text)


def normalize_whitespace(text):
    return re.sub(r"\s+", " ", text).strip()


def remove_special_characters(text):
    return re.sub(r"[^\w\s\.,!?-]", "", text)


def truncate_text(text, max_length=MAX_ARTICLE_LENGTH):
    return text[:max_length]


def clean_text(text):

    if not text:
        return ""

    text = remove_html(text)
    text = remove_urls(text)
    text = remove_special_characters(text)
    text = normalize_whitespace(text)
    text = truncate_text(text)

    return text


def clean_article(article):

    cleaned = {
        "title": clean_text(article.get("title", "")),
        "content": clean_text(article.get("content", "")),
        "description": clean_text(article.get("description", "")),
        "source": article.get("source"),
        "url": article.get("url"),
        "published_at": article.get("published_at")
    }

    return cleaned


def clean_articles(articles):

    cleaned_articles = []

    for article in articles:

        cleaned = clean_article(article)

        if cleaned["content"]:
            cleaned_articles.append(cleaned)

    return cleaned_articles


# -----------------------------
# DATA LOADING
# -----------------------------

def load_articles():

    articles = []

    if not os.path.exists(RAW_DATA_PATH):
        print("Raw data file not found")
        return articles

    with open(RAW_DATA_PATH, "r", encoding="utf-8") as f:

        for line in f:

            try:
                article = json.loads(line)
                articles.append(article)

            except:
                continue

    return articles


# -----------------------------
# SAVE CLEAN DATA
# -----------------------------

def save_clean_articles(articles):

    os.makedirs("data/processed", exist_ok=True)

    with open(CLEAN_DATA_PATH, "w", encoding="utf-8") as f:

        json.dump(articles, f, indent=2)


# -----------------------------
# TEST PIPELINE
# -----------------------------

def run_cleaning_pipeline():

    print("Loading raw articles...")

    articles = load_articles()

    print(f"Loaded {len(articles)} articles")

    print("Cleaning articles...")

    cleaned_articles = clean_articles(articles)

    print(f"Cleaned {len(cleaned_articles)} articles")

    save_clean_articles(cleaned_articles)

    print("Saved cleaned articles to data/processed/clean_articles.json")


# -----------------------------
# MAIN
# -----------------------------

if __name__ == "__main__":

    run_cleaning_pipeline()
