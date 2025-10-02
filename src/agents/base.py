"""Shared interfaces and helpers for analysis agents."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Iterable, Mapping, Sequence

__all__ = ["Agent", "AgentReport"]


@dataclass(slots=True)
class AgentReport:
    """Structured representation of an agent's analytical output."""

    title: str
    highlights: Sequence[str]
    metrics: Sequence[Mapping[str, object]] = field(default_factory=tuple)
    policy_events: Sequence[Mapping[str, object]] = field(default_factory=tuple)
    metadata: Mapping[str, object] | None = None

    def to_markdown(self) -> str:
        """Render the report as a Markdown document for preview/export."""

        lines = [f"# {self.title}"]
        if self.highlights:
            lines.append("\n## 关键结论")
            lines.extend(f"- {item}" for item in self.highlights)
        if self.metrics:
            lines.append("\n## 指标速览")
            header = "| 指标 | 最新值 | 对比期 | 变化 | 趋势 |"
            separator = "| --- | --- | --- | --- | --- |"
            lines.extend([header, separator])
            for metric in self.metrics:
                latest = metric.get("latest")
                previous_period = metric.get("previous_period", "-")
                previous_value = metric.get("previous", "-")
                change = metric.get("change_display", "-")
                row = "| {indicator} | {latest} | {prev_period}（{prev_value}） | {change} | {trend} |".format(
                    indicator=metric.get("indicator", "-"),
                    latest=latest,
                    prev_period=previous_period,
                    prev_value=previous_value,
                    change=change,
                    trend=metric.get("trend", "-"),
                )
                lines.append(row)
        if self.policy_events:
            lines.append("\n## 政策与事件")
            for event in self.policy_events:
                timestamp = event.get("timestamp", "")
                title = event.get("title", "")
                impact = event.get("impact", "")
                lines.append(f"- [{timestamp}] {title}（影响：{impact}）")
        return "\n".join(lines)


class Agent(ABC):
    """Interface implemented by all analysis agents."""

    @abstractmethod
    def generate_report(self, context: Mapping[str, object] | Iterable[tuple[str, object]]) -> AgentReport:
        """Produce a structured report from the provided execution context."""

