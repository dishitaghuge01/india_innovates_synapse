import json
from pathlib import Path
from datetime import datetime

STATUS_FILE = Path("data/cache/pipeline_status.json")


def set_pipeline_status(status: str):
    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "status": status,
        "timestamp": datetime.utcnow().isoformat()
    }
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f)


def get_pipeline_status() -> str:
    if not STATUS_FILE.exists():
        return json.dumps({"status": "NONE", "timestamp": None})
    with open(STATUS_FILE, "r", encoding="utf-8") as f:
        return f.read()
