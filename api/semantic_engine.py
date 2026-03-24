from datetime import datetime, timedelta
from rapidfuzz import process, fuzz
from sentence_transformers import SentenceTransformer, util

# =========================
# Load model
# =========================

model = SentenceTransformer("all-MiniLM-L6-v2")

# =========================
# Relation synonyms
# =========================

RELATION_MAP = {
    "attack": ["attack", "attacks", "attacking", "strike", "bomb", "hit"],
    "control": ["control", "controls", "govern"],
    "influence": ["influence", "affect"],
    "approve": ["approve", "approves"],
    "sanction": ["sanction", "impose", "imposed"]
}

# reverse lookup
RELATION_LOOKUP = {
    word: key
    for key, values in RELATION_MAP.items()
    for word in values
}
    # =========================
    # TEXT NORMALIZATION
    # =========================

def normalize_text(text: str) -> str:
    return text.lower().strip()

# =========================
# INTENT + DIRECTION
# =========================

def extract_intent(query: str):

    query = query.lower().split()

    for word in query:
        if word in RELATION_LOOKUP:
            return RELATION_LOOKUP[word]

    return None


def extract_direction(query: str):

    query = query.lower()

    if "who" in query:
        return "incoming"  # who did X → incoming edge

    return "any"


# =========================
# ENTITY (fuzzy)
# =========================

def extract_entity(query: str, graph):

    nodes = list(graph.nodes)
    query = query.lower()

    match, score, _ = process.extractOne(
        query,
        nodes,
        scorer=fuzz.partial_ratio
    )

    if score > 75:
        return match

    return None


# =========================
# TIME
# =========================

def extract_time(query: str):

    query = query.lower()

    if "recent" in query or "currently" in query or "now" in query:
        return 24

    if "today" in query:
        return 12

    if "week" in query:
        return 24 * 7

    return None


# =========================
# MAIN ENGINE
# =========================

def process_query(query: str, graph):

    intent = extract_intent(query)
    entity = extract_entity(query, graph)
    direction = extract_direction(query)
    time_window = extract_time(query)

    results = []

    now = datetime.utcnow()

    for u, v, data in graph.edges(data=True):

        relation = data.get("relation", "")
        timestamp = data.get("timestamp")
        context = data.get("context", "")

        score = 0

        # -----------------
        # 1. RELATION FILTER (STRICT)
        # -----------------
        if intent:
            valid_words = RELATION_MAP.get(intent, [])

            if not any(word in relation for word in valid_words):
                continue

            score += 2


        # -----------------
        # 2. ENTITY FILTER
        # -----------------
        if entity:
            if direction == "incoming":
                if v != entity:
                    continue
                score += 3

            elif direction == "any":
                if not (u == entity or v == entity):
                    continue
                score += 1

        # -----------------
        # 3. TIME FILTER
        # -----------------
        if time_window and timestamp:

            ts = datetime.fromisoformat(timestamp)
            cutoff = now - timedelta(hours=time_window)

            if ts < cutoff:
                continue

            score += 2

        # -----------------
        # 4. SEMANTIC SCORE
        # -----------------
        text = f"{u} {relation} {v}. {context}"

        emb_score = util.cos_sim(
            model.encode(query, convert_to_tensor=True),
            model.encode(text, convert_to_tensor=True)
        ).item()

        if emb_score < 0.5:
            continue

        score += emb_score

        results.append({
            "source": u,
            "relation": relation,
            "target": v,
            "timestamp": timestamp,
            "context": context,
            "score": float(score)
        })


    # -----------------
    # SORT + CLEAN
    # -----------------
    results.sort(key=lambda x: x["score"], reverse=True)

    return results[:10]
