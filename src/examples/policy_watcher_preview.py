"""Generate a policy flash snapshot using the Policy Watcher agent."""

from __future__ import annotations

from src.agents import PolicyWatcherAgent
from src.examples.personal_pipeline import build_runtime


def main() -> None:
    runtime = build_runtime()
    context = runtime.run()
    agent = PolicyWatcherAgent()
    report = agent.generate_report(context)

    print(report.to_markdown())


if __name__ == "__main__":  # pragma: no cover - manual execution helper
    main()
