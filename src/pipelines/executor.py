"""Execution utilities for running planned pipeline tasks."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, MutableMapping, Sequence

from .planner import PipelinePlan, PipelineTask

__all__ = [
    "PipelineContext",
    "PipelineExecutor",
    "TaskHandler",
]

TaskHandler = Callable[[PipelineTask, "PipelineContext"], object]


@dataclass(slots=True)
class PipelineContext:
    """Mutable context shared across pipeline task executions."""

    state: MutableMapping[str, object] = field(default_factory=dict)

    def record(self, task_id: str, result: object) -> None:
        """Store the execution result for a task."""

        self.state[task_id] = result

    def get(self, task_id: str) -> object:
        """Retrieve a previously recorded task result."""

        return self.state[task_id]

    def __contains__(self, task_id: object) -> bool:  # pragma: no cover - trivial
        return task_id in self.state


class PipelineExecutor:
    """Execute tasks defined in a :class:`PipelinePlan` in dependency order."""

    def __init__(self, plan: PipelinePlan) -> None:
        self._plan = plan
        self._task_handlers: Dict[str, TaskHandler] = {}
        self._source_handlers: Dict[str, TaskHandler] = {}
        self._default_handler: TaskHandler | None = None

    def register_task_handler(self, task_id: str, handler: TaskHandler) -> None:
        """Register a handler for a specific task identifier."""

        self._task_handlers[task_id] = handler

    def register_source_handler(self, source: str, handler: TaskHandler) -> None:
        """Register a handler that will be used for all tasks pulling from a source."""

        self._source_handlers[source] = handler

    def set_default_handler(self, handler: TaskHandler) -> None:
        """Register a fallback handler used when no specific handler is found."""

        self._default_handler = handler

    def execute(
        self,
        tasks: Sequence[str] | None = None,
        context: PipelineContext | None = None,
    ) -> PipelineContext:
        """Execute a subset (or all) tasks in dependency order.

        Parameters
        ----------
        tasks:
            Optional sequence of task identifiers to execute. Dependencies of the
            selected tasks are automatically included. When ``None`` (default),
            all tasks in the plan are executed.
        context:
            Optional existing :class:`PipelineContext` to reuse between runs.
        """

        execution_context = context or PipelineContext()
        ordered_tasks = self._plan.topological_order()
        tasks_to_run = self._select_tasks(ordered_tasks, tasks)

        for task in tasks_to_run:
            handler = self._resolve_handler(task)
            if handler is None:
                raise KeyError(
                    f"No handler registered for task '{task.id}' (source='{task.source}')"
                )
            result = handler(task, execution_context)
            execution_context.record(task.id, result)

        return execution_context

    def _select_tasks(
        self,
        ordered_tasks: Sequence[PipelineTask],
        requested: Sequence[str] | None,
    ) -> Sequence[PipelineTask]:
        if requested is None:
            return ordered_tasks

        request_set = set(requested)
        task_by_id = {task.id: task for task in ordered_tasks}
        missing = request_set - task_by_id.keys()
        if missing:
            missing_ids = ", ".join(sorted(missing))
            raise KeyError(f"Requested tasks not found in plan: {missing_ids}")

        required: set[str] = set()

        def include_with_dependencies(task_id: str) -> None:
            if task_id in required:
                return
            required.add(task_id)
            task = task_by_id[task_id]
            for dependency in task.depends_on:
                include_with_dependencies(dependency)

        for task_id in request_set:
            include_with_dependencies(task_id)

        return [task for task in ordered_tasks if task.id in required]

    def _resolve_handler(self, task: PipelineTask) -> TaskHandler | None:
        if task.id in self._task_handlers:
            return self._task_handlers[task.id]
        if task.source in self._source_handlers:
            return self._source_handlers[task.source]
        return self._default_handler
