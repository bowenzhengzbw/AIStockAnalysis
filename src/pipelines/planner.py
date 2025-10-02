"""Pipeline planning utilities for data ingestion and refresh scheduling."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, MutableMapping, Sequence

import tomllib

from src.utils.data_sources import DataPortfolio

__all__ = [
    "PipelineTask",
    "PipelinePlan",
    "UnknownDataSourceError",
    "CyclicDependencyError",
    "load_pipeline_plan_from_toml",
]


class UnknownDataSourceError(ValueError):
    """Raised when a pipeline task references a data source not present in the portfolio."""


class CyclicDependencyError(ValueError):
    """Raised when pipeline tasks contain a dependency cycle."""


@dataclass(frozen=True, slots=True)
class PipelineTask:
    """Definition of a single ingestion or refresh task within the pipeline plan."""

    id: str
    source: str
    dataset: str
    frequency: str
    owners: Sequence[str] = field(default_factory=tuple)
    depends_on: Sequence[str] = field(default_factory=tuple)
    description: str = ""
    tags: Sequence[str] = field(default_factory=tuple)
    window: str | None = None

    def to_dict(self) -> Dict[str, object]:
        """Serialize the task to a plain dictionary."""

        return {
            "id": self.id,
            "source": self.source,
            "dataset": self.dataset,
            "frequency": self.frequency,
            "owners": tuple(self.owners),
            "depends_on": tuple(self.depends_on),
            "description": self.description,
            "tags": tuple(self.tags),
            "window": self.window,
        }


@dataclass(slots=True)
class PipelinePlan:
    """Collection of pipeline tasks with helper accessors for orchestration."""

    tasks: List[PipelineTask]
    name: str | None = None
    currency: str = "CNY"

    def group_by_frequency(self) -> Dict[str, List[PipelineTask]]:
        """Group tasks by their declared refresh frequency."""

        grouped: Dict[str, List[PipelineTask]] = {}
        for task in self.tasks:
            grouped.setdefault(task.frequency, []).append(task)
        return grouped

    def tasks_for_source(self, source: str) -> List[PipelineTask]:
        """Return all tasks that pull from a given data source."""

        return [task for task in self.tasks if task.source == source]

    def missing_dependencies(self) -> Dict[str, List[str]]:
        """Return mapping of task IDs to unresolved dependency identifiers."""

        known_ids = {task.id for task in self.tasks}
        missing: Dict[str, List[str]] = {}
        for task in self.tasks:
            unresolved = [dep for dep in task.depends_on if dep not in known_ids]
            if unresolved:
                missing[task.id] = unresolved
        return missing

    def assert_no_missing_dependencies(self) -> None:
        """Raise an error if any task depends on an undefined task ID."""

        missing = self.missing_dependencies()
        if missing:
            details = ", ".join(
                f"{task_id}: {deps}" for task_id, deps in sorted(missing.items())
            )
            raise ValueError(f"Undefined dependencies detected: {details}")

    def topological_order(self) -> List[PipelineTask]:
        """Return tasks ordered so that dependencies always precede dependants."""

        self.assert_no_missing_dependencies()

        tasks_by_id = {task.id: task for task in self.tasks}
        adjacency: Dict[str, List[str]] = {task.id: [] for task in self.tasks}
        in_degree: Dict[str, int] = {task.id: 0 for task in self.tasks}

        for task in self.tasks:
            for dependency in task.depends_on:
                if dependency not in tasks_by_id:
                    # ``assert_no_missing_dependencies`` already guards against this,
                    # but keep the check for defensive programming.
                    continue
                adjacency.setdefault(dependency, []).append(task.id)
                in_degree[task.id] += 1

        traversal_queue: deque[str] = deque(
            task_id for task_id, degree in in_degree.items() if degree == 0
        )
        ordered_ids: List[str] = []

        while traversal_queue:
            current = traversal_queue.popleft()
            ordered_ids.append(current)

            for dependant in adjacency.get(current, ()):  # pragma: no branch - simple lookup
                in_degree[dependant] -= 1
                if in_degree[dependant] == 0:
                    traversal_queue.append(dependant)

        if len(ordered_ids) != len(self.tasks):
            cycle_nodes = [task_id for task_id, degree in in_degree.items() if degree > 0]
            cycle_nodes.sort()
            raise CyclicDependencyError(
                "Cyclic dependency detected among tasks: " + ", ".join(cycle_nodes)
            )

        return [tasks_by_id[task_id] for task_id in ordered_ids]

    def assert_no_cycles(self) -> None:
        """Raise an error if the task dependency graph contains a cycle."""

        self.topological_order()

    def to_dict(self) -> Dict[str, object]:
        """Serialize the full plan to a dictionary representation."""

        return {
            "name": self.name,
            "currency": self.currency,
            "tasks": [task.to_dict() for task in self.tasks],
        }


def _normalise_sequence(value: object, field_name: str) -> Sequence[str]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, Iterable):
        return tuple(str(item) for item in value)
    raise TypeError(f"Expected iterable for field '{field_name}', got {type(value)!r}")


def _normalise_task_mapping(mapping: Mapping[str, object]) -> PipelineTask:
    try:
        task_id = str(mapping["id"])
    except KeyError as exc:
        raise KeyError("Each task must define an 'id'") from exc

    dataset = str(mapping.get("dataset", task_id))
    frequency = str(mapping.get("frequency", "unspecified"))
    source = str(mapping.get("source", ""))
    if not source:
        raise ValueError(f"Task '{task_id}' must define a 'source'")

    owners = _normalise_sequence(mapping.get("owners"), "owners")
    depends_on = _normalise_sequence(mapping.get("depends_on"), "depends_on")
    tags = _normalise_sequence(mapping.get("tags"), "tags")

    description = str(mapping.get("description", ""))
    window = mapping.get("window")
    if window is not None:
        window = str(window)

    return PipelineTask(
        id=task_id,
        source=source,
        dataset=dataset,
        frequency=frequency,
        owners=owners,
        depends_on=depends_on,
        description=description,
        tags=tags,
        window=window,
    )


def load_pipeline_plan_from_toml(
    path: str | Path,
    portfolio: DataPortfolio | None = None,
) -> PipelinePlan:
    """Load a :class:`PipelinePlan` definition from a TOML configuration file."""

    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Pipeline plan configuration not found: {config_path}")

    with config_path.open("rb") as fh:
        payload: MutableMapping[str, object] = tomllib.load(fh)

    raw_tasks = payload.get("tasks", [])
    if not isinstance(raw_tasks, list):
        raise TypeError("Expected 'tasks' to be a list of mappings")

    known_sources = None
    if portfolio is not None:
        known_sources = {source.name for source in portfolio.sources}

    tasks: List[PipelineTask] = []
    seen_ids: set[str] = set()
    for raw_task in raw_tasks:
        if not isinstance(raw_task, Mapping):
            raise TypeError("Each task definition must be a mapping")
        task = _normalise_task_mapping(raw_task)
        if task.id in seen_ids:
            raise ValueError(f"Duplicate task id detected: {task.id}")
        seen_ids.add(task.id)
        if known_sources is not None and task.source not in known_sources:
            raise UnknownDataSourceError(
                f"Task '{task.id}' references unknown data source '{task.source}'"
            )
        tasks.append(task)

    plan = PipelinePlan(
        tasks=tasks,
        name=str(payload.get("name")) if payload.get("name") else None,
        currency=str(payload.get("currency", "CNY")),
    )
    plan.assert_no_missing_dependencies()
    plan.assert_no_cycles()
    return plan
