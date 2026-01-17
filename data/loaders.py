import json
from pathlib import Path

DATA_DIR = Path(__file__).parent

def load_transporters():
    path = DATA_DIR / "transporters.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
