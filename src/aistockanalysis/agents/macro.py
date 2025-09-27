"""Macro analysis agent aligned with top-down investment research."""

from __future__ import annotations

from typing import Any, Dict

from .base import AgentResult, safe_float


class MacroAgent:
    """Assess macroeconomic cycle and policy stance."""

    name = "macro_agent"

    def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        indicators = context.get("macro", {})
        policy = context.get("policy", {})
        summary = (
            "宏观环境监测完成：关注增长、通胀、政策三大维度，初版采用模板化评分。"
        )
        metrics = {
            "growth_score": safe_float(indicators.get("gdp_growth", 0.0)),
            "inflation_score": safe_float(indicators.get("cpi", 0.0)),
            "policy_support": safe_float(policy.get("support_score", 0.0)),
        }
        insights = {
            "policy_highlights": policy.get("highlights", []),
            "risk_flags": context.get("macro_risks", []),
        }
        return AgentResult(name=self.name, summary=summary, metrics=metrics, insights=insights).__dict__
