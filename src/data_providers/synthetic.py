"""Synthetic data providers emulating paid/official data sources for testing."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence

from .base import DataProvider, IngestionResult

__all__ = [
    "SyntheticTushareClient",
    "SyntheticCailiansheClient",
    "SyntheticNbsClient",
]


def _slice_by_window(records: Sequence[Mapping[str, object]], window: str | None) -> list[Mapping[str, object]]:
    if not window or len(records) <= 1:
        return list(records)
    try:
        span = int(window[:-1])
    except (ValueError, TypeError):
        return list(records)
    unit = window[-1].lower()
    if unit not in {"d", "w", "m", "y"}:
        return list(records)
    # interpret the window as the maximum number of records to return.
    limit = span
    if unit == "w":
        limit = span * 7
    elif unit == "m":
        limit = span * 30
    elif unit == "y":
        limit = span * 365
    limit = max(1, limit)
    return list(records)[-limit:]


@dataclass(slots=True)
class SyntheticTushareClient(DataProvider):
    """In-memory representation of selected Tushare datasets."""

    name: str = "Tushare Pro"
    macro_records: Sequence[Mapping[str, object]] = field(
        default_factory=lambda: [
            {"date": "2023-12-31", "indicator": "GDP", "value": 126000.0},
            {"date": "2024-03-31", "indicator": "GDP", "value": 129500.0},
            {"date": "2024-06-30", "indicator": "GDP", "value": 131200.0},
            {"date": "2024-06-30", "indicator": "PMI", "value": 50.2},
            {"date": "2024-07-31", "indicator": "PMI", "value": 50.7},
        ]
    )
    quote_records: Sequence[Mapping[str, object]] = field(
        default_factory=lambda: [
            {"date": "2024-07-29", "symbol": "600519.SH", "close": 1723.5, "turnover": 1.2e9},
            {"date": "2024-07-30", "symbol": "600519.SH", "close": 1738.0, "turnover": 1.3e9},
            {"date": "2024-07-31", "symbol": "600519.SH", "close": 1745.6, "turnover": 1.45e9},
            {"date": "2024-07-31", "symbol": "300750.SZ", "close": 198.5, "turnover": 8.1e8},
        ]
    )
    financial_records: Sequence[Mapping[str, object]] = field(
        default_factory=lambda: [
            {
                "symbol": "600519.SH",
                "report_date": "2023-03-31",
                "revenue": 298.6,
                "net_profit": 150.4,
                "roe": 0.062,
                "gross_margin": 0.909,
            },
            {
                "symbol": "600519.SH",
                "report_date": "2024-03-31",
                "revenue": 316.2,
                "net_profit": 158.9,
                "roe": 0.065,
                "gross_margin": 0.912,
            },
            {
                "symbol": "300750.SZ",
                "report_date": "2023-03-31",
                "revenue": 890.1,
                "net_profit": 90.3,
                "roe": 0.118,
                "gross_margin": 0.211,
            },
            {
                "symbol": "300750.SZ",
                "report_date": "2024-03-31",
                "revenue": 945.7,
                "net_profit": 110.5,
                "roe": 0.124,
                "gross_margin": 0.226,
            },
        ]
    )
    valuation_records: Sequence[Mapping[str, object]] = field(
        default_factory=lambda: [
            {
                "symbol": "600519.SH",
                "date": "2024-07-30",
                "pe_ttm": 28.4,
                "pb": 7.1,
                "dividend_yield": 0.017,
            },
            {
                "symbol": "600519.SH",
                "date": "2024-07-31",
                "pe_ttm": 27.9,
                "pb": 7.0,
                "dividend_yield": 0.017,
            },
            {
                "symbol": "300750.SZ",
                "date": "2024-07-30",
                "pe_ttm": 35.2,
                "pb": 5.8,
                "dividend_yield": 0.004,
            },
            {
                "symbol": "300750.SZ",
                "date": "2024-07-31",
                "pe_ttm": 34.6,
                "pb": 5.7,
                "dividend_yield": 0.004,
            },
        ]
    )
    industry_climate_records: Sequence[Mapping[str, object]] = field(
        default_factory=lambda: [
            {"month": "2024-06", "industry": "白酒", "score": 108.4},
            {"month": "2024-07", "industry": "白酒", "score": 112.7},
            {"month": "2024-06", "industry": "新能源汽车", "score": 97.1},
            {"month": "2024-07", "industry": "新能源汽车", "score": 101.9},
            {"month": "2024-06", "industry": "光伏设备", "score": 92.3},
            {"month": "2024-07", "industry": "光伏设备", "score": 95.4},
        ]
    )
    industry_capital_flow_records: Sequence[Mapping[str, object]] = field(
        default_factory=lambda: [
            {
                "date": "2024-07-30",
                "industry": "白酒",
                "net_flow": 8.6e8,
                "main_force_ratio": 0.62,
            },
            {
                "date": "2024-07-31",
                "industry": "白酒",
                "net_flow": 1.24e9,
                "main_force_ratio": 0.67,
            },
            {
                "date": "2024-07-30",
                "industry": "新能源汽车",
                "net_flow": 5.1e8,
                "main_force_ratio": 0.55,
            },
            {
                "date": "2024-07-31",
                "industry": "新能源汽车",
                "net_flow": 7.8e8,
                "main_force_ratio": 0.61,
            },
            {
                "date": "2024-07-30",
                "industry": "光伏设备",
                "net_flow": -2.4e8,
                "main_force_ratio": 0.44,
            },
            {
                "date": "2024-07-31",
                "industry": "光伏设备",
                "net_flow": -1.1e8,
                "main_force_ratio": 0.48,
            },
        ]
    )
    risk_metric_records: Sequence[Mapping[str, object]] = field(
        default_factory=lambda: [
            {
                "date": "2024-07-24",
                "metric": "组合年化波动率",
                "value": 0.192,
                "previous_date": "2024-07-17",
                "previous_value": 0.198,
                "unit": "ratio",
                "warning_upper": 0.24,
            },
            {
                "date": "2024-07-31",
                "metric": "组合年化波动率",
                "value": 0.184,
                "previous_date": "2024-07-24",
                "previous_value": 0.192,
                "unit": "ratio",
                "warning_upper": 0.24,
            },
            {
                "date": "2024-07-24",
                "metric": "最大回撤（1Y）",
                "value": -0.138,
                "previous_date": "2024-06-30",
                "previous_value": -0.152,
                "unit": "ratio",
                "warning_lower": -0.18,
            },
            {
                "date": "2024-07-31",
                "metric": "最大回撤（1Y）",
                "value": -0.129,
                "previous_date": "2024-07-24",
                "previous_value": -0.138,
                "unit": "ratio",
                "warning_lower": -0.18,
            },
            {
                "date": "2024-07-31",
                "metric": "1日VaR(95%)",
                "value": -0.027,
                "previous_date": "2024-06-30",
                "previous_value": -0.031,
                "unit": "ratio",
                "warning_lower": -0.04,
            },
        ]
    )
    risk_exposure_records: Sequence[Mapping[str, object]] = field(
        default_factory=lambda: [
            {
                "date": "2024-07-31",
                "metric": "沪深300 Beta",
                "value": 0.94,
                "previous_value": 0.98,
                "unit": "ratio",
                "direction": "max",
                "limit": 1.1,
            },
            {
                "date": "2024-07-31",
                "metric": "行业集中度(前3名)",
                "value": 0.41,
                "previous_value": 0.43,
                "unit": "ratio",
                "direction": "max",
                "limit": 0.45,
            },
            {
                "date": "2024-07-31",
                "metric": "现金仓位占比",
                "value": 0.11,
                "previous_value": 0.08,
                "unit": "ratio",
                "direction": "range",
                "lower_bound": 0.05,
                "upper_bound": 0.15,
            },
        ]
    )
    risk_alert_records: Sequence[Mapping[str, object]] = field(
        default_factory=lambda: [
            {
                "timestamp": "2024-07-31T15:05:00+08:00",
                "title": "组合波动率低于预警线，风险水平回落",
                "impact": "positive",
                "severity": "low",
                "detail": "最新年化波动率 18.4%，预警阈值 24%。",
            },
            {
                "timestamp": "2024-07-31T15:06:00+08:00",
                "title": "现金仓位上升，需确认配置意图",
                "impact": "watch",
                "severity": "medium",
                "detail": "现金仓位 11%，建议对照目标区间 5%-15%。",
            },
        ]
    )
    portfolio_position_records: Sequence[Mapping[str, object]] = field(
        default_factory=lambda: [
            {
                "date": "2024-07-31",
                "symbol": "600519.SH",
                "weight": 0.14,
                "benchmark_weight": 0.1,
                "return_mtd": 0.045,
                "return_ytd": 0.12,
            },
            {
                "date": "2024-07-31",
                "symbol": "300750.SZ",
                "weight": 0.11,
                "benchmark_weight": 0.08,
                "return_mtd": 0.038,
                "return_ytd": 0.26,
            },
            {
                "date": "2024-07-31",
                "symbol": "159915.SZ",
                "weight": 0.07,
                "benchmark_weight": 0.1,
                "return_mtd": -0.012,
                "return_ytd": 0.041,
            },
            {
                "date": "2024-07-31",
                "symbol": "510500.SH",
                "weight": 0.05,
                "benchmark_weight": 0.08,
                "return_mtd": -0.007,
                "return_ytd": 0.056,
            },
        ]
    )
    rebalance_scenario_records: Sequence[Mapping[str, object]] = field(
        default_factory=lambda: [
            {
                "as_of": "2024-08-01",
                "scenario": "维持当前配置",
                "expected_return": 0.078,
                "expected_vol": 0.168,
                "delta_return": 0.0,
                "delta_vol": 0.0,
                "actions": [
                    "保持白酒与新能源车双主线",
                    "适度提高现金流回收标的仓位",
                ],
            },
            {
                "as_of": "2024-08-01",
                "scenario": "攻守均衡",
                "expected_return": 0.085,
                "expected_vol": 0.172,
                "delta_return": 0.007,
                "delta_vol": 0.004,
                "actions": [
                    "将新能源车仓位提升 2%",
                    "引入数字经济龙头 1% 权重",
                ],
            },
            {
                "as_of": "2024-08-01",
                "scenario": "防御增强",
                "expected_return": 0.072,
                "expected_vol": 0.155,
                "delta_return": -0.006,
                "delta_vol": -0.013,
                "actions": [
                    "降低白酒仓位 2%",
                    "提升高股息公用事业仓位 2%",
                ],
            },
        ]
    )

    def available_datasets(self) -> Sequence[str]:
        return (
            "macro_indicators",
            "market_quotes",
            "financial_summary",
            "valuation_snapshot",
            "industry_climate",
            "industry_capital_flow",
            "risk_metrics",
            "risk_exposure",
            "risk_alerts",
            "portfolio_positions",
            "rebalance_scenarios",
        )

    def fetch(
        self,
        dataset: str,
        *,
        window: str | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> IngestionResult:
        self._validate_dataset(dataset)
        payload: list[Mapping[str, object]]
        if dataset == "macro_indicators":
            payload = _slice_by_window(self.macro_records, window)
        elif dataset == "market_quotes":
            payload = _slice_by_window(self.quote_records, window)
        elif dataset == "financial_summary":
            payload = _slice_by_window(self.financial_records, window)
        elif dataset == "valuation_snapshot":
            payload = _slice_by_window(self.valuation_records, window)
        elif dataset == "industry_climate":
            payload = _slice_by_window(self.industry_climate_records, window)
        elif dataset == "industry_capital_flow":
            payload = _slice_by_window(self.industry_capital_flow_records, window)
        elif dataset == "risk_metrics":
            payload = _slice_by_window(self.risk_metric_records, window)
        elif dataset == "risk_exposure":
            payload = _slice_by_window(self.risk_exposure_records, window)
        elif dataset == "risk_alerts":
            payload = _slice_by_window(self.risk_alert_records, window)
        elif dataset == "portfolio_positions":
            payload = _slice_by_window(self.portfolio_position_records, window)
        elif dataset == "rebalance_scenarios":
            payload = _slice_by_window(self.rebalance_scenario_records, window)
        else:  # pragma: no cover - guarded by _validate_dataset
            payload = []
        return IngestionResult(
            dataset=dataset,
            payload=payload,
            metadata=self._merge_metadata(metadata, {"window": window}),
        )


@dataclass(slots=True)
class SyntheticCailiansheClient(DataProvider):
    """Synthetic 财联社数据源，覆盖政策快讯与资讯情绪。"""

    name: str = "财联社 Lite"
    policy_events: Sequence[Mapping[str, object]] = field(
        default_factory=lambda: [
            {
                "timestamp": "2024-07-31T09:15:00+08:00",
                "title": "央行发布支持中小企业融资指导意见",
                "impact": "positive",
                "related": ["银行", "中小企业"],
            },
            {
                "timestamp": "2024-07-31T14:02:00+08:00",
                "title": "发改委推进新能源车下乡活动",
                "impact": "positive",
                "related": ["新能源汽车", "消费刺激"],
            },
        ]
    )
    news_sentiment: Sequence[Mapping[str, object]] = field(
        default_factory=lambda: [
            {
                "timestamp": "2024-07-31T10:30:00+08:00",
                "symbol": "600519.SH",
                "sentiment": 0.15,
                "summary": "贵州茅台推出暑期营销活动",
            },
            {
                "timestamp": "2024-07-31T10:35:00+08:00",
                "symbol": "300750.SZ",
                "sentiment": 0.32,
                "summary": "宁德时代获得海外大订单",
            },
        ]
    )
    theme_heat: Sequence[Mapping[str, object]] = field(
        default_factory=lambda: [
            {
                "date": "2024-07-30",
                "theme": "数字经济",
                "heat": 76,
                "attention_change": -3.2,
            },
            {
                "date": "2024-07-31",
                "theme": "数字经济",
                "heat": 78,
                "attention_change": 2.6,
            },
            {
                "date": "2024-07-30",
                "theme": "新能源车",
                "heat": 88,
                "attention_change": 1.5,
            },
            {
                "date": "2024-07-31",
                "theme": "新能源车",
                "heat": 92,
                "attention_change": 4.1,
            },
        ]
    )
    alpha_signals: Sequence[Mapping[str, object]] = field(
        default_factory=lambda: [
            {
                "timestamp": "2024-07-31T15:10:00+08:00",
                "symbol": "600519.SH",
                "direction": "overweight",
                "horizon": "3m",
                "score": 0.72,
                "confidence": 0.78,
                "rationale": "渠道调研反馈动销改善，消费税改革预期落地",
            },
            {
                "timestamp": "2024-07-31T15:11:00+08:00",
                "symbol": "300750.SZ",
                "direction": "add",
                "horizon": "6m",
                "score": 0.81,
                "confidence": 0.83,
                "rationale": "发改委新能源车下乡政策叠加海外订单落地",
            },
            {
                "timestamp": "2024-07-31T15:12:00+08:00",
                "symbol": "159915.SZ",
                "direction": "reduce",
                "horizon": "1m",
                "score": -0.46,
                "confidence": 0.65,
                "rationale": "成长风格阶段性回调，建议收缩指数化敞口",
            },
        ]
    )

    def available_datasets(self) -> Sequence[str]:
        return ("policy_flash", "news_sentiment", "theme_heat", "alpha_signals")

    def fetch(
        self,
        dataset: str,
        *,
        window: str | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> IngestionResult:
        self._validate_dataset(dataset)
        payload: list[Mapping[str, object]]
        if dataset == "policy_flash":
            payload = _slice_by_window(self.policy_events, window)
        elif dataset == "news_sentiment":
            payload = _slice_by_window(self.news_sentiment, window)
        elif dataset == "theme_heat":
            payload = _slice_by_window(self.theme_heat, window)
        elif dataset == "alpha_signals":
            payload = _slice_by_window(self.alpha_signals, window)
        else:  # pragma: no cover - guarded by _validate_dataset
            payload = []
        enriched_meta = self._merge_metadata(
            metadata,
            {
                "window": window,
                "records": len(payload),
            },
        )
        return IngestionResult(dataset=dataset, payload=payload, metadata=enriched_meta)


@dataclass(slots=True)
class SyntheticNbsClient(DataProvider):
    """Synthetic 国家统计局数据源，提供月度宏观指标。"""

    name: str = "国家统计局公开数据"
    statistical_series: Sequence[Mapping[str, object]] = field(
        default_factory=lambda: [
            {"month": "2024-05", "indicator": "工业增加值", "value": 5.6},
            {"month": "2024-06", "indicator": "工业增加值", "value": 5.9},
            {"month": "2024-06", "indicator": "社会消费品零售总额", "value": 3.7},
        ]
    )

    def available_datasets(self) -> Sequence[str]:
        return ("macro_statistical",)

    def fetch(
        self,
        dataset: str,
        *,
        window: str | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> IngestionResult:
        self._validate_dataset(dataset)
        payload = _slice_by_window(self.statistical_series, window)
        return IngestionResult(
            dataset=dataset,
            payload=payload,
            metadata=self._merge_metadata(metadata, {"window": window}),
        )
