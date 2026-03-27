import json
from pathlib import Path
from datetime import datetime, timedelta
import os

from rapidfuzz import process, fuzz
from sentence_transformers import SentenceTransformer, util

# =========================
# Paths
# =========================

DATA_PATH = Path("data/processed/triple_embeddings.json")

# =========================
# GLOBAL CACHE (AUTO-RELOAD)
# =========================

TRIPLES = []
LAST_LOADED_TIME = 0

# =========================
# Load model (once)
# =========================

model = SentenceTransformer("all-MiniLM-L6-v2")


# =========================
# LOAD EMBEDDINGS (AUTO RELOAD)
# =========================

def load_embeddings():
    global TRIPLES, LAST_LOADED_TIME

    if not DATA_PATH.exists():
        return

    modified_time = os.path.getmtime(DATA_PATH)

    if modified_time != LAST_LOADED_TIME:
        print("🔄 Reloading embeddings...")

        with open(DATA_PATH, "r", encoding="utf-8") as f:
            TRIPLES = json.load(f)

        LAST_LOADED_TIME = modified_time


# =========================
# NORMALIZE
# =========================

def normalize_text(text: str) -> str:
    return text.lower().strip()


# =========================
# RELATION MAP
# =========================

RELATION_MAP = {
    "attack": ["attack", "attacks", "attacking", "strike", "bomb"],
    "control": ["control", "controls"],
    "influence": ["influence", "affect"],
    "approve": ["approve"],
    "sanction": ["sanction", "impose"]
}

RELATION_LOOKUP = {
    word: key
    for key, values in RELATION_MAP.items()
    for word in values
}


# =========================
# INTENT
# =========================

def extract_intent(query):
    for word in query.lower().split():
        if word in RELATION_LOOKUP:
            return RELATION_LOOKUP[word]
    return None


# =========================
# ENTITY (FUZZY)
# =========================

def extract_entity(query, graph):
    nodes = list(graph.nodes)

    match, score, _ = process.extractOne(
        query,
        nodes,
        scorer=fuzz.partial_ratio
    )

    if score > 75:
        return match

    return None


# =========================
# DIRECTION
# =========================

def extract_direction(query):
    if "who" in query.lower():
        return "incoming"
    return "any"


# =========================
# TIME
# =========================

def extract_time(query):
    q = query.lower()

    if "recent" in q or "now" in q:
        return 24
    if "today" in q:
        return 12
    if "week" in q:
        return 24 * 7

    return None


# =========================
# MAIN ENGINE
# =========================

def process_query(query, graph):

    # 🔥 AUTO-RELOAD embeddings
    load_embeddings()

    intent = extract_intent(query)
    entity = extract_entity(query, graph)
    direction = extract_direction(query)
    time_window = extract_time(query)

    query_embedding = model.encode(query, convert_to_tensor=True)

    now = datetime.utcnow()

    results = []

    for triple in TRIPLES:

        u = triple["subject"]
        v = triple["object"]
        relation = triple["relation"]
        timestamp = triple.get("published_at")
        context = triple.get("context", "")
        embedding = triple["embedding"]

        score = 0

        # -----------------
        # RELATION FILTER
        # -----------------
        if intent:
            if intent not in relation:
                continue
            score += 3

        # -----------------
        # ENTITY FILTER
        # -----------------
        if entity:
            if direction == "incoming":
                if v != entity:
                    continue
                score += 3
            else:
                if not (u == entity or v == entity):
                    continue
                score += 1

        # -----------------
        # TIME FILTER
        # -----------------
        if time_window and timestamp:
            ts = datetime.fromisoformat(timestamp)
            cutoff = now - timedelta(hours=time_window)

            if ts < cutoff:
                continue

            score += 2

        # -----------------
        # EMBEDDING SCORE
        # -----------------
        emb_score = util.cos_sim(
            query_embedding,
            embedding
        ).item()

        if emb_score < 0.3:
            continue

        score += emb_score * 2

        results.append({
            "source": u,
            "relation": relation,
            "target": v,
            "timestamp": timestamp,
            "context": context,
            "score": float(score)
        })

    results.sort(key=lambda x: x["score"], reverse=True)

    return results[:10]
