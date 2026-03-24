from stanza.server import CoreNLPClient
from pathlib import Path
import os
import json
import re

# =========================
# Paths
# =========================

INPUT_PATH = Path("data/processed/ner_linked_articles.json")
OUTPUT_PATH = Path("data/processed/relation_candidates.json")

# =========================
# CoreNLP setup
# =========================

CORENLP_PATH = Path(r"C:\stanford-corenlp-4.5.10")
os.environ["CORENLP_HOME"] = str(CORENLP_PATH)

jar_files = ";".join(str(jar) for jar in CORENLP_PATH.glob("*.jar"))

# =========================
# Filters
# =========================

BAD_SUBJECTS = {"we","they","it","this","that","i","he","she"}

WEAK_RELATIONS = {
    "is","are","was","were",
    "has","have","had",
    "to","in","on","at","of"
}

# =========================
# Clean triple
# =========================

def clean_triple(triple):

    subj = triple["subject"].strip()
    rel = triple["relation"].strip()
    obj = triple["object"].strip()

    if subj.lower() in BAD_SUBJECTS:
        return None

    rel_root = rel.lower().split()[0]

    if rel_root in WEAK_RELATIONS:
        return None

    if len(obj) < 3:
        return None

    return {
        "subject": subj,
        "relation": rel_root,
        "object": obj
    }

# =========================
# Confidence heuristic
# =========================

def compute_confidence(subj, rel, obj):

    score = 0.5

    if len(subj) > 3:
        score += 0.1
    if len(obj) > 3:
        score += 0.1
    if len(rel) > 3:
        score += 0.1

    return min(score, 0.95)

# =========================
# Extractor
# =========================

class RelationExtractor:

    def extract_from_sentence(self, sentence, client):

        results = []

        try:
            ann = client.annotate(sentence)

            for s in ann.sentence:
                for triple in s.openieTriple:

                    raw = {
                        "subject": triple.subject,
                        "relation": triple.relation,
                        "object": triple.object
                    }

                    cleaned = clean_triple(raw)

                    if not cleaned:
                        continue

                    confidence = compute_confidence(
                        cleaned["subject"],
                        cleaned["relation"],
                        cleaned["object"]
                    )

                    results.append({
                        "subject": cleaned["subject"],
                        "relation": cleaned["relation"],
                        "object": cleaned["object"],
                        "context": sentence,
                        "confidence": confidence
                    })

        except Exception:
            pass

        return results

# =========================
# Main
# =========================

if __name__ == "__main__":

    if not INPUT_PATH.exists():
        print("Missing input:", INPUT_PATH)
        exit()

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        articles = [json.loads(line) for line in f]

    extractor = RelationExtractor()

    with CoreNLPClient(
        annotators=['tokenize','ssplit','pos','lemma','depparse','natlog','openie'],
        timeout=30000,
        memory='4G',
        classpath=jar_files,
        port=9001
    ) as client:

        all_triples = []

        for article in articles:

            article_id = article.get("article_id")
            source_url = article.get("source_url")
            published_at = article.get("published_at")

            sentences = article.get("sentences", [])

            for sent in sentences:

                triples = extractor.extract_from_sentence(sent, client)

                for t in triples:

                    t["article_id"] = article_id
                    t["source_url"] = source_url
                    t["published_at"] = published_at

                    all_triples.append(t)

    # =========================
    # Deduplication
    # =========================

    seen = set()
    final_triples = []

    for t in all_triples:

        key = (
            t["subject"].lower(),
            t["relation"],
            t["object"].lower(),
            t["article_id"]
        )

        if key not in seen:
            seen.add(key)
            final_triples.append(t)

    # =========================
    # Save
    # =========================

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for t in final_triples:
            f.write(json.dumps(t) + "\n")

    print(f"Extracted {len(final_triples)} triples")
    print("Saved to:", OUTPUT_PATH)
