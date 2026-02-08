"""Phase 2: AI participant design with Gemini assistance."""

from __future__ import annotations

import asyncio
import enum
from typing import Optional

import yaml
from openai import AsyncOpenAI
from pydantic import ValidationError

from .models import BasicMeetingConfig, ParticipantConfig
from .ui_helpers import clear_screen


class SetupResult(enum.Enum):
    """Result of participant setup."""
    SUCCESS = "success"
    CANCELLED = "cancelled"
    GO_BACK = "go_back"

PARTICIPANT_SETUP_SYSTEM_PROMPT = """\
你是會議規劃 AI。協助使用者設計 AI 參與者。

會議標題：{meeting_title}

根據使用者需求，建議 2-6 個 AI 參與者，每個包含：
- name: 角色名稱
- role: 專業領域/職責
- personality: 性格特質
- description: 會議中的責任
- model: 使用的 LLM（從可用模型中選擇）
- priority: 發言順序（1 = 先發言）

系統中已配置的可用模型清單：
{models}

重要規則：
- 上述模型清單就是系統中所有可用的模型，這是完整且準確的列表
- 必須嚴格使用清單中的模型名稱，不要替換、修改或質疑模型名稱
- 如果使用者指定的模型名稱在清單中，就直接使用該名稱，不要自作主張改成其他模型
- 不要基於你的知識判斷哪些模型存在或不存在，只需信任系統提供的清單
- 根據角色複雜度選擇模型（困難角色用更強的模型）
- 每個參與者必須有唯一的名稱和優先級
- 始終使用與使用者相同的語言回覆
- 不要在對話中主動列出所有可用模型，除非使用者明確詢問
- 在給出參與者建議後，使用這個提醒：「滿意此設計可輸入 /start 開始會議，或繼續提出修改需求（例如：增加某個角色、更換模型等）」
- 重要：提及命令時絕對不要使用加粗格式（**command**），只寫純文字 /start，避免使用者誤以為星號是命令的一部分
- 當使用者明確輸入 /start 或要求最終配置時，只輸出 YAML 代碼塊，不要其他文字

YAML 格式：
```yaml
participants:
  - name: "..."
    role: "..."
    personality: "..."
    description: "..."
    model: "..."
    priority: 1
  - name: "..."
    role: "..."
    personality: "..."
    description: "..."
    model: "..."
    priority: 2
```
"""


def extract_participants_yaml(text: str) -> str | None:
    """Extract the first ```yaml ... ``` block from text.

    Args:
        text: Text containing YAML code block

    Returns:
        Extracted YAML string or None if not found
    """
    if "```yaml" not in text:
        return None
    try:
        return text.split("```yaml")[1].split("```")[0].strip()
    except IndexError:
        return None


def parse_participants(yaml_str: str) -> list[ParticipantConfig] | None:
    """Parse and validate YAML string into list of ParticipantConfig.

    Args:
        yaml_str: YAML string containing participants array

    Returns:
        List of ParticipantConfig or None if validation fails
    """
    try:
        raw = yaml.safe_load(yaml_str)
        if not isinstance(raw, dict) or "participants" not in raw:
            print("  驗證錯誤：YAML 必須包含 'participants' 鍵")
            return None

        participants = [
            ParticipantConfig.model_validate(p) for p in raw["participants"]
        ]
        return participants
    except (ValidationError, yaml.YAMLError, KeyError, TypeError) as exc:
        print(f"  驗證錯誤：{exc}")
        return None


async def run_participant_setup(
    basic_config: BasicMeetingConfig,
    api_key: str,
    available_models: list[str],
    planning_assistant_model: str = "gemini-3-pro"
) -> tuple[SetupResult, Optional[list[ParticipantConfig]]]:
    """Run participant design with AI assistance.

    Args:
        basic_config: Basic meeting configuration
        api_key: POE API key
        available_models: List of available model names
        planning_assistant_model: Model to use for planning assistant

    Returns:
        Tuple of (SetupResult, Optional[list[ParticipantConfig]])
        - (SUCCESS, participants) if successful
        - (CANCELLED, None) if user quit
        - (GO_BACK, None) if user wants to return to main menu
    """
    clear_screen()
    print("\n" + "=" * 60)
    print(f"  參與者設計（{planning_assistant_model}）")
    print("=" * 60)

    # Prompt for meeting title - required input
    while True:
        new_title = input("\n會議標題：").strip()
        if new_title:
            basic_config.title = new_title
            break
        # If empty, loop will ask again

    print(f"\n規劃助手：{planning_assistant_model}")
    print(f"可用模型：已配置 {len(available_models)} 個模型\n")
    print("請向 AI 提出你的會議需求。")
    print("\n指令：")
    print("  /start  - 確認設計並開始會議")
    print("  /back   - 返回主選單")
    print("  /quit   - 離開程式")
    print()

    client = AsyncOpenAI(
        api_key=api_key,
        base_url="https://api.poe.com/v1",
    )

    system_prompt = PARTICIPANT_SETUP_SYSTEM_PROMPT.format(
        meeting_title=basic_config.title,
        models=", ".join(available_models)
    )
    messages: list[dict[str, str]] = [
        {"role": "system", "content": system_prompt},
    ]

    try:
        while True:
            try:
                user_input = (
                    await asyncio.to_thread(input, "你：")
                ).strip()
            except (EOFError, KeyboardInterrupt):
                print()
                return SetupResult.CANCELLED, None

            if not user_input:
                continue

            cmd = user_input.lower()
            if cmd == "/quit":
                return SetupResult.CANCELLED, None
            elif cmd == "/back":
                clear_screen()
                print("\n正在返回主選單...")
                return SetupResult.GO_BACK, None

            requesting_start = cmd == "/start"
            if requesting_start:
                messages.append({
                    "role": "user",
                    "content": (
                        "請輸出最終的參與者配置 YAML。"
                        "只輸出 ```yaml ... ``` 代碼塊，不要其他文字。"
                    ),
                })
            else:
                messages.append({"role": "user", "content": user_input})

            # Stream assistant's response
            try:
                stream = await client.chat.completions.create(
                    model=planning_assistant_model,
                    messages=messages,
                    stream=True,
                )
                print(f"\n{planning_assistant_model}: ", end="", flush=True)
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
                print(f"\n  錯誤：{exc}\n")
                # Remove the failed user message so conversation stays clean
                messages.pop()
                continue

            # If user requested /start, try to extract and validate participants
            if requesting_start:
                yaml_str = extract_participants_yaml(full_response)
                if yaml_str is None:
                    print("  無法從回應中擷取 YAML，請再試一次。\n")
                    continue

                participants = parse_participants(yaml_str)
                if participants is None:
                    print("  YAML 驗證失敗，請繼續修改。\n")
                    continue

                # Show summary
                print("  設定驗證通過！")
                print(f"  參與者：")
                for p in participants:
                    print(f"    {p.priority}. {p.name}（{p.role}, {p.model}）")
                print("\n  正在開始會議...\n")
                clear_screen()
                return SetupResult.SUCCESS, participants

    finally:
        await client.close()
