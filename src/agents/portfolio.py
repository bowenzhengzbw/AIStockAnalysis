"""Portfolio Strategist agent generating allocation and rebalancing guidance."""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable, Mapping, MutableMapping, Sequence

from src.data_providers import IngestionResult
from src.pipelines.executor import PipelineContext

from .base import Agent, AgentReport

__all__ = ["PortfolioStrategistAgent"]


class PortfolioStrategistAgent(Agent):
    """Summarise holdings, alpha signals, and rebalancing options."""

    DEFAULT_TASKS: Sequence[str] = (
        "portfolio_positions_daily",
        "alpha_signals_daily",
        "rebalance_scenarios_weekly",
        "risk_metrics_daily",
    )

    def __init__(
        self,
        *,
        tracked_tasks: Sequence[str] | None = None,
        top_positions: int = 2,
        top_signals: int = 3,
    ) -> None:
        self._tracked_tasks = tuple(tracked_tasks or self.DEFAULT_TASKS)
        self._top_positions = top_positions
        self._top_signals = top_signals

    def generate_report(
        self, context: Mapping[str, object] | Iterable[tuple[str, object]]
    ) -> AgentReport:
        results = self._collect_results(context)
        metadata = {"source_tasks": tuple(results.keys())}

        position_result = results.get("portfolio_positions_daily")
        signal_result = results.get("alpha_signals_daily")
        scenario_result = results.get("rebalance_scenarios_weekly")
        risk_result = results.get("risk_metrics_daily")

        metrics: list[dict[str, object]] = []
        highlights: list[str] = []
        events: list[dict[str, object]] = []

        if position_result is not None:
            position_metrics, position_highlights = self._summarise_positions(
                position_result.payload
            )
            metrics.extend(position_metrics)
            highlights.extend(position_highlights)

        if signal_result is not None:
            highlights.extend(self._summarise_signals(signal_result.payload))

        if scenario_result is not None:
            scenario_metrics, scenario_events, scenario_highlights = (
                self._summarise_scenarios(scenario_result.payload)
            )
            metrics.extend(scenario_metrics)
            events.extend(scenario_events)
            highlights.extend(scenario_highlights)

        if risk_result is not None:
            risk_highlight = self._extract_risk_highlight(risk_result.payload)
            if risk_highlight:
                highlights.append(risk_highlight)

        if not highlights:
            highlights.append("暂无足够数据生成组合策略洞察。")

        return AgentReport(
            title="组合策略巡航",
            highlights=tuple(highlights),
            metrics=tuple(metrics),
            policy_events=tuple(events),
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
    # Position handling
    # ------------------------------------------------------------------
    def _summarise_positions(
        self, records: Sequence[Mapping[str, object]]
    ) -> tuple[list[dict[str, object]], list[str]]:
        metrics: list[dict[str, object]] = []
        exposures: list[dict[str, object]] = []
        for row in records:
            symbol = str(row.get("symbol") or "").strip()
            if not symbol:
                continue
            weight = self._coerce_float(row.get("weight"))
            benchmark_weight = self._coerce_float(row.get("benchmark_weight"))
            diff = None
            if weight is not None and benchmark_weight is not None:
                diff = weight - benchmark_weight
            metrics.append(
                {
                    "indicator": f"{symbol} 持仓权重",
                    "latest": self._format_pct(weight),
                    "previous_period": "基准权重",
                    "previous": self._format_pct(benchmark_weight),
                    "change_display": self._format_pct(diff, signed=True),
                    "trend": self._trend_label(diff),
                    "dataset": "portfolio_positions_daily",
                    "latest_raw": weight,
                    "previous_raw": benchmark_weight,
                }
            )
            exposures.append(
                {
                    "symbol": symbol,
                    "diff": diff or 0.0,
                    "return_mtd": self._coerce_float(row.get("return_mtd")),
                    "return_ytd": self._coerce_float(row.get("return_ytd")),
                }
            )

        highlights: list[str] = []
        if exposures:
            exposures.sort(key=lambda item: item["diff"], reverse=True)
            overweight = [item for item in exposures if item["diff"] > 0]
            underweight = [item for item in exposures if item["diff"] < 0]

            for item in overweight[: self._top_positions]:
                highlights.append(
                    "超配：{symbol} 相对基准 {diff}，本月贡献 {mtd}，年初至今 {ytd}。".format(
                        symbol=item["symbol"],
                        diff=self._format_pct(item["diff"], signed=True),
                        mtd=self._format_pct(item.get("return_mtd"), signed=True),
                        ytd=self._format_pct(item.get("return_ytd"), signed=True),
                    )
                )
            for item in underweight[: self._top_positions]:
                highlights.append(
                    "低配：{symbol} 相对基准 {diff}，本月贡献 {mtd}，年初至今 {ytd}。".format(
                        symbol=item["symbol"],
                        diff=self._format_pct(item["diff"], signed=True),
                        mtd=self._format_pct(item.get("return_mtd"), signed=True),
                        ytd=self._format_pct(item.get("return_ytd"), signed=True),
                    )
                )

        return metrics, highlights

    # ------------------------------------------------------------------
    # Alpha signals
    # ------------------------------------------------------------------
    def _summarise_signals(
        self, records: Sequence[Mapping[str, object]]
    ) -> list[str]:
        scored = sorted(
            (
                {
                    "symbol": str(row.get("symbol") or ""),
                    "direction": str(row.get("direction") or ""),
                    "score": self._coerce_float(row.get("score")) or 0.0,
                    "confidence": self._coerce_float(row.get("confidence")),
                    "horizon": str(row.get("horizon") or ""),
                    "rationale": str(row.get("rationale") or ""),
                }
                for row in records
                if row.get("symbol")
            ),
            key=lambda item: abs(item["score"]),
            reverse=True,
        )
        highlights: list[str] = []
        for item in scored[: self._top_signals]:
            action = self._direction_label(item["direction"], item["score"])
            highlights.append(
                "Alpha 信号：建议{action} {symbol}（评分 {score}，置信度 {confidence}，持有 {horizon}）。{rationale}".format(
                    action=action,
                    symbol=item["symbol"],
                    score=self._format_decimal(item["score"], signed=True, decimals=2),
                    confidence=self._format_pct(item["confidence"]),
                    horizon=item["horizon"] or "-",
                    rationale=item["rationale"] or "",
                ).strip()
            )
        return highlights

    # ------------------------------------------------------------------
    # Scenario summaries
    # ------------------------------------------------------------------
    def _summarise_scenarios(
        self, records: Sequence[Mapping[str, object]]
    ) -> tuple[list[dict[str, object]], list[dict[str, object]], list[str]]:
        metrics: list[dict[str, object]] = []
        events: list[dict[str, object]] = []
        best_return = None
        lowest_vol = None
        for row in records:
            scenario = str(row.get("scenario") or "")
            if not scenario:
                continue
            expected_return = self._coerce_float(row.get("expected_return"))
            expected_vol = self._coerce_float(row.get("expected_vol"))
            delta_return = self._coerce_float(row.get("delta_return"))
            delta_vol = self._coerce_float(row.get("delta_vol"))
            actions = row.get("actions") or []
            metrics.append(
                {
                    "indicator": f"{scenario} 预期收益",
                    "latest": self._format_pct(expected_return),
                    "previous_period": "风险变化",
                    "previous": self._format_pct(delta_vol, signed=True),
                    "change_display": self._format_pct(delta_return, signed=True),
                    "trend": self._trend_label(delta_return),
                    "dataset": "rebalance_scenarios",
                }
            )
            events.append(
                {
                    "timestamp": row.get("as_of"),
                    "title": scenario,
                    "impact": "方案",
                    "detail": "；".join(actions),
                }
            )
            if expected_return is not None:
                if best_return is None or expected_return > best_return[0]:
                    best_return = (expected_return, delta_vol, scenario, actions)
            if expected_vol is not None:
                if lowest_vol is None or expected_vol < lowest_vol[0]:
                    lowest_vol = (expected_vol, expected_return, scenario, actions)

        highlights: list[str] = []
        if best_return:
            highlights.append(
                "最优收益方案：{scenario} 预期收益 {ret}，风险变化 {risk}。核心操作：{actions}".format(
                    scenario=best_return[2],
                    ret=self._format_pct(best_return[0]),
                    risk=self._format_pct(best_return[1], signed=True),
                    actions="；".join(best_return[3]) or "-",
                )
            )
        if lowest_vol:
            highlights.append(
                "最低波动方案：{scenario} 预期收益 {ret}，预期波动 {risk}。操作建议：{actions}".format(
                    scenario=lowest_vol[2],
                    ret=self._format_pct(lowest_vol[1]),
                    risk=self._format_pct(lowest_vol[0]),
                    actions="；".join(lowest_vol[3]) or "-",
                )
            )
        return metrics, events, highlights

    # ------------------------------------------------------------------
    # Risk highlight
    # ------------------------------------------------------------------
    def _extract_risk_highlight(
        self, records: Sequence[Mapping[str, object]]
    ) -> str | None:
        grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
        for row in records:
            metric = row.get("metric")
            if metric:
                grouped[str(metric)].append(row)
        volatility_rows = grouped.get("组合年化波动率")
        if not volatility_rows:
            return None
        volatility_rows.sort(key=lambda item: str(item.get("date")))
        latest = volatility_rows[-1]
        value = self._coerce_float(latest.get("value"))
        warning = self._coerce_float(latest.get("warning_upper"))
        previous = self._coerce_float(latest.get("previous_value"))
        if value is None:
            return None
        parts = [
            "组合年化波动率 {value}".format(value=self._format_pct(value)),
        ]
        if warning is not None:
            parts.append("预警线 {warning}".format(warning=self._format_pct(warning)))
        if previous is not None:
            delta = value - previous
            parts.append(
                "较前值 {previous}（{delta}）".format(
                    previous=self._format_pct(previous),
                    delta=self._format_pct(delta, signed=True),
                )
            )
        return "，".join(parts)

    # ------------------------------------------------------------------
    # Formatting helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _coerce_float(value: object) -> float | None:
        try:
            if value is None:
                return None
            return float(value)
        except (TypeError, ValueError):  # pragma: no cover - defensive
            return None

    @staticmethod
    def _format_pct(value: float | None, *, signed: bool = False) -> str:
        if value is None:
            return "-"
        if signed:
            return f"{value:+.1%}"
        return f"{value:.1%}"

    @staticmethod
    def _format_decimal(
        value: float | None, *, signed: bool = False, decimals: int = 2
    ) -> str:
        if value is None:
            return "-"
        formatted = f"{value:.{decimals}f}"
        if signed and not formatted.startswith("-"):
            return f"+{formatted}"
        return formatted

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
    def _direction_label(direction: str, score: float) -> str:
        mapping = {
            "overweight": "增持",
            "add": "加仓",
            "accumulate": "增仓",
            "reduce": "减仓",
            "underweight": "低配",
            "trim": "减持",
            "sell": "卖出",
        }
        label = mapping.get(direction.lower()) if direction else None
        if not label:
            label = "增持" if score >= 0 else "减持"
        return label
