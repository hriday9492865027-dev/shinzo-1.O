"""
Tests for social intelligence (intent selection, dynamics, relationship state).
"""
import os

os.environ.setdefault("LLM_PROVIDER", "mock")


def test_intent_advise_on_advice_request():
    from app.emotion.signals import EmotionSignal
    from app.social.conversation_dynamics import ConversationDynamics
    from app.social.relationship_state import RelationshipState
    from app.social.social_intent import SocialIntent, select

    emotion = EmotionSignal(primary_emotion="neutral", confidence=0.8, is_significant=False, is_distressed=False)
    dynamics = ConversationDynamics(energy=0.5, depth=0.3, user_verbosity=0.5, pace="medium")
    rel = RelationshipState(familiarity=0.3, trust=0.3, energy=0.5, recency=0.8, message_count=10)

    intent = select("what should I do about my job?", emotion, dynamics, rel)
    assert intent == SocialIntent.ADVISE


def test_intent_listen_on_distress():
    from app.emotion.signals import EmotionSignal
    from app.social.conversation_dynamics import ConversationDynamics
    from app.social.relationship_state import RelationshipState
    from app.social.social_intent import SocialIntent, select

    emotion = EmotionSignal(primary_emotion="sadness", confidence=0.85, is_significant=True, is_distressed=True)
    dynamics = ConversationDynamics(energy=0.2, depth=0.7, user_verbosity=0.3, pace="slow")
    rel = RelationshipState(familiarity=0.4, trust=0.5, energy=0.2, recency=0.9, message_count=20)

    intent = select("I feel so alone and hopeless", emotion, dynamics, rel)
    assert intent == SocialIntent.LISTEN


def test_intent_give_space_on_short_message():
    from app.emotion.signals import EmotionSignal
    from app.social.conversation_dynamics import ConversationDynamics
    from app.social.relationship_state import RelationshipState
    from app.social.social_intent import SocialIntent, select

    emotion = EmotionSignal(primary_emotion="neutral", confidence=0.6, is_significant=False, is_distressed=False)
    dynamics = ConversationDynamics(energy=0.4, depth=0.2, user_verbosity=0.2, pace="slow")
    rel = RelationshipState(familiarity=0.2, trust=0.2, energy=0.4, recency=0.9, message_count=5)

    intent = select("ok", emotion, dynamics, rel)
    assert intent == SocialIntent.GIVE_SPACE


def test_dynamics_analysis_empty():
    from app.social.conversation_dynamics import analyze

    dynamics = analyze([])
    assert 0.0 <= dynamics.energy <= 1.0
    assert dynamics.pace == "medium"


def test_interaction_planner_returns_string():
    from app.social.interaction_planner import plan
    from app.social.social_intent import SocialIntent

    for intent in SocialIntent:
        instruction = plan(intent)
        assert isinstance(instruction, str)
        assert len(instruction) > 0


def test_relationship_state_build():
    from datetime import UTC, datetime, timedelta

    from app.social.relationship_state import build_state

    last_active = datetime.now(UTC) - timedelta(hours=2)
    state = build_state(
        message_count=50,
        emotion_is_distressed=False,
        last_active_at=last_active,
        memory_count=10,
    )
    assert 0.0 <= state.familiarity <= 1.0
    assert state.recency > 0.8  # recent — should be high
