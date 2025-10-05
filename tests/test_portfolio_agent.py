"""Tests for the Portfolio Strategist agent report."""

from __future__ import annotations

from src.agents import PortfolioStrategistAgent
from src.examples.personal_pipeline import build_runtime


def test_portfolio_strategist_generates_combined_view():
    runtime = build_runtime()
    context = runtime.run()

    agent = PortfolioStrategistAgent(top_positions=1, top_signals=2)
    report = agent.generate_report(context)

    assert report.title == "组合策略巡航"
    assert any("超配" in item or "Alpha" in item for item in report.highlights)

    metrics = {metric["indicator"]: metric for metric in report.metrics}
    assert any(indicator.endswith("持仓权重") for indicator in metrics)
    assert any("预期收益" in indicator for indicator in metrics)

    assert report.policy_events
    assert report.policy_events[0]["impact"] == "方案"

    markdown = report.to_markdown()
    assert markdown.startswith("# 组合策略巡航")

    html = report.to_html()
    assert "<!DOCTYPE html>" in html
    assert "组合策略巡航" in html
