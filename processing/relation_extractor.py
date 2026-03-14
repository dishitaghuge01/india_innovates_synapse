from stanza.server import CoreNLPClient
from pathlib import Path
import os
import json
import re

# =========================
# Paths
# =========================
INPUT_PATH = Path("data/processed/canonical_entities.json")
OUTPUT_PATH = Path("data/processed/relation_candidates.json")

# =========================
# CoreNLP setup
# =========================
CORENLP_PATH = Path(r"C:\stanford-corenlp-4.5.10")
os.environ["CORENLP_HOME"] = str(CORENLP_PATH)

# Build classpath from all .jar files
jar_files = ";".join(str(jar) for jar in CORENLP_PATH.glob("*.jar"))

# =========================
# Filtering rules
# =========================
BAD_SUBJECTS = {
    "we","they","it","this","that","i","he","she"
}

BAD_TOKENS = [
    "reuters",
    "getty",
    "credit",
    "chars",
    "photo",
    "image"
]

DATE_PATTERN = re.compile(r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\b", re.I)
CHAR_PATTERN = re.compile(r"\d+\s*chars")

# =========================
# Triple Cleaning
# =========================
def clean_triple(triple):

    subj = triple["subject"].strip()
    rel = triple["relation"].strip()
    obj = triple["object"].strip()

    subj_lower = subj.lower()

    # remove pronoun subjects
    if subj_lower in BAD_SUBJECTS:
        return None

    # remove metadata tokens
    if any(token in subj_lower for token in BAD_TOKENS):
        return None

    # remove Reuters/date boilerplate
    subj = DATE_PATTERN.sub("", subj)
    subj = subj.replace("Reuters", "")
    subj = subj.strip()

    # remove truncated objects
    if CHAR_PATTERN.search(obj):
        return None

    # remove extremely small objects
    if len(obj) < 3:
        return None

    return {
        "subject": subj,
        "relation": rel,
        "object": obj
    }

# =========================
# Relation Extractor Class
# =========================
class RelationExtractor:
    def extract_relations(self, text, client):
        """
        Extract relations from a single text using an existing CoreNLPClient.
        """
        relations = []
        if not text.strip():
            return relations
        try:
            ann = client.annotate(text)
            for sentence in ann.sentence:
                for triple in sentence.openieTriple:

                    raw = {
                        "subject": triple.subject,
                        "relation": triple.relation,
                        "object": triple.object
                    }

                    cleaned = clean_triple(raw)

                    if cleaned:
                        relations.append(cleaned)

        except Exception as e:
            print(f"Extraction error for text: {text}\n{e}")
        return relations

# =========================
# Main Execution
# =========================
if __name__ == "__main__":
    if not INPUT_PATH.exists():
        print(f"Input file not found: {INPUT_PATH}")
        exit(1)

    # Load canonical entities JSON
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        articles = json.load(f)

    extractor = RelationExtractor()

    # Start CoreNLP server once on port 9001
    with CoreNLPClient(
        annotators=['tokenize','ssplit','pos','lemma','depparse','natlog','openie'],
        timeout=30000,
        memory='4G',
        classpath=jar_files,
        port=9001
    ) as client:

        all_results = []
        for article in articles:
            title = article.get("title", "")
            content = article.get("content", "")  # if content exists
            relations = []

            # Extract from title and content
            relations += extractor.extract_relations(title, client)
            content_excerpt = content[:2000]
            relations += extractor.extract_relations(content_excerpt, client)

            # Deduplicate relations
            seen_triples = set()
            clean_relations = []
            for r in relations:

                key = (
                    r['subject'].lower(),
                    r['relation'].lower().split()[0],
                    r['object'].lower()
                )

                if key not in seen_triples:
                    clean_relations.append(r)
                    seen_triples.add(key)

            relations = clean_relations

            all_results.append({
                "title": title,
                "url": article.get("url", ""),
                "relations": relations
            })

    # Save results
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)

    print(f"Extraction completed. Results saved to {OUTPUT_PATH}")