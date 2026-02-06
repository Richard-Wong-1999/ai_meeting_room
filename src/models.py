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
