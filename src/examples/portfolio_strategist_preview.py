"""Preview script for the Portfolio Strategist agent."""

from __future__ import annotations

from src.agents import PortfolioStrategistAgent
from src.examples.personal_pipeline import build_runtime


def main() -> None:
    runtime = build_runtime()
    context = runtime.run()
    agent = PortfolioStrategistAgent()

    report = agent.generate_report(context)
    print(report.to_markdown())


if __name__ == "__main__":  # pragma: no cover - manual execution helper
    main()
