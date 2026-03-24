import json
from pathlib import Path

INPUT_PATH = Path("data/processed/entity_filtered_relations.json")
OUTPUT_PATH = Path("data/processed/canonical_triples.json")

# =========================
# Relation normalization
# =========================

RELATION_MAP = {

    # communication
    "say": "communicates",
    "tell": "communicates",
    "report": "communicates",
    "announce": "communicates",

    # conflict
    "attack": "attacks",
    "strike": "attacks",
    "bomb": "attacks",
    "fire": "attacks",
    "launch": "attacks",

    # control
    "control": "controls",
    "seize": "controls",
    "occupy": "controls",

    # diplomacy
    "meet": "diplomatic_meeting",
    "talk": "diplomatic_meeting",

    # economy
    "sanction": "sanctions",
    "block": "sanctions",

    # influence
    "urge": "influences",
    "call": "influences",

    # legislation
    "approve": "approves",
    "confirm": "appoints",

    # military
    "disarm": "disarms",
}

# =========================
# BAD RELATIONS
# =========================

BAD_RELATIONS = {
    "is","are","was","were","be","been",
    "have","has","had","do","did",

    "said","told","says","report","reports",

    "once","comes","goes","came","went",
    "made","make","take","took",
    "heard","hears",

    "part","large","will","however",
    "figure","figures","network","jury",

    "company","leader","case","group"
}

# =========================
# Normalize relation
# =========================

def normalize_relation(rel):

    rel = rel.lower().strip().split()[0]

    if rel in BAD_RELATIONS:
        return None

    for key in RELATION_MAP:
        if rel.startswith(key):
            return RELATION_MAP[key]

    if len(rel) < 4:
        return None

    return rel

# =========================
# Clean triple
# =========================

def clean_triple(r):

    subj = r["subject"].lower().strip()
    obj = r["object"].lower().strip()
    rel = normalize_relation(r["relation"])

    if not rel:
        return None

    if subj == obj:
        return None

    if len(subj) < 3 or len(obj) < 3:
        return None

    return {
        "subject": subj,
        "relation": rel,
        "object": obj,
        "context": r.get("context", ""),
        "article_id": r.get("article_id", ""),
        "source_url": r.get("source_url", ""),
        "published_at": r.get("published_at", "")
    }

# =========================
# Process
# =========================

triples = []

with open(INPUT_PATH, "r", encoding="utf-8") as f:
    for line in f:
        r = json.loads(line)

        cleaned = clean_triple(r)
        if cleaned:
            triples.append(cleaned)

# Deduplicate (preserve metadata)
unique = {}
for t in triples:
    key = (t["subject"], t["relation"], t["object"])
    if key not in unique:
        unique[key] = t

triples = list(unique.values())

# =========================
# Save
# =========================

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    for t in triples:
        f.write(json.dumps(t) + "\n")

print("Canonical triples:", len(triples))
print("Saved →", OUTPUT_PATH)
