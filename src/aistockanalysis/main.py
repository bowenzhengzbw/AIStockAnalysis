"""FastAPI entry point exposing agent orchestration."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import FastAPI

from .agents.orchestrator import AgentOrchestrator
from .config import settings
from .pipelines.feature_engineering import FeatureEngineeringPipeline
from .pipelines.ingestion import IngestionPipeline
from .services.reporting import build_report

app = FastAPI(title=settings.app_name)

_ingestion = IngestionPipeline()
_feature_engineering = FeatureEngineeringPipeline()
_orchestrator = AgentOrchestrator()


@app.get("/health")
def health() -> Dict[str, str]:
    """Return service health indicator."""

    return {"status": "ok", "environment": settings.environment}


@app.post("/analyze")
def analyze(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Trigger end-to-end macro-to-micro analysis."""

    # Step 1: ingest baseline datasets (placeholder for real connectors)
    datasets = _ingestion.run()

    # Step 2: feature engineering pipeline
    features = _feature_engineering.transform(datasets)

    # Step 3: combine payload context with engineered features for agents
    context = {**payload, "features": features}
    analysis = _orchestrator.run(context)
    return build_report(analysis)
