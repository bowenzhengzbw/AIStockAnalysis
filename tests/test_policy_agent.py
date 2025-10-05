"""Tests for the Policy Watcher agent preview report."""

from __future__ import annotations

from src.agents import PolicyWatcherAgent
from src.examples.personal_pipeline import build_runtime


def test_policy_watcher_generates_policy_summary():
    runtime = build_runtime()
    context = runtime.run()
    agent = PolicyWatcherAgent(top_events=2)

    report = agent.generate_report(context)

    assert report.title == "政策速览巡航"
    assert any("政策快讯" in item for item in report.highlights)

    metrics = {metric["indicator"]: metric for metric in report.metrics}
    assert "正面事件数量" in metrics
    assert metrics["正面事件数量"]["latest"].endswith("条")

    assert report.policy_events
    assert len(report.policy_events) <= 2
    assert report.policy_events[0]["title"]

    markdown = report.to_markdown()
    assert markdown.startswith("# 政策速览巡航")
    assert "政策与事件" in markdown

    html = report.to_html()
    assert "<!DOCTYPE html>" in html
    assert "政策速览巡航" in html
    assert "关键结论" in html
