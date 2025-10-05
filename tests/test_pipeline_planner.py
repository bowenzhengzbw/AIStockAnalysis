import pytest

from src.pipelines import (
    CyclicDependencyError,
    UnknownDataSourceError,
    load_pipeline_plan_from_toml,
)
from src.utils import load_portfolio_from_toml


@pytest.fixture(scope="module")
def personal_portfolio():
    return load_portfolio_from_toml("configs/data_sources.personal.toml")


def test_load_pipeline_plan_success(personal_portfolio):
    plan = load_pipeline_plan_from_toml(
        "configs/pipeline.personal.toml", portfolio=personal_portfolio
    )

    assert plan.name == "personal_investor_phase1"
    assert plan.currency == "CNY"
    assert len(plan.tasks) == 13

    grouped = plan.group_by_frequency()
    assert set(grouped) == {"daily", "intraday", "hourly", "monthly", "quarterly", "weekly"}
    assert {task.id for task in grouped["daily"]} == {
        "macro_indicators_daily",
        "market_quotes_eod",
        "company_valuation_daily",
        "industry_capital_flow_daily",
        "theme_heat_daily",
        "risk_metrics_daily",
        "risk_alerts_daily",
    }
    assert {task.id for task in grouped["quarterly"]} == {"company_financials_quarterly"}
    assert {task.id for task in grouped["monthly"]} == {
        "macro_monthly_statistical",
        "industry_climate_monthly",
    }
    assert {task.id for task in grouped["weekly"]} == {"risk_exposure_snapshot"}

    tushare_tasks = plan.tasks_for_source("Tushare Pro")
    assert {task.dataset for task in tushare_tasks} == {
        "macro_indicators",
        "market_quotes",
        "financial_summary",
        "valuation_snapshot",
        "industry_climate",
        "industry_capital_flow",
        "risk_metrics",
        "risk_exposure",
        "risk_alerts",
    }

    assert plan.missing_dependencies() == {}

    serialized = plan.to_dict()
    assert serialized["name"] == "personal_investor_phase1"
    assert len(serialized["tasks"]) == 13


def test_topological_order_respects_dependencies(personal_portfolio):
    plan = load_pipeline_plan_from_toml(
        "configs/pipeline.personal.toml", portfolio=personal_portfolio
    )

    ordered = [task.id for task in plan.topological_order()]

    assert ordered.index("macro_indicators_daily") < ordered.index(
        "macro_monthly_statistical"
    )
    assert ordered.index("policy_flash_alerts") < ordered.index("news_sentiment_hourly")
    assert ordered.index("market_quotes_eod") < ordered.index("company_valuation_daily")


def test_unknown_data_source(personal_portfolio, tmp_path):
    config = tmp_path / "invalid_pipeline.toml"
    config.write_text(
        """
        [[tasks]]
        id = "unknown_source_task"
        source = "不存在的数据源"
        dataset = "demo"
        frequency = "daily"
        """
    )

    with pytest.raises(UnknownDataSourceError):
        load_pipeline_plan_from_toml(config, portfolio=personal_portfolio)


def test_duplicate_task_ids(tmp_path):
    config = tmp_path / "duplicate_ids.toml"
    config.write_text(
        """
        [[tasks]]
        id = "dup"
        source = "Tushare Pro"
        dataset = "demo"
        frequency = "daily"

        [[tasks]]
        id = "dup"
        source = "Tushare Pro"
        dataset = "demo2"
        frequency = "weekly"
        """
    )

    plan = load_portfolio_from_toml("configs/data_sources.personal.toml")

    with pytest.raises(ValueError):
        load_pipeline_plan_from_toml(config, portfolio=plan)


def test_cycle_detection(tmp_path):
    config = tmp_path / "cycle.toml"
    config.write_text(
        """
        [[tasks]]
        id = "task_a"
        source = "Tushare Pro"
        dataset = "a"
        frequency = "daily"
        depends_on = ["task_b"]

        [[tasks]]
        id = "task_b"
        source = "Tushare Pro"
        dataset = "b"
        frequency = "daily"
        depends_on = ["task_a"]
        """
    )

    portfolio = load_portfolio_from_toml("configs/data_sources.personal.toml")

    with pytest.raises(CyclicDependencyError):
        load_pipeline_plan_from_toml(config, portfolio=portfolio)
