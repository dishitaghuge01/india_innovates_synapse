import json
from pathlib import Path

# =========================
# Paths
# =========================

INPUT_PATH = Path("data/processed/entity_filtered_relations.json")
OUTPUT_PATH = Path("data/processed/canonical_triples.json")

# =========================
# Relation normalization
# =========================

RELATION_MAP = {

    "urge": "influences",
    "call": "influences",
    "say": "communicates",

    "target": "attacks",
    "attack": "attacks",
    "bomb": "attacks",
    "strike": "attacks",

    "ally": "ally_of",
    "support": "ally_of",

    "block": "sanctions",
    "sanction": "sanctions",

    "meet": "diplomatic_meeting",

}

# =========================
# New: weak relations
# =========================

BAD_RELATIONS = {
    "war",
    "hub",
    "fear",
    "could",
    "continued",
    "wanted"
}

# =========================
# Normalize relation
# =========================

def normalize_relation(rel):

    rel = rel.lower().split()[0]

    for key in RELATION_MAP:

        if rel.startswith(key):
            return RELATION_MAP[key]

    return rel


# =========================
# Clean triples
# =========================

def clean_triple(subj, rel, obj):

    rel = normalize_relation(rel)

    # Remove weak relations
    if rel in BAD_RELATIONS:
        return None

    # very short relations are usually bad
    if len(rel) < 3:
        return None

    if len(subj) < 2 or len(obj) < 2:
        return None

    if subj == obj:
        return None

    return (subj, rel, obj)

# =========================
# Process
# =========================

with open(INPUT_PATH, "r", encoding="utf-8") as f:
    articles = json.load(f)

triples = []

for article in articles:

    for r in article["relations"]:

        cleaned = clean_triple(
            r["subject"],
            r["relation"],
            r["object"]
        )

        if cleaned:
            triples.append(cleaned)

# Deduplicate
triples = list(set(triples))

# =========================
# Save
# =========================

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:

    for s,r,o in triples:

        record = {
            "subject": s,
            "relation": r,
            "object": o
        }

        f.write(json.dumps(record) + "\n")

print("Canonical triples:", len(triples))
print("Saved →", OUTPUT_PATH)
