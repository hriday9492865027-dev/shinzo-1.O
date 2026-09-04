"""
Centralized settings loader.
Reads environment variables (see .env.example) into a typed, validated Settings object.
Every other module should import `get_settings()` rather than reading os.environ directly,
so config has one source of truth and is easy to override in tests.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    shinzo_env: str = "development"

    # Database
    database_url: str = "sqlite:///./shinzo.db"

    # LLM provider
    llm_provider: str = "mock"  # "mock" | "local_hf"
    llm_model_name: str = "Qwen/Qwen2.5-1.5B-Instruct"
    llm_adapter_path: str = ""
    llm_max_new_tokens: int = 256
    llm_temperature: float = 0.8

    # Emotion
    emotion_model_name: str = "j-hartmann/emotion-english-distilroberta-base"

    # Security
    api_key_hash_algo: str = "argon2"
    rate_limit_per_minute: int = 60

    # Proactive
    proactive_enabled: bool = True
    quiet_hours_start: str = "22:00"
    quiet_hours_end: str = "08:00"

    # Logging
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — safe to call this everywhere, it only loads once per process."""
    return Settings()
