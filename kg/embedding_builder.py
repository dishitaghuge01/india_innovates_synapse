import json
import hashlib
from pathlib import Path
from sentence_transformers import SentenceTransformer

# =========================
# Paths
# =========================

INPUT_PATH = Path("data/processed/validated_triples.json")
OUTPUT_PATH = Path("data/processed/triple_embeddings.json")

# =========================
# Model
# =========================

model = SentenceTransformer("all-MiniLM-L6-v2")

# =========================
# Hash function (for dedup)
# =========================

def generate_hash(triple):

    unique_string = (
        triple.get("subject", "") +
        triple.get("relation", "") +
        triple.get("object", "") +
        triple.get("article_id", "") +
        str(triple.get("timestamp", ""))
    )

    return hashlib.md5(unique_string.encode()).hexdigest()

# =========================
# Load existing embeddings
# =========================

def load_existing():

    if not OUTPUT_PATH.exists():
        return []

    with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# =========================
# Main builder (incremental)
# =========================

def build_embeddings():

    if not INPUT_PATH.exists():
        print("❌ Input file not found")
        return

    print("🔄 Loading existing embeddings...")
    existing_data = load_existing()

    existing_hashes = {
        item.get("hash")
        for item in existing_data
        if "hash" in item
    }

    new_embeddings = []
    processed = 0
    skipped = 0

    print("🚀 Processing new triples...")

    with open(INPUT_PATH, "r", encoding="utf-8") as f:

        for line in f:

            triple = json.loads(line)

            triple_hash = generate_hash(triple)

            # -------------------------
            # Skip duplicates
            # -------------------------
            if triple_hash in existing_hashes:
                skipped += 1
                continue

            # -------------------------
            # Create embedding
            # -------------------------
            text = f"{triple['subject']} {triple['relation']} {triple['object']}. {triple.get('context','')}"

            embedding = model.encode(text).tolist()

            triple["embedding"] = embedding
            triple["hash"] = triple_hash

            new_embeddings.append(triple)
            processed += 1

    # -------------------------
    # Append mode
    # -------------------------

    final_data = existing_data + new_embeddings

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(final_data, f)

    # -------------------------
    # Stats
    # -------------------------

    print("\n✅ Embedding update complete")
    print("New embeddings added:", processed)
    print("Skipped (duplicates):", skipped)
    print("Total stored:", len(final_data))
    print("Saved →", OUTPUT_PATH)


# =========================
# Run
# =========================

if __name__ == "__main__":
    build_embeddings()
