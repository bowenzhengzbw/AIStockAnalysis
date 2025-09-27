"""Data ingestion orchestration."""

from __future__ import annotations

from typing import Dict, Iterable, List

from ..data.sources import DataSource, default_sources
from ..utils.logging import get_logger

logger = get_logger(__name__)


class IngestionPipeline:
    """Coordinate raw data acquisition across macro, industry, and micro layers."""

    def __init__(self, sources: Dict[str, DataSource] | None = None) -> None:
        self.sources = sources or default_sources()

    def run(self) -> Dict[str, List[Dict[str, object]]]:
        """Execute ingestion respecting regulatory traceability requirements."""

        aggregated: Dict[str, List[Dict[str, object]]] = {}
        for key, source in self.sources.items():
            logger.info(
                "Fetching data", extra={"trace_id": key, "source": source.name}
            )
            aggregated[key] = list(source.fetcher())
        return aggregated
