import json
from pathlib import Path

# =========================
# Paths
# =========================

INPUT_PATH = Path("data/processed/canonical_triples.json")
OUTPUT_PATH = Path("data/processed/validated_triples.json")

# =========================
# Simple entity type hints
# =========================

COUNTRY_WORDS = {
    "iran","iraq","israel","russia","china",
    "ukraine","japan","turkey","brazil",
    "mexico","cuba","argentina","australia",
    "germany","france","india","us","u.s."
}

ORG_WORDS = {
    "hamas","nato","un","white house",
    "us navy","menasource"
}

FILM_HINTS = {
    "film","movie"
}

# =========================
# Entity classifier
# =========================

def classify_entity(entity):

    e = entity.lower()

    if e in COUNTRY_WORDS:
        return "country"

    if e in ORG_WORDS:
        return "org"

    if any(word in e for word in FILM_HINTS):
        return "film"

    if len(e.split()) == 2:
        return "person"

    return "unknown"


# =========================
# Ontology rules
# =========================

RULES = {

    "attacks": {
        "subject": {"country","org"},
        "object": {"country","location"}
    },

    "ally_of": {
        "subject": {"country","org"},
        "object": {"country","org"}
    },

    "influences": {
        "subject": {"person","org","country"},
        "object": {"country","org"}
    },

    "director": {
        "subject": {"person"},
        "object": {"film","unknown"}
    },

    "adviser": {
        "subject": {"person"},
        "object": {"country","org"}
    }

}

# =========================
# Validation
# =========================

def validate_triple(s, r, o):

    subj_type = classify_entity(s)
    obj_type = classify_entity(o)

    if r not in RULES:
        return True

    rule = RULES[r]

    if subj_type not in rule["subject"]:
        return False

    if obj_type not in rule["object"]:
        return False

    return True


# =========================
# Main processing
# =========================

valid_triples = []

with open(INPUT_PATH, "r", encoding="utf-8") as f:

    for line in f:

        triple = json.loads(line)

        s = triple["subject"]
        r = triple["relation"]
        o = triple["object"]

        if validate_triple(s, r, o):

            valid_triples.append(triple)

# =========================
# Save
# =========================

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:

    for t in valid_triples:

        f.write(json.dumps(t) + "\n")

print("Validated triples:", len(valid_triples))
print("Saved →", OUTPUT_PATH)
