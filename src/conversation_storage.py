"""Conversation persistence and management."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field

from .models import AppConfig


class ConversationMessage(BaseModel):
    """A single message in the conversation display."""
    author: str  # "使用者" or participant name
    text: str
    timestamp: str  # ISO format


class ParticipantSessionData(BaseModel):
    """Saved session data for one participant."""
    participant_name: str
    model: str
    messages: list[dict[str, str]]  # role + content


class NotesEntry(BaseModel):
    """A single round's notes."""
    round: int
    summary: str
    timestamp: str


class ConversationData(BaseModel):
    """Complete conversation state."""
    participant_sessions: list[ParticipantSessionData] = Field(default_factory=list)
    chat_display: list[ConversationMessage] = Field(default_factory=list)
    notes: list[NotesEntry] = Field(default_factory=list)


class SessionData(BaseModel):
    """Complete saved session."""
    session_id: str
    title: str
    created_at: str
    updated_at: str
    config: AppConfig
    conversation: ConversationData


class ConversationMetadata(BaseModel):
    """Metadata for conversation list."""
    session_id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int


def get_conversations_dir() -> Path:
    """Get the conversations storage directory."""
    base_dir = Path.home() / ".ai_meeting_room"
    conv_dir = base_dir / "conversations"
    conv_dir.mkdir(parents=True, exist_ok=True)
    return conv_dir


def generate_session_id() -> str:
    """Generate a unique session ID."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"meeting_{timestamp}"


def save_conversation(session_data: SessionData) -> None:
    """Save conversation to disk.

    Args:
        session_data: Complete session data to save
    """
    conv_dir = get_conversations_dir()
    file_path = conv_dir / f"{session_data.session_id}.yaml"

    # Update timestamp
    session_data.updated_at = datetime.utcnow().isoformat()

    with open(file_path, 'w', encoding='utf-8') as f:
        yaml.safe_dump(session_data.model_dump(), f, allow_unicode=True)


def load_conversation(session_id: str) -> Optional[SessionData]:
    """Load conversation from disk.

    Args:
        session_id: Session ID to load

    Returns:
        SessionData or None if not found
    """
    conv_dir = get_conversations_dir()
    file_path = conv_dir / f"{session_id}.yaml"

    if not file_path.exists():
        return None

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return SessionData(**data)
    except Exception as e:
        print(f"載入會議時發生錯誤：{e}")
        return None


def list_conversations() -> list[ConversationMetadata]:
    """List all saved conversations.

    Returns:
        List of conversation metadata, sorted by updated_at (newest first)
    """
    conv_dir = get_conversations_dir()
    conversations = []

    for file_path in conv_dir.glob("*.yaml"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            metadata = ConversationMetadata(
                session_id=data["session_id"],
                title=data["title"],
                created_at=data["created_at"],
                updated_at=data["updated_at"],
                message_count=len(data.get("conversation", {}).get("chat_display", []))
            )
            conversations.append(metadata)
        except Exception as e:
            print(f"讀取 {file_path} 時發生錯誤：{e}")
            continue

    # Sort by updated_at, newest first
    conversations.sort(key=lambda x: x.updated_at, reverse=True)
    return conversations


def delete_conversation(session_id: str) -> bool:
    """Delete a conversation.

    Args:
        session_id: Session ID to delete

    Returns:
        True if deleted, False if not found
    """
    conv_dir = get_conversations_dir()
    file_path = conv_dir / f"{session_id}.yaml"

    if file_path.exists():
        file_path.unlink()
        return True
    return False
