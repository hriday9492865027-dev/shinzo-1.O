"""
Provider-agnostic generation entry point used by the orchestrator / chat route.
Wraps prompt construction + provider invocation behind one function so callers never touch a
concrete provider class directly.
"""
from app.model.loader import get_llm_provider
from app.model.prompts import build_system_prompt


def generate_reply(user_message: str, extra_context: str = "") -> str:
    provider = get_llm_provider()
    system_prompt = build_system_prompt(extra_context)
    return provider.generate(system_prompt=system_prompt, user_message=user_message)
