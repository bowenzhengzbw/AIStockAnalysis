"""Abstract interfaces for data providers used by the ingestion pipelines."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Mapping, Sequence

__all__ = [
    "DatasetNotFoundError",
    "DataProvider",
    "IngestionResult",
]


class DatasetNotFoundError(KeyError):
    """Raised when a provider cannot serve the requested dataset."""


@dataclass(frozen=True, slots=True)
class IngestionResult:
    """Wrapper around raw payloads produced by provider fetch operations."""

    dataset: str
    payload: object
    metadata: Mapping[str, object]


class DataProvider(ABC):
    """Base class for concrete data providers (Tushare, 财联社等)."""

    name: str

    @abstractmethod
    def available_datasets(self) -> Sequence[str]:
        """Return the identifiers of datasets served by the provider."""

    @abstractmethod
    def fetch(
        self,
        dataset: str,
        *,
        window: str | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> IngestionResult:
        """Retrieve data for the given dataset."""

    def _validate_dataset(self, dataset: str) -> None:
        if dataset not in self.available_datasets():
            raise DatasetNotFoundError(
                f"Provider '{self.name}' does not serve dataset '{dataset}'"
            )

    @staticmethod
    def _merge_metadata(
        metadata: Mapping[str, object] | None,
        extra: Mapping[str, object] | None = None,
    ) -> Mapping[str, object]:
        base = dict(metadata or {})
        if extra:
            base.update(extra)
        return base
