"""Tests for the Company Analyst agent preview report."""

from __future__ import annotations

from src.agents import CompanyAnalystAgent
from src.examples.personal_pipeline import build_runtime


def test_company_analyst_generates_company_snapshot():
    runtime = build_runtime()
    context = runtime.run()
    agent = CompanyAnalystAgent(top_events=2)

    report = agent.generate_report(context)

    assert report.title == "核心公司质地巡检"
    assert any("600519.SH" in item for item in report.highlights)

    metrics = {metric["indicator"]: metric for metric in report.metrics}
    revenue_metric = metrics["600519.SH 营业收入"]
    assert revenue_metric["trend"] == "rising"
    assert revenue_metric["change_display"].startswith("+")

    pe_metric = metrics["600519.SH PE(TTM)"]
    assert pe_metric["indicator"].endswith("PE(TTM)")
    assert pe_metric["latest"].endswith("倍")

    assert report.policy_events
    assert len(report.policy_events) <= 2
    assert report.policy_events[0]["impact"] in {"正面", "中性", "负面"}

    markdown = report.to_markdown()
    assert markdown.startswith("# 核心公司质地巡检")

    html = report.to_html()
    assert "<!DOCTYPE html>" in html
    assert "核心公司质地巡检" in html
