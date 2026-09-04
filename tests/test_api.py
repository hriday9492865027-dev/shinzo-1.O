"""API endpoint tests (health + basic chat)."""
from fastapi.testclient import TestClient

from app.api.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_chat_roundtrip() -> None:
    payload = {
        "user_id": "u1",
        "conversation_id": "c1",
        "message": "hey, rough day today",
    }
    response = client.post("/v1/chat", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["conversation_id"] == "c1"
    assert "rough day today" in body["reply"]


def test_chat_rejects_empty_message() -> None:
    payload = {"user_id": "u1", "conversation_id": "c1", "message": ""}
    response = client.post("/v1/chat", json=payload)
    assert response.status_code == 422
