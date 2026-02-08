from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import ParticipantConfig, RelevanceResult


def format_participant_label(participant: ParticipantConfig) -> str:
    """格式化參與者標籤為 'Name（Role, Model）' 格式。"""
    return f"{participant.name}（{participant.role}, {participant.model}）"


def build_participant_labels(
    participants: list[ParticipantConfig],
) -> dict[str, str]:
    """為所有參與者建立 name→label 映射字典。"""
    return {p.name: format_participant_label(p) for p in participants}


def sort_speakers(results: list[RelevanceResult]) -> list[RelevanceResult]:
    """過濾想發言的參與者並按優先級排序。"""
    return sorted(
        [r for r in results if r.wants_to_speak],
        key=lambda r: r.priority,
    )


def format_relevance_result(
    result: RelevanceResult, label_func: Callable[[str], str], prefix: str = ""
) -> str:
    """格式化相關性檢查結果為日誌字串。

    Args:
        result: 相關性檢查結果
        label_func: 將參與者名稱轉換為顯示標籤的函數
        prefix: 可選的行前綴（例如 "  ↳ " 用於縮排）

    Returns:
        格式化的日誌字串
    """
    tag = "YES" if result.wants_to_speak else "NO"
    label = label_func(result.participant_name)
    return f"{prefix}[{label}] {tag}: {result.summary}"
