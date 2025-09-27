"""Definitions of structured data sources used by the platform."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Callable, Dict, Iterable


@dataclass(frozen=True)
class DataSource:
    """Descriptor for data ingestion.

    Attributes:
        name: 唯一名称，对应金融机构常用的简称。
        frequency: 刷新频率，宏观使用月度/季度，行情使用分钟/日度。
        retention: 数据保留周期，满足监管对历史可追溯性的要求。
        fetcher: 执行抓取的回调函数。
    """

    name: str
    frequency: str
    retention: timedelta
    fetcher: Callable[..., Iterable[Dict[str, object]]]


def default_sources() -> Dict[str, DataSource]:
    """Return baseline data source configuration."""

    one_day = timedelta(days=1)
    one_quarter = timedelta(days=90)
    return {
        "macro_world_bank": DataSource(
            name="WorldBank",
            frequency="monthly",
            retention=one_quarter * 20,
            fetcher=lambda **_: [],
        ),
        "macro_fred": DataSource(
            name="FRED",
            frequency="monthly",
            retention=one_quarter * 8,
            fetcher=lambda **_: [],
        ),
        "policy_state_council": DataSource(
            name="StateCouncil",
            frequency="daily",
            retention=one_quarter * 4,
            fetcher=lambda **_: [],
        ),
        "industry_morningstar": DataSource(
            name="MorningstarIndustry",
            frequency="weekly",
            retention=one_quarter * 12,
            fetcher=lambda **_: [],
        ),
        "equity_exchange": DataSource(
            name="ExchangeQuote",
            frequency="intraday",
            retention=one_day * 365,
            fetcher=lambda **_: [],
        ),
        "news_regulatory": DataSource(
            name="RegulatoryNews",
            frequency="daily",
            retention=one_quarter * 4,
            fetcher=lambda **_: [],
        ),
    }
