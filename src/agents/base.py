"""Shared interfaces and helpers for analysis agents."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from html import escape
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

    def to_html(self) -> str:
        """Render the report as a simple HTML document."""

        def _esc(value: object) -> str:
            return escape(str(value)) if value is not None else ""

        parts = [
            "<!DOCTYPE html>",
            '<html lang="zh-CN">',
            "<head>",
            "<meta charset=\"utf-8\">",
            f"<title>{_esc(self.title)}</title>",
            "<style>body{font-family:'Noto Sans SC',system-ui,sans-serif;margin:2rem;background-color:#f8fafc;color:#0f172a;}",
            "h1{margin-bottom:1rem;font-size:2rem;}",
            "h2{margin-top:2rem;font-size:1.25rem;color:#1e293b;}",
            "ul{padding-left:1.2rem;}",
            "table{border-collapse:collapse;width:100%;max-width:960px;margin-top:1rem;background:#fff;box-shadow:0 1px 3px rgba(15,23,42,0.1);}"
            "th,td{border:1px solid #e2e8f0;padding:0.6rem;text-align:left;font-size:0.95rem;}",
            "th{background-color:#f1f5f9;color:#0f172a;font-weight:600;}",
            "tr:nth-child(even){background-color:#f8fafc;}",
            ".highlight{background:#fff;padding:1rem;border-left:4px solid #2563eb;margin-bottom:0.5rem;}",
            ".bad{color:#dc2626;}.good{color:#16a34a;}.neutral{color:#334155;}",
            "footer{margin-top:2rem;font-size:0.85rem;color:#64748b;}",
            "</style>",
            "</head>",
            "<body>",
            f"<header><h1>{_esc(self.title)}</h1></header>",
        ]

        if self.highlights:
            parts.append("<section><h2>关键结论</h2>")
            for item in self.highlights:
                parts.append(f"<div class=\"highlight\">{_esc(item)}</div>")
            parts.append("</section>")

        if self.metrics:
            parts.append("<section><h2>指标速览</h2>")
            parts.append(
                "<table><thead><tr><th>指标</th><th>最新值</th><th>对比期</th><th>变化</th><th>趋势</th></tr></thead><tbody>"
            )
            for metric in self.metrics:
                indicator = _esc(metric.get("indicator", "-"))
                latest = _esc(metric.get("latest", "-"))
                prev_period = _esc(metric.get("previous_period", "-"))
                prev_value = _esc(metric.get("previous", "-"))
                change_display = _esc(metric.get("change_display", "-"))
                trend = str(metric.get("trend", "neutral"))
                trend_class = "good" if trend == "rising" else "bad" if trend == "falling" else "neutral"
                parts.append(
                    "<tr><td>{indicator}</td><td>{latest}</td><td>{prev_period}（{prev_value}）</td>"
                    "<td>{change}</td><td class=\"{trend_class}\">{trend}</td></tr>".format(
                        indicator=indicator,
                        latest=latest,
                        prev_period=prev_period,
                        prev_value=prev_value,
                        change=change_display,
                        trend=escape(trend),
                        trend_class=trend_class,
                    )
                )
            parts.append("</tbody></table></section>")

        if self.policy_events:
            parts.append("<section><h2>政策与事件</h2><ul>")
            for event in self.policy_events:
                timestamp = _esc(event.get("timestamp", ""))
                title = _esc(event.get("title", ""))
                impact = _esc(event.get("impact", ""))
                parts.append(
                    f"<li><strong>{timestamp}</strong> — {title} <span class=\"neutral\">(影响：{impact})</span></li>"
                )
            parts.append("</ul></section>")

        if self.metadata:
            parts.append("<footer>")
            source_tasks = self.metadata.get("source_tasks")
            if source_tasks:
                parts.append(
                    "<div>数据来源任务：{sources}</div>".format(
                        sources=_esc(", ".join(map(str, source_tasks)))
                    )
                )
            parts.append("</footer>")

        parts.extend(["</body>", "</html>"])
        return "".join(parts)


class Agent(ABC):
    """Interface implemented by all analysis agents."""

    @abstractmethod
    def generate_report(self, context: Mapping[str, object] | Iterable[tuple[str, object]]) -> AgentReport:
        """Produce a structured report from the provided execution context."""

