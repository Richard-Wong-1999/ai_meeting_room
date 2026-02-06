from __future__ import annotations

import asyncio
from collections.abc import Callable, Coroutine
from typing import Any

from .models import AppConfig, ModeratorState, RelevanceResult
from .notes import NotesManager
from .poe_client import PoeClient

# Callback signatures (all are async)
OnChatMessage = Callable[[str, str], Coroutine[Any, Any, None]]   # (author, text)
OnChatChunk = Callable[[str, str], Coroutine[Any, Any, None]]     # (author, chunk)
OnNote = Callable[[str], Coroutine[Any, Any, None]]               # (note text)
OnStatus = Callable[[ModeratorState, str], Coroutine[Any, Any, None]]  # (state, detail)


class Moderator:
    """Core meeting moderator — pure logic, no TUI dependency."""

    def __init__(
        self,
        config: AppConfig,
        poe: PoeClient,
        *,
        on_chat_message: OnChatMessage,
        on_chat_chunk: OnChatChunk,
        on_note: OnNote,
        on_status: OnStatus,
    ) -> None:
        self._config = config
        self._poe = poe
        self._notes = NotesManager(poe)
        self._shutdown = False

        self.on_chat_message = on_chat_message
        self.on_chat_chunk = on_chat_chunk
        self.on_note = on_note
        self.on_status = on_status

    def request_shutdown(self) -> None:
        self._shutdown = True

    def _check_shutdown(self) -> None:
        if self._shutdown:
            raise asyncio.CancelledError("shutdown requested")

    async def handle_user_input(self, text: str) -> None:
        """Called when the user submits a message. Runs the full turn."""
        self._check_shutdown()

        # Broadcast user message to all participants
        for session in self._poe.sessions.values():
            session.add_user_message("User", text)
        self._notes.add_message("User", text)

        # --- Phase 1: initial relevance check ---
        await self.on_status(ModeratorState.CHECKING_RELEVANCE, "Asking all AIs…")
        results = await self._parallel_relevance_check("User", text)
        self._check_shutdown()

        # Log relevance results to notes panel
        for r in results:
            tag = "YES" if r.wants_to_speak else "NO"
            await self.on_note(
                f"[{r.participant_name}] {tag}: {r.summary}"
            )

        speakers = sorted(
            [r for r in results if r.wants_to_speak],
            key=lambda r: r.priority,
        )

        if not speakers:
            await self.on_note("No AI wants to speak. Generating summary…")
            await self._generate_round_summary()
            await self.on_status(ModeratorState.WAITING_FOR_USER, "")
            return

        # --- Phase 2: speaking loop ---
        rounds = 0
        while speakers and rounds < self._config.meeting.max_rounds_per_turn:
            self._check_shutdown()
            current = speakers.pop(0)
            rounds += 1

            session = self._poe.sessions[current.participant_name]
            await self.on_status(
                ModeratorState.AI_SPEAKING,
                f"{current.participant_name} is speaking…",
            )

            # Stream the AI response
            full_text = ""
            try:
                async for chunk in session.get_full_response():
                    self._check_shutdown()
                    full_text += chunk
                    await self.on_chat_chunk(current.participant_name, chunk)
            except asyncio.TimeoutError:
                full_text += "\n(response timed out)"
                await self.on_note(
                    f"[{current.participant_name}] response timed out"
                )
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                full_text += f"\n(error: {exc!s})"
                await self.on_note(
                    f"[{current.participant_name}] error: {exc!s}"
                )

            # Finalize message
            await self.on_chat_message(current.participant_name, full_text)
            session.add_assistant_message(full_text)
            self._notes.add_message(current.participant_name, full_text)

            # Broadcast to other participants
            for name, other in self._poe.sessions.items():
                if name != current.participant_name:
                    other.add_other_ai_message(
                        current.participant_name, full_text
                    )

            # --- Phase 3: recheck remaining candidates ---
            remaining_names = {s.participant_name for s in speakers}
            if not remaining_names:
                # Also check those who previously said NO
                all_names = set(self._poe.sessions.keys())
                already_spoke = {current.participant_name}
                remaining_names = all_names - already_spoke

            if remaining_names and rounds < self._config.meeting.max_rounds_per_turn:
                self._check_shutdown()
                await self.on_status(
                    ModeratorState.RECHECKING_RELEVANCE,
                    "Rechecking remaining AIs…",
                )
                recheck_results = await self._parallel_recheck(
                    remaining_names,
                    current.participant_name,
                    full_text,
                )

                for r in recheck_results:
                    tag = "YES" if r.wants_to_speak else "NO"
                    await self.on_note(
                        f"  ↳ [{r.participant_name}] {tag}: {r.summary}"
                    )

                speakers = sorted(
                    [r for r in recheck_results if r.wants_to_speak],
                    key=lambda r: r.priority,
                )

        # --- Phase 4: generate round summary ---
        await self._generate_round_summary()
        await self.on_status(ModeratorState.WAITING_FOR_USER, "")

    async def _parallel_relevance_check(
        self, author: str, text: str
    ) -> list[RelevanceResult]:
        tasks = [
            session.check_relevance(author, text)
            for session in self._poe.sessions.values()
        ]
        return list(await asyncio.gather(*tasks, return_exceptions=False))

    async def _parallel_recheck(
        self,
        names: set[str],
        speaker: str,
        message: str,
    ) -> list[RelevanceResult]:
        tasks = [
            self._poe.sessions[name].recheck_relevance(speaker, message)
            for name in names
            if name in self._poe.sessions
        ]
        return list(await asyncio.gather(*tasks, return_exceptions=False))

    async def _generate_round_summary(self) -> None:
        await self.on_status(ModeratorState.GENERATING_NOTES, "Generating summary…")
        summary = await self._notes.generate_summary()
        await self.on_note(f"\n--- Round Summary ---\n{summary}\n")
        self._notes.clear_round()
