"""
Guards the compiled system prompt (app/model/prompts.py) against silently drifting from the
boundaries defined in docs/PERSONALITY_SPEC.md §6-7. This is a cheap regression check, not a
substitute for evaluation/naturalness.json (Milestone 7), which will test actual model *outputs*
against the spec rather than just the prompt text.
"""
from app.model.prompts import BASE_PERSONALITY_PROMPT, build_system_prompt


def test_prompt_mentions_hard_boundaries() -> None:
    prompt = BASE_PERSONALITY_PROMPT.lower()
    assert "exclusivity" in prompt
    assert "guilt" in prompt
    assert "professional help" in prompt


def test_prompt_prohibits_robotic_openers() -> None:
    prompt = BASE_PERSONALITY_PROMPT.lower()
    assert "it sounds like" in prompt  # named as a pattern to avoid
    assert "robotic" in prompt or "avoid robotic patterns" in prompt


def test_build_system_prompt_appends_context() -> None:
    result = build_system_prompt(extra_context="User mentioned finals week is stressful.")
    assert "finals week" in result
    assert BASE_PERSONALITY_PROMPT in result


def test_build_system_prompt_without_context_returns_base() -> None:
    assert build_system_prompt() == BASE_PERSONALITY_PROMPT
