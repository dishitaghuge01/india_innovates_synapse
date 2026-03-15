import json
import os
import time
import requests
import spacy
from transformers import pipeline

# =====================
# Configuration
# =====================

REL_API = "https://rel.cs.ru.nl/api"

REQUEST_DELAY = 1.2
MAX_RETRIES = 3

# Allowed ontology entity types
ALLOWED_TYPES = {"PERSON", "ORG", "GPE", "LOC", "EVENT"}

# =====================
# Load SpaCy
# =====================

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Downloading SpaCy model...")
    os.system("python -m spacy download en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# Lightweight fallback NER
ner_pipeline = pipeline(
    "ner",
    model="dslim/bert-base-NER",
    aggregation_strategy="simple"
)

# =====================
# Entity cache
# =====================

entity_cache = {}

# =====================
# Normalization helper
# =====================

def normalize_entity(surface):

    normalized = surface.strip()

    if normalized in {"US", "U.S.", "USA", "U.S.A"}:
        return "United States"

    return normalized

# =====================
# REL API call
# =====================

def rel_entity_link(text):

    if text in entity_cache:
        return entity_cache[text]

    for attempt in range(MAX_RETRIES):

        try:
            r = requests.post(
                REL_API,
                json={"text": text, "spans": []},
                timeout=20
            )

            if r.status_code == 503:
                time.sleep(3)
                continue

            r.raise_for_status()

            data = r.json()

            entities = []

            for item in data:

                surface = normalize_entity(item[2])
                wiki_entity = item[3]

                if wiki_entity:
                    uri = "http://dbpedia.org/resource/" + wiki_entity.replace(" ", "_")
                else:
                    uri = ""

                entities.append((surface, uri))

            entity_cache[text] = entities

            time.sleep(REQUEST_DELAY)

            return entities

        except Exception as e:

            print("REL API error:", e)
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

# =====================
# Load articles
# =====================

articles = []

with open(input_path, "r", encoding="utf-8") as f:
    for line in f:
        if line.strip():
            articles.append(json.loads(line))

print(f"Loaded {len(articles)} articles")

linked_articles = []

# =====================
# Process articles
# =====================

for i, article in enumerate(articles):

    title = article.get("title", "")
    content = article.get("content") or article.get("description") or ""

    url = article.get("url", "")
    published_at = article.get("published_at", "")

    if not content.strip():
        print(f"Skipping empty article: {title}")
        continue

    print(f"Processing {i+1}/{len(articles)}")

    # Combine title + content for better entity detection
    combined_text = f"{title}. {content}"

    clean_text = combined_text.replace("\n", " ").strip()
    clean_text = clean_text[:2000]

    doc = nlp(clean_text)

    sentences = [s.text for s in doc.sents]

    # Filter spaCy entities
    entities_spacy = [
        (ent.text, ent.label_)
        for ent in doc.ents
        if ent.label_ in ALLOWED_TYPES
    ]

    # =====================
    # REL linking
    # =====================

    linked_entities = rel_entity_link(clean_text)

    # Remove duplicates
    seen = set()
    filtered_entities = []

    for surface, uri in linked_entities:

        key = surface.lower()

        if key not in seen:
            seen.add(key)
            filtered_entities.append((surface, uri))

    linked_entities = filtered_entities

    # =====================
    # Fallback NER
    # =====================

    if not linked_entities:

        try:

            results = ner_pipeline(clean_text)

            linked_entities = [
                (normalize_entity(r["word"]), "")
                for r in results
            ]

        except Exception as e:

            print("Fallback NER error:", e)

            linked_entities = [
                (normalize_entity(ent.text), "")
                for ent in doc.ents
                if ent.label_ in ALLOWED_TYPES
            ]

    # =====================
    # Store result
    # =====================

    linked_articles.append({
        "title": title,
        "sentences": sentences,
        "entities": entities_spacy,
        "linked_entities": linked_entities,
        "url": url,
        "published_at": published_at
    })

# =====================
# Save output
# =====================

with open(output_path, "w", encoding="utf-8") as f:

    for article in linked_articles:
        f.write(json.dumps(article) + "\n")

print("\nFinished processing.")
print(f"Output saved to: {output_path}")
