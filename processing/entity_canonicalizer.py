import json
from pathlib import Path

INPUT_PATH = Path("data/processed/canonical_triples.json")
OUTPUT_PATH = Path("data/processed/canonicalized_entities.json")

# =========================
# Canonical dictionary
# =========================

CANONICAL_MAP = {
    "trump": "donald trump",
    "donald j trump": "donald trump",
    "biden": "joe biden",
    "mullin": "markwayne mullin",

    "us": "united states",
    "u.s": "united states",
    "usa": "united states",

    "uk": "united kingdom",
    "eu": "european union"
}

# =========================
# Filters
# =========================

DEMONYMS = {
    "american","british","french","israeli","iranian",
    "russian","chinese","danish","turkish","danes","canadian"
}

BAD_ENTITIES = {
    "army","defence","leader","company",
    "official","minister","group",
    "polls","orthodox","gulf oil",
    "people","country","state"
}

# =========================
# Normalize
# =========================

def normalize_text(e):
    return (
        e.lower()
        .replace(".", "")
        .replace(",", "")
        .strip()
    )

# =========================
# Canonicalize
# =========================

def canonicalize(e):

    e = normalize_text(e)

    if e in DEMONYMS:
        return None

    if e in BAD_ENTITIES:
        return None

    for key in CANONICAL_MAP:
        if key in e:
            return CANONICAL_MAP[key]

    if len(e.split()) == 1 and len(e) < 4:
        return None

    return e

# =========================
# Process
# =========================

results = []

with open(INPUT_PATH, "r", encoding="utf-8") as f:

    for line in f:

        r = json.loads(line)

        s = canonicalize(r["subject"])
        o = canonicalize(r["object"])

        if not s or not o:
            continue

        if s == o:
            continue

        results.append({
            "subject": s,
            "relation": r["relation"],
            "object": o,
            "context": r.get("context", ""),
            "article_id": r.get("article_id", ""),
            "source_url": r.get("source_url", ""),
            "published_at": r.get("published_at", "")
        })

# =========================
# Save
# =========================

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    for r in results:
        f.write(json.dumps(r) + "\n")

print("Canonicalized entities:", len(results))
print("Saved →", OUTPUT_PATH)
