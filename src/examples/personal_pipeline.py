"""Run the Phase 1 personal-investor ingestion pipeline with synthetic providers."""

from __future__ import annotations

from pprint import pprint

from src.data_providers import (
    SyntheticCailiansheClient,
    SyntheticNbsClient,
    SyntheticTushareClient,
)
from src.pipelines import create_runtime_from_config


def build_runtime():
    providers = [
        SyntheticTushareClient(),
        SyntheticCailiansheClient(),
        SyntheticNbsClient(),
    ]
    return create_runtime_from_config(
        plan_path="configs/pipeline.personal.toml",
        portfolio_path="configs/data_sources.personal.toml",
        providers=providers,
    )


def main() -> None:
    runtime = build_runtime()
    context = runtime.run()

    print("Pipeline execution completed. Task outputs:")
    for task_id, result in context.state.items():
        print(f"\n[{task_id}]")
        meta = dict(result.metadata)
        pprint({"dataset": result.dataset, "metadata": meta})
        preview = result.payload[:2] if isinstance(result.payload, list) else result.payload
        pprint({"preview": preview})


if __name__ == "__main__":  # pragma: no cover - manual execution entry point
    main()
