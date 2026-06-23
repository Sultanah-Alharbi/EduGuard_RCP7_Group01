# Import libraries
import json
from pathlib import Path
from sklearn.metrics import accuracy_score, classification_report
from eduguard_pipeline import classify_message

# Define files
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "01_data"
LOG_DIR = BASE_DIR / "logs"
BENCHMARK_FILE = DATA_DIR / "benchmark_boundary_100.jsonl"
ERROR_FILE = LOG_DIR / "benchmark_errors.jsonl"

# Read JSONL file
def read_jsonl(file_path):
    lines = file_path.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]

# Save wrong predictions
def save_errors(errors):
    ERROR_FILE.parent.mkdir(exist_ok=True)
    with ERROR_FILE.open("w", encoding="utf-8") as file:
        for row in errors:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")

# Evaluate pipeline labels
records = read_jsonl(BENCHMARK_FILE)
true_labels = []
pred_labels = []
errors = []

for row in records:
    label, confidence, method, matched_rule = classify_message(row["text"])

    true_labels.append(row["label"])
    pred_labels.append(label)

    if label != row["label"]:
        errors.append({
            "id": row["id"],
            "text": row["text"],
            "true_label": row["label"],
            "predicted_label": label,
            "confidence": round(confidence, 4),
            "method": method,
            "matched_rule": matched_rule
        })

# Print results
accuracy = accuracy_score(true_labels, pred_labels)

print("Benchmark samples:", len(records))
print("Benchmark accuracy:", round(accuracy, 4))
print("\nClassification report:")
print(classification_report(true_labels, pred_labels, zero_division=0))

print("Errors:", len(errors))
save_errors(errors)
print("Saved errors to:", ERROR_FILE)