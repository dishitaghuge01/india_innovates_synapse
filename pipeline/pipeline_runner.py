import subprocess
import time

STEPS = [
    "python -m ingestion.ingestion_manager",
    "python -m processing.ner_entity_linking",
    "python -m processing.relation_extraction",
    "python -m processing.entity_relation_filter",
    "python -m processing.canonicalize_relations",
    "python -m processing.entity_canonicalizer",
    "python -m processing.ontology_validator",
    "python -m kg.kg_builder",
    "python -m kg.embedding_builder"
]

def run_pipeline():

    print("Starting pipeline...\n")

    for step in STEPS:
        print(f"▶ Running: {step}")

        result = subprocess.run(step, shell=True)

        if result.returncode != 0:
            print(f"Failed at step: {step}")
            return

        print("✅ Done\n")
        time.sleep(1)

    print("Pipeline completed successfully!")


if __name__ == "__main__":
    run_pipeline()
