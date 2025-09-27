"""Reporting service assembling comprehensive output."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from ..config import settings


def build_report(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Compose final report payload."""

    timestamp = datetime.utcnow().isoformat()
    return {
        "generated_at": timestamp,
        "environment": settings.environment,
        "app_name": settings.app_name,
        "analysis": analysis,
    }
