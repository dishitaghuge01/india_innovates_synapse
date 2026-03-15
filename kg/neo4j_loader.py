import json
from pathlib import Path
from neo4j import GraphDatabase

# =========================
# Neo4j connection
# =========================

URI = "neo4j://127.0.0.1:7687"
USERNAME = "neo4j"
PASSWORD = "Coffee@1125"   # change this

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
# Cypher query
# =========================

def create_triple(tx, subj, rel, obj):

    query = f"""
    MERGE (s:Entity {{name:$subj}})
    MERGE (o:Entity {{name:$obj}})
    MERGE (s)-[r:{rel.upper()}]->(o)
    """

    tx.run(query, subj=subj, obj=obj)

# =========================
# Load triples
# =========================

def load_graph():

    if not INPUT_PATH.exists():
        print("Triple file not found")
        return

    with driver.session() as session:

        with open(INPUT_PATH, "r", encoding="utf-8") as f:

            count = 0

            for line in f:

                triple = json.loads(line)

                subj = triple["subject"].lower()
                rel = triple["relation"].replace(" ", "_")
                obj = triple["object"].lower()

                session.write_transaction(
                    create_triple,
                    subj,
                    rel,
                    obj
                )

                count += 1

    print("Loaded triples:", count)


# =========================
# Run
# =========================

if __name__ == "__main__":

    load_graph()
    driver.close()
