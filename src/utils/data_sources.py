"""Utilities for managing personal-investor data source portfolios."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, MutableMapping, Sequence

import tomllib


__all__ = [
    "BudgetExceededError",
    "DataSource",
    "DataPortfolio",
    "load_portfolio_from_toml",
]


class BudgetExceededError(ValueError):
    """Raised when a data source portfolio breaches its configured budget."""


@dataclass(frozen=True, slots=True)
class DataSource:
    """A single data source subscription or feed."""

    name: str
    category: str
    cost: float = 0.0
    currency: str = "CNY"
    frequency: str | None = None
    description: str = ""
    tags: Sequence[str] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, object]:
        """Serialize the data source to a plain dictionary."""

        return {
            "name": self.name,
            "category": self.category,
            "cost": float(self.cost),
            "currency": self.currency,
            "frequency": self.frequency,
            "description": self.description,
            "tags": tuple(self.tags),
        }


@dataclass(slots=True)
class DataPortfolio:
    """A collection of data sources managed under a shared annual budget."""

    sources: List[DataSource]
    budget_limit: float
    default_currency: str = "CNY"

    def annual_cost(self, currency: str | None = None) -> float:
        """Return the total annual cost for sources in the specified currency."""

        target_currency = currency or self.default_currency
        total = 0.0
        for source in self.sources:
            if source.currency != target_currency:
                continue
            total += float(source.cost)
        return round(total, 2)

    def check_budget(self, currency: str | None = None) -> float:
        """Validate that annual cost does not exceed the configured budget."""

        target_currency = currency or self.default_currency
        total = self.annual_cost(target_currency)
        if total > self.budget_limit:
            raise BudgetExceededError(
                "Annual cost %.2f %s exceeds budget limit %.2f %s"
                % (total, target_currency, self.budget_limit, target_currency)
            )
        return total

    def group_by_category(self) -> Dict[str, List[DataSource]]:
        """Group sources by their category."""

        grouped: Dict[str, List[DataSource]] = {}
        for source in self.sources:
            grouped.setdefault(source.category, []).append(source)
        return grouped

    def tag_index(self) -> Dict[str, List[DataSource]]:
        """Build an inverted index of tags to the sources carrying them."""

        index: Dict[str, List[DataSource]] = {}
        for source in self.sources:
            for tag in source.tags:
                index.setdefault(tag, []).append(source)
        return index

    def to_dict(self) -> Dict[str, object]:
        """Serialize the portfolio to a dictionary."""

        return {
            "budget_limit": float(self.budget_limit),
            "default_currency": self.default_currency,
            "sources": [source.to_dict() for source in self.sources],
        }


def _normalise_source_mapping(
    mapping: Mapping[str, object],
    *,
    default_currency: str,
) -> DataSource:
    """Create a :class:`DataSource` from an arbitrary mapping."""

    tags = mapping.get("tags", ())
    if isinstance(tags, str):
        tags = (tags,)
    elif isinstance(tags, Iterable):
        tags = tuple(str(tag) for tag in tags)
    else:
        tags = ()

    return DataSource(
        name=str(mapping["name"]),
        category=str(mapping.get("category", "uncategorised")),
        cost=float(mapping.get("cost", 0.0)),
        currency=str(mapping.get("currency", default_currency)),
        frequency=(
            None
            if mapping.get("frequency") in (None, "")
            else str(mapping.get("frequency"))
        ),
        description=str(mapping.get("description", "")),
        tags=tags,
    )


def load_portfolio_from_toml(path: str | Path) -> DataPortfolio:
    """Load a :class:`DataPortfolio` definition from a TOML configuration file."""

    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Portfolio configuration not found: {config_path}")

    with config_path.open("rb") as fh:
        payload: MutableMapping[str, object] = tomllib.load(fh)

    default_currency = str(payload.get("currency", "CNY"))
    raw_sources = payload.get("sources", [])
    if not isinstance(raw_sources, list):
        raise TypeError("Expected 'sources' to be a list of mappings")

    sources = [
        _normalise_source_mapping(raw_source, default_currency=default_currency)
        for raw_source in raw_sources
    ]

    budget_limit = float(payload.get("budget_limit", 0.0))

    portfolio = DataPortfolio(
        sources=sources,
        budget_limit=budget_limit,
        default_currency=default_currency,
    )
    return portfolio
