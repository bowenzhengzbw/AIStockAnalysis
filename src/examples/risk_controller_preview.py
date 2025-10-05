"""Preview script for the Risk Controller agent using synthetic data."""

from __future__ import annotations

from src.agents import RiskControllerAgent
from src.examples.personal_pipeline import build_runtime


def main() -> None:
    runtime = build_runtime()
    context = runtime.run()
    agent = RiskControllerAgent()
    report = agent.generate_report(context)
    print(report.to_markdown())


if __name__ == "__main__":  # pragma: no cover - manual execution helper
    main()
