import pytest

from src.pipelines import PipelineExecutor, PipelinePlan, PipelineTask, PipelineContext


def _sample_plan() -> PipelinePlan:
    return PipelinePlan(
        tasks=[
            PipelineTask(
                id="macro_ingest",
                source="tushare",
                dataset="macro.daily",
                frequency="daily",
            ),
            PipelineTask(
                id="policy_digest",
                source="newswire",
                dataset="policy.events",
                frequency="intraday",
                depends_on=("macro_ingest",),
            ),
            PipelineTask(
                id="company_refresh",
                source="tushare",
                dataset="company.quarterly",
                frequency="weekly",
                depends_on=("macro_ingest", "policy_digest"),
            ),
            PipelineTask(
                id="sentiment_scan",
                source="newswire",
                dataset="sentiment.headlines",
                frequency="intraday",
                depends_on=("policy_digest",),
            ),
        ]
    )


def test_executor_runs_tasks_in_dependency_order():
    plan = _sample_plan()
    executor = PipelineExecutor(plan)

    execution_order: list[str] = []

    def record_handler(task: PipelineTask, context: PipelineContext) -> str:
        execution_order.append(task.id)
        return f"ok-{task.id}"

    executor.set_default_handler(record_handler)
    context = executor.execute()

    assert execution_order == [
        "macro_ingest",
        "policy_digest",
        "company_refresh",
        "sentiment_scan",
    ]
    assert context.get("macro_ingest") == "ok-macro_ingest"
    assert context.get("company_refresh") == "ok-company_refresh"


def test_executor_honours_source_specific_handlers():
    plan = _sample_plan()
    executor = PipelineExecutor(plan)

    handled_by_source: list[str] = []
    handled_by_default: list[str] = []

    def tushare_handler(task: PipelineTask, context: PipelineContext) -> str:
        handled_by_source.append(task.id)
        return "tushare"

    def default_handler(task: PipelineTask, context: PipelineContext) -> str:
        handled_by_default.append(task.id)
        return "default"

    executor.register_source_handler("tushare", tushare_handler)
    executor.set_default_handler(default_handler)
    executor.execute()

    assert handled_by_source == ["macro_ingest", "company_refresh"]
    assert handled_by_default == ["policy_digest", "sentiment_scan"]


def test_executor_executes_requested_tasks_with_dependencies():
    plan = _sample_plan()
    executor = PipelineExecutor(plan)

    execution_order: list[str] = []

    def handler(task: PipelineTask, context: PipelineContext) -> str:
        execution_order.append(task.id)
        return task.id

    executor.set_default_handler(handler)
    executor.execute(tasks=["company_refresh"])

    assert execution_order == ["macro_ingest", "policy_digest", "company_refresh"]


def test_executor_raises_when_handler_missing():
    plan = _sample_plan()
    executor = PipelineExecutor(plan)

    with pytest.raises(KeyError):
        executor.execute()


def test_executor_errors_on_unknown_task_request():
    plan = _sample_plan()
    executor = PipelineExecutor(plan)
    executor.set_default_handler(lambda task, ctx: None)

    with pytest.raises(KeyError):
        executor.execute(tasks=["unknown_task"])
