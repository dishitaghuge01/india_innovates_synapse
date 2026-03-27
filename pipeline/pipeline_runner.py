import subprocess
import time
from pipeline.state_manager import set_pipeline_status

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
    set_pipeline_status("RUNNING")
    print("Starting pipeline...\n")
    try:
        for step in STEPS:
            print(f"▶ Running: {step}")
            result = subprocess.run(step, shell=True)
            if result.returncode != 0:
                print(f"Failed at step: {step}")
                set_pipeline_status("FAILED")
                return
            print("✅ Done\n")
            time.sleep(1)
        set_pipeline_status("COMPLETED")
        print("Pipeline completed successfully!")
    except Exception as ex:
        set_pipeline_status("FAILED")
        raise


if __name__ == "__main__":
    run_pipeline()
