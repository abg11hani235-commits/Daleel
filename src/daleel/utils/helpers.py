"""Common helper functions (file I/O, JSONL readers/writers)."""
import json

def load_jsonl(filepath: str) -> list:
    with open(filepath, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

def save_jsonl(data: list, filepath: str):
    with open(filepath, "w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")