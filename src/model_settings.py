"""Model settings configuration."""

from typing import Optional

from .model_manager import (
    DEFAULT_MODELS,
    add_model_interactive,
    display_models,
    get_default_models,
    remove_model_interactive,
)
from .models import BasicMeetingConfig, ModelSettings
from .ui_helpers import clear_screen, wait_for_enter


def auto_save_model_settings(
    settings: ModelSettings,
    available: list[str],
    meeting_config: BasicMeetingConfig
) -> None:
    """Auto-save model settings to disk.

    Args:
        settings: Current model settings
        available: Current available models list
        meeting_config: Meeting config (needed for save_preferences)
    """
    from .main_menu import save_preferences

    # Sync available models
    settings.available_models = available

    # Save to disk
    save_preferences(meeting_config, settings)

    # Show feedback
    print("  ✓ 已儲存")
    wait_for_enter()


def display_model_settings(settings: ModelSettings) -> None:
    """Display current model settings.

    Args:
        settings: ModelSettings object
    """
    available = settings.available_models if settings.available_models else get_default_models()

    print("\n" + "=" * 60)
    print("  目前模型設定")
    print("=" * 60)
    print(f"  規劃助手模型：{settings.planning_assistant_model}")
    print(f"  會議記錄模型：{settings.notes_model}")
    print(f"  可用模型：已配置 {len(available)} 個模型")
    print("=" * 60 + "\n")


def select_model_from_list(
    prompt: str,
    current_model: str,
    available_models: list[str]
) -> str:
    """Let user select a model from available models.

    Args:
        prompt: Prompt message
        current_model: Current model selection
        available_models: List of available models

    Returns:
        Selected model name
    """
    clear_screen()
    print(f"\n{prompt}")
    print(f"目前：{current_model}\n")

    display_models(available_models)

    while True:
        user_input = input("輸入模型編號或名稱（按 Enter 保留目前設定）：").strip()

        if not user_input:
            print(f"\n  → 保留目前模型：{current_model}")
            wait_for_enter()
            return current_model

        # Try as number
        try:
            idx = int(user_input) - 1
            if 0 <= idx < len(available_models):
                selected = available_models[idx]
                print(f"\n  ✓ 已變更為：{selected}")
                wait_for_enter()
                return selected
            else:
                print(f"  ❌ 無效的數字。請選擇 1-{len(available_models)}")
                continue
        except ValueError:
            pass

        # Try as model name
        if user_input in available_models:
            print(f"\n  ✓ 已變更為：{user_input}")
            wait_for_enter()
            return user_input
        else:
            print(f"  ❌ 模型 '{user_input}' 不在可用模型清單中。")
            print("  提示：請先將其加入可用模型，或從清單中選擇。")


def manage_model_settings(
    current_settings: Optional[ModelSettings] = None,
    meeting_config: Optional[BasicMeetingConfig] = None
) -> ModelSettings:
    """Interactive model settings configuration.

    Args:
        current_settings: Current ModelSettings, or None for defaults
        meeting_config: Meeting config (needed for auto-save)

    Returns:
        Updated ModelSettings
    """
    settings = current_settings.model_copy() if current_settings else ModelSettings()

    # Use available models or defaults
    available = settings.available_models if settings.available_models else get_default_models()

    def show_model_settings_menu():
        """Display model settings menu."""
        print("\n" + "=" * 60)
        print("  模型設定")
        print("=" * 60)
        print("\n目前設定：")
        print(f"  規劃助手：{settings.planning_assistant_model}")
        print(f"  會議記錄：{settings.notes_model}")
        print(f"  可用模型：已配置 {len(available)} 個")
        print("\n指令：")
        print("  1 - 設定規劃助手模型（參與者設計）")
        print("  2 - 設定會議記錄模型")
        print("  3 - 管理可用模型（新增/移除）")
        print("  v - 檢視目前設定")
        print("  b - 返回主選單\n")

    while True:
        clear_screen()
        show_model_settings_menu()
        cmd = input("指令：").strip().lower()

        if not cmd:
            print("  ℹ️  請輸入指令（1、2、3、v 或 b）")
            wait_for_enter()
            continue

        if cmd == '1':
            settings.planning_assistant_model = select_model_from_list(
                "設定規劃助手模型",
                settings.planning_assistant_model,
                available
            )
            # Auto-save
            auto_save_model_settings(settings, available, meeting_config)

        elif cmd == '2':
            settings.notes_model = select_model_from_list(
                "設定會議記錄模型",
                settings.notes_model,
                available
            )
            # Auto-save
            auto_save_model_settings(settings, available, meeting_config)

        elif cmd == '3':
            def show_manage_models_menu():
                """Display manage models submenu."""
                print("\n" + "=" * 60)
                print("  管理可用模型")
                print("=" * 60)
                print(f"\n目前可用：{len(available)} 個模型")
                print("\n指令：")
                print("  a - 新增模型")
                print("  r - 移除模型")
                print("  d - 重設為預設值")
                print("  v - 檢視模型")
                print("  b - 返回模型設定\n")

            while True:
                clear_screen()
                show_manage_models_menu()
                sub_cmd = input("指令：").strip().lower()

                if not sub_cmd:
                    print("  ℹ️  請輸入指令（a、r、d、v 或 b）")
                    wait_for_enter()
                    continue

                if sub_cmd == 'a':
                    available = add_model_interactive(available)
                    print(f"\n  ✓ 模型已更新")
                    wait_for_enter()
                    # Auto-save
                    auto_save_model_settings(settings, available, meeting_config)
                elif sub_cmd == 'r':
                    available = remove_model_interactive(available)
                    print(f"\n  ✓ 模型已更新")
                    wait_for_enter()
                    # Auto-save
                    auto_save_model_settings(settings, available, meeting_config)
                elif sub_cmd == 'd':
                    clear_screen()
                    available = get_default_models()
                    print("\n  ✓ 已重設為預設模型")
                    wait_for_enter()
                    # Auto-save
                    auto_save_model_settings(settings, available, meeting_config)
                elif sub_cmd == 'v':
                    clear_screen()
                    display_models(available)
                    wait_for_enter()
                elif sub_cmd == 'b':
                    break
                else:
                    print("  ❌ 未知的指令。請使用：a、r、d、v 或 b")
                    wait_for_enter()

            # Update settings with modified list (already done in auto_save)
            settings.available_models = available

        elif cmd == 'v':
            # Update available list for display
            clear_screen()
            temp_display = settings.model_copy()
            temp_display.available_models = available
            display_model_settings(temp_display)
            wait_for_enter()

        elif cmd == 'b':
            # Validate that selected models are in available list
            if settings.planning_assistant_model not in available:
                clear_screen()
                print(f"\n  ⚠️  警告：規劃助手模型 '{settings.planning_assistant_model}' 不在可用模型清單中。")
                print("  正在加入可用模型...")
                available.append(settings.planning_assistant_model)
                wait_for_enter()

            if settings.notes_model not in available:
                clear_screen()
                print(f"\n  ⚠️  警告：會議記錄模型 '{settings.notes_model}' 不在可用模型清單中。")
                print("  正在加入可用模型...")
                available.append(settings.notes_model)
                wait_for_enter()

            settings.available_models = available
            clear_screen()
            return settings

        else:
            print("  ❌ 未知的指令。請使用：1、2、3、v 或 b")
            wait_for_enter()
