"""
Shinzo Orchestrator — the central pipeline that wires all modules together.

Pipeline (in order):
  1. Safety: rules → classifier → risk scoring → routing decision
  2. Emotion: classify message → EmotionSignal
  3. Memory: retrieve relevant memories (read path)
  4. RAG: retrieve relevant knowledge context
  5. Social: relationship state → conversation dynamics → intent → planner
  6. Human: humor context → rhythm guide → silence logic → shared context → spontaneity
  7. Language: detect language → build style profile → adaptation instruction
  8. Decision Router: determine ConversationMode
  9. Context Builder: assemble full system prompt
 10. LLM: generate reply
 11. Authenticity Filter: check reply → optional 1-retry refinement
 12. Memory: store new memories from user message (write path)

Returns (reply: str, risk_tier: RiskTier, mode: ConversationMode)

Design contract:
  - The orchestrator is the ONLY place that imports and calls all modules.
  - Routes and other modules import from orchestrator, not from individual modules.
  - Each module is independently testable without the orchestrator.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from app.api.schemas.common import ConversationMode, RiskTier
from app.core.context_builder import build_system_prompt
from app.core.decision_router import determine_mode
from app.emotion.signals import EmotionSignal, build_signal
from app.human.authenticity_filter import check as auth_check
from app.human.conversation_rhythm import guide as rhythm_guide
from app.human.humor_context import evaluate as humor_evaluate
from app.human.shared_context import build_context_note
from app.human.silence_logic import evaluate as silence_evaluate
from app.human.spontaneity import get_variation_nudge
from app.language.adaptation import build_adaptation_instruction
from app.language.style_profile import build_profile as build_lang_profile
from app.memory.retrieval import format_memories_for_context, get_relevant_memories
from app.memory.store import save_turn_memories
from app.model.loader import get_llm_provider
from app.rag.retriever import retrieve_context
from app.safety.classifier import classify as safety_classify
from app.safety.response_routing import route as safety_route
from app.safety.risk_scoring import score as safety_score
from app.safety.rules import evaluate as rule_evaluate
from app.social.conversation_dynamics import analyze as analyze_dynamics
from app.social.relationship_state import build_state as build_rel_state
from app.social.social_intent import select as select_intent

logger = logging.getLogger(__name__)

# Max one authenticity retry per turn
MAX_AUTHENTICITY_RETRIES = 1


@dataclass
class OrchestratorResult:
    reply: str
    risk_tier: RiskTier
    mode: ConversationMode
    emotion: EmotionSignal | None = None


def process_message(
    user_id: str,
    conversation_id: str,
    user_message: str,
    recent_messages: list[dict] | None = None,
    message_count: int = 0,
    last_active_at=None,
    recent_shinzo_replies: list[str] | None = None,
) -> OrchestratorResult:
    """
    Full pipeline: user_message in → (reply, risk_tier, mode) out.

    Args:
        user_id:               stable user identifier
        conversation_id:       current conversation ID
        user_message:          the raw user input
        recent_messages:       last N turns as [{"role": ..., "content": ...}]
        message_count:         total messages in this relationship
        last_active_at:        datetime of last message (for relationship state)
        recent_shinzo_replies: last 3–5 Shinzo replies (for authenticity filter)
    """
    recent_messages = recent_messages or []
    recent_shinzo_replies = recent_shinzo_replies or []

    # ── 1. Safety ─────────────────────────────────────────────────────────────
    rule_result = rule_evaluate(user_message)
    clf_result = safety_classify(user_message)
    risk_tier = safety_score(rule_result, clf_result)
    routing = safety_route(risk_tier)

    if routing.short_circuit:
        logger.info("Safety short-circuit for user %s (tier=HIGH)", user_id)
        return OrchestratorResult(
            reply=routing.fixed_reply,
            risk_tier=risk_tier,
            mode=ConversationMode.CRISIS,
        )

    # ── 2. Emotion ─────────────────────────────────────────────────────────────
    emotion = build_signal(user_message)

    # ── 3. Memory (read) ───────────────────────────────────────────────────────
    memories = get_relevant_memories(user_id=user_id, query=user_message)
    memory_context = format_memories_for_context(memories)
    has_shared_memory = bool(memories)

    # ── 4. RAG ─────────────────────────────────────────────────────────────────
    rag_context = retrieve_context(query=user_message)

    # ── 5. Social ──────────────────────────────────────────────────────────────
    dynamics = analyze_dynamics(recent_messages)
    memory_count = len(memories)
    relationship = build_rel_state(
        message_count=message_count,
        emotion_is_distressed=emotion.is_distressed,
        last_active_at=last_active_at,
        memory_count=memory_count,
    )
    relationship.energy = dynamics.energy  # overwrite with real dynamics energy

    intent = select_intent(
        user_message=user_message,
        emotion=emotion,
        dynamics=dynamics,
        relationship=relationship,
        has_shared_memory=has_shared_memory,
    )

    # ── 6. Human Essence ──────────────────────────────────────────────────────
    silence = silence_evaluate(user_message)
    humor = humor_evaluate(emotion=emotion, dynamics=dynamics, relationship=relationship)
    rhythm = rhythm_guide(intent=intent, dynamics=dynamics)
    if silence.should_be_brief and rhythm.target_length not in ("very_short",):
        from app.human.conversation_rhythm import RhythmGuide
        rhythm = RhythmGuide(target_length="very_short", pacing_note="Match their low energy.")
    shared_ctx = build_context_note(memories=memories, dynamics_depth=dynamics.depth)
    spontaneity = get_variation_nudge()

    # ── 7. Language ────────────────────────────────────────────────────────────
    user_texts = [m["content"] for m in recent_messages if m.get("role") == "user"]
    lang_profile = build_lang_profile(user_texts[-10:])
    lang_instruction = build_adaptation_instruction(lang_profile)

    # ── 8. Decision Router ────────────────────────────────────────────────────
    mode = determine_mode(risk_tier, emotion, intent, rule_result)

    # ── 9. Context Builder ────────────────────────────────────────────────────
    system_prompt = build_system_prompt(
        routing=routing,
        mode=mode,
        emotion=emotion,
        relationship=relationship,
        intent=intent,
        humor=humor,
        rhythm=rhythm,
        language_instruction=lang_instruction,
        memory_context=shared_ctx or memory_context,
        rag_context=rag_context,
        spontaneity_nudge=spontaneity,
    )

    # ── 10. LLM Generation ────────────────────────────────────────────────────
    provider = get_llm_provider()
    reply = provider.generate(system_prompt=system_prompt, user_message=user_message)

    # ── 11. Authenticity Filter (with 1 retry) ────────────────────────────────
    auth_result = auth_check(
        reply=reply,
        target_length=rhythm.target_length,
        recent_shinzo_replies=recent_shinzo_replies,
    )
    if not auth_result.passed and MAX_AUTHENTICITY_RETRIES > 0:
        refinement = auth_result.refinement_instruction()
        retry_prompt = build_system_prompt(
            routing=routing,
            mode=mode,
            emotion=emotion,
            relationship=relationship,
            intent=intent,
            humor=humor,
            rhythm=rhythm,
            language_instruction=lang_instruction,
            memory_context=shared_ctx or memory_context,
            rag_context=rag_context,
            spontaneity_nudge=spontaneity,
            refinement_instruction=refinement,
        )
        reply = provider.generate(system_prompt=retry_prompt, user_message=user_message)
        logger.debug("Authenticity filter triggered retry for user %s", user_id)

    # ── 12. Memory (write) ────────────────────────────────────────────────────
    try:
        save_turn_memories(
            user_id=user_id,
            user_message=user_message,
            conversation_id=conversation_id,
        )
    except Exception as exc:
        logger.error("Memory write failed for user %s: %s", user_id, exc)

    return OrchestratorResult(reply=reply, risk_tier=risk_tier, mode=mode, emotion=emotion)
