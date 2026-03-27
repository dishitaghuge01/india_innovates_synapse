import json
import os
from pathlib import Path
from neo4j import GraphDatabase
from dotenv import load_dotenv

# =========================
# Load ENV
# =========================

load_dotenv()

URI = os.getenv("NEO4J_URI")  # MUST be: bolt://127.0.0.1:7687
USERNAME = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")

# =========================
# Paths
# =========================

INPUT_PATH = Path("data/processed/validated_triples.json")

# =========================
# Config
# =========================

BATCH_SIZE = 500  # you can tune: 200–1000 depending on RAM

# =========================
# Driver
# =========================

driver = GraphDatabase.driver(
    URI,
    auth=(USERNAME, PASSWORD)
)

# =========================
# Create indexes
# =========================

def create_indexes(tx):
    tx.run("CREATE INDEX IF NOT EXISTS FOR (n:Entity) ON (n.name)")
    tx.run("CREATE INDEX IF NOT EXISTS FOR ()-[r:RELATION]-() ON (r.timestamp)")

# =========================
# Batch insert
# =========================

def create_batch(tx, batch):

    query = """
    UNWIND $triples AS triple

    MERGE (s:Entity {name: toLower(triple.subject)})
    MERGE (o:Entity {name: toLower(triple.object)})

    CREATE (s)-[r:RELATION {
        type: triple.relation,
        context: triple.context,
        article_id: triple.article_id,
        timestamp: triple.timestamp
    }]->(o)
    """

    tx.run(query, triples=batch)

# =========================
# Load graph
# =========================

def load_graph():

    if not INPUT_PATH.exists():
        print("❌ Triple file not found")
        return

    print("📥 Loading triples...")

    # Read all triples first
    triples = []

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        for line in f:
            triple = json.loads(line)

            triples.append({
                "subject": triple["subject"],
                "object": triple["object"],
                "relation": triple["relation"],
                "context": triple.get("context", ""),
                "article_id": triple.get("article_id", ""),
                "timestamp": triple.get("published_at") or triple.get("timestamp", "")
            })

    total = len(triples)
    print(f"📊 Total triples: {total}")

    with driver.session() as session:

        # Create indexes once
        print("⚙️ Creating indexes...")
        session.execute_write(create_indexes)

        # Batch insert
        count = 0

        for i in range(0, total, BATCH_SIZE):
            batch = triples[i:i+BATCH_SIZE]

            session.execute_write(create_batch, batch)

            count += len(batch)
            print(f"✅ Inserted: {count}/{total}")

    print(f"\n🚀 DONE: Loaded {total} triples successfully")

# =========================
# Run
# =========================

if __name__ == "__main__":
    try:
        load_graph()
    finally:
        driver.close()
