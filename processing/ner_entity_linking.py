import json
import os
import time
import requests
import spacy
import hashlib
from transformers import pipeline

from utils import logger

REL_API = "https://rel.cs.ru.nl/api"

REQUEST_DELAY = 1.0
MAX_RETRIES = 3

ALLOWED_TYPES = {"PERSON", "ORG", "GPE", "LOC", "EVENT"}

# =====================
# Load SpaCy
# =====================

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    os.system("python -m spacy download en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# Fallback NER
local_model_dir = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")), "models", "dslim-bert-base-NER")
os.makedirs(local_model_dir, exist_ok=True)
ner_pipeline = pipeline(
    "ner",
    model="dslim/bert-base-NER",
    aggregation_strategy="simple",
    model_kwargs={"cache_dir": local_model_dir}
)

# =====================
# Cache
# =====================

entity_cache = {}

# =====================
# Normalize entity
# =====================

def normalize_entity(text):
    text = text.strip()

    if text in {"US", "U.S.", "USA"}:
        return "United States"

    return text


# =====================
# REL API
# =====================

def rel_entity_link(text):

    if text in entity_cache:
        return entity_cache[text]

    for _ in range(MAX_RETRIES):
        try:
            r = requests.post(
                REL_API,
                json={"text": text, "spans": []},
                timeout=15
            )

            if r.status_code == 503:
                time.sleep(2)
                continue

            r.raise_for_status()

            data = r.json()

            results = []

            for item in data:
                surface = normalize_entity(item[2])
                wiki_entity = item[3]

                uri = ""
                if wiki_entity:
                    uri = "http://dbpedia.org/resource/" + wiki_entity.replace(" ", "_")

                results.append({
                    "text": surface,
                    "uri": uri
                })

            entity_cache[text] = results
            time.sleep(REQUEST_DELAY)

            return results

        except Exception:
            time.sleep(2)

    return []


# =====================
# Paths
# =====================

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

input_path = os.path.join(base_dir, "data", "raw", "articles.json")

output_dir = os.path.join(base_dir, "data", "processed")
os.makedirs(output_dir, exist_ok=True)

output_path = os.path.join(output_dir, "ner_linked_articles.json")

cache_dir = os.path.join(base_dir, "data", "cache")
os.makedirs(cache_dir, exist_ok=True)

processed_articles_path = os.path.join(cache_dir, "processed_articles.json")

# =====================
# Load Processed Articles Cache
# =====================

processed_articles = {}
if os.path.exists(processed_articles_path):
    with open(processed_articles_path, "r", encoding="utf-8") as f:
        processed_articles = json.load(f)

# =====================
# Load Articles
# =====================

articles = []

with open(input_path, "r", encoding="utf-8") as f:
    for line in f:
        if line.strip():
            articles.append(json.loads(line))

print(f"Loaded {len(articles)} articles")

linked_articles = []

# =====================
# Processing
# =====================

for i, article in enumerate(articles):

    # Compute article hash for deduplication
    if article.get("article_id"):
        article_hash = hashlib.md5(article["article_id"].encode()).hexdigest()
    else:
        content = f"{article.get('source_title', '')} {article.get('raw_text', '')}"
        article_hash = hashlib.md5(content.encode()).hexdigest()

    if article_hash in processed_articles:
        logger.info(f"Skipping duplicate article: {article_hash}")
        continue

    logger.info(f"Processing new article: {article.get('article_id') or article_hash}")

    # ✅ Correct fields from ingestion
    article_id = article.get("article_id")
    source_url = article.get("source_url")
    source_name = article.get("source_name")
    published_at = article.get("published_at")

    title = article.get("source_title", "")
    content = article.get("raw_text", "")

    if not content.strip():
        continue

    combined_text = f"{title}. {content}"
    clean_text = combined_text.replace("\n", " ").strip()[:2000]

    doc = nlp(clean_text)

    sentences = [s.text for s in doc.sents]

    # =====================
    # spaCy entities
    # =====================

    spacy_entities = [
        {
            "text": normalize_entity(ent.text),
            "label": ent.label_
        }
        for ent in doc.ents
        if ent.label_ in ALLOWED_TYPES
    ]

    # =====================
    # REL linking
    # =====================

    linked = rel_entity_link(clean_text)

    # =====================
    # Merge entities
    # =====================

    final_entities = []
    seen = set()

    # Add REL entities first (higher quality)
    for ent in linked:
        key = ent["text"].lower()
        if key not in seen:
            seen.add(key)
            final_entities.append({
                "text": ent["text"],
                "label": None,
                "uri": ent["uri"],
                "normalized": ent["text"]
            })

    # Add spaCy entities if missing
    for ent in spacy_entities:
        key = ent["text"].lower()
        if key not in seen:
            seen.add(key)
            final_entities.append({
                "text": ent["text"],
                "label": ent["label"],
                "uri": "",
                "normalized": ent["text"]
            })

    # =====================
    # Fallback (if nothing found)
    # =====================

    if not final_entities:
        try:
            results = ner_pipeline(clean_text)
            for r in results:
                text = normalize_entity(r["word"])
                final_entities.append({
                    "text": text,
                    "label": r.get("entity_group"),
                    "uri": "",
                    "normalized": text
                })
        except:
            pass

    # =====================
    # Store
    # =====================

    linked_articles.append({
        "article_id": article_id,
        "source_url": source_url,
        "source_name": source_name,
        "published_at": published_at,
        "sentences": sentences,
        "entities": final_entities
    })

    # Mark as processed
    processed_articles[article_hash] = published_at or ""

# =====================
# Save
# =====================

with open(output_path, "a", encoding="utf-8") as f:
    for article in linked_articles:
        f.write(json.dumps(article) + "\n")

# Save processed articles cache
with open(processed_articles_path, "w", encoding="utf-8") as f:
    json.dump(processed_articles, f, indent=2)

print("\nFinished processing.")
print(f"Saved to: {output_path}")
