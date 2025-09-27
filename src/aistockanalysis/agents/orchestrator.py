"""Agent orchestrator that synthesizes macro-to-micro insights."""

from __future__ import annotations

from typing import Any, Dict, List, Sequence

from .base import Agent
from .equity import EquityAgent
from .industry import IndustryAgent
from .macro import MacroAgent


class AgentOrchestrator:
    """Coordinate agent execution and aggregate outputs."""

    def __init__(self, agents: Sequence[Agent] | None = None) -> None:
        self.agents: List[Agent] = list(agents) if agents else [
            MacroAgent(),
            IndustryAgent(),
            EquityAgent(),
        ]

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run agents sequentially and compile their results."""

        results = {}
        for agent in self.agents:
            results[agent.name] = agent.analyze(context)
        results["summary"] = self._compose_summary(results)
        return results

    def _compose_summary(self, results: Dict[str, Any]) -> str:
        """Create narrative summary following investment committee format."""

        macro = results.get("macro_agent", {})
        industry = results.get("industry_agent", {})
        equity = results.get("equity_agent", {})
        return (
            "宏观层面: {macro_summary}\n"
            "行业层面: {industry_summary}\n"
            "个股层面: {equity_summary}"
        ).format(
            macro_summary=macro.get("summary", "N/A"),
            industry_summary=industry.get("summary", "N/A"),
            equity_summary=equity.get("summary", "N/A"),
        )
