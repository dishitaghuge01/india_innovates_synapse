import json
from pathlib import Path

# =========================
# Paths
# =========================

RELATIONS_PATH = Path("data/processed/relation_candidates.json")
ENTITIES_PATH = Path("data/processed/ner_linked_articles.json")
OUTPUT_PATH = Path("data/processed/entity_filtered_relations.json")

# =========================
# NEW: NORP filter
# =========================

NORP_WORDS = {
    "israeli",
    "norwegian",
    "american",
    "iranians",
    "russian",
    "chinese",
    "british",
    "french"
}

# =========================
# Load entity lists
# =========================

article_entities = {}

with open(ENTITIES_PATH, "r", encoding="utf-8") as f:

    for line in f:

        article = json.loads(line)

        title = article["title"]

        entities = set()

        for e, label in article["entities"]:
            entities.add(e.lower())

        for e, uri in article["linked_entities"]:
            entities.add(e.lower())

        article_entities[title] = entities


# =========================
# Helper
# =========================

def find_entity(text, entity_set):

    text_lower = text.lower()

    for entity in entity_set:

        if entity in NORP_WORDS:
            continue

        if entity in text_lower:
            return entity

    return None


# =========================
# Filter triples
# =========================

filtered_articles = []

with open(RELATIONS_PATH, "r", encoding="utf-8") as f:

    articles = json.load(f)

for article in articles:

    title = article["title"]

    entities = article_entities.get(title, set())

    clean_relations = []

    for r in article["relations"]:

        subj = r["subject"]
        rel = r["relation"]
        obj = r["object"]

        subj_entity = find_entity(subj, entities)
        obj_entity = find_entity(obj, entities)

        if subj_entity and obj_entity:

            clean_relations.append({
                "subject": subj_entity,
                "relation": rel,
                "object": obj_entity
            })

    # remove duplicates
    seen = set()
    unique_relations = []

    for r in clean_relations:

        key = (r["subject"], r["relation"], r["object"])

        if key not in seen:
            unique_relations.append(r)
            seen.add(key)

    filtered_articles.append({
        "title": title,
        "url": article.get("url",""),
        "relations": unique_relations
    })


# =========================
# Save
# =========================

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(filtered_articles, f, indent=2)

print("Filtered relations saved to:", OUTPUT_PATH)
