from __future__ import annotations

import asyncio
import re
from collections.abc import AsyncIterator

from openai import AsyncOpenAI

from .models import AppConfig, ParticipantConfig, RelevanceResult
from .prompts import (
    build_relevance_check_prompt,
    build_recheck_prompt,
    build_system_prompt,
)

_DECISION_RE = re.compile(r"DECISION:\s*(YES|NO)", re.IGNORECASE)
_SUMMARY_RE = re.compile(r"SUMMARY:\s*(.+)", re.IGNORECASE)


class ParticipantSession:
    """Manages conversation history and API calls for one participant."""

    def __init__(
        self,
        client: AsyncOpenAI,
        participant: ParticipantConfig,
        system_prompt: str,
        relevance_timeout: int,
        response_timeout: int,
    ) -> None:
        self.client = client
        self.participant = participant
        self.relevance_timeout = relevance_timeout
        self.response_timeout = response_timeout
        self.messages: list[dict[str, str]] = [
            {"role": "system", "content": system_prompt},
        ]

    @property
    def name(self) -> str:
        return self.participant.name

    @property
    def model(self) -> str:
        return self.participant.model

    @property
    def priority(self) -> int:
        return self.participant.priority

    def add_user_message(self, author: str, text: str) -> None:
        self.messages.append(
            {"role": "user", "content": f"[{author}]: {text}"}
        )

    def add_assistant_message(self, text: str) -> None:
        self.messages.append({"role": "assistant", "content": text})

    def add_other_ai_message(self, speaker: str, text: str) -> None:
        self.messages.append(
            {"role": "user", "content": f"[{speaker}]: {text}"}
        )

    async def check_relevance(
        self, author: str, text: str
    ) -> RelevanceResult:
        prompt = build_relevance_check_prompt(self.name, author, text)
        return await self._do_relevance_call(prompt)

    async def recheck_relevance(
        self, speaker: str, message: str
    ) -> RelevanceResult:
        prompt = build_recheck_prompt(self.name, speaker, message)
        return await self._do_relevance_call(prompt)

    async def _do_relevance_call(self, prompt: str) -> RelevanceResult:
        temp_messages = self.messages + [{"role": "user", "content": prompt}]
        try:
            resp = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=self.model,
                    messages=temp_messages,
                    max_tokens=150,
                ),
                timeout=self.relevance_timeout,
            )
            content = resp.choices[0].message.content or ""
            return self._parse_relevance(content)
        except asyncio.TimeoutError:
            return RelevanceResult(
                participant_name=self.name,
                wants_to_speak=False,
                summary="(timed out on relevance check)",
                priority=self.priority,
            )
        except Exception as exc:
            return RelevanceResult(
                participant_name=self.name,
                wants_to_speak=False,
                summary=f"(error: {exc!s})",
                priority=self.priority,
            )

    def _parse_relevance(self, text: str) -> RelevanceResult:
        decision_match = _DECISION_RE.search(text)
        summary_match = _SUMMARY_RE.search(text)
        wants = (
            decision_match.group(1).upper() == "YES"
            if decision_match
            else False
        )
        summary = summary_match.group(1).strip() if summary_match else text.strip()
        return RelevanceResult(
            participant_name=self.name,
            wants_to_speak=wants,
            summary=summary,
            priority=self.priority,
        )

    async def get_full_response(self) -> AsyncIterator[str]:
        """Stream a full response; caller must collect chunks and call
        add_assistant_message with the complete text afterward."""
        stream = await asyncio.wait_for(
            self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                stream=True,
            ),
            timeout=self.response_timeout,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content


class PoeClient:
    """Top-level client managing all participant sessions."""

    def __init__(self, api_key: str, config: AppConfig) -> None:
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=config.poe.base_url,
        )
        self._notes_model = config.notes_summarizer.model
        self._config = config
        self.sessions: dict[str, ParticipantSession] = {}
        for p in config.participants:
            sys_prompt = build_system_prompt(p, config.meeting.title)
            self.sessions[p.name] = ParticipantSession(
                client=self._client,
                participant=p,
                system_prompt=sys_prompt,
                relevance_timeout=config.meeting.relevance_timeout_seconds,
                response_timeout=config.meeting.response_timeout_seconds,
            )

    async def get_notes_summary(self, prompt: str) -> str:
        try:
            resp = await asyncio.wait_for(
                self._client.chat.completions.create(
                    model=self._notes_model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=500,
                ),
                timeout=30,
            )
            return resp.choices[0].message.content or ""
        except Exception as exc:
            return f"(Failed to generate summary: {exc!s})"

    async def close(self) -> None:
        await self._client.close()
