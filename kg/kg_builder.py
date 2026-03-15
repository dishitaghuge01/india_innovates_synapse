import json
from pathlib import Path
import networkx as nx

# =========================
# Paths
# =========================

INPUT_PATH = Path("data/processed/validated_triples.json")
OUTPUT_GRAPH = Path("data/processed/knowledge_graph.graphml")

# =========================
# Create graph
# =========================

G = nx.DiGraph()

# =========================
# Load triples
# =========================

if not INPUT_PATH.exists():
    print("Input triples not found:", INPUT_PATH)
    exit()

with open(INPUT_PATH, "r", encoding="utf-8") as f:

    for line in f:

        triple = json.loads(line)

        subj = triple["subject"].lower().strip()
        rel = triple["relation"].lower().strip()
        obj = triple["object"].lower().strip()

        # add nodes
        G.add_node(subj)
        G.add_node(obj)

        # add edge
        if G.has_edge(subj, obj):

            # increase support count
            G[subj][obj]["weight"] += 1

        else:

            G.add_edge(
                subj,
                obj,
                relation=rel,
                weight=1
            )

# =========================
# Save graph
# =========================

OUTPUT_GRAPH.parent.mkdir(parents=True, exist_ok=True)

nx.write_graphml(G, OUTPUT_GRAPH)

print("Graph built successfully")
print("Nodes:", G.number_of_nodes())
print("Edges:", G.number_of_edges())
print("Saved →", OUTPUT_GRAPH)
