"""
Stage 2 — Validation.
Validates each normalized raw record dict against dataset/scripts/schema.py::TrainingRecord.
Returns (valid_records, errors) so the pipeline can report bad rows without crashing the whole run.
"""
from pydantic import ValidationError

from dataset.scripts.schema import TrainingRecord


def validate_records(raw_records: list[dict]) -> tuple[list[TrainingRecord], list[str]]:
    valid: list[TrainingRecord] = []
    errors: list[str] = []

    for i, raw in enumerate(raw_records):
        try:
            valid.append(TrainingRecord(**raw))
        except ValidationError as e:
            errors.append(f"record[{i}] (id={raw.get('id', '?')}): {e}")

    return valid, errors
