"""
Request/response contracts for POST /v1/chat.
Kept intentionally minimal for Milestone 2 (basic chat) — will grow as memory/social/emotion
outputs need to be optionally surfaced to the client (e.g. for debugging in dev mode).
"""
from pydantic import BaseModel, Field

from app.api.schemas.common import RiskTier


class ChatRequest(BaseModel):
    user_id: str = Field(..., description="Stable identifier for the user")
    conversation_id: str = Field(..., description="Identifier for the ongoing conversation")
    message: str = Field(..., min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    reply: str
    conversation_id: str
    risk_tier: RiskTier = RiskTier.LOW
