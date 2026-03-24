import json
from pathlib import Path
import networkx as nx
import strawberry
from typing import List, Optional

from api.semantic_engine import process_query, normalize_text

# =========================
# Load Graph
# =========================

GRAPH_PATH = Path("data/processed/knowledge_graph.graphml")

if not GRAPH_PATH.exists():
    raise FileNotFoundError("Graph not found. Run kg_builder first.")

G = nx.read_graphml(GRAPH_PATH)

# =========================
# GraphQL Types
# =========================

@strawberry.type
class Relationship:
    source: str
    target: str
    relation: str
    context: Optional[str]
    timestamp: Optional[str]


@strawberry.type
class SemanticResult:
    source: str
    relation: str
    target: str
    timestamp: Optional[str]
    context: Optional[str]
    score: float


@strawberry.type
class Entity:
    name: str
    relations: List[Relationship]


# =========================
# Helpers
# =========================

def find_best_entity_match(name: str):
    """
    Fuzzy match entity name to graph nodes
    """
    name = normalize_text(name)

    for node in G.nodes:
        if name == node:
            return node

    # fallback: partial match
    for node in G.nodes:
        if name in node:
            return node

    return name


def get_relationships(entity_name: str):
    entity_name = find_best_entity_match(entity_name)

    results = []

    for u, v, data in G.edges(data=True):

        if u == entity_name or v == entity_name:

            results.append(
                Relationship(
                    source=u,
                    target=v,
                    relation=data.get("relation"),
                    context=data.get("context"),
                    timestamp=data.get("timestamp")
                )
            )

    return results


# =========================
# Query Resolvers
# =========================

@strawberry.type
class Query:

    # -------------------------
    # Entity Query
    # -------------------------
    @strawberry.field
    def entity(self, name: str) -> Entity:

        matched = find_best_entity_match(name)

        return Entity(
            name=matched,
            relations=get_relationships(matched)
        )

    # -------------------------
    # Basic Search
    # -------------------------
    @strawberry.field
    def search(
        self,
        relation: Optional[str] = None,
        limit: int = 50
    ) -> List[Relationship]:

        results = []

        for u, v, data in G.edges(data=True):

            if relation and data.get("relation") != relation:
                continue

            results.append(
                Relationship(
                    source=u,
                    target=v,
                    relation=data.get("relation"),
                    context=data.get("context"),
                    timestamp=data.get("timestamp")
                )
            )

        return results[:limit]

    # -------------------------
    # 🔥 Semantic Query
    # -------------------------
    @strawberry.field
    def ask(
        self,
        question: str,
        limit: int = 10
    ) -> List[SemanticResult]:

        results = process_query(question, G)

        # sort by score (important)
        results = sorted(results, key=lambda x: x["score"], reverse=True)

        # limit results
        results = results[:limit]

        return [
            SemanticResult(**r)
            for r in results
        ]


# =========================
# Schema
# =========================

schema = strawberry.Schema(query=Query)
