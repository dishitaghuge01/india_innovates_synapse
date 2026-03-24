import json
import os
from pathlib import Path
from neo4j import GraphDatabase
from dotenv import load_dotenv

# =========================
# Load ENV
# =========================

load_dotenv()

URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")

# =========================
# Paths
# =========================

INPUT_PATH = Path("data/processed/validated_triples.json")

# =========================
# Driver
# =========================

driver = GraphDatabase.driver(
    URI,
    auth=(USERNAME, PASSWORD)
)

# =========================
# Create indexes (important)
# =========================

def create_indexes(tx):
    tx.run("CREATE INDEX IF NOT EXISTS FOR (n:Entity) ON (n.name)")
    tx.run("CREATE INDEX IF NOT EXISTS FOR ()-[r:RELATION]-() ON (r.timestamp)")

# =========================
# Insert triple
# =========================

def create_triple(tx, triple):

    query = """
    MERGE (s:Entity {name: $subj})
    MERGE (o:Entity {name: $obj})

    CREATE (s)-[r:RELATION {
        type: $rel,
        context: $context,
        article_id: $article_id,
        timestamp: $timestamp
    }]->(o)
    """

    tx.run(
        query,
        subj=triple["subject"].lower(),
        obj=triple["object"].lower(),
        rel=triple["relation"],
        context=triple.get("context", ""),
        article_id=triple.get("article_id", ""),
        timestamp=triple.get("published_at") or triple.get("timestamp", "")
    )

# =========================
# Load graph
# =========================

def load_graph():

    if not INPUT_PATH.exists():
        print("Triple file not found")
        return

    with driver.session() as session:

        # create indexes once
        session.write_transaction(create_indexes)

        count = 0

        with open(INPUT_PATH, "r", encoding="utf-8") as f:

            for line in f:
                triple = json.loads(line)

                session.write_transaction(
                    create_triple,
                    triple
                )

                count += 1

    print("✅ Loaded triples:", count)

# =========================
# Run
# =========================

if __name__ == "__main__":
    load_graph()
    driver.close()
