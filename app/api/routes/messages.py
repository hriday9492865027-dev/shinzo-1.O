"""
GET /v1/messages       — list recent messages for a user
GET /v1/conversations/{id} — get a conversation and its messages
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    created_at: str


class ConversationOut(BaseModel):
    id: str
    user_id: str
    mode: str
    started_at: str
    last_active_at: str
    messages: list[MessageOut] = []


@router.get("/v1/messages")
def list_messages(user_id: str, limit: int = 20) -> list[MessageOut]:
    """Return recent messages for a user across all conversations."""
    try:
        from app.memory.db import get_session
        from app.memory.models import Conversation, Message

        with get_session() as session:
            rows = (
                session.query(Message)
                .join(Conversation, Message.conversation_id == Conversation.id)
                .filter(Conversation.user_id == user_id)
                .order_by(Message.created_at.desc())
                .limit(limit)
                .all()
            )
            return [
                MessageOut(
                    id=r.id,
                    role=r.role,
                    content=r.content,
                    created_at=r.created_at.isoformat(),
                )
                for r in rows
            ]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/v1/conversations/{conversation_id}", response_model=ConversationOut)
def get_conversation(conversation_id: str) -> ConversationOut:
    """Return a conversation and all its messages."""
    try:
        from app.memory.db import get_session
        from app.memory.models import Conversation

        with get_session() as session:
            conv = session.get(Conversation, conversation_id)
            if conv is None:
                raise HTTPException(status_code=404, detail="Conversation not found")
            messages = [
                MessageOut(
                    id=m.id,
                    role=m.role,
                    content=m.content,
                    created_at=m.created_at.isoformat(),
                )
                for m in conv.messages
            ]
            return ConversationOut(
                id=conv.id,
                user_id=conv.user_id,
                mode=conv.mode,
                started_at=conv.started_at.isoformat(),
                last_active_at=conv.last_active_at.isoformat(),
                messages=messages,
            )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
