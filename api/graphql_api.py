import json
from pathlib import Path
import networkx as nx
import strawberry
from typing import List, Optional

# =========================
# Load Graph
# =========================

GRAPH_PATH = Path("data/processed/knowledge_graph.graphml")

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
class Entity:
    name: str
    relations: List[Relationship]


# =========================
# Query Resolvers
# =========================

def get_relationships(entity_name: str):

    results = []

    for u, v, data in G.edges(data=True):

        if u == entity_name:

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


@strawberry.type
class Query:

    @strawberry.field
    def entity(self, name: str) -> Entity:

        name = name.lower()

        return Entity(
            name=name,
            relations=get_relationships(name)
        )

    @strawberry.field
    def search(self, relation: Optional[str] = None) -> List[Relationship]:

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

        return results


# =========================
# Schema
# =========================

schema = strawberry.Schema(query=Query)
