from company.core.task import TaskType
from company.core.task_context import TaskContext
from company.core.task_factory import TaskFactory
from company.core.task_planner import SequentialTaskPlanner
from company.core.workflow_coordinator import WorkflowCoordinator
from main_v10_mini_company_demo import create_demo_company, run_demo


def test_demo_company_can_be_created():
    calls = []

    registry = create_demo_company(calls)

    assert registry.get("Researcher").role == "Researcher"
    assert registry.get("Writer").role == "Writer"
    assert registry.get("Reviewer").role == "Reviewer"


def test_demo_runs_researcher_writer_reviewer_in_order():
    result = run_demo()

    assert result["execution_order"] == ["Researcher", "Writer", "Reviewer"]


def test_demo_adds_three_artifacts_to_task_context():
    result = run_demo()

    assert len(result["context"].get_artifacts()) == 3
    assert len(result["artifacts"]) == 3


def test_demo_artifact_contents_are_expected():
    result = run_demo()

    assert result["artifacts"] == [
        {
            "employee_role": "Researcher",
            "task_id": result["task"].task_id,
            "result": "research result",
        },
        {
            "employee_role": "Writer",
            "task_id": result["task"].task_id,
            "result": "script draft",
        },
        {
            "employee_role": "Reviewer",
            "task_id": result["task"].task_id,
            "result": "review result",
        },
    ]


def test_demo_uses_existing_core_components():
    calls = []
    task = TaskFactory.create_task(
        task_type=TaskType.GENERAL,
        instruction="Demo component assembly test",
        input_data={"theme": "test"},
    )
    context = TaskContext(task=task)
    plan = SequentialTaskPlanner().create_plan(task)
    registry = create_demo_company(calls)
    coordinator = WorkflowCoordinator(employee_registry=registry)

    result_context = coordinator.run(plan, context)

    assert result_context is context
    assert calls == ["Researcher", "Writer", "Reviewer"]
    assert [artifact["result"] for artifact in context.get_artifacts()] == [
        "research result",
        "script draft",
        "review result",
    ]
