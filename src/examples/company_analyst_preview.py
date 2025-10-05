"""Preview script for the Company Analyst agent using synthetic data."""

from __future__ import annotations

from src.agents import CompanyAnalystAgent
from src.examples.personal_pipeline import build_runtime


def main() -> None:
    runtime = build_runtime()
    context = runtime.run()
    agent = CompanyAnalystAgent()
    report = agent.generate_report(context)

    print("Company Analyst report (Markdown preview):\n")
    print(report.to_markdown())


if __name__ == "__main__":  # pragma: no cover - manual execution helper
    main()

