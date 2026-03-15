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

DATE_PATTERN = re.compile(
    r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\b",
    re.I
)

CHAR_PATTERN = re.compile(r"\d+\s*chars")

# =========================
# NEW: Relation filters
# =========================

JOURNALISM_VERBS = {
    "visit","visits","visited",
    "join","joins","joined",
    "say","says","said",
    "tell","tells","told",
    "report","reports","reported",
    "talk","talks","talked",
    "explain","explains","explained",
    "show","shows","showed"
}

WEAK_RELATIONS = {
    "is","are","was","were",
    "has","have","had",
    "from",
    "to","in","on","at","of","'s"
}

# =========================
# Triple Cleaning
# =========================

def clean_triple(triple):

    subj = triple["subject"].strip()
    rel = triple["relation"].strip()
    obj = triple["object"].strip()

    subj_lower = subj.lower()

    if subj_lower in BAD_SUBJECTS:
        return None

    if any(token in subj_lower for token in BAD_TOKENS):
        return None

    subj = DATE_PATTERN.sub("", subj)
    subj = subj.replace("Reuters", "")
    subj = subj.strip()

    if CHAR_PATTERN.search(obj):
        return None

    if len(obj) < 3:
        return None

    # =========================
    # NEW: relation filtering
    # =========================

    rel_root = rel.lower().split()[0]

    # remove possessive relations like "'s"
    if rel_root == "'s":
        return None

    # remove extremely short relations
    if len(rel_root) < 3:
        return None

    if rel_root in JOURNALISM_VERBS:
        return None

    if rel_root in WEAK_RELATIONS:
        return None

    return {
        "subject": subj,
        "relation": rel,
        "object": obj
    }

# =========================
# Relation extractor
# =========================

class RelationExtractor:

    def extract_relations(self, text, client):

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

            print(f"Extraction error for text:\n{text}\n{e}")

        return relations


# =========================
# Main
# =========================

if __name__ == "__main__":

    if not INPUT_PATH.exists():
        print("Input file missing:", INPUT_PATH)
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

        all_results = []

        for article in articles:

            title = article.get("title", "")
            sentences = article.get("sentences", [])

            relations = []

            relations += extractor.extract_relations(title, client)

            for sent in sentences:

                relations += extractor.extract_relations(sent, client)

            seen = set()
            clean_relations = []

            for r in relations:

                key = (
                    r["subject"].lower(),
                    r["relation"].lower().split()[0],
                    r["object"].lower()
                )

                if key not in seen:

                    clean_relations.append(r)
                    seen.add(key)

            all_results.append({
                "title": title,
                "url": article.get("url",""),
                "relations": clean_relations
            })

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)

    print("Relations extracted →", OUTPUT_PATH)
