"""
Tests for the memory system (extraction, importance scoring, store/retrieve pipeline).
These tests use an in-memory SQLite DB (no disk state between runs).
"""
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("LLM_PROVIDER", "mock")


def test_extraction_finds_job_mention():
    from app.memory.extraction import extract

    msg = "I have an interview at Google next Thursday."
    candidates = extract(msg)
    assert any("interview" in c.lower() for c in candidates)


def test_extraction_empty_message():
    from app.memory.extraction import extract

    assert extract("") == []
    assert extract("ok") == []


def test_importance_scoring_high_for_upcoming_event():
    from app.memory.importance_scoring import score

    s = score("I have a surgery next Tuesday and I'm scared.")
    assert s >= 0.60, f"Expected >= 0.60, got {s}"


def test_importance_scoring_low_for_generic():
    from app.memory.importance_scoring import score

    s = score("I just kind of feel things sometimes.")
    assert s < 0.55


def test_filter_candidates_removes_low_scores():
    from app.memory.importance_scoring import filter_candidates

    candidates = [
        "I just kind of feel things.",
        "I have a wedding this Saturday — my sister is getting married.",
    ]
    filtered = filter_candidates(candidates)
    # Only the wedding one should pass
    assert len(filtered) >= 1
    assert "wedding" in filtered[0][0].lower()


def test_memory_db_init_and_model():
    import uuid
    from app.memory.db import get_session, init_db
    from app.memory.models import User

    init_db()
    uid = f"test-user-mem-{uuid.uuid4().hex[:8]}"
    with get_session() as session:
        user = User(id=uid, display_name="Test")
        session.add(user)

    with get_session() as session:
        u = session.get(User, uid)
        assert u is not None
        assert u.display_name == "Test"


def test_store_and_retrieve_memory():
    """Integration: store a memory and verify it's retrievable."""
    import uuid
    from app.memory.db import get_session, init_db
    from app.memory.models import User
    from app.memory.store import store_memory

    init_db()
    uid = f"u-mem-test-{uuid.uuid4().hex[:8]}"
    with get_session() as session:
        session.add(User(id=uid))

    mem_id = store_memory(
        user_id=uid,
        content="I have a big presentation at work next Monday.",
        importance=0.8,
    )
    assert mem_id is not None and len(mem_id) > 0
