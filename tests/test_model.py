"""LLM provider interface tests."""
from app.model.loader import get_llm_provider
from app.model.provider_base import MockProvider


def test_default_provider_is_mock() -> None:
    provider = get_llm_provider()
    assert isinstance(provider, MockProvider)


def test_mock_provider_echoes_message() -> None:
    provider = MockProvider()
    reply = provider.generate(system_prompt="be nice", user_message="hello there")
    assert "hello there" in reply
