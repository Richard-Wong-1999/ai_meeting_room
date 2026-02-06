from __future__ import annotations

import asyncio

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Input, Static, TextArea

from .models import AppConfig, ModeratorState
from .moderator import Moderator
from .poe_client import PoeClient

class MeetingApp(App):
    """Multi-AI Meeting Room TUI."""

    TITLE = "AI Meeting Room"
    CSS_PATH = "app.tcss"
    BINDINGS = [
        Binding("ctrl+q", "request_quit", "Quit", show=True),
        Binding("ctrl+c", "request_quit", "Quit", show=False),
    ]

    def __init__(self, config: AppConfig, api_key: str) -> None:
        super().__init__()
        self._config = config
        self._api_key = api_key
        self._poe: PoeClient | None = None
        self._moderator: Moderator | None = None
        self._streaming_buffer: str = ""
        self._streaming_name: str | None = None
        # Build name→label lookup for display
        self._labels: dict[str, str] = {
            p.name: f"{p.name}（{p.role}, {p.model}）"
            for p in config.participants
        }

    def compose(self) -> ComposeResult:
        yield TextArea(
            "",
            id="chat-panel",
            read_only=True,
            show_line_numbers=False,
            soft_wrap=True,
        )
        yield TextArea(
            "會議記錄將顯示在此…",
            id="notes-panel",
            read_only=True,
            show_line_numbers=False,
            soft_wrap=True,
        )
        yield Static("Ready — type a message to begin", id="status-bar")
        yield Input(
            placeholder="Type your message and press Enter…",
            id="input-box",
        )

    def on_mount(self) -> None:
        chat = self.query_one("#chat-panel", TextArea)
        notes = self.query_one("#notes-panel", TextArea)
        chat.border_title = f"Chat — {self._config.meeting.title}"
        notes.border_title = "Meeting Notes"

        self._poe = PoeClient(self._api_key, self._config)
        self._moderator = Moderator(
            config=self._config,
            poe=self._poe,
            on_chat_message=self._on_chat_message,
            on_chat_chunk=self._on_chat_chunk,
            on_note=self._on_note,
            on_status=self._on_status,
        )

        participants = ", ".join(
            f"{p.name}（{p.role}, {p.model}）" for p in self._config.participants
        )
        chat.text = f"參與者：{participants}\n"

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        if not text:
            return

        input_box = self.query_one("#input-box", Input)
        input_box.value = ""
        input_box.disabled = True

        chat = self.query_one("#chat-panel", TextArea)
        chat.text += f"\n【使用者】 {text}\n"

        self.run_worker(
            self._run_turn(text),
            name="moderator_turn",
            exclusive=True,
        )

    async def _run_turn(self, text: str) -> None:
        try:
            assert self._moderator is not None
            await self._moderator.handle_user_input(text)
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            notes = self.query_one("#notes-panel", TextArea)
            notes.text += f"\nERROR: {exc!s}"
        finally:
            input_box = self.query_one("#input-box", Input)
            input_box.disabled = False
            input_box.focus()

    # ---- Moderator callbacks ----

    async def _on_chat_message(self, author: str, text: str) -> None:
        """Called when an AI finishes speaking — write the complete message."""
        chat = self.query_one("#chat-panel", TextArea)
        if author == "主持人":
            chat.text += f"\n【主持人】 {text}\n"
        else:
            label = self._labels.get(author, author)
            chat.text += f"\n【{label}】\n{text}\n"
        self._streaming_name = None
        self._streaming_buffer = ""

    async def _on_chat_chunk(self, author: str, chunk: str) -> None:
        """Called for each streaming token. We accumulate and show progress
        in the status bar since RichLog doesn't support partial writes."""
        if self._streaming_name != author:
            self._streaming_name = author
            self._streaming_buffer = ""
        self._streaming_buffer += chunk
        label = self._labels.get(author, author)
        preview = self._streaming_buffer[:80].replace("\n", " ")
        bar = self.query_one("#status-bar", Static)
        bar.update(f"{label} speaking: {preview}…")

    async def _on_note(self, text: str) -> None:
        notes = self.query_one("#notes-panel", TextArea)
        if notes.text == "會議記錄將顯示在此…":
            notes.text = text
        else:
            notes.text += "\n" + text

    async def _on_status(self, state: ModeratorState, detail: str) -> None:
        bar = self.query_one("#status-bar", Static)
        if state == ModeratorState.WAITING_FOR_USER:
            bar.update("Ready — type a message to continue")
        else:
            label = state.value.replace("_", " ").title()
            bar.update(f"{label}: {detail}" if detail else label)

    # ---- Shutdown ----

    async def action_request_quit(self) -> None:
        if self._moderator:
            self._moderator.request_shutdown()
        if self._poe:
            await self._poe.close()
        self.exit()
