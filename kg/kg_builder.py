import json
from pathlib import Path
import networkx as nx

# =========================
# Paths
# =========================

INPUT_PATH = Path("data/processed/validated_triples.json")
OUTPUT_GRAPH = Path("data/processed/knowledge_graph.graphml")

# =========================
# Graph (Multi-edge for realism)
# =========================

G = nx.MultiDiGraph()

# =========================
# Load existing graph (incremental updates)
# =========================

if OUTPUT_GRAPH.exists():
    print("Loading existing graph...")
    G = nx.read_graphml(OUTPUT_GRAPH)

# =========================
# Add triple to graph
# =========================

def add_triple(triple):

    subj = triple["subject"].lower().strip()
    obj = triple["object"].lower().strip()
    rel = triple["relation"].lower().strip()

    context = triple.get("context", "")
    article_id = triple.get("article_id", "")
    timestamp = triple.get("published_at") or triple.get("timestamp", "")

    # add nodes with metadata placeholder
    if subj not in G:
        G.add_node(subj, type="entity")

    if obj not in G:
        G.add_node(obj, type="entity")

    # create unique edge key (important for multi-edges)
    edge_key = f"{rel}_{article_id}_{timestamp}"

    G.add_edge(
        subj,
        obj,
        key=edge_key,
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
    print("Input triples not found:", INPUT_PATH)
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

print("\n✅ Graph built successfully")
print("Triples added:", count)
print("Nodes:", G.number_of_nodes())
print("Edges:", G.number_of_edges())
print("Saved →", OUTPUT_GRAPH)
