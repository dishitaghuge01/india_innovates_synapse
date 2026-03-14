from sentence_transformers import SentenceTransformer
import numpy as np
import json
import os
MODEL_NAME = "all-MiniLM-L6-v2"

model = SentenceTransformer(MODEL_NAME)
CLEAN_DATA_PATH = "data/processed/clean_articles.json"
EMBEDDING_OUTPUT_PATH = "data/processed/article_embeddings.npy"
ARTICLE_META_PATH = "data/processed/article_metadata.json"

def load_clean_articles():

    if not os.path.exists(CLEAN_DATA_PATH):
        print("Clean articles not found")
        return []

    with open(CLEAN_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def generate_embeddings(articles):

    texts = []

    for article in articles:

        combined_text = f"{article['title']} {article['content']}"

        texts.append(combined_text)

    embeddings = model.encode(texts, show_progress_bar=True)

    return embeddings

def save_embeddings(embeddings):

    os.makedirs("data/processed", exist_ok=True)

    np.save(EMBEDDING_OUTPUT_PATH, embeddings)

def save_metadata(articles):

    metadata = []

    for article in articles:

        metadata.append({
            "title": article["title"],
            "source": article["source"],
            "url": article["url"],
            "published_at": article["published_at"]
        })

    with open(ARTICLE_META_PATH, "w", encoding="utf-8") as f:

        json.dump(metadata, f, indent=2)

def run_embedding_pipeline():

    print("Loading clean articles...")

    articles = load_clean_articles()

    print(f"Loaded {len(articles)} articles")

    print("Generating embeddings...")

    embeddings = generate_embeddings(articles)

    print("Saving embeddings...")

    save_embeddings(embeddings)

    save_metadata(articles)

    print("Embeddings saved successfully")

if __name__ == "__main__":

    run_embedding_pipeline()
