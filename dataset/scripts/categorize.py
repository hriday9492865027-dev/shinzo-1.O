"""
Stage 4 — Category coverage report.
Categorization itself happens at authoring time (each TrainingRecord already carries a
DatasetCategory) — this stage's job is to report coverage per category so gaps are visible before
fine-tuning, per the roadmap's "start with ~100 high-quality, diverse examples" guidance.
"""
from collections import Counter

from dataset.scripts.schema import DatasetCategory, TrainingRecord


def category_counts(records: list[TrainingRecord]) -> dict[str, int]:
    counts = Counter(r.category.value for r in records)
    # ensure every category appears in the report even if count is 0
    return {cat.value: counts.get(cat.value, 0) for cat in DatasetCategory}
