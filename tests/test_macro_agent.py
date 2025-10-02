"""Tests for the Macro Sentinel agent preview report."""

from __future__ import annotations

from src.agents import MacroSentinelAgent
from src.examples.personal_pipeline import build_runtime


def test_macro_sentinel_generates_macro_summary():
    runtime = build_runtime()
    context = runtime.run()
    agent = MacroSentinelAgent()

    report = agent.generate_report(context)

    assert report.title == "宏观巡检快照"
    assert any("GDP" in item for item in report.highlights)

    metrics = {metric["indicator"]: metric for metric in report.metrics}
    assert "PMI" in metrics
    assert metrics["PMI"]["trend"] == "rising"

    assert report.policy_events
    assert report.policy_events[0]["title"] == "发改委推进新能源车下乡活动"

    markdown = report.to_markdown()
    assert markdown.startswith("# 宏观巡检快照")
    assert "政策快讯" in markdown
