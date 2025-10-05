"""Preview script for the Industry Mapper agent using synthetic data."""

from __future__ import annotations

from src.agents import IndustryMapperAgent
from src.examples.personal_pipeline import build_runtime


def main() -> None:
    runtime = build_runtime()
    context = runtime.run()
    agent = IndustryMapperAgent(top_industries=3, top_themes=2)
    report = agent.generate_report(context)

    print("Industry Mapper report (Markdown preview):\n")
    print(report.to_markdown())


if __name__ == "__main__":  # pragma: no cover - manual execution helper
    main()
