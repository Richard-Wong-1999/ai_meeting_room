"""Main menu for AI Meeting Room."""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml
from pydantic import ValidationError

from .conversation_storage import SessionData
from .meeting_settings import display_meeting_settings, get_default_meeting_config, manage_meeting_settings
from .model_manager import get_default_models
from .model_settings import display_model_settings, manage_model_settings
from .models import BasicMeetingConfig, ModelSettings, UserPreferences
from .ui_helpers import clear_screen, confirm_yes_no, wait_for_enter


def get_preferences_path() -> Path:
    """Get the path to user preferences file."""
    config_dir = Path.home() / ".ai_meeting_room"
    config_dir.mkdir(exist_ok=True)
    return config_dir / "preferences.yaml"


def load_preferences() -> tuple[BasicMeetingConfig, ModelSettings]:
    """Load user preferences from disk.

    Returns:
        Tuple of (BasicMeetingConfig, ModelSettings)
    """
    prefs_path = get_preferences_path()

    if not prefs_path.exists():
        # First run: initialize with actual default models
        model_settings = ModelSettings()
        model_settings.available_models = get_default_models()
        return get_default_meeting_config(), model_settings

    try:
        with open(prefs_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        prefs = UserPreferences(**data)

        # Migrate old custom_models to model_settings.available_models
        if prefs.custom_models and not prefs.model_settings.available_models:
            prefs.model_settings.available_models = prefs.custom_models

        # Migrate empty available_models to actual defaults
        if not prefs.model_settings.available_models:
            prefs.model_settings.available_models = get_default_models()

        return prefs.basic_config, prefs.model_settings

    except (ValidationError, yaml.YAMLError, KeyError, TypeError):
        # Corrupted or invalid preferences file
        model_settings = ModelSettings()
        model_settings.available_models = get_default_models()
        return get_default_meeting_config(), model_settings


def save_preferences(meeting_config: BasicMeetingConfig, model_settings: ModelSettings) -> None:
    """Save user preferences to disk.

    Args:
        meeting_config: Meeting configuration
        model_settings: Model settings
    """
    prefs = UserPreferences(
        basic_config=meeting_config,
        model_settings=model_settings,
        saved_at=datetime.utcnow().isoformat()
    )

    prefs_path = get_preferences_path()
    with open(prefs_path, 'w', encoding='utf-8') as f:
        yaml.safe_dump(prefs.model_dump(), f, allow_unicode=True)


def display_main_menu() -> None:
    """Display the main menu."""
    print("\n" + "=" * 60)
    print("  AI 會議室")
    print("=" * 60)
    print("\n主選單：")
    print("  1 - 新會議")
    print("  2 - 載入會議")
    print("  3 - 管理會議記錄")
    print("  4 - 模型設定")
    print("  5 - 會議設定")
    print("  v - 檢視目前設定")
    print("  q - 離開")
    print()


def display_current_config(meeting_config: BasicMeetingConfig, model_settings: ModelSettings) -> None:
    """Display current configuration.

    Args:
        meeting_config: Meeting configuration
        model_settings: Model settings
    """
    print("\n" + "=" * 60)
    print("  目前設定")
    print("=" * 60)

    # Meeting settings
    print("\n會議設定：")
    print(f"  標題：{meeting_config.title}")
    print(f"  每輪最大回合數：{meeting_config.max_rounds_per_turn}")
    print(f"  相關性逾時：{meeting_config.relevance_timeout_seconds}s")
    print(f"  回應逾時：{meeting_config.response_timeout_seconds}s")

    # Model settings
    available = model_settings.available_models if model_settings.available_models else get_default_models()
    print("\n模型設定：")
    print(f"  規劃助手：{model_settings.planning_assistant_model}")
    print(f"  會議記錄：{model_settings.notes_model}")
    print(f"  可用模型：已配置 {len(available)} 個模型")

    print("=" * 60 + "\n")


def manage_conversations_menu() -> None:
    """Manage saved conversations."""
    from .conversation_storage import delete_conversation, list_conversations

    while True:
        clear_screen()
        conversations = list_conversations()

        print("\n" + "=" * 60)
        print("  管理會議記錄")
        print("=" * 60)

        if not conversations:
            print("\n沒有已儲存的會議。")
            wait_for_enter()
            return

        print("\n已儲存的會議：")
        for i, conv in enumerate(conversations, 1):
            print(f"  {i}. {conv.title}")
            print(f"     建立時間：{conv.created_at[:19]}")
            print(f"     更新時間：{conv.updated_at[:19]}")
            print(f"     訊息數：{conv.message_count}")
            print()

        print("指令：")
        print("  <數字> - 刪除會議")
        print("  b - 返回主選單")

        cmd = input("\n指令：").strip().lower()

        if cmd == 'b':
            return
        elif cmd.isdigit():
            try:
                num = int(cmd)
                idx = num - 1
                if 0 <= idx < len(conversations):
                    conv = conversations[idx]
                    if confirm_yes_no(f"\n確定刪除「{conv.title}」？", default_yes=False):
                        if delete_conversation(conv.session_id):
                            print(f"\n  ✓ 已刪除：{conv.title}")
                            wait_for_enter()
                else:
                    print("  ❌ 無效的數字")
                    wait_for_enter()
            except ValueError:
                print("  ❌ 無效的數字")
                wait_for_enter()
        else:
            print("  ❌ 無效的指令。請輸入數字刪除或 'b' 返回。")
            wait_for_enter()


def show_main_menu() -> tuple[str, BasicMeetingConfig, ModelSettings, Optional[SessionData]]:
    """Show main menu and handle user interaction.

    Returns:
        Tuple of (action, meeting_config, model_settings, session_data)
        where action is 'start_new', 'load_conversation', 'quit', or None
        session_data is None for new meetings, SessionData for loaded ones
    """
    # Load saved preferences
    meeting_config, model_settings = load_preferences()

    # Show welcome message only on first launch
    clear_screen()

    first_run = True

    try:
        while True:
            if not first_run:
                clear_screen()
            first_run = False

            display_main_menu()
            cmd = input("選擇：").strip().lower()

            if not cmd:
                print("  ℹ️  請輸入選項")
                wait_for_enter()
                continue

            if cmd == '1':
                # Start new meeting
                print("\n  → 正在開始新會議...")
                return 'start_new', meeting_config, model_settings, None

            elif cmd == '2':
                # Load conversation
                from .conversation_storage import list_conversations, load_conversation

                clear_screen()
                conversations = list_conversations()
                if not conversations:
                    print("\n  ℹ️  找不到已儲存的會議")
                    wait_for_enter()
                    continue

                print("\n" + "=" * 60)
                print("  載入會議")
                print("=" * 60)
                print("\n已儲存的會議：")
                for i, conv in enumerate(conversations, 1):
                    print(f"  {i}. {conv.title}")
                    print(f"     最後更新：{conv.updated_at[:19]}")
                    print(f"     訊息數：{conv.message_count}")

                choice = input("\n輸入數字載入（或按 Enter 取消）：").strip()
                if not choice:
                    # User pressed Enter to cancel
                    continue
                elif choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(conversations):
                        session_data = load_conversation(conversations[idx].session_id)
                        if session_data:
                            print(f"\n  ✓ 已載入：{session_data.title}")
                            return 'load_conversation', meeting_config, model_settings, session_data
                        else:
                            print("  ❌ 載入會議失敗")
                            wait_for_enter()
                    else:
                        print("  ❌ 無效的數字")
                        wait_for_enter()
                else:
                    print("  ❌ 無效的輸入，請輸入數字。")
                    wait_for_enter()

            elif cmd == '3':
                # Manage conversations
                manage_conversations_menu()

            elif cmd == '4':
                # Model settings
                clear_screen()
                model_settings = manage_model_settings(model_settings, meeting_config)
                # Already auto-saved within the function

            elif cmd == '5':
                # Meeting settings
                clear_screen()
                meeting_config = manage_meeting_settings(meeting_config, model_settings)
                # Already auto-saved within the function

            elif cmd == 'v':
                # View configuration
                clear_screen()
                display_current_config(meeting_config, model_settings)
                wait_for_enter()

            elif cmd == 'q':
                # Quit
                clear_screen()
                print("\n再見！\n")
                wait_for_enter()
                clear_screen()
                return 'quit', meeting_config, model_settings, None

            else:
                print("  ❌ 無效的選項")
                wait_for_enter()

    except KeyboardInterrupt:
        print("\n\n再見！\n")
        return 'quit', meeting_config, model_settings, None
