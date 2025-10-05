"""Policy Watcher agent turning policy flashes into actionable insights."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from typing import Iterable, Mapping, MutableMapping, Sequence

from src.data_providers import IngestionResult
from src.pipelines.executor import PipelineContext

from .base import Agent, AgentReport

__all__ = ["PolicyWatcherAgent"]


class PolicyWatcherAgent(Agent):
    """Summarise policy flashes and related sentiment signals."""

    DEFAULT_TASKS: Sequence[str] = (
        "policy_flash_alerts",
        "news_sentiment_hourly",
    )

    def __init__(self, tracked_tasks: Sequence[str] | None = None, *, top_events: int = 5) -> None:
        self._tracked_tasks = tuple(tracked_tasks or self.DEFAULT_TASKS)
        self._top_events = max(1, int(top_events))

    def generate_report(
        self, context: Mapping[str, object] | Iterable[tuple[str, object]]
    ) -> AgentReport:
        results = self._collect_results(context)
        events = self._collect_policy_events(results.get("policy_flash_alerts"))
        sentiment = self._collect_sentiment(results.get("news_sentiment_hourly"))
        metrics = self._build_metrics(events, sentiment)
        highlights = self._build_highlights(events, sentiment)
        metadata = {
            "source_tasks": tuple(results.keys()),
            "event_count": len(events),
            "symbols_tracked": tuple(sorted(sentiment)) if sentiment else (),
        }
        return AgentReport(
            title="政策速览巡航",
            highlights=highlights,
            metrics=metrics,
            policy_events=events[: self._top_events],
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
    # Policy event extraction
    # ------------------------------------------------------------------
    def _collect_policy_events(
        self, result: IngestionResult | None
    ) -> list[dict[str, object]]:
        if result is None:
            return []
        events_with_ts: list[tuple[datetime, dict[str, object]]] = []
        for row in result.payload:
            title = row.get("title")
            if not title:
                continue
            timestamp = row.get("timestamp")
            parsed_ts = self._parse_timestamp(timestamp)
            impact = (row.get("impact") or "neutral").lower()
            related = tuple(row.get("related", []))
            events_with_ts.append(
                (
                    parsed_ts,
                    {
                        "timestamp": timestamp,
                        "title": title,
                        "impact": impact,
                        "related": related,
                        "summary": row.get("summary"),
                    },
                )
            )
        events_with_ts.sort(key=lambda item: item[0], reverse=True)
        return [event for _, event in events_with_ts]

    # ------------------------------------------------------------------
    # Sentiment aggregation
    # ------------------------------------------------------------------
    def _collect_sentiment(
        self, result: IngestionResult | None
    ) -> dict[str, float]:
        if result is None:
            return {}
        totals: dict[str, list[float]] = defaultdict(list)
        for row in result.payload:
            symbol = row.get("symbol")
            sentiment = row.get("sentiment")
            if not symbol or not isinstance(sentiment, (int, float)):
                continue
            totals[str(symbol)].append(float(sentiment))
        averages: dict[str, float] = {}
        for symbol, values in totals.items():
            averages[symbol] = sum(values) / len(values)
        return averages

    # ------------------------------------------------------------------
    # Metrics & highlights
    # ------------------------------------------------------------------
    def _build_metrics(
        self,
        events: Sequence[Mapping[str, object]],
        sentiment: Mapping[str, float],
    ) -> list[dict[str, object]]:
        metrics: list[dict[str, object]] = []
        if events:
            impact_counts = Counter(event.get("impact", "neutral") for event in events)
            impact_label = {
                "positive": "正面事件数量",
                "negative": "负面事件数量",
                "neutral": "中性事件数量",
            }
            for impact, label in impact_label.items():
                count = impact_counts.get(impact, 0)
                metrics.append(
                    {
                        "indicator": label,
                        "latest": f"{count} 条",
                        "trend": "rising" if impact == "positive" else "falling" if impact == "negative" else "stable",
                        "change_display": "-",
                    }
                )
            theme_counter: Counter[str] = Counter()
            for event in events:
                theme_counter.update(event.get("related", ()))
            for theme, count in theme_counter.most_common(3):
                metrics.append(
                    {
                        "indicator": f"主题热度：{theme}",
                        "latest": f"提及 {count} 次",
                        "trend": "rising",
                        "change_display": "-",
                    }
                )
        if sentiment:
            for symbol, score in sorted(sentiment.items(), key=lambda item: item[1], reverse=True):
                metrics.append(
                    {
                        "indicator": f"情绪评分 {symbol}",
                        "latest": f"{score:+.2f}",
                        "trend": "rising" if score >= 0 else "falling",
                        "change_display": "-",
                    }
                )
        return metrics

    def _build_highlights(
        self,
        events: Sequence[Mapping[str, object]],
        sentiment: Mapping[str, float],
    ) -> list[str]:
        highlights: list[str] = []
        if events:
            total = len(events)
            impact_counts = Counter(event.get("impact", "neutral") for event in events)
            positive = impact_counts.get("positive", 0)
            negative = impact_counts.get("negative", 0)
            neutral = impact_counts.get("neutral", 0)
            highlights.append(
                f"最近捕捉到 {total} 条政策快讯，其中正面 {positive} 条、负面 {negative} 条、中性 {neutral} 条。"
            )
            theme_counter: Counter[str] = Counter()
            for event in events:
                theme_counter.update(event.get("related", ()))
            if theme_counter:
                top_themes = ", ".join(theme for theme, _ in theme_counter.most_common(3))
                highlights.append(f"高频涉及主题：{top_themes}。")
        else:
            highlights.append("当前窗口内未捕捉到新的政策快讯。")

        if sentiment:
            sorted_symbols = sorted(sentiment.items(), key=lambda item: item[1], reverse=True)
            top_symbol, top_score = sorted_symbols[0]
            highlights.append(
                f"新闻情绪显示 {top_symbol} 平均得分 {top_score:+.2f}，整体情绪呈{'偏多' if top_score >= 0 else '偏空'}走势。"
            )
            if len(sorted_symbols) > 1:
                bottom_symbol, bottom_score = sorted_symbols[-1]
                highlights.append(
                    f"相对偏弱的标的为 {bottom_symbol}（{bottom_score:+.2f}）。"
                )
        return highlights

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
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
