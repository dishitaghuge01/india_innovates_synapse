import faiss
import numpy as np
import os

EMBEDDING_PATH = "data/processed/article_embeddings.npy"
INDEX_PATH = "data/vector_store/faiss_index.index"


def load_embeddings():

    if not os.path.exists(EMBEDDING_PATH):
        raise FileNotFoundError("Embeddings not found")

    embeddings = np.load(EMBEDDING_PATH)

    return embeddings


def build_faiss_index(embeddings):

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatL2(dimension)

    index.add(embeddings)

    return index


def save_index(index):

    os.makedirs("data/vector_store", exist_ok=True)

    faiss.write_index(index, INDEX_PATH)

    print("FAISS index saved")


def run_faiss_pipeline():

    print("Loading embeddings...")

    embeddings = load_embeddings()

    print(f"Loaded {len(embeddings)} embeddings")

    print("Building FAISS index...")

    index = build_faiss_index(embeddings)

    print("Saving index...")

    save_index(index)

    print("FAISS pipeline completed")


if __name__ == "__main__":

    run_faiss_pipeline()
