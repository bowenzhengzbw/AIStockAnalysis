"""Industry Mapper agent turning sector datasets into actionable signals."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Iterable, Mapping, MutableMapping, Sequence

from src.data_providers import IngestionResult
from src.pipelines.executor import PipelineContext

from .base import Agent, AgentReport

__all__ = ["IndustryMapperAgent"]


class IndustryMapperAgent(Agent):
    """Aggregate景气、资金与主题热度，输出行业雷达报告。"""

    CLIMATE_TASK = "industry_climate_monthly"
    FLOW_TASK = "industry_capital_flow_daily"
    THEME_TASK = "theme_heat_daily"
    POLICY_TASK = "policy_flash_alerts"

    def __init__(
        self,
        *,
        top_industries: int = 3,
        top_themes: int = 2,
    ) -> None:
        self._top_industries = max(1, int(top_industries))
        self._top_themes = max(1, int(top_themes))

    def generate_report(
        self, context: Mapping[str, object] | Iterable[tuple[str, object]]
    ) -> AgentReport:
        results = self._collect_results(context)
        profiles = self._build_industry_profiles(
            results.get(self.CLIMATE_TASK), results.get(self.FLOW_TASK)
        )
        themes = self._build_theme_signals(results.get(self.THEME_TASK))
        policy_events = self._select_policy_events(
            results.get(self.POLICY_TASK), {item["industry"] for item in profiles}
        )
        metrics = self._assemble_metrics(profiles, themes)
        highlights = self._build_highlights(profiles, themes, policy_events)
        metadata = {
            "source_tasks": tuple(results.keys()),
            "top_industries": tuple(item["industry"] for item in profiles),
            "top_themes": tuple(item["theme"] for item in themes),
        }
        return AgentReport(
            title="行业景气雷达",
            highlights=highlights,
            metrics=metrics,
            policy_events=policy_events,
            metadata=metadata,
        )

    # ------------------------------------------------------------------
    # Result helpers
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
        for task_id in (
            self.CLIMATE_TASK,
            self.FLOW_TASK,
            self.THEME_TASK,
            self.POLICY_TASK,
        ):
            result = pool.get(task_id) if hasattr(pool, "get") else None
            if isinstance(result, IngestionResult):
                collected[task_id] = result
        return collected

    # ------------------------------------------------------------------
    # Profile builders
    # ------------------------------------------------------------------
    def _build_industry_profiles(
        self,
        climate_result: IngestionResult | None,
        flow_result: IngestionResult | None,
    ) -> list[dict[str, object]]:
        climate_series: dict[str, list[tuple[str, float]]] = defaultdict(list)
        if climate_result is not None:
            for row in climate_result.payload:
                industry = str(row.get("industry")) if row.get("industry") else None
                score = row.get("score")
                period = row.get("month") or row.get("date")
                if industry and isinstance(score, (int, float)) and period:
                    climate_series[industry].append((str(period), float(score)))

        flow_series: dict[str, list[tuple[str, float]]] = defaultdict(list)
        if flow_result is not None:
            for row in flow_result.payload:
                industry = str(row.get("industry")) if row.get("industry") else None
                net_flow = row.get("net_flow")
                date = row.get("date")
                if industry and isinstance(net_flow, (int, float)) and date:
                    flow_series[industry].append((str(date), float(net_flow)))

        profiles: list[dict[str, object]] = []
        for industry, points in climate_series.items():
            points.sort(key=lambda item: self._parse_period(item[0]))
            latest_period, latest_value = points[-1]
            profile: dict[str, object] = {
                "industry": industry,
                "climate_latest": latest_value,
                "climate_period": latest_period,
            }
            if len(points) > 1:
                prev_period, prev_value = points[-2]
                delta = latest_value - prev_value
                profile.update(
                    {
                        "climate_previous": prev_value,
                        "climate_previous_period": prev_period,
                        "climate_change": delta,
                        "climate_trend": self._trend_label(delta),
                    }
                )
                if prev_value:
                    profile["climate_change_pct"] = delta / abs(prev_value) * 100

            flow_points = flow_series.get(industry)
            if flow_points:
                flow_points.sort(key=lambda item: self._parse_date(item[0]))
                flow_date, flow_value = flow_points[-1]
                profile.update(
                    {
                        "flow_latest": flow_value,
                        "flow_date": flow_date,
                    }
                )
                if len(flow_points) > 1:
                    prev_flow_date, prev_flow_value = flow_points[-2]
                    flow_delta = flow_value - prev_flow_value
                    profile.update(
                        {
                            "flow_previous": prev_flow_value,
                            "flow_previous_date": prev_flow_date,
                            "flow_change": flow_delta,
                            "flow_trend": self._trend_label(flow_delta),
                        }
                    )

            profiles.append(profile)

        profiles.sort(
            key=lambda item: (
                abs(item.get("climate_change", 0.0)),
                item.get("climate_latest", 0.0),
            ),
            reverse=True,
        )
        return profiles[: self._top_industries]

    def _build_theme_signals(
        self, theme_result: IngestionResult | None
    ) -> list[dict[str, object]]:
        if theme_result is None:
            return []

        series: dict[str, list[tuple[str, float, float | None]]] = defaultdict(list)
        for row in theme_result.payload:
            theme = str(row.get("theme")) if row.get("theme") else None
            heat = row.get("heat")
            date = row.get("date")
            attention_change = row.get("attention_change")
            if theme and isinstance(heat, (int, float)) and date:
                series[theme].append((str(date), float(heat), self._to_float(attention_change)))

        signals: list[dict[str, object]] = []
        for theme, points in series.items():
            points.sort(key=lambda item: self._parse_date(item[0]))
            latest_date, latest_heat, latest_attention = points[-1]
            signal: dict[str, object] = {
                "theme": theme,
                "heat_latest": latest_heat,
                "heat_date": latest_date,
                "attention_change": latest_attention,
            }
            if len(points) > 1:
                prev_date, prev_heat, _ = points[-2]
                delta = latest_heat - prev_heat
                signal.update(
                    {
                        "heat_previous": prev_heat,
                        "heat_previous_date": prev_date,
                        "heat_change": delta,
                        "heat_trend": self._trend_label(delta),
                    }
                )
            signals.append(signal)

        signals.sort(
            key=lambda item: (
                item.get("heat_change", 0.0),
                item.get("attention_change", 0.0) or 0.0,
            ),
            reverse=True,
        )
        return signals[: self._top_themes]

    def _select_policy_events(
        self,
        policy_result: IngestionResult | None,
        focus_industries: Sequence[str],
    ) -> list[dict[str, object]]:
        if policy_result is None:
            return []
        focus = {str(item) for item in focus_industries if item}
        events: list[dict[str, object]] = []
        for row in policy_result.payload:
            related = {str(tag) for tag in row.get("related", [])}
            if focus and not (focus & related):
                continue
            events.append(
                {
                    "timestamp": row.get("timestamp"),
                    "title": row.get("title"),
                    "impact": row.get("impact") or "未知",
                    "related": tuple(related) or tuple(row.get("related", [])),
                }
            )

        events.sort(
            key=lambda item: self._parse_timestamp(item.get("timestamp")), reverse=True
        )
        return events[:3]

    # ------------------------------------------------------------------
    # Report assembly
    # ------------------------------------------------------------------
    def _assemble_metrics(
        self,
        profiles: Sequence[Mapping[str, object]],
        themes: Sequence[Mapping[str, object]],
    ) -> list[dict[str, object]]:
        metrics: list[dict[str, object]] = []
        for profile in profiles:
            industry = profile.get("industry", "-")
            metrics.append(
                {
                    "indicator": f"{industry} 景气指数",
                    "latest": self._format_number(profile.get("climate_latest")),
                    "latest_raw": profile.get("climate_latest"),
                    "period": profile.get("climate_period"),
                    "previous": self._format_number(profile.get("climate_previous")),
                    "previous_period": profile.get("climate_previous_period"),
                    "change_display": self._format_change(profile.get("climate_change")),
                    "trend": profile.get("climate_trend", "stable"),
                    "dataset": self.CLIMATE_TASK,
                }
            )
            if profile.get("flow_latest") is not None:
                metrics.append(
                    {
                        "indicator": f"{industry} 主力净流入",
                        "latest": self._format_currency(profile.get("flow_latest")),
                        "latest_raw": profile.get("flow_latest"),
                        "period": profile.get("flow_date"),
                        "previous": self._format_currency(profile.get("flow_previous")),
                        "previous_period": profile.get("flow_previous_date"),
                        "change_display": self._format_currency(
                            profile.get("flow_change"), signed=True
                        ),
                        "trend": profile.get("flow_trend", "stable"),
                        "dataset": self.FLOW_TASK,
                    }
                )

        for theme in themes:
            metrics.append(
                {
                    "indicator": f"{theme.get('theme', '-') } 主题热度",
                    "latest": self._format_number(theme.get("heat_latest")),
                    "latest_raw": theme.get("heat_latest"),
                    "period": theme.get("heat_date"),
                    "previous": self._format_number(theme.get("heat_previous")),
                    "previous_period": theme.get("heat_previous_date"),
                    "change_display": self._format_change(theme.get("heat_change")),
                    "trend": theme.get("heat_trend", "stable"),
                    "dataset": self.THEME_TASK,
                }
            )
        return metrics

    def _build_highlights(
        self,
        profiles: Sequence[Mapping[str, object]],
        themes: Sequence[Mapping[str, object]],
        policy_events: Sequence[Mapping[str, object]],
    ) -> list[str]:
        messages: list[str] = []
        for profile in profiles:
            industry = profile.get("industry", "行业")
            latest = self._format_number(profile.get("climate_latest"))
            period = profile.get("climate_period", "最新")
            change = self._format_change(profile.get("climate_change"))
            flow = self._format_currency(profile.get("flow_latest"))
            message = (
                f"{industry} 景气指数 {latest}（{period}），环比 {change}；"
                f"主力净流入 {flow}。"
            )
            messages.append(message)

        if themes:
            theme_summary = "；".join(
                f"{item.get('theme')} 热度 {self._format_number(item.get('heat_latest'))}"
                for item in themes
                if item.get("theme")
            )
            if theme_summary:
                messages.append(f"热门主题跟踪：{theme_summary}。")

        if policy_events:
            policy_summary = "；".join(
                f"{event.get('title')}（影响：{event.get('impact')}）"
                for event in policy_events
                if event.get("title")
            )
            if policy_summary:
                messages.append(f"政策脉冲聚焦：{policy_summary}。")

        return messages

    # ------------------------------------------------------------------
    # Formatting helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _parse_period(value: str | None) -> datetime:
        if not value:
            return datetime.min
        for fmt in ("%Y-%m", "%Y-%m-%d", "%Y%m%d"):
            try:
                return datetime.strptime(value, fmt)
            except (TypeError, ValueError):
                continue
        return datetime.min

    @staticmethod
    def _parse_date(value: str | None) -> datetime:
        if not value:
            return datetime.min
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d"):
            try:
                return datetime.strptime(value, fmt)
            except (TypeError, ValueError):
                continue
        return datetime.min

    @staticmethod
    def _parse_timestamp(value: str | None) -> datetime:
        if not value:
            return datetime.min
        for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.strptime(value, fmt)
            except (TypeError, ValueError):
                continue
        return datetime.min

    @staticmethod
    def _trend_label(delta: float | None) -> str:
        if delta is None:
            return "stable"
        if delta > 0:
            return "rising"
        if delta < 0:
            return "falling"
        return "stable"

    @staticmethod
    def _format_number(value: object) -> str:
        if value is None:
            return "-"
        if isinstance(value, (int, float)):
            if abs(value) >= 100:
                return f"{value:.1f}"
            return f"{value:.2f}"
        return str(value)

    @staticmethod
    def _format_currency(value: object, *, signed: bool = False) -> str:
        if value is None:
            return "-"
        if isinstance(value, (int, float)):
            num = value / 1e8
            sign = "+" if signed and num >= 0 else "" if not signed else ""
            return f"{sign}{num:.2f} 亿"
        return str(value)

    @staticmethod
    def _format_change(value: object) -> str:
        if value is None:
            return "0.00"
        if isinstance(value, (int, float)):
            return f"{value:+.2f}"
        return str(value)

    @staticmethod
    def _to_float(value: object | None) -> float | None:
        if isinstance(value, (int, float)):
            return float(value)
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None
