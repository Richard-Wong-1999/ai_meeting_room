from __future__ import annotations

import asyncio
import sys

import yaml
from openai import AsyncOpenAI

from .models import AppConfig

AVAILABLE_MODELS = [
    "gpt-5.2", "gpt-4o", "gemini-3-pro", "gemini-3-flash",
    "claude-opus-4.5", "claude-sonnet-4.5", "claude-haiku-4.5",
    "grok-4",
]

SETUP_SYSTEM_PROMPT = """\
You are a meeting planner AI. Help the user set up a multi-AI meeting room.

Based on the user's meeting topic and requirements, suggest:
1. A meeting title
2. 2-6 AI participants, each with:
   - name: A fitting character name
   - role: Their expertise/role
   - personality: Their personality traits
   - description: Their responsibility in the meeting
   - model: Which LLM to use (from available models)
   - priority: Speaking order (1 = speaks first)

Available LLM models: {models}

Rules:
- Choose models that fit the role complexity (stronger models for harder roles)
- Each participant must have a unique name and unique priority number
- Always respond in the same language as the user
- When the user confirms or you are asked for the final config, output ONLY a \
YAML code block in the exact format shown below, with no other text

The YAML format:
```yaml
meeting:
  title: "..."
  max_rounds_per_turn: 10
  relevance_timeout_seconds: 20
  response_timeout_seconds: 90

poe:
  base_url: "https://api.poe.com/v1"

participants:
  - name: "..."
    role: "..."
    personality: "..."
    description: "..."
    model: "..."
    priority: 1

notes_summarizer:
  model: "gpt-4o"
```

IMPORTANT: notes_summarizer model must always be "gpt-4o".
"""


def _extract_yaml(text: str) -> str | None:
    """Extract the first ```yaml ... ``` block from text."""
    if "```yaml" not in text:
        return None
    try:
        return text.split("```yaml")[1].split("```")[0].strip()
    except IndexError:
        return None


def _parse_config(yaml_str: str) -> AppConfig | None:
    """Parse and validate YAML string into AppConfig."""
    try:
        raw = yaml.safe_load(yaml_str)
        return AppConfig.model_validate(raw)
    except Exception as exc:
        print(f"  驗證錯誤: {exc}")
        return None


async def run_setup(api_key: str) -> AppConfig | None:
    """Run an interactive setup conversation with Gemini-3-Pro.

    Returns a validated AppConfig, or None if the user cancels.
    """
    client = AsyncOpenAI(
        api_key=api_key,
        base_url="https://api.poe.com/v1",
    )

    system_prompt = SETUP_SYSTEM_PROMPT.format(
        models=", ".join(AVAILABLE_MODELS)
    )
    messages: list[dict[str, str]] = [
        {"role": "system", "content": system_prompt},
    ]

    print("=" * 60)
    print("  會議設定助手 (Gemini-3-Pro)")
    print("  請描述你想要的會議主題和需求。")
    print("  設定滿意後輸入 /start 確認並開始會議")
    print("  輸入 /quit 退出程式")
    print("=" * 60)
    print()

    try:
        while True:
            try:
                user_input = (
                    await asyncio.to_thread(input, "You: ")
                ).strip()
            except (EOFError, KeyboardInterrupt):
                print()
                return None

            if not user_input:
                continue
            if user_input.lower() == "/quit":
                return None

            requesting_start = user_input.lower() == "/start"
            if requesting_start:
                messages.append({
                    "role": "user",
                    "content": (
                        "請輸出最終的會議 YAML 設定檔。"
                        "只輸出 ```yaml ... ``` 代碼塊，不要其他內容。"
                    ),
                })
            else:
                messages.append({"role": "user", "content": user_input})

            # Stream Gemini's response
            try:
                stream = await client.chat.completions.create(
                    model="gemini-3-pro",
                    messages=messages,
                    stream=True,
                )
                print("\nGemini: ", end="", flush=True)
                full_response = ""
                async for chunk in stream:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        print(delta.content, end="", flush=True)
                        full_response += delta.content
                print("\n")
                messages.append({
                    "role": "assistant",
                    "content": full_response,
                })
            except Exception as exc:
                print(f"\n  錯誤: {exc}\n")
                # Remove the failed user message so conversation stays clean
                messages.pop()
                continue

            # If user requested /start, try to extract and validate config
            if requesting_start:
                yaml_str = _extract_yaml(full_response)
                if yaml_str is None:
                    print("  無法從回應中提取 YAML，請再試一次。\n")
                    continue
                config = _parse_config(yaml_str)
                if config is None:
                    print("  YAML 格式驗證失敗，請繼續修改。\n")
                    continue

                # Show summary
                print("  設定驗證通過！")
                print(f"  會議主題: {config.meeting.title}")
                print(f"  參與者:")
                for p in config.participants:
                    print(f"    {p.priority}. {p.name}（{p.role}, {p.model}）")
                print(f"  會議記錄模型: {config.notes_summarizer.model}")
                print("\n  正在啟動會議…\n")
                return config

    finally:
        await client.close()
