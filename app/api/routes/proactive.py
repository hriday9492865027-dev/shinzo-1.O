"""
POST /v1/proactive/trigger — manually trigger proactive message generation.

Used for testing/admin and future scheduler integration.
In production the scheduler (app/proactive/scheduler.py) calls this logic
on its own cadence.
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.proactive.decision_engine import evaluate as evaluate_decision
from app.proactive.frequency_guard import get_recent_proactive_count, is_pause_mode_active
from app.proactive.message_planner import plan as plan_message

router = APIRouter()


class ProactiveTriggerRequest(BaseModel):
    user_id: str
    hook: str = "check_in"   # e.g. "check_in", "follow_up_interview"
    relationship_context: str = ""


class ProactiveTriggerResponse(BaseModel):
    initiated: bool
    message: str = ""
    reason: str = ""


@router.post("/v1/proactive/trigger", response_model=ProactiveTriggerResponse)
def trigger_proactive(payload: ProactiveTriggerRequest) -> ProactiveTriggerResponse:
    pause_mode = is_pause_mode_active(payload.user_id)
    recent_count = get_recent_proactive_count(payload.user_id)

    decision = evaluate_decision(
        last_message_at=None,  # full implementation reads from DB
        recent_proactive_count=recent_count,
        pause_mode_active=pause_mode,
        follow_up_hook=payload.hook,
        message_count=10,     # stub — full implementation reads from DB
    )

    if not decision.should_initiate:
        return ProactiveTriggerResponse(initiated=False, reason=decision.reason)

    message = plan_message(hook=decision.hook, relationship_context=payload.relationship_context)
    return ProactiveTriggerResponse(initiated=True, message=message, reason=decision.reason)
