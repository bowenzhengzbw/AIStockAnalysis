"""High-level runtime wiring pipeline plans with registered data providers."""

from __future__ import annotations

from typing import Iterable, Sequence

from src.data_providers import DataProvider, IngestionResult
from src.utils.data_sources import DataPortfolio, load_portfolio_from_toml

from .executor import PipelineContext, PipelineExecutor
from .planner import PipelinePlan, load_pipeline_plan_from_toml

__all__ = ["MissingProviderError", "PipelineRuntime", "create_runtime_from_config"]


class MissingProviderError(RuntimeError):
    """Raised when the runtime cannot find a provider for a required data source."""


class PipelineRuntime:
    """Facade bundling plan loading, provider registration, and execution."""

    def __init__(self, plan: PipelinePlan, providers: Iterable[DataProvider]):
        self._plan = plan
        self._executor = PipelineExecutor(plan)
        self._providers = {provider.name: provider for provider in providers}
        for source, provider in self._providers.items():
            self._executor.register_source_handler(source, self._make_handler(provider))
        missing_sources = {
            task.source for task in plan.tasks if task.source not in self._providers
        }
        if missing_sources:
            missing = ", ".join(sorted(missing_sources))
            raise MissingProviderError(
                "No providers registered for sources: " + missing
            )

    @staticmethod
    def _make_handler(provider: DataProvider):
        def handler(task, context: PipelineContext) -> IngestionResult:
            metadata = {
                "task_id": task.id,
                "frequency": task.frequency,
                "owners": tuple(task.owners),
                "tags": tuple(task.tags),
            }
            return provider.fetch(
                task.dataset,
                window=task.window,
                metadata=metadata,
            )

        return handler

    @property
    def plan(self) -> PipelinePlan:
        return self._plan

    def run(
        self,
        tasks: Sequence[str] | None = None,
        *,
        context: PipelineContext | None = None,
    ) -> PipelineContext:
        return self._executor.execute(tasks=tasks, context=context)


def create_runtime_from_config(
    *,
    plan_path: str,
    providers: Iterable[DataProvider],
    portfolio_path: str | None = None,
) -> PipelineRuntime:
    """Load pipeline plan (and optional portfolio) before constructing runtime."""

    portfolio: DataPortfolio | None = None
    if portfolio_path is not None:
        portfolio = load_portfolio_from_toml(portfolio_path)
    plan = load_pipeline_plan_from_toml(plan_path, portfolio=portfolio)
    return PipelineRuntime(plan, providers)
