"""Macro Sentinel agent turning ingestion outputs into actionable signals."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Iterable, Mapping, MutableMapping, Sequence

from src.data_providers import IngestionResult
from src.pipelines.executor import PipelineContext

from .base import Agent, AgentReport

__all__ = ["MacroSentinelAgent"]


class MacroSentinelAgent(Agent):
    """Summarise macro indicators and policy events for quick review."""

    DEFAULT_TASKS: Sequence[str] = (
        "macro_indicators_daily",
        "macro_monthly_statistical",
        "policy_flash_alerts",
    )

    def __init__(self, tracked_tasks: Sequence[str] | None = None) -> None:
        self._tracked_tasks = tuple(tracked_tasks or self.DEFAULT_TASKS)

    def generate_report(
        self, context: Mapping[str, object] | Iterable[tuple[str, object]]
    ) -> AgentReport:
        results = self._collect_results(context)
        metrics = self._build_metrics(results)
        policy_events = self._collect_policy_events(results)
        highlights = self._format_highlights(metrics, policy_events)
        metadata = {"source_tasks": tuple(results.keys())}
        return AgentReport(
            title="宏观巡检快照",
            highlights=highlights,
            metrics=metrics,
            policy_events=policy_events,
            metadata=metadata,
        )

    # ------------------------------------------------------------------
    # Result collection helpers
    # ------------------------------------------------------------------
    def _collect_results(
        self, context: Mapping[str, object] | Iterable[tuple[str, object]]
    ) -> MutableMapping[str, IngestionResult]:
        if isinstance(context, PipelineContext):
            pool = context.state
        elif isinstance(context, Mapping):
            pool = context
        else:
            pool = dict(context)
        collected: MutableMapping[str, IngestionResult] = {}
        for task_id in self._tracked_tasks:
            result = pool.get(task_id) if hasattr(pool, "get") else None
            if isinstance(result, IngestionResult):
                collected[task_id] = result
        return collected

    # ------------------------------------------------------------------
    # Metric extraction
    # ------------------------------------------------------------------
    def _build_metrics(
        self, results: Mapping[str, IngestionResult]
    ) -> list[dict[str, object]]:
        metrics: list[dict[str, object]] = []
        macro_daily = results.get("macro_indicators_daily")
        if macro_daily is not None:
            metrics.extend(
                self._extract_indicator_series(
                    macro_daily.payload,
                    dataset="macro_indicators_daily",
                    period_key="date",
                )
            )
        macro_stat = results.get("macro_monthly_statistical")
        if macro_stat is not None:
            metrics.extend(
                self._extract_indicator_series(
                    macro_stat.payload,
                    dataset="macro_monthly_statistical",
                    period_key="month",
                )
            )
        return metrics

    def _extract_indicator_series(
        self,
        records: Sequence[Mapping[str, object]],
        *,
        dataset: str,
        period_key: str,
    ) -> list[dict[str, object]]:
        grouped: dict[str, list[tuple[str, float]]] = defaultdict(list)
        for row in records:
            indicator = str(row.get("indicator")) if row.get("indicator") else None
            value = row.get("value")
            period = row.get(period_key) or row.get("date") or row.get("month")
            if not indicator or not isinstance(value, (int, float)) or not period:
                continue
            grouped[indicator].append((str(period), float(value)))

        metrics: list[dict[str, object]] = []
        for indicator, points in grouped.items():
            points.sort(key=lambda item: self._parse_period(item[0]))
            latest_period, latest_value = points[-1]
            metric: dict[str, object] = {
                "indicator": indicator,
                "latest": self._format_number(latest_value),
                "latest_raw": latest_value,
                "period": latest_period,
                "dataset": dataset,
                "trend": "stable",
                "change_display": "-",
            }
            if len(points) > 1:
                prev_period, prev_value = points[-2]
                delta = latest_value - prev_value
                metric["previous"] = self._format_number(prev_value)
                metric["previous_raw"] = prev_value
                metric["previous_period"] = prev_period
                metric["delta"] = delta
                metric["trend"] = self._trend_label(delta)
                if prev_value:
                    change_pct = delta / abs(prev_value) * 100
                    metric["change_pct"] = change_pct
                    metric["change_display"] = f"{change_pct:+.2f}%"
                else:
                    metric["change_display"] = self._format_number(delta, signed=True)
                if delta == 0:
                    metric["change_display"] = "+0.00%"
            metrics.append(metric)
        return metrics

    # ------------------------------------------------------------------
    # Highlight formatting
    # ------------------------------------------------------------------
    def _format_highlights(
        self,
        metrics: Sequence[Mapping[str, object]],
        policy_events: Sequence[Mapping[str, object]],
    ) -> list[str]:
        messages: list[str] = []
        for metric in metrics:
            indicator = metric.get("indicator", "-")
            latest = metric.get("latest", "-")
            period = metric.get("period", "-")
            trend = metric.get("trend", "stable")
            change = metric.get("change_display", "-")
            previous_period = metric.get("previous_period")
            direction = {"rising": "上升", "falling": "下降", "stable": "持平"}.get(
                str(trend), "变化不大"
            )
            if previous_period:
                message = (
                    f"{indicator} 最新值 {latest}（{period}），较 {previous_period} {direction} {change}。"
                )
            else:
                message = f"{indicator} 最新值 {latest}（{period}），缺少对比历史值。"
            if indicator.upper() == "PMI" and isinstance(metric.get("latest_raw"), (int, float)):
                latest_value = metric.get("latest_raw")
                if latest_value and latest_value >= 50:
                    message += " PMI 高于荣枯线，制造业景气度延续扩张。"
                elif latest_value and latest_value < 50:
                    message += " PMI 低于荣枯线，制造业景气度承压。"
            messages.append(message)
        if policy_events:
            policy_summary = "；".join(
                f"{event.get('title')}（影响：{event.get('impact')}）"
                for event in policy_events
                if event.get("title")
            )
            if policy_summary:
                messages.append(f"政策快讯焦点：{policy_summary}。")
        return messages

    # ------------------------------------------------------------------
    # Policy events
    # ------------------------------------------------------------------
    def _collect_policy_events(
        self, results: Mapping[str, IngestionResult]
    ) -> list[dict[str, object]]:
        policy_result = results.get("policy_flash_alerts")
        if policy_result is None:
            return []
        events = [
            {
                "timestamp": row.get("timestamp"),
                "title": row.get("title"),
                "impact": row.get("impact") or "未知",
                "related": tuple(row.get("related", [])),
            }
            for row in policy_result.payload
            if row.get("title")
        ]
        events.sort(key=lambda item: self._parse_timestamp(item.get("timestamp")), reverse=True)
        return events[:3]

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    @staticmethod
    def _parse_period(value: str) -> datetime:
        for fmt in ("%Y-%m-%d", "%Y-%m"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return datetime.min

    @staticmethod
    def _parse_timestamp(value: str | None) -> datetime:
        if not value:
            return datetime.min
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M"):
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
        return datetime.min

    @staticmethod
    def _format_number(value: float, *, signed: bool = False) -> str:
        fmt = "+,.2f" if signed else ",.2f"
        if abs(value) >= 100:
            fmt = "+,.0f" if signed else ",.0f"
        formatted = format(value, fmt)
        return formatted.replace(",", "_") if "e" in formatted.lower() else formatted

    @staticmethod
    def _trend_label(delta: float) -> str:
        if delta > 0:
            return "rising"
        if delta < 0:
            return "falling"
        return "stable"
