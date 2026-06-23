# Import libraries
import json
from pathlib import Path
from collections import Counter

# Define dataset files and labels
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "01_data"
FILES = [
    "eduguard_guardrail_clean_800.json",
    "train.jsonl",
    "validation.jsonl",
    "test.jsonl",
    "benchmark_boundary_100.jsonl"
]

EXPECTED_LABELS = {"SAFE", "UNSAFE", "SENSITIVE", "OUT_OF_SCOPE", "PROMPT_INJECTION"}

# Read dataset file
def read_records(file_name):
    file_path = DATA_DIR / file_name

    if file_path.suffix == ".json":
        return json.loads(file_path.read_text(encoding="utf-8"))

    lines = file_path.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]

# Check dataset quality
def check_file(file_name):
    records = read_records(file_name)
    labels = Counter(row["label"] for row in records)
    empty_text = sum(1 for row in records if not row.get("text", "").strip())
    bad_labels = set(labels) - EXPECTED_LABELS

    print("\n---", file_name, "---")
    print("Total:", len(records))
    print("Labels:", dict(labels))
    print("Empty text:", empty_text)
    print("Bad labels:", bad_labels)

# Run checks
for file_name in FILES:
    check_file(file_name)