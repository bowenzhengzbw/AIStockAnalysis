"""Application configuration module.

采用轻量化实现以适配初版环境，同时保留金融行业常见的配置字段，支持后续替换为企业级配置中心。
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List


def _comma_separated(value: str | None, default: List[str]) -> List[str]:
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(slots=True)
class Settings:
    """Global application settings."""

    app_name: str = os.getenv("AISTOCK_APP_NAME", "AIStockAnalysis Platform")
    environment: str = os.getenv("AISTOCK_ENVIRONMENT", "dev")
    data_sources: List[str] = field(
        default_factory=lambda: _comma_separated(
            os.getenv("AISTOCK_DATA_SOURCES"),
            [
                "macro_world_bank",
                "macro_fred",
                "policy_state_council",
                "industry_morningstar",
                "equity_exchange",
                "news_regulatory",
            ],
        )
    )
    risk_metrics: List[str] = field(
        default_factory=lambda: _comma_separated(
            os.getenv("AISTOCK_RISK_METRICS"),
            [
                "volatility_annualized",
                "max_drawdown",
                "var_95",
                "cvar_95",
                "liquidity_score",
            ],
        )
    )
    report_locales: List[str] = field(
        default_factory=lambda: _comma_separated(
            os.getenv("AISTOCK_REPORT_LOCALES"),
            ["zh_CN", "en_US"],
        )
    )


def get_settings() -> Settings:
    """Return settings instance."""

    return Settings()


settings = get_settings()
