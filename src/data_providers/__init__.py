"""Synthetic data providers and base interfaces for ingestion pipelines."""

from .base import DataProvider, DatasetNotFoundError, IngestionResult
from .synthetic import (
    SyntheticCailiansheClient,
    SyntheticNbsClient,
    SyntheticTushareClient,
)

__all__ = [
    "DataProvider",
    "DatasetNotFoundError",
    "IngestionResult",
    "SyntheticCailiansheClient",
    "SyntheticNbsClient",
    "SyntheticTushareClient",
]
