import json
from pathlib import Path
import networkx as nx
import strawberry
from typing import List, Optional
import subprocess
from pipeline.state_manager import set_pipeline_status, get_pipeline_status
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
    entity_type: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    relations: List[Relationship]


# =========================
# Mutation
# =========================


@strawberry.type
class Mutation:
    @strawberry.mutation
    def run_pipeline(self) -> str:
        set_pipeline_status("RUNNING")
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
        G = load_graph()
        node_data = G.nodes.get(matched, {})
        entity_type = node_data.get("type")
        lat = node_data.get("latitude")
        lon = node_data.get("longitude")

        latitude, longitude = None, None
        try:
            if lat is not None:
                latitude = float(lat)
            if lon is not None:
                longitude = float(lon)
        except Exception:
            latitude, longitude = None, None

        return Entity(
            name=matched,
            entity_type=entity_type,
            latitude=latitude,
            longitude=longitude,
            relations=get_relationships(matched)
        )

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

    @strawberry.field
    def pipelineStatus(self) -> str:
        return get_pipeline_status()

    @strawberry.field
    def getGeospatialEntities(self) -> List[Entity]:
        G = load_graph()
        geospatial_entities = []
        for node, data in G.nodes(data=True):
            entity_type = data.get("type")
            name = node
            lat = data.get("latitude")
            lon = data.get("longitude")
            latitude, longitude = None, None
            try:
                if lat is not None:
                    latitude = float(lat)
                if lon is not None:
                    longitude = float(lon)
            except Exception:
                latitude, longitude = None, None
            # Only include plausible location types or those having lat/lon/geo-type (fallback to type-match on string)
            is_location = False
            if entity_type is not None and entity_type.lower() in {"country", "state", "province", "city", "location", "facility", "region"}:
                is_location = True
            # Accept if lat/lon provided
            if latitude is not None and longitude is not None:
                is_location = True
            # Optionally add more logic for other plausible type heuristics

            if is_location:
                geospatial_entities.append(
                    Entity(
                        name=name,
                        entity_type=entity_type,
                        latitude=latitude,
                        longitude=longitude,
                        relations=[]
                    )
                )
            # Fallback: If not recognized as a geospatial entity but has plausible name/type, ensure at least name/type is included.
            elif entity_type is not None and entity_type.lower() in {"country", "state", "province", "city", "facility", "region"}:
                geospatial_entities.append(
                    Entity(
                        name=name,
                        entity_type=entity_type,
                        latitude=None,
                        longitude=None,
                        relations=[]
                    )
                )
        return geospatial_entities
        G = load_graph()

        results = process_query(question, G)

        return [SemanticResult(**r) for r in results[:limit]]


# =========================
# Schema
# =========================

schema = strawberry.Schema(query=Query, mutation=Mutation)
