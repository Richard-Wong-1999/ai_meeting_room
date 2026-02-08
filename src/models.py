from __future__ import annotations

import enum
from pydantic import BaseModel, Field


class ParticipantConfig(BaseModel):
    name: str
    role: str
    personality: str
    description: str
    model: str
    priority: int = Field(ge=1)


class PoeConfig(BaseModel):
    base_url: str = "https://api.poe.com/v1"


class NotesSummarizerConfig(BaseModel):
    model: str = "GPT-4o-Mini"


class BasicMeetingConfig(BaseModel):
    """Basic meeting configuration for Phase 1 setup."""
    title: str
    max_rounds_per_turn: int = Field(default=10, ge=1, le=50)
    relevance_timeout_seconds: int = Field(default=20, ge=5, le=120)
    response_timeout_seconds: int = Field(default=90, ge=10, le=300)


class ModelSettings(BaseModel):
    """Model configuration settings."""
    planning_assistant_model: str = "gemini-3-pro"  # Model for participant design
    notes_model: str = "gpt-4o"  # Model for meeting notes
    available_models: list[str] = []  # Will be populated with defaults on first load


class UserPreferences(BaseModel):
    """User preferences saved to disk."""
    basic_config: BasicMeetingConfig
    model_settings: ModelSettings = ModelSettings()
    # Deprecated field for backward compatibility
    custom_models: list[str] = []
    saved_at: str  # ISO timestamp


class MeetingSettings(BaseModel):
    title: str = "AI Meeting"
    max_rounds_per_turn: int = Field(default=10, ge=1)
    relevance_timeout_seconds: int = Field(default=15, ge=1)
    response_timeout_seconds: int = Field(default=60, ge=1)


class AppConfig(BaseModel):
    meeting: MeetingSettings = MeetingSettings()
    poe: PoeConfig = PoeConfig()
    participants: list[ParticipantConfig]
    notes_summarizer: NotesSummarizerConfig = NotesSummarizerConfig()


class RelevanceResult(BaseModel):
    participant_name: str
    wants_to_speak: bool
    summary: str = ""
    priority: int = 0


class ModeratorState(enum.Enum):
    WAITING_FOR_USER = "waiting_for_user"
    CHECKING_RELEVANCE = "checking_relevance"
    AI_SPEAKING = "ai_speaking"
    RECHECKING_RELEVANCE = "rechecking_relevance"
    GENERATING_NOTES = "generating_notes"
    SHUTTING_DOWN = "shutting_down"
