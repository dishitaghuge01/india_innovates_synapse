from stanza.server import CoreNLPClient
from pathlib import Path
import os
import json
import re
import hashlib

from utils import logger

# =========================
# Paths
# =========================

INPUT_PATH = Path("data/processed/ner_linked_articles.json")
OUTPUT_PATH = Path("data/processed/relation_candidates.json")

CACHE_DIR = Path("data/cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

PROCESSED_ARTICLES_PATH = CACHE_DIR / "processed_articles.json"
PROCESSED_TRIPLES_PATH = CACHE_DIR / "processed_relation_candidates.json"

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
# Load Articles
# =========================

if not INPUT_PATH.exists():
    print("Missing input:", INPUT_PATH)
    exit()

with open(INPUT_PATH, "r", encoding="utf-8") as f:
    articles = [json.loads(line) for line in f]

    extractor = RelationExtractor()

all_triples = []

with CoreNLPClient(
    annotators=['tokenize','ssplit','pos','lemma','depparse','natlog','openie'],
    timeout=30000,
    memory='4G',
    classpath=jar_files,
    port=9001
) as client:

    for article in articles:

        article_id = article.get("article_id")
        source_url = article.get("source_url")
        published_at = article.get("published_at")

        # Compute hash
        if article_id:
            article_hash = hashlib.md5(article_id.encode()).hexdigest()
        else:
            # Reconstruct content for hash
            title = article.get("source_title", "")
            content = article.get("raw_text", "")
            content_str = f"{title} {content}"
            article_hash = hashlib.md5(content_str.encode()).hexdigest()

        if article_hash in processed_articles:
            logger.info(f"Skipping duplicate article: {article_hash}")
            continue

        logger.info(f"Processing new article: {article_id or article_hash}")

        sentences = article.get("sentences", [])

        for sent in sentences:

            triples = extractor.extract_from_sentence(sent, client)

            for t in triples:

                t["article_id"] = article_id
                t["source_url"] = source_url
                t["published_at"] = published_at

                # Triple hash for dedup
                triple_key = (
                    t["subject"].lower(),
                    t["relation"],
                    t["object"].lower(),
                    t["article_id"] or ""
                )
                triple_hash = hashlib.md5(json.dumps(triple_key, sort_keys=True).encode()).hexdigest()

                if triple_hash not in processed_triples:
                    all_triples.append(t)
                    processed_triples[triple_hash] = ""

        # Mark article as processed
        processed_articles[article_hash] = published_at or ""

# =========================
# Save
# =========================

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

with open(OUTPUT_PATH, "a", encoding="utf-8") as f:
    for t in all_triples:
        f.write(json.dumps(t) + "\n")

# Save caches
with open(PROCESSED_ARTICLES_PATH, "w", encoding="utf-8") as f:
    json.dump(processed_articles, f, indent=2)

with open(PROCESSED_TRIPLES_PATH, "w", encoding="utf-8") as f:
    json.dump(processed_triples, f, indent=2)

print(f"Extracted {len(all_triples)} new triples")
