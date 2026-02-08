"""Model management for AI Meeting Room."""

from typing import Optional

from .ui_helpers import clear_screen

# Default models based on Poe API
DEFAULT_MODELS = [
    # OpenAI models
    "gpt-5.2",
    "gpt-4o",
    "gpt-4o-search",
    "o3",
    "o4-mini",

    # Anthropic Claude models
    "claude-opus-4.6",
    "claude-sonnet-4.5",
    "claude-haiku-4.5",

    # Google Gemini models
    "gemini-3-pro",
    "gemini-3-flash",

    # xAI models
    "grok-4",

    # Other models
    "deepseek-r1",
    "llama-4-maverick-t",
    "qwen3-max",
]


def display_models(models: list[str]) -> None:
    """Display available models in a formatted list.

    Args:
        models: List of model names
    """
    print("\n可用 AI 模型：")
    print("-" * 50)
    for i, model in enumerate(models, 1):
        print(f"  {i:2d}. {model}")
    print("-" * 50)
    print(f"共 {len(models)} 個模型\n")


def add_model_interactive(current_models: list[str]) -> list[str]:
    """Interactive model addition.

    Args:
        current_models: Current list of models

    Returns:
        Updated list of models
    """
    clear_screen()
    print("\n新增自訂模型")
    print("-" * 50)
    print("請輸入 Poe API 中的模型名稱（需完全一致）。")
    print("參考：https://poe.com/api/models")
    print("輸入空行結束新增。\n")

    models = current_models.copy()

    while True:
        model_name = input("模型名稱（或按 Enter 結束）：").strip()

        if not model_name:
            break

        if model_name in models:
            print(f"  ⚠️  '{model_name}' 已在清單中。")
            continue

        models.append(model_name)
        print(f"  ✓ 已新增 '{model_name}'")

    return models


def remove_model_interactive(current_models: list[str]) -> list[str]:
    """Interactive model removal.

    Args:
        current_models: Current list of models

    Returns:
        Updated list of models
    """
    clear_screen()
    if not current_models:
        print("\n⚠️  沒有可移除的模型。")
        return current_models

    display_models(current_models)
    print("輸入要移除的模型編號（以逗號分隔），或按 Enter 取消。\n")

    user_input = input("要移除的模型：").strip()
    if not user_input:
        return current_models

    try:
        indices = [int(x.strip()) - 1 for x in user_input.split(",")]
        models = current_models.copy()

        # Remove in reverse order to maintain indices
        for idx in sorted(set(indices), reverse=True):
            if 0 <= idx < len(models):
                removed = models.pop(idx)
                print(f"  ✓ 已移除 '{removed}'")
            else:
                print(f"  ⚠️  無效的索引：{idx + 1}")

        return models
    except ValueError:
        print("  ❌ 無效的輸入，請輸入以逗號分隔的數字。")
        return current_models


def manage_models_interactive(current_models: Optional[list[str]] = None) -> list[str]:
    """Interactive model management menu.

    Args:
        current_models: Current list of models, or None to use defaults

    Returns:
        Final list of models
    """
    models = current_models.copy() if current_models else DEFAULT_MODELS.copy()

    print("\n" + "=" * 60)
    print("  模型管理")
    print("=" * 60)
    print("\n管理會議參與者可用的 AI 模型。")
    print("\n指令：")
    print("  v - 檢視目前模型")
    print("  a - 新增自訂模型")
    print("  r - 移除模型")
    print("  d - 重設為預設值")
    print("  s - 儲存並繼續")
    print("  q - 取消變更\n")

    while True:
        cmd = input("指令：").strip().lower()

        if cmd == 'v':
            display_models(models)
        elif cmd == 'a':
            models = add_model_interactive(models)
        elif cmd == 'r':
            models = remove_model_interactive(models)
        elif cmd == 'd':
            models = DEFAULT_MODELS.copy()
            print("  ✓ 已重設為預設模型")
            display_models(models)
        elif cmd == 's':
            if not models:
                print("  ❌ 無法儲存空的模型清單。請至少新增一個模型。")
                continue
            print(f"\n  ✓ 已儲存 {len(models)} 個模型\n")
            return models
        elif cmd == 'q':
            print("\n  已取消模型變更。\n")
            return current_models if current_models else DEFAULT_MODELS.copy()
        else:
            print("  ❌ 未知的指令。請使用：v、a、r、d、s 或 q")


def get_default_models() -> list[str]:
    """Get default model list.

    Returns:
        List of default model names
    """
    return DEFAULT_MODELS.copy()
