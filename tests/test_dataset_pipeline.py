"""Tests for the dataset pipeline stages (Milestone 4)."""
import json

from dataset.scripts.categorize import category_counts
from dataset.scripts.dedupe import dedupe_records
from dataset.scripts.export_jsonl import export_jsonl, load_jsonl
from dataset.scripts.normalize import normalize_text
from dataset.scripts.schema import DatasetCategory, TrainingRecord
from dataset.scripts.validate import validate_records


def make_raw(i: int, category: str = "natural_conversation") -> dict:
    return {
        "id": f"{category}_{i}",
        "category": category,
        "user_message": f"  message {i}  \n\n\n",
        "shinzo_reply": f"reply {i}",
    }


def test_normalize_text_collapses_whitespace() -> None:
    assert normalize_text("  hi   there  \n\n\n\nbud  ") == "hi there \n\nbud"


def test_validate_accepts_good_records() -> None:
    raw = [make_raw(1), make_raw(2)]
    valid, errors = validate_records(raw)
    assert len(valid) == 2
    assert errors == []


def test_validate_rejects_bad_category() -> None:
    raw = [{**make_raw(1), "category": "not_a_real_category"}]
    valid, errors = validate_records(raw)
    assert len(valid) == 0
    assert len(errors) == 1


def test_validate_rejects_empty_message() -> None:
    raw = [{**make_raw(1), "user_message": ""}]
    valid, errors = validate_records(raw)
    assert len(valid) == 0
    assert len(errors) == 1


def test_dedupe_removes_exact_duplicates() -> None:
    r1 = TrainingRecord(id="a", category=DatasetCategory.NATURAL_CONVERSATION,
                         user_message="hi", shinzo_reply="hey")
    r2 = TrainingRecord(id="b", category=DatasetCategory.NATURAL_CONVERSATION,
                         user_message="hi", shinzo_reply="hey")
    r3 = TrainingRecord(id="c", category=DatasetCategory.NATURAL_CONVERSATION,
                         user_message="hi", shinzo_reply="different reply")
    deduped = dedupe_records([r1, r2, r3])
    assert len(deduped) == 2


def test_category_counts_includes_all_categories_even_at_zero() -> None:
    r1 = TrainingRecord(id="a", category=DatasetCategory.LONELINESS,
                         user_message="hi", shinzo_reply="hey")
    counts = category_counts([r1])
    assert counts["loneliness"] == 1
    assert counts["breakups_recovery"] == 0
    assert len(counts) == len(DatasetCategory)


def test_export_and_load_jsonl_roundtrip(tmp_path) -> None:
    records = [
        TrainingRecord(id="a", category=DatasetCategory.HUMOR_PLAYFUL,
                        user_message="tell me a joke", shinzo_reply="why did the chicken..."),
    ]
    out_path = tmp_path / "out.jsonl"
    written = export_jsonl(records, out_path)
    assert written == 1

    with out_path.open() as f:
        line = json.loads(f.readline())
    assert line["id"] == "a"

    loaded = load_jsonl(out_path)
    assert len(loaded) == 1
    assert loaded[0].user_message == "tell me a joke"
