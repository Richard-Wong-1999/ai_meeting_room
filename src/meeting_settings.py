"""Meeting settings configuration."""

from typing import Optional

from .models import BasicMeetingConfig, ModelSettings
from .ui_helpers import clear_screen, confirm_yes_no, print_config_summary, wait_for_enter


def auto_save_meeting_settings(
    config: BasicMeetingConfig,
    model_settings: ModelSettings
) -> None:
    """Auto-save meeting settings to disk.

    Args:
        config: Current meeting config
        model_settings: Model settings (needed for save_preferences)
    """
    from .main_menu import save_preferences

    # Save to disk
    save_preferences(config, model_settings)

    # Show feedback
    print("  ✓ 已儲存")
    wait_for_enter()


def get_default_meeting_config() -> BasicMeetingConfig:
    """Get default meeting configuration.

    Returns:
        BasicMeetingConfig with default values
    """
    return BasicMeetingConfig(
        title="AI Meeting",
        max_rounds_per_turn=10,
        relevance_timeout_seconds=20,
        response_timeout_seconds=90
    )


def display_meeting_settings(config: BasicMeetingConfig) -> None:
    """Display meeting settings.

    Args:
        config: BasicMeetingConfig object
    """
    print_config_summary(config)


def prompt_title(current: str) -> str:
    """Prompt for meeting title.

    Args:
        current: Current title

    Returns:
        New title
    """
    clear_screen()
    print(f"\n目前標題：{current}")
    new_title = input("新標題（按 Enter 保留目前設定）：").strip()
    if new_title:
        print(f"\n  ✓ 已變更為：{new_title}")
        wait_for_enter()
        return new_title
    else:
        print(f"\n  → 保留目前設定：{current}")
        wait_for_enter()
        return current


def prompt_max_rounds(current: int) -> int:
    """Prompt for max rounds.

    Args:
        current: Current value

    Returns:
        New value
    """
    clear_screen()
    help_text = (
        "\n每輪最大回合數：單輪中 AI 回應的最大次數。\n"
        "  - 較低值 (3-5)：較快，討論更集中\n"
        "  - 中等值 (8-12)：深度與速度兼顧\n"
        "  - 較高值 (15-30)：深入探討，等待時間較長\n"
        "有效範圍：1-50"
    )
    print(help_text)
    print(f"目前：{current}")

    while True:
        user_input = input("新數值（按 Enter 保留目前設定）：").strip()
        if not user_input:
            print(f"\n  → 保留目前設定：{current}")
            wait_for_enter()
            return current

        try:
            value = int(user_input)
            if 1 <= value <= 50:
                print(f"\n  ✓ 已變更為：{value}")
                wait_for_enter()
                return value
            else:
                print("  ❌ 數值必須介於 1 到 50 之間")
        except ValueError:
            print("  ❌ 請輸入有效的整數")


def prompt_relevance_timeout(current: int) -> int:
    """Prompt for relevance timeout.

    Args:
        current: Current value

    Returns:
        New value
    """
    clear_screen()
    help_text = (
        "\n相關性逾時：等待 AI 決定是否要發言的時間。\n"
        "  - 較低值 (5-10s)：較快但可能中斷思考\n"
        "  - 中等值 (15-25s)：平衡\n"
        "  - 較高值 (30-60s)：思考更充分但較慢\n"
        "有效範圍：5-120 秒"
    )
    print(help_text)
    print(f"目前：{current}s")

    while True:
        user_input = input("新數值（按 Enter 保留目前設定）：").strip()
        if not user_input:
            print(f"\n  → 保留目前設定：{current}s")
            wait_for_enter()
            return current

        try:
            value = int(user_input)
            if 5 <= value <= 120:
                print(f"\n  ✓ 已變更為：{value}s")
                wait_for_enter()
                return value
            else:
                print("  ❌ 數值必須介於 5 到 120 之間")
        except ValueError:
            print("  ❌ 請輸入有效的整數")


def prompt_response_timeout(current: int, min_value: int) -> int:
    """Prompt for response timeout.

    Args:
        current: Current value
        min_value: Minimum allowed value (should be > relevance timeout)

    Returns:
        New value
    """
    clear_screen()
    help_text = (
        "\n回應逾時：等待 AI 產生完整回應的時間。\n"
        "  - 較低值 (30-60s)：回應較快，但可能被截斷\n"
        "  - 中等值 (90-120s)：平衡\n"
        "  - 較高值 (150-300s)：回應更詳盡\n"
        f"有效範圍：{min_value}-300 秒（必須大於相關性逾時）"
    )
    print(help_text)
    print(f"目前：{current}s")

    while True:
        user_input = input("新數值（按 Enter 保留目前設定）：").strip()
        if not user_input:
            print(f"\n  → 保留目前設定：{current}s")
            wait_for_enter()
            return current

        try:
            value = int(user_input)
            if min_value <= value <= 300:
                print(f"\n  ✓ 已變更為：{value}s")
                wait_for_enter()
                return value
            else:
                print(f"  ❌ 數值必須介於 {min_value} 到 300 之間")
        except ValueError:
            print("  ❌ 請輸入有效的整數")


def manage_meeting_settings(
    current_config: Optional[BasicMeetingConfig] = None,
    model_settings: Optional[ModelSettings] = None
) -> BasicMeetingConfig:
    """Interactive meeting settings configuration.

    Args:
        current_config: Current BasicMeetingConfig, or None for defaults
        model_settings: Model settings (needed for auto-save)

    Returns:
        Updated BasicMeetingConfig
    """
    config = current_config.model_copy() if current_config else get_default_meeting_config()

    def show_meeting_settings_menu():
        """Display meeting settings menu."""
        print("\n" + "=" * 60)
        print("  會議設定")
        print("=" * 60)
        print("\n目前設定：")
        print(f"  標題：{config.title}")
        print(f"  每輪最大回合數：{config.max_rounds_per_turn}")
        print(f"  相關性逾時：{config.relevance_timeout_seconds}s")
        print(f"  回應逾時：{config.response_timeout_seconds}s")
        print("\n指令：")
        print("  1 - 設定每輪最大回合數")
        print("  2 - 設定相關性逾時")
        print("  3 - 設定回應逾時")
        print("  d - 重設為預設值")
        print("  v - 檢視目前設定")
        print("  b - 返回主選單\n")

    while True:
        clear_screen()
        show_meeting_settings_menu()
        cmd = input("指令：").strip().lower()

        if not cmd:
            print("  ℹ️  請輸入指令（1、2、3、d、v 或 b）")
            wait_for_enter()
            continue

        if cmd == '1':
            config.max_rounds_per_turn = prompt_max_rounds(config.max_rounds_per_turn)
            # Auto-save
            auto_save_meeting_settings(config, model_settings)

        elif cmd == '2':
            config.relevance_timeout_seconds = prompt_relevance_timeout(config.relevance_timeout_seconds)
            # Ensure response timeout is still greater
            if config.response_timeout_seconds <= config.relevance_timeout_seconds:
                config.response_timeout_seconds = config.relevance_timeout_seconds + 10
                print(f"\n  ℹ️  回應逾時已自動調整為 {config.response_timeout_seconds}s")
                wait_for_enter()
            # Auto-save
            auto_save_meeting_settings(config, model_settings)

        elif cmd == '3':
            min_value = config.relevance_timeout_seconds + 1
            config.response_timeout_seconds = prompt_response_timeout(
                config.response_timeout_seconds,
                min_value
            )
            # Auto-save
            auto_save_meeting_settings(config, model_settings)

        elif cmd == 'd':
            clear_screen()
            if confirm_yes_no("\n確定重設所有會議設定為預設值？", default_yes=False):
                config = get_default_meeting_config()
                print("\n  ✓ 已重設為預設值")
                # Auto-save
                auto_save_meeting_settings(config, model_settings)
            else:
                wait_for_enter()

        elif cmd == 'v':
            clear_screen()
            display_meeting_settings(config)
            wait_for_enter()

        elif cmd == 'b':
            clear_screen()
            return config

        else:
            print("  ❌ 未知的指令。請使用：1、2、3、d、v 或 b")
            wait_for_enter()
