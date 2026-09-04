"""
POST /v1/chat — reactive conversation endpoint.

Milestone 15: routes through the full Shinzo orchestrator pipeline:
  safety → emotion → memory (read) → RAG → social → human essence →
  language → context builder → LLM → authenticity filter → memory (write)
"""
from fastapi import APIRouter

from app.api.schemas.chat import ChatRequest, ChatResponse
from app.core.orchestrator import process_message

router = APIRouter()


@router.post("/v1/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    result = process_message(
        user_id=payload.user_id,
        conversation_id=payload.conversation_id,
        user_message=payload.message,
    )
    return ChatResponse(
        reply=result.reply,
        conversation_id=payload.conversation_id,
        risk_tier=result.risk_tier,
    )
