import pytest

from src.data_providers import (
    SyntheticCailiansheClient,
    SyntheticNbsClient,
    SyntheticTushareClient,
)
from src.pipelines import (
    MissingProviderError,
    PipelineRuntime,
    create_runtime_from_config,
    load_pipeline_plan_from_toml,
)
from src.utils.data_sources import load_portfolio_from_toml


@pytest.fixture()
def runtime() -> PipelineRuntime:
    providers = (
        SyntheticTushareClient(),
        SyntheticCailiansheClient(),
        SyntheticNbsClient(),
    )
    return create_runtime_from_config(
        plan_path="configs/pipeline.personal.toml",
        portfolio_path="configs/data_sources.personal.toml",
        providers=providers,
    )


def test_runtime_executes_all_tasks(runtime: PipelineRuntime) -> None:
    context = runtime.run()

    macro = context.get("macro_indicators_daily")
    assert macro.dataset == "macro_indicators"
    assert len(macro.payload) >= 3

    quotes = context.get("market_quotes_eod")
    assert quotes.dataset == "market_quotes"
    assert {record["symbol"] for record in quotes.payload} >= {
        "600519.SH",
        "300750.SZ",
    }

    policy = context.get("policy_flash_alerts")
    assert policy.metadata["records"] == len(policy.payload) == 2

    sentiment = context.get("news_sentiment_hourly")
    assert sentiment.metadata["task_id"] == "news_sentiment_hourly"
    assert all("sentiment" in record for record in sentiment.payload)

    official = context.get("macro_monthly_statistical")
    assert official.dataset == "macro_statistical"
    assert any(
        record["indicator"] == "工业增加值" for record in official.payload
    )

    financials = context.get("company_financials_quarterly")
    assert financials.dataset == "financial_summary"
    assert {row["symbol"] for row in financials.payload} >= {"600519.SH", "300750.SZ"}

    valuation = context.get("company_valuation_daily")
    assert valuation.dataset == "valuation_snapshot"
    assert any(row["pe_ttm"] for row in valuation.payload)


def test_runtime_supports_partial_execution(runtime: PipelineRuntime) -> None:
    context = runtime.run(tasks=["news_sentiment_hourly"])

    assert "policy_flash_alerts" in context.state
    assert "news_sentiment_hourly" in context.state
    assert "market_quotes_eod" not in context.state


def test_runtime_requires_all_providers() -> None:
    providers = (SyntheticTushareClient(), SyntheticCailiansheClient())
    with pytest.raises(MissingProviderError):
        create_runtime_from_config(
            plan_path="configs/pipeline.personal.toml",
            portfolio_path="configs/data_sources.personal.toml",
            providers=providers,
        )


def test_runtime_passes_metadata() -> None:
    plan = load_pipeline_plan_from_toml(
        "configs/pipeline.personal.toml",
        portfolio=load_portfolio_from_toml("configs/data_sources.personal.toml"),
    )

    class RecordingProvider(SyntheticTushareClient):
        def __init__(self) -> None:
            super().__init__()
            self.calls: list[tuple[str, dict]] = []

        def fetch(self, dataset: str, *, window=None, metadata=None):  # type: ignore[override]
            result = super().fetch(dataset, window=window, metadata=metadata)
            self.calls.append((dataset, dict(result.metadata)))
            return result

    provider = RecordingProvider()
    runtime = PipelineRuntime(plan, [provider, SyntheticCailiansheClient(), SyntheticNbsClient()])
    runtime.run(tasks=["macro_indicators_daily"])

    assert provider.calls[0][1]["task_id"] == "macro_indicators_daily"
    assert provider.calls[0][1]["window"] == "10y"
