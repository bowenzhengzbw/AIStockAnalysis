"""Tests for the Risk Controller agent report generation."""

from __future__ import annotations

from src.agents import RiskControllerAgent
from src.examples.personal_pipeline import build_runtime


def test_risk_controller_generates_risk_report() -> None:
    runtime = build_runtime()
    context = runtime.run()
    agent = RiskControllerAgent()

    report = agent.generate_report(context)

    assert report.title == "组合风险雷达"
    assert report.highlights
    assert any("波动率" in highlight for highlight in report.highlights)

    indicator_names = {metric["indicator"] for metric in report.metrics}
    assert any("组合年化波动率" in name for name in indicator_names)
    assert any("集中度" in name or "Beta" in name for name in indicator_names)

    html = report.to_html()
    assert "组合风险雷达" in html

    markdown = report.to_markdown()
    assert markdown.startswith("# 组合风险雷达")

    assert report.policy_events
    assert all(event.get("title") for event in report.policy_events)
    assert "source_tasks" in report.metadata
