"""
Runs the full pipeline: normalize -> validate -> dedupe -> categorize (report) -> export JSONL.
Usage: python -m dataset.scripts.pipeline <raw_json_path> <output_jsonl_path>
Raw input is a JSON array of record dicts (id, category, user_message, shinzo_reply, notes).
"""
import json
import sys

from dataset.scripts.categorize import category_counts
from dataset.scripts.dedupe import dedupe_records
from dataset.scripts.export_jsonl import export_jsonl
from dataset.scripts.normalize import normalize_record
from dataset.scripts.validate import validate_records


def run_pipeline(raw_path: str, output_path: str) -> None:
    with open(raw_path, encoding="utf-8") as f:
        raw_records = json.load(f)

    normalized = [normalize_record(r) for r in raw_records]
    valid, errors = validate_records(normalized)

    if errors:
        print(f"{len(errors)} record(s) failed validation:")
        for e in errors:
            print(f"  - {e}")

    deduped = dedupe_records(valid)
    print(f"Records: raw={len(raw_records)} valid={len(valid)} after_dedupe={len(deduped)}")

    counts = category_counts(deduped)
    print("Category coverage:")
    for cat, count in counts.items():
        print(f"  {cat}: {count}")

    written = export_jsonl(deduped, output_path)
    print(f"Wrote {written} records to {output_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python -m dataset.scripts.pipeline <raw_json_path> <output_jsonl_path>")
        sys.exit(1)
    run_pipeline(sys.argv[1], sys.argv[2])
