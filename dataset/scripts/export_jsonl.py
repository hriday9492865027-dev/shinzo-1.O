"""
Stage 5 — JSONL export.
Writes validated, deduplicated TrainingRecords to a JSONL file (one JSON object per line), the
format training/train.py (Milestone 6) will consume.
"""
import json
from pathlib import Path

from dataset.scripts.schema import TrainingRecord


def export_jsonl(records: list[TrainingRecord], output_path: str | Path) -> int:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(record.model_dump_json() + "\n")

    return len(records)


def load_jsonl(input_path: str | Path) -> list[TrainingRecord]:
    input_path = Path(input_path)
    records = []
    with input_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(TrainingRecord(**json.loads(line)))
    return records
