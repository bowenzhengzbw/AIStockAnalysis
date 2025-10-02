import pytest

from src.utils import (
    BudgetExceededError,
    DataPortfolio,
    DataSource,
    load_portfolio_from_toml,
)


def test_load_portfolio_from_toml_round_trip(tmp_path):
    config_file = tmp_path / "portfolio.toml"
    config_file.write_text(
        """
        budget_limit = 1500
        currency = "CNY"

        [[sources]]
        name = "测试源A"
        category = "macro"
        cost = 500
        frequency = "monthly"
        description = "Macro data feed"
        tags = ["macro", "official"]

        [[sources]]
        name = "测试源B"
        category = "news"
        cost = 800
        tags = ["news"]
        """
    )

    portfolio = load_portfolio_from_toml(config_file)

    assert portfolio.budget_limit == 1500
    assert portfolio.default_currency == "CNY"
    assert len(portfolio.sources) == 2
    assert {source.name for source in portfolio.sources} == {"测试源A", "测试源B"}
    assert pytest.approx(portfolio.annual_cost()) == 1300

    grouped = portfolio.group_by_category()
    assert set(grouped) == {"macro", "news"}
    assert grouped["macro"][0].name == "测试源A"

    tag_index = portfolio.tag_index()
    assert set(tag_index) == {"macro", "official", "news"}


def test_check_budget_success():
    portfolio = DataPortfolio(
        sources=[
            DataSource(name="A", category="macro", cost=400),
            DataSource(name="B", category="news", cost=300),
        ],
        budget_limit=800,
    )

    total = portfolio.check_budget()
    assert pytest.approx(total) == 700


def test_check_budget_failure():
    portfolio = DataPortfolio(
        sources=[
            DataSource(name="A", category="macro", cost=1000),
            DataSource(name="B", category="news", cost=600),
        ],
        budget_limit=1500,
    )

    with pytest.raises(BudgetExceededError):
        portfolio.check_budget()
