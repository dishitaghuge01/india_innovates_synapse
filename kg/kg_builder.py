import json
from pathlib import Path
import networkx as nx

# =========================
# Paths
# =========================

INPUT_PATH = Path("data/processed/validated_triples.json")
OUTPUT_GRAPH = Path("data/processed/knowledge_graph.graphml")

# =========================
# Load or Create Graph (Incremental)
# =========================

if OUTPUT_GRAPH.exists():
    print("📦 Loading existing graph...")
    G = nx.read_graphml(OUTPUT_GRAPH)
else:
    print("🆕 Creating new graph...")
    G = nx.DiGraph()

# =========================
# Add triple (Incremental + Dedup)
# =========================

def add_triple(triple):

    subj = triple["subject"].lower().strip()
    obj = triple["object"].lower().strip()
    rel = triple["relation"].lower().strip()

    context = triple.get("context", "")
    article_id = triple.get("article_id", "")
    timestamp = triple.get("published_at") or triple.get("timestamp", "")

    # -----------------
    # Add nodes
    # -----------------
    if subj not in G:
        G.add_node(subj, type="entity")

    if obj not in G:
        G.add_node(obj, type="entity")

    # -----------------
    # Edge exists → UPDATE
    # -----------------
    if G.has_edge(subj, obj):

        edge = G[subj][obj]

        # increment weight
        edge["weight"] = int(edge.get("weight", 1)) + 1

        # update relation (keep latest)
        edge["relation"] = rel

        # update latest timestamp
        if timestamp:
            edge["timestamp"] = timestamp

        # append context safely
        existing_context = edge.get("context", "")

        if context and context not in existing_context:
            edge["context"] = existing_context + " | " + context

    # -----------------
    # New edge → CREATE
    # -----------------
    else:

        G.add_edge(
            subj,
            obj,
            relation=rel,
            context=context,
            article_id=article_id,
            timestamp=timestamp,
            weight=1
        )

# =========================
# Process triples
# =========================

if not INPUT_PATH.exists():
    print("❌ Input triples not found:", INPUT_PATH)
    exit()

count = 0

with open(INPUT_PATH, "r", encoding="utf-8") as f:
    for line in f:
        triple = json.loads(line)
        add_triple(triple)
        count += 1

# =========================
# Save graph
# =========================

OUTPUT_GRAPH.parent.mkdir(parents=True, exist_ok=True)
nx.write_graphml(G, OUTPUT_GRAPH)

print("\n✅ Graph updated successfully")
print("Triples processed:", count)
print("Nodes:", G.number_of_nodes())
print("Edges:", G.number_of_edges())
print("Saved →", OUTPUT_GRAPH)
