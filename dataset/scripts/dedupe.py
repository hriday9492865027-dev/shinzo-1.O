"""
Stage 3 — Deduplication.
Removes exact and near-duplicate records by normalized (user_message, shinzo_reply) pair, since
the roadmap explicitly prioritizes quality/diversity over volume — duplicate examples add noise
to fine-tuning without adding signal.
"""
from dataset.scripts.schema import TrainingRecord


def dedupe_records(records: list[TrainingRecord]) -> list[TrainingRecord]:
    seen: set[tuple[str, str]] = set()
    deduped: list[TrainingRecord] = []

    for record in records:
        key = (record.user_message.lower(), record.shinzo_reply.lower())
        if key in seen:
            continue
        seen.add(key)
        deduped.append(record)

    return deduped
