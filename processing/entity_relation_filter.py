import json
from pathlib import Path
import hashlib

from utils import logger

# =========================
# Paths
# =========================

RELATIONS_PATH = Path("data/processed/relation_candidates.json")
ENTITIES_PATH = Path("data/processed/ner_linked_articles.json")
OUTPUT_PATH = Path("data/processed/entity_filtered_relations.json")

CACHE_DIR = Path("data/cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

PROCESSED_ARTICLES_PATH = CACHE_DIR / "processed_articles.json"
PROCESSED_TRIPLES_PATH = CACHE_DIR / "processed_entity_filtered_relations.json"

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
# Load Caches
# =========================

processed_articles = {}
if PROCESSED_ARTICLES_PATH.exists():
    with open(PROCESSED_ARTICLES_PATH, "r", encoding="utf-8") as f:
        processed_articles = json.load(f)

processed_triples = {}
if PROCESSED_TRIPLES_PATH.exists():
    with open(PROCESSED_TRIPLES_PATH, "r", encoding="utf-8") as f:
        processed_triples = json.load(f)

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
    for line in f:
        if not line.strip():
            continue
        r = json.loads(line)

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

        triple = {
            "subject": subj_entity,
            "relation": rel.lower().split()[0],
            "object": obj_entity,
            "context": r["context"],
            "confidence": r["confidence"],
            "article_id": article_id,
            "source_url": r["source_url"],
            "published_at": r["published_at"]
        }

        # Triple hash for dedup
        triple_key = (
            triple["subject"].lower(),
            triple["relation"],
            triple["object"].lower(),
            triple["article_id"] or ""
        )
        triple_hash = hashlib.md5(json.dumps(triple_key, sort_keys=True).encode()).hexdigest()

        if triple_hash not in processed_triples:
            filtered_relations.append(triple)
            processed_triples[triple_hash] = ""


# =========================
# Save
# =========================

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

with open(OUTPUT_PATH, "a", encoding="utf-8") as f:
    for r in filtered_relations:
        f.write(json.dumps(r) + "\n")

# Save caches
with open(PROCESSED_ARTICLES_PATH, "w", encoding="utf-8") as f:
    json.dump(processed_articles, f, indent=2)

with open(PROCESSED_TRIPLES_PATH, "w", encoding="utf-8") as f:
    json.dump(processed_triples, f, indent=2)

print(f"Filtered {len(filtered_relations)} new relations")
