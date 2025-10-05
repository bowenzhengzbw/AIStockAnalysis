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

    def available_datasets(self) -> Sequence[str]:
        return (
            "macro_indicators",
            "market_quotes",
            "financial_summary",
            "valuation_snapshot",
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

    def available_datasets(self) -> Sequence[str]:
        return ("policy_flash", "news_sentiment")

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
