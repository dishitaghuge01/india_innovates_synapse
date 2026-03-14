import json
import os
from collections import defaultdict

INPUT_PATH = "data/processed/extracted_entities.json"
OUTPUT_PATH = "data/processed/canonical_entities.json"

# -------------------------
# Load entities
# -------------------------
def load_entities():
    if not os.path.exists(INPUT_PATH):
        print("Extracted entities not found")
        return []
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# -------------------------
# Normalize / canonicalize entity
# -------------------------
def normalize_entity(text):
    text = text.strip()
    # Replace common variants with canonical forms
    replacements = {
        "US": "United States",
        "U.S.": "United States",
        "USA": "United States",
        "UK": "United Kingdom",
        "U.K.": "United Kingdom",
        "DOJ": "Department of Justice",
        "Trump": "Donald Trump",
        "Merz": "Friedrich Merz",
        "OpenAI": "OpenAI",
        "Anthropic": "Anthropic"
        # add more rules as needed
    }
    if text in replacements:
        return replacements[text]

    # Strip trailing title fragments or punctuation (optional)
    text = text.rstrip(".,;")
    return text

# -------------------------
# Canonicalize articles
# -------------------------
def canonicalize_entities(articles):
    results = []
    for article in articles:
        canonical_entities = []

        # Deduplicate
        seen = set()
        for ent in article["entities"]:
            normalized = normalize_entity(ent["text"])
            key = (normalized, ent["label"])
            if key not in seen:
                canonical_entities.append({
                    "text": normalized,
                    "label": ent["label"]
                })
                seen.add(key)

        results.append({
            "title": article["title"],
            "url": article["url"],
            "content": article.get("content", ""),
            "entities": canonical_entities
        })
    return results

# -------------------------
# Save canonical entities
# -------------------------
def save_canonical_entities(data):
    os.makedirs("data/processed", exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# -------------------------
# Run canonicalization
# -------------------------
def run_canonicalization():
    print("Loading extracted entities...")
    articles = load_entities()
    print(f"Loaded {len(articles)} articles")
    print("Canonicalizing entities...")
    canonicalized = canonicalize_entities(articles)
    print("Saving canonical entities...")
    save_canonical_entities(canonicalized)
    print("Entity canonicalization completed")

if __name__ == "__main__":
    run_canonicalization()
