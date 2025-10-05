"""Risk Controller agent for summarising portfolio risk indicators."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Iterable, Mapping, MutableMapping, Sequence

from src.data_providers import IngestionResult
from src.pipelines.executor import PipelineContext

from .base import Agent, AgentReport

__all__ = ["RiskControllerAgent"]


class RiskControllerAgent(Agent):
    """Aggregate risk metrics, exposures, and alerts for oversight."""

    DEFAULT_TASKS: Sequence[str] = (
        "risk_metrics_daily",
        "risk_exposure_snapshot",
        "risk_alerts_daily",
    )

    def __init__(self, tracked_tasks: Sequence[str] | None = None) -> None:
        self._tracked_tasks = tuple(tracked_tasks or self.DEFAULT_TASKS)

    def generate_report(
        self, context: Mapping[str, object] | Iterable[tuple[str, object]]
    ) -> AgentReport:
        results = self._collect_results(context)
        metrics = self._build_metrics(results)
        alerts = self._collect_alerts(results)
        highlights = self._format_highlights(metrics, alerts)
        metadata = {"source_tasks": tuple(results.keys())}
        return AgentReport(
            title="组合风险雷达",
            highlights=highlights,
            metrics=metrics,
            policy_events=alerts,
            metadata=metadata,
        )

    # ------------------------------------------------------------------
    # Collection helpers
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
    # Metric construction
    # ------------------------------------------------------------------
    def _build_metrics(self, results: Mapping[str, IngestionResult]) -> list[dict[str, object]]:
        metrics: list[dict[str, object]] = []
        risk_metrics = results.get("risk_metrics_daily")
        if risk_metrics is not None:
            metrics.extend(self._normalize_risk_metrics(risk_metrics.payload))
        exposures = results.get("risk_exposure_snapshot")
        if exposures is not None:
            metrics.extend(self._normalize_risk_exposure(exposures.payload))
        return metrics

    def _normalize_risk_metrics(
        self, records: Sequence[Mapping[str, object]]
    ) -> list[dict[str, object]]:
        grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
        for row in records:
            metric = row.get("metric")
            if not metric:
                continue
            grouped[str(metric)].append(row)

        metrics: list[dict[str, object]] = []
        for indicator, rows in grouped.items():
            rows.sort(key=lambda item: str(item.get("date")))
            latest_row = rows[-1]
            latest_value = self._coerce_float(latest_row.get("value"))
            previous_value = self._coerce_float(latest_row.get("previous_value"))
            is_ratio = (latest_row.get("unit") or "").lower() == "ratio"

            metric: dict[str, object] = {
                "indicator": indicator,
                "latest": self._format_value(latest_value, is_ratio),
                "latest_raw": latest_value,
                "period": latest_row.get("date"),
                "dataset": "risk_metrics_daily",
                "trend": "stable",
                "change_display": "-",
                "is_percent": is_ratio,
            }

            previous_period = latest_row.get("previous_date")
            if previous_value is not None:
                metric["previous_raw"] = previous_value
                metric["previous"] = self._format_value(previous_value, is_ratio)
                metric["previous_period"] = previous_period or "前期"
                delta = (latest_value or 0.0) - previous_value
                metric["delta"] = delta
                metric["trend"] = self._trend_label(delta)
                metric["change_display"] = self._format_value(delta, is_ratio, signed=True)

            warning_upper = self._coerce_float(latest_row.get("warning_upper"))
            warning_lower = self._coerce_float(latest_row.get("warning_lower"))
            if warning_upper is not None:
                metric["warning_upper"] = warning_upper
            if warning_lower is not None:
                metric["warning_lower"] = warning_lower

            metrics.append(metric)
        return metrics

    def _normalize_risk_exposure(
        self, records: Sequence[Mapping[str, object]]
    ) -> list[dict[str, object]]:
        metrics: list[dict[str, object]] = []
        for row in records:
            indicator = row.get("metric")
            if not indicator:
                continue
            value = self._coerce_float(row.get("value"))
            previous_value = self._coerce_float(row.get("previous_value"))
            is_ratio = (row.get("unit") or "").lower() == "ratio"
            metric: dict[str, object] = {
                "indicator": str(indicator),
                "latest": self._format_value(value, is_ratio),
                "latest_raw": value,
                "dataset": "risk_exposure_snapshot",
                "period": row.get("date"),
                "trend": "stable",
                "change_display": "-",
                "is_percent": is_ratio,
            }
            if previous_value is not None:
                metric["previous_raw"] = previous_value
                metric["previous"] = self._format_value(previous_value, is_ratio)
                metric["previous_period"] = row.get("previous_period") or "前值"
                delta = (value or 0.0) - previous_value
                metric["delta"] = delta
                metric["trend"] = self._trend_label(delta)
                metric["change_display"] = self._format_value(delta, is_ratio, signed=True)

            direction = str(row.get("direction") or "")
            if direction:
                metric["limit_direction"] = direction
            limit = self._coerce_float(row.get("limit"))
            if limit is not None:
                metric["limit"] = limit
            lower_bound = self._coerce_float(row.get("lower_bound"))
            upper_bound = self._coerce_float(row.get("upper_bound"))
            if lower_bound is not None:
                metric["lower_bound"] = lower_bound
            if upper_bound is not None:
                metric["upper_bound"] = upper_bound

            metrics.append(metric)
        return metrics

    # ------------------------------------------------------------------
    # Alerts
    # ------------------------------------------------------------------
    def _collect_alerts(
        self, results: Mapping[str, IngestionResult]
    ) -> list[dict[str, object]]:
        alert_result = results.get("risk_alerts_daily")
        if alert_result is None:
            return []
        alerts: list[dict[str, object]] = []
        for row in alert_result.payload:
            title = row.get("title")
            if not title:
                continue
            alerts.append(
                {
                    "timestamp": row.get("timestamp"),
                    "title": title,
                    "impact": row.get("impact") or row.get("severity") or "info",
                    "detail": row.get("detail"),
                    "severity": row.get("severity"),
                }
            )
        alerts.sort(key=lambda item: self._parse_timestamp(item.get("timestamp")), reverse=True)
        return alerts

    # ------------------------------------------------------------------
    # Highlight formatting
    # ------------------------------------------------------------------
    def _format_highlights(
        self,
        metrics: Sequence[Mapping[str, object]],
        alerts: Sequence[Mapping[str, object]],
    ) -> list[str]:
        highlights: list[str] = []
        for metric in metrics:
            indicator = metric.get("indicator", "-")
            latest = metric.get("latest", "-")
            trend = str(metric.get("trend", "stable"))
            change = metric.get("change_display", "-")
            previous_period = metric.get("previous_period")
            if previous_period and change != "-":
                message = (
                    f"{indicator} 最新值 {latest}，较 {previous_period} {self._trend_message(trend)} {change}。"
                )
            elif previous_period:
                message = f"{indicator} 最新值 {latest}，较 {previous_period} 变化不大。"
            else:
                message = f"{indicator} 最新值 {latest}。"
            if message not in highlights:
                highlights.append(message)
            threshold_note = self._check_threshold(metric)
            if threshold_note and threshold_note not in highlights:
                highlights.append(threshold_note)

        if alerts:
            summary = "；".join(
                f"{alert.get('title')}（等级：{alert.get('impact')}）"
                for alert in alerts
                if alert.get("title")
            )
            if summary:
                highlights.append(f"风控提醒：{summary}。")

        return highlights[:8]

    def _check_threshold(self, metric: Mapping[str, object]) -> str | None:
        latest = self._coerce_float(metric.get("latest_raw"))
        if latest is None:
            return None
        is_ratio = bool(metric.get("is_percent"))
        indicator = metric.get("indicator", "风险指标")

        warning_upper = self._coerce_float(metric.get("warning_upper"))
        if warning_upper is not None and latest > warning_upper:
            return (
                f"{indicator} 已超过上限 {self._format_value(warning_upper, is_ratio)}，"
                "请及时降风险。"
            )
        warning_lower = self._coerce_float(metric.get("warning_lower"))
        if warning_lower is not None and latest < warning_lower:
            return (
                f"{indicator} 已跌破下限 {self._format_value(warning_lower, is_ratio)}，"
                "需评估潜在损失。"
            )

        direction = metric.get("limit_direction")
        limit = self._coerce_float(metric.get("limit"))
        if direction == "max" and limit is not None:
            if latest >= 0.95 * limit:
                return f"{indicator} 接近上限 {self._format_value(limit, is_ratio)}，当前为 {metric.get('latest')}。"
        if direction == "min" and limit is not None:
            if latest <= 1.05 * limit:
                return f"{indicator} 接近下限 {self._format_value(limit, is_ratio)}，当前为 {metric.get('latest')}。"
        if direction == "range":
            lower_bound = self._coerce_float(metric.get("lower_bound"))
            upper_bound = self._coerce_float(metric.get("upper_bound"))
            if lower_bound is not None and latest < lower_bound:
                return (
                    f"{indicator} 低于区间下限 {self._format_value(lower_bound, is_ratio)}，"
                    "请确认是否需要增配风险资产。"
                )
            if upper_bound is not None and latest > upper_bound:
                return (
                    f"{indicator} 高于区间上限 {self._format_value(upper_bound, is_ratio)}，"
                    "建议检查资金使用计划。"
                )
        return None

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _coerce_float(value: object) -> float | None:
        if isinstance(value, (int, float)):
            return float(value)
        try:
            return float(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _parse_timestamp(value: object) -> datetime:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                pass
        return datetime.min

    @staticmethod
    def _trend_label(delta: float) -> str:
        if delta > 0:
            return "rising"
        if delta < 0:
            return "falling"
        return "stable"

    @staticmethod
    def _trend_message(label: str) -> str:
        return {"rising": "上升", "falling": "下降", "stable": "持平"}.get(label, "变化不大")

    def _format_value(
        self,
        value: float | None,
        is_percent: bool,
        *,
        signed: bool = False,
    ) -> str:
        if value is None:
            return "-"
        if is_percent:
            formatted = f"{value * 100:.2f}%"
        else:
            formatted = f"{value:.2f}"
        if signed and not formatted.startswith(("+", "-")):
            formatted = ("+" if value >= 0 else "-") + formatted.lstrip("-+")
        return formatted
