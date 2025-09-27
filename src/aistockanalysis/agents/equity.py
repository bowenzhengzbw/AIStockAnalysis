"""Equity deep dive agent covering valuation and quality metrics."""

from __future__ import annotations

from typing import Any, Dict

from .base import AgentResult, safe_float


class EquityAgent:
    """Generate bottom-up valuation snapshots."""

    name = "equity_agent"

    def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        equity = context.get("equity", {})
        valuation = equity.get("valuation", {})
        quality = equity.get("quality", {})
        summary = "个股研究完成，覆盖盈利能力、估值与风险提示。"
        metrics = {
            "pe": safe_float(valuation.get("pe", 0.0)),
            "pb": safe_float(valuation.get("pb", 0.0)),
            "roe": safe_float(quality.get("roe", 0.0)),
            "net_margin": safe_float(quality.get("net_margin", 0.0)),
        }
        insights = {
            "growth_drivers": equity.get("growth_drivers", []),
            "risk_factors": equity.get("risk_factors", []),
            "esg_flags": equity.get("esg_flags", []),
        }
        return AgentResult(name=self.name, summary=summary, metrics=metrics, insights=insights).__dict__
