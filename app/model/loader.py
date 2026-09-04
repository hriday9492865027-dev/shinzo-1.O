"""
Provider factory. Reads Settings.llm_provider and returns the correct LLMProvider instance.
This is the ONLY place that decides which concrete provider class gets used — see
docs/MODEL_STRATEGY.md "Swap Procedure".
"""
from functools import lru_cache

from app.core.config import get_settings
from app.model.provider_base import LLMProvider, LocalHFProvider, MockProvider


@lru_cache
def get_llm_provider() -> LLMProvider:
    settings = get_settings()

    if settings.llm_provider == "mock":
        return MockProvider()

    if settings.llm_provider == "local_hf":
        return LocalHFProvider(
            model_name=settings.llm_model_name,
            adapter_path=settings.llm_adapter_path,
            max_new_tokens=settings.llm_max_new_tokens,
            temperature=settings.llm_temperature,
        )

    raise ValueError(f"Unknown LLM_PROVIDER: {settings.llm_provider!r}")
