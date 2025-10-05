"""Tests for the Industry Mapper agent report generation."""

from __future__ import annotations

from src.agents import IndustryMapperAgent
from src.examples.personal_pipeline import build_runtime


def test_industry_mapper_generates_industry_report() -> None:
    runtime = build_runtime()
    context = runtime.run()
    agent = IndustryMapperAgent(top_industries=2, top_themes=1)

    report = agent.generate_report(context)

    assert report.title == "行业景气雷达"
    assert report.highlights
    assert any("景气指数" in highlight for highlight in report.highlights)

    metric_names = {metric["indicator"] for metric in report.metrics}
    assert any("景气指数" in name for name in metric_names)
    assert any("主力净流入" in name for name in metric_names)

    html = report.to_html()
    assert "<!DOCTYPE html>" in html
    assert "行业景气雷达" in html

    markdown = report.to_markdown()
    assert markdown.startswith("# 行业景气雷达")

    if report.policy_events:
        assert all(event.get("title") for event in report.policy_events)

    assert "source_tasks" in report.metadata
