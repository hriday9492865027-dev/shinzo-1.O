"""
Pydantic schema for a single training record, shared by every pipeline stage so validation is
consistent from raw input through JSONL export.

Categories are the 11 recommended in docs/ (see roadmap "Recommended custom categories").
"""
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class DatasetCategory(str, Enum):
    NATURAL_CONVERSATION = "natural_conversation"
    RELATIONSHIP_STRUGGLES = "relationship_struggles"
    BREAKUPS_RECOVERY = "breakups_recovery"
    LONELINESS = "loneliness"
    EMOTIONAL_SUPPORT = "emotional_support"
    HUMOR_PLAYFUL = "humor_playful"
    SOCIAL_CONTEXT = "social_context"
    SILENCE_BREVITY = "silence_brevity"
    SHARED_REFERENCE_CALLBACKS = "shared_reference_callbacks"
    PROACTIVE_MESSAGE = "proactive_message"
    SAFETY_BOUNDARY = "safety_boundary"


class TrainingRecord(BaseModel):
    """One (user_message, shinzo_reply) pair plus metadata used by the fine-tuning pipeline."""

    id: str = Field(..., description="Stable unique id, e.g. 'natural_conversation_0007'")
    category: DatasetCategory
    user_message: str = Field(..., min_length=1, max_length=2000)
    shinzo_reply: str = Field(..., min_length=1, max_length=2000)
    notes: str = Field(default="", description="Why this example is a good exemplar (optional)")

    @field_validator("user_message", "shinzo_reply")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        return v.strip()
