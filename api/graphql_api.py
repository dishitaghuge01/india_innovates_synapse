import json
from pathlib import Path
import networkx as nx
import strawberry
from typing import List, Optional
import subprocess
import os

from api.semantic_engine import process_query, normalize_text

# =========================
# Graph path
# =========================

GRAPH_PATH = Path("data/processed/knowledge_graph.graphml")

G = None
LAST_GRAPH_LOAD_TIME = 0


# =========================
# AUTO-RELOAD GRAPH
# =========================


def load_graph():
    global G, LAST_GRAPH_LOAD_TIME

    if not GRAPH_PATH.exists():
        raise FileNotFoundError("Graph not found. Run kg_builder first.")

    modified_time = os.path.getmtime(GRAPH_PATH)

    if G is None or modified_time != LAST_GRAPH_LOAD_TIME:
        print("🔄 Reloading graph...")
        G = nx.read_graphml(GRAPH_PATH)
        LAST_GRAPH_LOAD_TIME = modified_time

    return G


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
# Mutation
# =========================


@strawberry.type
class Mutation:
    @strawberry.mutation
    def run_pipeline(self) -> str:
        subprocess.Popen(["python", "-m", "pipeline.pipeline_runner"])
        return "🚀 Pipeline started in background"


# =========================
# Helpers
# =========================


def find_best_entity_match(name: str):
    G = load_graph()

    name = normalize_text(name)

    for node in G.nodes:
        if name == node:
            return node

    for node in G.nodes:
        if name in node:
            return node

    return name


def get_relationships(entity_name: str):
    G = load_graph()

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
                    timestamp=data.get("timestamp"),
                )
            )

    return results


# =========================
# Query
# =========================


@strawberry.type
class Query:
    @strawberry.field
    def entity(self, name: str) -> Entity:
        matched = find_best_entity_match(name)

        return Entity(name=matched, relations=get_relationships(matched))

    @strawberry.field
    def search(
        self, relation: Optional[str] = None, limit: int = 50
    ) -> List[Relationship]:
        G = load_graph()

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
                    timestamp=data.get("timestamp"),
                )
            )

        return results[:limit]

    @strawberry.field
    def ask(self, question: str, limit: int = 10) -> List[SemanticResult]:
        G = load_graph()

        results = process_query(question, G)

        return [SemanticResult(**r) for r in results[:limit]]


# =========================
# Schema
# =========================

schema = strawberry.Schema(query=Query, mutation=Mutation)
