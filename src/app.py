from __future__ import annotations

import asyncio
from datetime import datetime

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Input, Static, TextArea

from .conversation_storage import (
    ConversationMessage,
    NotesEntry,
    ParticipantSessionData,
    SessionData,
    save_conversation,
)
from .models import AppConfig, ModeratorState
from .moderator import Moderator
from .poe_client import PoeClient
from .utils import build_participant_labels

class MeetingApp(App):
    """Multi-AI Meeting Room TUI."""

    TITLE = "AI 會議室"
    CSS_PATH = "app.tcss"
    BINDINGS = [
        Binding("ctrl+s", "save_conversation", "儲存", show=True),
        Binding("ctrl+q", "request_quit", "離開", show=True),
        Binding("ctrl+c", "request_quit", "離開", show=False),
    ]

    def __init__(
        self,
        config: AppConfig,
        api_key: str,
        session_id: str,
        session_data: SessionData
    ) -> None:
        super().__init__()
        self._config = config
        self._api_key = api_key
        self._session_id = session_id
        self._session_data = session_data
        self._poe: PoeClient | None = None
        self._moderator: Moderator | None = None
        self._streaming_buffer: str = ""
        self._streaming_name: str | None = None
        self._current_round: int = 0
        # Build name→label lookup for display
        self._labels: dict[str, str] = build_participant_labels(config.participants)

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
        yield Static("就緒 — 輸入訊息開始討論", id="status-bar")
        yield Input(
            placeholder="輸入訊息後按 Enter 發送…",
            id="input-box",
        )

    def on_mount(self) -> None:
        chat = self.query_one("#chat-panel", TextArea)
        notes = self.query_one("#notes-panel", TextArea)
        chat.border_title = f"Chat — {self._config.meeting.title}"
        notes.border_title = "會議記錄"

        self._poe = PoeClient(self._api_key, self._config)
        self._moderator = Moderator(
            config=self._config,
            poe=self._poe,
            on_chat_message=self._on_chat_message,
            on_chat_chunk=self._on_chat_chunk,
            on_note=self._on_note,
            on_status=self._on_status,
        )

        # Check if restoring conversation
        if self._session_data.conversation.chat_display:
            self._restore_conversation()
        else:
            # Show welcome message for new meeting
            welcome = (
                "歡迎來到 AI 會議室！\n\n"
                "提示：\n"
                "  • 在下方輸入框輸入訊息參與討論\n"
                "  • 按 Ctrl+S 隨時儲存會議記錄\n"
                "  • 按 Ctrl+Q 退出會議室（自動儲存）\n\n"
                "────────────────────────────────────────────────────\n\n"
            )
            participants = ", ".join(
                f"{p.name}（{p.role}, {p.model}）" for p in self._config.participants
            )
            chat.text = welcome + f"參與者：{participants}\n"

    def _restore_conversation(self) -> None:
        """Restore conversation from saved session."""
        chat = self.query_one("#chat-panel", TextArea)
        notes = self.query_one("#notes-panel", TextArea)

        # Show welcome message
        welcome = (
            "歡迎來到 AI 會議室！\n\n"
            "提示：\n"
            "  • 在下方輸入框輸入訊息參與討論\n"
            "  • 按 Ctrl+S 隨時儲存會議記錄\n"
            "  • 按 Ctrl+Q 退出會議室（自動儲存）\n\n"
            "────────────────────────────────────────────────────\n\n"
        )

        # Show participants
        participants = ", ".join(
            f"{p.name}（{p.role}, {p.model}）" for p in self._config.participants
        )
        chat.text = welcome + f"參與者：{participants}\n\n"
        chat.text += "── 繼續先前的會議 ──\n"

        # Restore chat messages
        for msg in self._session_data.conversation.chat_display:
            if msg.author == "使用者":
                chat.text += f"\n【使用者】 {msg.text}\n"
            elif msg.author == "主持人":
                chat.text += f"\n【主持人】 {msg.text}\n"
            else:
                chat.text += f"\n【{msg.author}】\n{msg.text}\n"

        # Restore notes
        if self._session_data.conversation.notes:
            notes.text = ""
            for note in self._session_data.conversation.notes:
                notes.text += f"\n=== 第 {note.round} 輪 ===\n{note.summary}\n"
            self._current_round = self._session_data.conversation.notes[-1].round

        # TODO: Restore participant session messages to moderator if needed

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        if not text:
            return

        input_box = self.query_one("#input-box", Input)
        input_box.value = ""
        input_box.disabled = True

        chat = self.query_one("#chat-panel", TextArea)
        chat.text += f"\n【使用者】 {text}\n"

        # Save user message to session data
        self._session_data.conversation.chat_display.append(
            ConversationMessage(
                author="使用者",
                text=text,
                timestamp=datetime.utcnow().isoformat()
            )
        )

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
            notes.text += f"\n錯誤：{exc!s}"
        finally:
            input_box = self.query_one("#input-box", Input)
            input_box.disabled = False
            input_box.focus()

    # ---- Moderator callbacks ----

    async def _on_chat_message(self, author: str, text: str) -> None:
        """Called when an AI finishes speaking — write the complete message."""
        chat = self.query_one("#chat-panel", TextArea)
        if author == "主持人":
            label = "主持人"
            chat.text += f"\n【主持人】 {text}\n"
        else:
            label = self._labels.get(author, author)
            chat.text += f"\n【{label}】\n{text}\n"

        # Save to session data
        self._session_data.conversation.chat_display.append(
            ConversationMessage(
                author=label,
                text=text,
                timestamp=datetime.utcnow().isoformat()
            )
        )

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
        bar.update(f"{label} 發言中：{preview}…")

    async def _on_note(self, text: str) -> None:
        notes = self.query_one("#notes-panel", TextArea)
        if notes.text == "會議記錄將顯示在此…":
            notes.text = text
        else:
            notes.text += "\n" + text

        # Save to session data
        self._current_round += 1
        self._session_data.conversation.notes.append(
            NotesEntry(
                round=self._current_round,
                summary=text,
                timestamp=datetime.utcnow().isoformat()
            )
        )

    async def _on_status(self, state: ModeratorState, detail: str) -> None:
        bar = self.query_one("#status-bar", Static)
        if state == ModeratorState.WAITING_FOR_USER:
            bar.update("就緒 — 輸入訊息繼續討論")
        else:
            label = state.value.replace("_", " ").title()
            bar.update(f"{label}: {detail}" if detail else label)

    # ---- Save/Shutdown ----

    def action_save_conversation(self) -> None:
        """Save current conversation to disk."""
        try:
            # Update participant session data
            self._update_session_data()

            # Save to disk
            save_conversation(self._session_data)
            self.notify("✓ 會議已儲存", severity="information", timeout=2)
        except Exception as e:
            self.notify(f"儲存失敗：{e}", severity="error")

    def _update_session_data(self) -> None:
        """Update session data with current moderator state."""
        if not self._poe:
            return

        # Update participant sessions
        participant_sessions = []
        for name, session in self._poe.sessions.items():
            participant_sessions.append(ParticipantSessionData(
                participant_name=name,
                model=session.model,
                messages=session.messages
            ))

        self._session_data.conversation.participant_sessions = participant_sessions

    async def action_request_quit(self) -> None:
        """Handle quit request - auto-save before exit."""
        # Auto-save on quit
        if self._session_data.conversation.chat_display:
            try:
                self._update_session_data()
                save_conversation(self._session_data)
            except Exception:
                pass  # Silent fail on auto-save

        if self._moderator:
            self._moderator.request_shutdown()
        if self._poe:
            await self._poe.close()
        self.exit()
