"""Industry analysis agent using Morningstar classification as baseline."""

from __future__ import annotations

from typing import Any, Dict

from .base import AgentResult, safe_float


class IndustryAgent:
    """Evaluate industry cycle and thematic opportunities."""

    name = "industry_agent"

    def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        industries = context.get("industries", {})
        focus = industries.get("focus", [])
        summary = "行业景气度评估完成，按照 Morningstar 分类生成热力图建议。"
        metrics = {
            f"{item}_score": safe_float(score)
            for item, score in industries.get("scores", {}).items()
        }
        insights = {
            "overweight": industries.get("overweight", []),
            "underweight": industries.get("underweight", []),
            "policy_sensitive": industries.get("policy_sensitive", []),
        }
        return AgentResult(name=self.name, summary=summary, metrics=metrics, insights=insights).__dict__
