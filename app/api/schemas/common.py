"""
Shared Pydantic types used across multiple schema/route modules
(so IDs/timestamps/enums are defined once, not re-declared per route).
"""
from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, Field


def utcnow() -> datetime:
    return datetime.now(UTC)


class ConversationMode(str, Enum):
    CASUAL = "casual"
    FUN = "fun"
    VENTING = "venting"
    ADVICE = "advice"
    EMOTIONAL = "emotional"
    REFLECTIVE = "reflective"
    LONELY = "lonely"
    CRISIS = "crisis"
    CELEBRATION = "celebration"
    SILENT = "silent"


class RiskTier(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TimestampedModel(BaseModel):
    created_at: datetime = Field(default_factory=utcnow)
