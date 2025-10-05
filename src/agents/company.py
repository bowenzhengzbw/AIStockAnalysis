"""Company Analyst agent producing valuation and fundamentals snapshots."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Iterable, Mapping, MutableMapping, Sequence

from src.data_providers import IngestionResult
from src.pipelines.executor import PipelineContext

from .base import Agent, AgentReport

__all__ = ["CompanyAnalystAgent"]


class CompanyAnalystAgent(Agent):
    """Summarise core fundamentals, valuation, and news sentiment for key symbols."""

    FINANCIAL_TASK = "company_financials_quarterly"
    VALUATION_TASK = "company_valuation_daily"
    SENTIMENT_TASK = "news_sentiment_hourly"

    DEFAULT_SYMBOLS: Sequence[str] = ("600519.SH", "300750.SZ")

    def __init__(
        self,
        *,
        symbols: Sequence[str] | None = None,
        top_events: int = 3,
    ) -> None:
        self._symbols = tuple(symbols or self.DEFAULT_SYMBOLS)
        self._top_events = max(1, int(top_events))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def generate_report(
        self, context: Mapping[str, object] | Iterable[tuple[str, object]]
    ) -> AgentReport:
        results = self._collect_results(context)
        metrics: list[dict[str, object]] = []
        metrics.extend(self._build_financial_metrics(results.get(self.FINANCIAL_TASK)))
        metrics.extend(self._build_valuation_metrics(results.get(self.VALUATION_TASK)))
        events = self._build_events(results.get(self.SENTIMENT_TASK))
        highlights = self._build_highlights(metrics, events)
        metadata = {
            "source_tasks": tuple(results.keys()),
            "symbols": self._symbols,
        }
        return AgentReport(
            title="核心公司质地巡检",
            highlights=highlights,
            metrics=metrics,
            policy_events=events,
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
        for task in (self.FINANCIAL_TASK, self.VALUATION_TASK, self.SENTIMENT_TASK):
            result = pool.get(task) if hasattr(pool, "get") else None
            if isinstance(result, IngestionResult):
                collected[task] = result
        return collected

    # ------------------------------------------------------------------
    # Financial metrics
    # ------------------------------------------------------------------
    def _build_financial_metrics(
        self, result: IngestionResult | None
    ) -> list[dict[str, object]]:
        if result is None:
            return []

        grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
        for row in result.payload:
            symbol = str(row.get("symbol")) if row.get("symbol") else None
            if symbol and symbol in self._symbols:
                grouped[symbol].append(row)

        metrics: list[dict[str, object]] = []
        for symbol, rows in grouped.items():
            rows.sort(key=lambda item: self._parse_date(item.get("report_date")))
            latest = rows[-1]
            previous = rows[-2] if len(rows) > 1 else None

            metrics.append(
                self._build_metric(
                    indicator=f"{symbol} 营业收入",
                    latest=latest.get("revenue"),
                    previous=previous.get("revenue") if previous else None,
                    period=latest.get("report_date"),
                    previous_period=previous.get("report_date") if previous else None,
                    unit="亿元",
                    symbol=symbol,
                    metric_type="revenue",
                )
            )
            metrics.append(
                self._build_metric(
                    indicator=f"{symbol} 归母净利润",
                    latest=latest.get("net_profit"),
                    previous=previous.get("net_profit") if previous else None,
                    period=latest.get("report_date"),
                    previous_period=previous.get("report_date") if previous else None,
                    unit="亿元",
                    symbol=symbol,
                    metric_type="net_profit",
                )
            )
            metrics.append(
                self._build_metric(
                    indicator=f"{symbol} ROE",
                    latest=latest.get("roe"),
                    previous=previous.get("roe") if previous else None,
                    period=latest.get("report_date"),
                    previous_period=previous.get("report_date") if previous else None,
                    formatter=self._format_percent,
                    symbol=symbol,
                    metric_type="roe",
                )
            )
            metrics.append(
                self._build_metric(
                    indicator=f"{symbol} 毛利率",
                    latest=latest.get("gross_margin"),
                    previous=previous.get("gross_margin") if previous else None,
                    period=latest.get("report_date"),
                    previous_period=previous.get("report_date") if previous else None,
                    formatter=self._format_percent,
                    symbol=symbol,
                    metric_type="margin",
                )
            )
        return [metric for metric in metrics if metric]

    # ------------------------------------------------------------------
    # Valuation metrics
    # ------------------------------------------------------------------
    def _build_valuation_metrics(
        self, result: IngestionResult | None
    ) -> list[dict[str, object]]:
        if result is None:
            return []

        grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
        for row in result.payload:
            symbol = str(row.get("symbol")) if row.get("symbol") else None
            if symbol and symbol in self._symbols:
                grouped[symbol].append(row)

        metrics: list[dict[str, object]] = []
        for symbol, rows in grouped.items():
            rows.sort(key=lambda item: self._parse_date(item.get("date")))
            latest = rows[-1]
            previous = rows[-2] if len(rows) > 1 else None

            metrics.append(
                self._build_metric(
                    indicator=f"{symbol} PE(TTM)",
                    latest=latest.get("pe_ttm"),
                    previous=previous.get("pe_ttm") if previous else None,
                    period=latest.get("date"),
                    previous_period=previous.get("date") if previous else None,
                    formatter=lambda value: f"{value:.1f} 倍" if value is not None else "-",
                    symbol=symbol,
                    metric_type="pe",
                )
            )
            metrics.append(
                self._build_metric(
                    indicator=f"{symbol} PB",
                    latest=latest.get("pb"),
                    previous=previous.get("pb") if previous else None,
                    period=latest.get("date"),
                    previous_period=previous.get("date") if previous else None,
                    formatter=lambda value: f"{value:.1f} 倍" if value is not None else "-",
                    symbol=symbol,
                    metric_type="pb",
                )
            )
            metrics.append(
                self._build_metric(
                    indicator=f"{symbol} 股息率",
                    latest=latest.get("dividend_yield"),
                    previous=previous.get("dividend_yield") if previous else None,
                    period=latest.get("date"),
                    previous_period=previous.get("date") if previous else None,
                    formatter=self._format_percent,
                    symbol=symbol,
                    metric_type="dividend",
                )
            )
        return [metric for metric in metrics if metric]

    # ------------------------------------------------------------------
    # Event extraction
    # ------------------------------------------------------------------
    def _build_events(self, result: IngestionResult | None) -> list[dict[str, object]]:
        if result is None:
            return []

        events: list[dict[str, object]] = []
        for row in result.payload:
            symbol = str(row.get("symbol")) if row.get("symbol") else None
            if symbol not in self._symbols:
                continue
            sentiment = row.get("sentiment")
            if not isinstance(sentiment, (int, float)):
                continue
            impact = self._sentiment_label(sentiment)
            events.append(
                {
                    "timestamp": row.get("timestamp"),
                    "title": f"{symbol} 新闻情绪：{row.get('summary', '暂无摘要')}",
                    "impact": impact,
                    "symbol": symbol,
                    "score": sentiment,
                }
            )
        events.sort(key=lambda item: self._parse_date(item.get("timestamp")), reverse=True)
        return events[: self._top_events]

    # ------------------------------------------------------------------
    # Highlight helpers
    # ------------------------------------------------------------------
    def _build_highlights(
        self,
        metrics: Sequence[Mapping[str, object]],
        events: Sequence[Mapping[str, object]],
    ) -> list[str]:
        highlights: list[str] = []

        for metric in metrics:
            metric_type = metric.get("metric_type")
            if metric_type not in {"revenue", "net_profit", "pe"}:
                continue
            symbol = metric.get("symbol", "")
            indicator = metric.get("indicator", "")
            latest = metric.get("latest", "-")
            change = metric.get("change_display", "-")
            trend = metric.get("trend", "stable")
            direction = {
                "rising": "上升",
                "falling": "下降",
                "stable": "基本持平",
            }.get(str(trend), "变化不大")
            if metric_type == "pe":
                highlights.append(
                    f"{symbol} 估值 {latest}，相较前值{direction}{change}。"
                )
            else:
                highlights.append(
                    f"{indicator} 最新 {latest}，同比{direction}{change}。"
                )

        if events:
            summary = "；".join(
                f"{event.get('symbol', '')} {event.get('impact')} ({event.get('score', 0):+0.2f})"
                for event in events
            )
            highlights.append(f"重点情绪速览：{summary}。")

        return highlights or ["未获取到覆盖公司的最新财务或估值数据，请检查数据源。"]

    # ------------------------------------------------------------------
    # Metric builder utility
    # ------------------------------------------------------------------
    def _build_metric(
        self,
        *,
        indicator: str,
        latest,
        previous,
        period,
        previous_period,
        unit: str | None = None,
        formatter=None,
        symbol: str,
        metric_type: str,
    ) -> dict[str, object] | None:
        if latest is None:
            return None
        if formatter is None:
            formatter = lambda value: f"{float(value):.1f} {unit}" if unit else f"{float(value):.2f}"

        metric: dict[str, object] = {
            "indicator": indicator,
            "latest": formatter(latest),
            "latest_raw": float(latest),
            "period": period,
            "symbol": symbol,
            "metric_type": metric_type,
            "trend": "stable",
            "change_display": "-",
        }
        if previous is not None:
            previous_value = float(previous)
            delta = float(latest) - previous_value
            metric["previous"] = formatter(previous)
            metric["previous_raw"] = previous_value
            metric["previous_period"] = previous_period
            metric["delta"] = delta
            metric["trend"] = self._trend_label(delta)
            if previous_value:
                change_pct = delta / abs(previous_value) * 100
                metric["change_pct"] = change_pct
                metric["change_display"] = f"{change_pct:+.2f}%"
            else:
                metric["change_display"] = f"{delta:+.2f}"
        return metric

    # ------------------------------------------------------------------
    # Formatting helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _parse_date(value) -> datetime:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str) and value:
            for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
        return datetime.min

    @staticmethod
    def _format_percent(value) -> str:
        if value is None:
            return "-"
        return f"{float(value) * 100:.2f}%"

    @staticmethod
    def _trend_label(delta: float) -> str:
        if delta > 0:
            return "rising"
        if delta < 0:
            return "falling"
        return "stable"

    @staticmethod
    def _sentiment_label(score: float) -> str:
        if score >= 0.15:
            return "正面"
        if score <= -0.1:
            return "负面"
        return "中性"

