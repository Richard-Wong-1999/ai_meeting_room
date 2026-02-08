"""UI helper functions for interactive prompts and displays."""

import os
from typing import Any, Callable, TypeVar

T = TypeVar('T')


def clear_screen() -> None:
    """Clear the terminal screen."""
    # Windows
    if os.name == 'nt':
        os.system('cls')
    # Unix/Linux/Mac
    else:
        os.system('clear')


def print_phase_header(phase: int, title: str) -> None:
    """Print a phase header banner.

    Args:
        phase: Phase number (1, 2, etc.)
        title: Title of the phase
    """
    banner_width = 60
    print("\n" + "=" * banner_width)
    print(f"  階段 {phase}：{title}")
    print("=" * banner_width + "\n")


def prompt_with_default(
    prompt: str,
    default: T,
    validator: Callable[[str], tuple[bool, T | str]] | None = None,
    help_text: str | None = None
) -> T:
    """Prompt user for input with a default value and optional validation.

    Args:
        prompt: The prompt message
        default: Default value if user presses Enter
        validator: Optional function that takes input string and returns (is_valid, value_or_error)
        help_text: Optional help text displayed before the prompt

    Returns:
        The validated user input or default value
    """
    if help_text:
        print(f"\n{help_text}")

    while True:
        user_input = input(f"{prompt}〔預設：{default}〕：").strip()

        # Use default if empty input
        if not user_input:
            return default

        # Check for special commands
        if user_input.lower() in ['/quit', '/exit']:
            raise KeyboardInterrupt()

        # Validate if validator provided
        if validator:
            is_valid, result = validator(user_input)
            if is_valid:
                return result  # type: ignore
            else:
                print(f"❌ {result}")  # result is error message
                continue

        # No validator, return as-is (cast to type of default)
        try:
            if isinstance(default, int):
                return int(user_input)  # type: ignore
            elif isinstance(default, float):
                return float(user_input)  # type: ignore
            else:
                return user_input  # type: ignore
        except ValueError:
            print(f"❌ 無效的輸入，預期 {type(default).__name__}。")
            continue


def confirm_yes_no(prompt: str, default_yes: bool = True) -> bool:
    """Ask user a yes/no question.

    Args:
        prompt: The question to ask
        default_yes: Whether default is yes (True) or no (False)

    Returns:
        True for yes, False for no
    """
    options = "[Y/N]"  # Unified format - both options available
    while True:
        response = input(f"{prompt} {options}: ").strip().lower()

        if not response:
            return default_yes

        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        else:
            print("❌ 請輸入 'y' 或 'n'。")


def wait_for_enter(message: str = "按 Enter 繼續...") -> None:
    """Wait for user to press Enter before continuing.

    Args:
        message: Message to display
    """
    input(f"\n  {message}")


def print_config_summary(config: Any) -> None:
    """Print a summary of the basic meeting configuration.

    Args:
        config: BasicMeetingConfig object
    """
    print("\n" + "-" * 50)
    print("設定摘要：")
    print("-" * 50)
    print(f"  會議標題：{config.title}")
    print(f"  每輪最大回合數：{config.max_rounds_per_turn}")
    print(f"  相關性逾時：{config.relevance_timeout_seconds}s")
    print(f"  回應逾時：{config.response_timeout_seconds}s")
    print("-" * 50 + "\n")
