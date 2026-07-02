import pytest

from company.core.ceo_orchestrator import CEOOrchestrator, CEOOrchestratorResult
from company.core.task import TaskType
from company.core.task_factory import TaskFactory


class FakeEmployee:
    def __init__(self, name, calls, should_fail=False):
        self.name = name
        self.calls = calls
        self.should_fail = should_fail

    def execute_task(self, task):
        self.calls.append(self.name)

        if self.should_fail:
            raise RuntimeError(f"{self.name} failed")

        return {
            "employee": self.name,
            "task_id": task.task_id,
        }


def _task():
    return TaskFactory.create_task(
        task_type=TaskType.GENERAL,
        instruction="CEO Orchestrator test task",
        input_data={"theme": "test"},
    )


def test_ceo_orchestrator_runs_employees_in_order():
    calls = []
    orchestrator = CEOOrchestrator(
        employees=[
            FakeEmployee("Researcher", calls),
            FakeEmployee("Writer", calls),
            FakeEmployee("Reviewer", calls),
        ]
    )

    orchestrator.run(_task())

    assert calls == ["Researcher", "Writer", "Reviewer"]


def test_ceo_orchestrator_returns_results_as_list():
    calls = []
    task = _task()
    orchestrator = CEOOrchestrator(
        employees=[
            FakeEmployee("Researcher", calls),
            FakeEmployee("Writer", calls),
        ]
    )

    result = orchestrator.run(task)

    assert isinstance(result.results, list)
    assert result.results == [
        {
            "employee": "Researcher",
            "task_id": task.task_id,
        },
        {
            "employee": "Writer",
            "task_id": task.task_id,
        },
    ]


def test_ceo_orchestrator_result_counts_are_correct():
    calls = []
    orchestrator = CEOOrchestrator(
        employees=[
            FakeEmployee("Researcher", calls),
            FakeEmployee("Writer", calls),
            FakeEmployee("Reviewer", calls),
        ]
    )

    result = orchestrator.run(_task())

    assert isinstance(result, CEOOrchestratorResult)
    assert result.completed_count == 3
    assert result.total_count == 3


def test_ceo_orchestrator_empty_employees_raises_value_error():
    with pytest.raises(ValueError):
        CEOOrchestrator(employees=[])


def test_ceo_orchestrator_calls_employee_execute_task():
    calls = []
    employee = FakeEmployee("Researcher", calls)
    orchestrator = CEOOrchestrator(employees=[employee])

    orchestrator.run(_task())

    assert calls == ["Researcher"]


def test_ceo_orchestrator_stops_and_raises_when_employee_fails():
    calls = []
    orchestrator = CEOOrchestrator(
        employees=[
            FakeEmployee("Researcher", calls),
            FakeEmployee("Writer", calls, should_fail=True),
            FakeEmployee("Reviewer", calls),
        ]
    )

    with pytest.raises(RuntimeError, match="Writer failed"):
        orchestrator.run(_task())

    assert calls == ["Researcher", "Writer"]
