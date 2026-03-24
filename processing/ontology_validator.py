import json
from pathlib import Path

# =========================
# Paths
# =========================

INPUT_PATH = Path("data/processed/canonicalized_entities.json")
OUTPUT_PATH = Path("data/processed/validated_triples.json")

# =========================
# Entity knowledge
# =========================

COUNTRIES = {
    "iran","iraq","israel","russia","china",
    "ukraine","japan","turkey","brazil",
    "mexico","cuba","argentina","australia",
    "germany","france","india",
    "united states","united kingdom",
    "lebanon","namibia","angola"
}

ORGS = {
    "nato","un","eu",
    "department of homeland security",
    "senate","white house",
    "hezbollah","hamas","irgc"
}

# =========================
# BAD RELATIONS (STRICT FILTER)
# =========================

BAD_RELATIONS = {
    "is","was","were","are","be","being",
    "also","very","more","most",
    "said","says","told",
    "near","close",
    "figure","figures",
    "missiles","iranian","large",
    "however","because","after","before"
}

# =========================
# Weak relations (optional drop)
# =========================

WEAK_RELATIONS = {
    "born","died","heard","comes","goes","turns"
}

# =========================
# Entity classifier
# =========================

def classify_entity(entity):
    e = entity.lower()

    if e in COUNTRIES:
        return "country"

    if e in ORGS:
        return "org"

    if 2 <= len(e.split()) <= 3:
        return "person"

    return "unknown"

# =========================
# Relation filter
# =========================

def is_valid_relation(r):

    r = r.lower()

    if r in BAD_RELATIONS:
        return False

    if len(r) < 3:
        return False

    # must be verb-like (simple heuristic)
    if not r.endswith(("s","ed")) and r not in {
        "attacks","controls","sanctions",
        "approves","appoints","disarms",
        "influences","meets"
    }:
        return False

    return True

# =========================
# Triple validation
# =========================

def validate_triple(s, r, o):

    # relation check
    if not is_valid_relation(r):
        return False

    # self loop
    if s == o:
        return False

    # entity sanity
    if len(s) < 2 or len(o) < 2:
        return False

    # weak relation filtering (optional but useful)
    if r in WEAK_RELATIONS:
        return False

    return True

# =========================
# Process
# =========================

validated = []

with open(INPUT_PATH, "r", encoding="utf-8") as f:

    for line in f:

        triple = json.loads(line)

        s = triple["subject"]
        r = triple["relation"]
        o = triple["object"]

        if validate_triple(s, r, o):

            # keep original metadata
            validated.append({
                "subject": s,
                "relation": r,
                "object": o,
                "context": triple.get("context"),
                "article_id": triple.get("article_id"),
                "source_url": triple.get("source_url"),
                "published_at": triple.get("published_at")
            })

# =========================
# Save
# =========================

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    for t in validated:
        f.write(json.dumps(t) + "\n")

print("Validated triples:", len(validated))
print("Saved →", OUTPUT_PATH)
