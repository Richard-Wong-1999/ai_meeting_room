from __future__ import annotations

from .prompts import build_notes_prompt

# Avoid circular import — we only need the client at runtime.
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .poe_client import PoeClient


class NotesManager:
    """Collects messages for the current round and generates summaries."""

    def __init__(self, poe: PoeClient) -> None:
        self._poe = poe
        self._round_messages: list[tuple[str, str]] = []  # (author, text)

    def add_message(self, author: str, text: str) -> None:
        self._round_messages.append((author, text))

    def clear_round(self) -> None:
        self._round_messages.clear()

    def _build_conversation_block(self) -> str:
        lines: list[str] = []
        for author, text in self._round_messages:
            lines.append(f"[{author}]: {text}")
        return "\n\n".join(lines)

    async def generate_summary(self) -> str:
        if not self._round_messages:
            return "（本輪無訊息）"
        block = self._build_conversation_block()
        prompt = build_notes_prompt(block)
        return await self._poe.get_notes_summary(prompt)
