"""
Context Builder — assembles the final system prompt from all module outputs.

Takes structured outputs from every upstream module and combines them
into a single coherent system prompt passed to the LLM provider.

The builder follows a strict ordering so the LLM reads signals in priority order:
  1. Base personality prompt
  2. Safety context injection (if MEDIUM risk)
  3. Conversation mode
  4. Emotion signal
  5. Relationship/social context
  6. Social intent instruction
  7. Humor context
  8. Conversation rhythm / length guide
  9. Language adaptation
 10. Shared memory context
 11. RAG context
 12. Spontaneity nudge

Each section is added only when non-empty — the prompt stays as short as possible.
"""
from __future__ import annotations

from app.api.schemas.common import ConversationMode
from app.emotion.signals import EmotionSignal
from app.human.conversation_rhythm import RhythmGuide
from app.human.humor_context import HumorContext
from app.model.prompts import BASE_PERSONALITY_PROMPT
from app.safety.response_routing import RoutingDecision
from app.social.interaction_planner import plan as intent_plan
from app.social.relationship_state import RelationshipState
from app.social.social_intent import SocialIntent


def build_system_prompt(
    routing: RoutingDecision,
    mode: ConversationMode,
    emotion: EmotionSignal,
    relationship: RelationshipState,
    intent: SocialIntent,
    humor: HumorContext,
    rhythm: RhythmGuide,
    language_instruction: str = "",
    memory_context: str = "",
    rag_context: str = "",
    spontaneity_nudge: str = "",
    refinement_instruction: str = "",
) -> str:
    """
    Assemble the full system prompt from all module outputs.
    """
    sections: list[str] = [BASE_PERSONALITY_PROMPT]

    # Safety context injection
    if routing.context_injection:
        sections.append(f"[Safety context] {routing.context_injection}")

    # Conversation mode
    sections.append(f"Current conversation mode: {mode.value}.")

    # Emotion signal
    emotion_str = emotion.to_context_string()
    if emotion_str:
        sections.append(emotion_str)

    # Relationship/social context
    rel_str = relationship.to_context_string()
    if rel_str:
        sections.append(rel_str)

    # Social intent instruction
    sections.append(f"Response intent: {intent_plan(intent)}")

    # Humor context
    sections.append(humor.to_instruction())

    # Rhythm guide
    sections.append(f"Length/pacing: {rhythm.to_instruction()}")

    # Language adaptation
    if language_instruction:
        sections.append(language_instruction)

    # Memory context
    if memory_context:
        sections.append(memory_context)

    # RAG context
    if rag_context:
        sections.append(rag_context)

    # Spontaneity nudge
    if spontaneity_nudge:
        sections.append(f"Style variation: {spontaneity_nudge}")

    # Refinement instruction (retry pass)
    if refinement_instruction:
        sections.append(refinement_instruction)

    return "\n\n".join(s for s in sections if s.strip())
