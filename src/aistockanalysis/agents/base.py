"""Base classes and utilities for AI agents."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, Protocol


class Agent(Protocol):
    """Protocol for agent implementations."""

    name: str

    def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Return structured analysis result."""


@dataclass
class AgentResult:
    """Unified agent response structure."""

    name: str
    summary: str
    metrics: Dict[str, float]
    insights: Dict[str, Any]


def safe_float(value: Any, default: float = 0.0) -> float:
    """Convert a value to float with graceful fallback.

    Financial datasets经常包含 ``None``、空字符串或 ``NaN`` 等异常值。
    直接 ``float(value)`` 会抛出 ``TypeError``/``ValueError``，导致
    agent 链路中断。该辅助函数统一处理这些情况，确保返回有限的浮点数。

    Args:
        value: 任意待转换对象。
        default: 转换失败时返回的默认值。

    Returns:
        float: 安全可用的浮点数结果。
    """

    if value is None:
        return default

    # 布尔值在 ``float`` 中会转换为 0/1，符合常见语义。
    if isinstance(value, bool):
        return float(value)

    if isinstance(value, (int, float)):
        if isinstance(value, float) and not math.isfinite(value):
            return default
        return float(value)

    try:
        converted = float(value)
    except (TypeError, ValueError):
        return default

    if not math.isfinite(converted):
        return default

    return converted
