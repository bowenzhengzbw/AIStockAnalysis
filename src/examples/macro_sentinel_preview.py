"""Generate a macro snapshot using the Macro Sentinel agent."""

from __future__ import annotations

from src.agents import MacroSentinelAgent
from src.examples.personal_pipeline import build_runtime


def main() -> None:
    runtime = build_runtime()
    context = runtime.run()
    agent = MacroSentinelAgent()
    report = agent.generate_report(context)

    print(report.to_markdown())


if __name__ == "__main__":  # pragma: no cover - manual execution helper
    main()
