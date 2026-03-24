import json
from pathlib import Path

# =========================
# Paths
# =========================

RELATIONS_PATH = Path("data/processed/relation_candidates.json")
ENTITIES_PATH = Path("data/processed/ner_linked_articles.json")
OUTPUT_PATH = Path("data/processed/entity_filtered_relations.json")

# =========================
# Filters
# =========================

NORP_WORDS = {
    "israeli","norwegian","american","iranians",
    "russian","chinese","british","french"
}

BAD_RELATIONS = {
    "is","are","was","were",
    "has","have","had",
    "will","would","can","could",
    "large","small","new","old",
    "part","swathe"
}

MIN_OBJECT_LENGTH = 4

# =========================
# Load entity lists (FIXED STRUCTURE)
# =========================

article_entities = {}

with open(ENTITIES_PATH, "r", encoding="utf-8") as f:
    for line in f:
        article = json.loads(line)

        article_id = article.get("article_id")
        entities = set()

        # NEW FORMAT support
        for e in article.get("entities", []):
            entities.add(e["normalized"].lower())

        article_entities[article_id] = entities

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


def is_valid_relation(rel):

    rel_root = rel.lower().split()[0]

    if rel_root in BAD_RELATIONS:
        return False

    if len(rel_root) < 3:
        return False

    return True


def is_valid_object(obj):

    if len(obj.strip()) < MIN_OBJECT_LENGTH:
        return False

    # remove useless generic objects
    bad_words = ["part", "thing", "something"]

    for w in bad_words:
        if obj.lower() == w:
            return False

    return True


# =========================
# Filter triples
# =========================

filtered_relations = []

with open(RELATIONS_PATH, "r", encoding="utf-8") as f:
    relations = [json.loads(line) for line in f]

for r in relations:

    article_id = r.get("article_id")
    entity_set = article_entities.get(article_id, set())

    subj = r["subject"]
    rel = r["relation"]
    obj = r["object"]

    # =========================
    # STEP 1: relation filter
    # =========================

    if not is_valid_relation(rel):
        continue

    # =========================
    # STEP 2: object filter
    # =========================

    if not is_valid_object(obj):
        continue

    # =========================
    # STEP 3: entity grounding
    # =========================

    subj_entity = find_entity(subj, entity_set)
    obj_entity = find_entity(obj, entity_set)

    if not subj_entity or not obj_entity:
        continue

    # =========================
    # STEP 4: final triple
    # =========================

    filtered_relations.append({
        "subject": subj_entity,
        "relation": rel.lower().split()[0],
        "object": obj_entity,
        "context": r["context"],
        "confidence": r["confidence"],
        "article_id": article_id,
        "source_url": r["source_url"],
        "published_at": r["published_at"]
    })


# =========================
# Remove duplicates (STRONG)
# =========================

seen = set()
unique_relations = []

for r in filtered_relations:

    key = (
        r["subject"],
        r["relation"],
        r["object"],
        r["article_id"]
    )

    if key not in seen:
        unique_relations.append(r)
        seen.add(key)

# =========================
# Save
# =========================

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    for r in unique_relations:
        f.write(json.dumps(r) + "\n")

print(f"✅ Clean triples saved: {len(unique_relations)}")
print("Output →", OUTPUT_PATH)
