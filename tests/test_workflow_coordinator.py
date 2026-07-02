import pytest

from company.core.task import TaskType
from company.core.task_context import TaskContext
from company.core.task_factory import TaskFactory
from company.core.task_planner import PlannedTask, SequentialTaskPlanner, TaskPlan
from company.core.workflow_coordinator import EmployeeRegistry, WorkflowCoordinator


class FakeEmployee:
    def __init__(self, role, calls):
        self.role = role
        self.calls = calls

    def execute_task(self, task):
        self.calls.append(self.role)
        return {
            "employee_role": self.role,
            "task_id": task.task_id,
        }


def _task():
    return TaskFactory.create_task(
        task_type=TaskType.GENERAL,
        instruction="Workflow coordinator test task",
        input_data={"theme": "test"},
    )


def _registry(calls=None):
    calls = calls if calls is not None else []
    registry = EmployeeRegistry()
    registry.register(FakeEmployee("Researcher", calls))
    registry.register(FakeEmployee("Writer", calls))
    registry.register(FakeEmployee("Reviewer", calls))
    return registry


def test_employee_registry_registers_employee():
    calls = []
    employee = FakeEmployee("Researcher", calls)
    registry = EmployeeRegistry()

    registry.register(employee)

    assert registry.get("Researcher") is employee


def test_employee_registry_gets_employee_by_role():
    calls = []
    researcher = FakeEmployee("Researcher", calls)
    writer = FakeEmployee("Writer", calls)
    registry = EmployeeRegistry()

    registry.register(researcher)
    registry.register(writer)

    assert registry.get("Writer") is writer


def test_employee_registry_missing_role_raises_key_error():
    registry = EmployeeRegistry()

    with pytest.raises(KeyError):
        registry.get("Researcher")


def test_workflow_coordinator_runs_task_plan_in_order():
    calls = []
    task = _task()
    context = TaskContext(task=task)
    plan = SequentialTaskPlanner().create_plan(task)
    coordinator = WorkflowCoordinator(employee_registry=_registry(calls))

    coordinator.run(plan, context)

    assert calls == ["Researcher", "Writer", "Reviewer"]


def test_workflow_coordinator_adds_artifacts_to_context():
    calls = []
    task = _task()
    context = TaskContext(task=task)
    plan = SequentialTaskPlanner().create_plan(task)
    coordinator = WorkflowCoordinator(employee_registry=_registry(calls))

    coordinator.run(plan, context)

    assert context.get_artifacts() == [
        {
            "employee_role": "Researcher",
            "task_id": task.task_id,
        },
        {
            "employee_role": "Writer",
            "task_id": task.task_id,
        },
        {
            "employee_role": "Reviewer",
            "task_id": task.task_id,
        },
    ]


def test_workflow_coordinator_returns_same_task_context_instance():
    task = _task()
    context = TaskContext(task=task)
    plan = SequentialTaskPlanner().create_plan(task)
    coordinator = WorkflowCoordinator(employee_registry=_registry())

    result_context = coordinator.run(plan, context)

    assert result_context is context


def test_workflow_coordinator_uses_ordered_plan_tasks():
    calls = []
    task = _task()
    context = TaskContext(task=task)
    plan = TaskPlan(
        planned_tasks=[
            PlannedTask(employee_role="Reviewer", task=task, order=2),
            PlannedTask(employee_role="Researcher", task=task, order=0),
            PlannedTask(employee_role="Writer", task=task, order=1),
        ]
    )
    coordinator = WorkflowCoordinator(employee_registry=_registry(calls))

    coordinator.run(plan, context)

    assert calls == ["Researcher", "Writer", "Reviewer"]


def test_workflow_coordinator_unregistered_role_raises_key_error():
    task = _task()
    context = TaskContext(task=task)
    plan = TaskPlan(
        planned_tasks=[
            PlannedTask(employee_role="Researcher", task=task, order=0),
        ]
    )
    coordinator = WorkflowCoordinator(employee_registry=EmployeeRegistry())

    with pytest.raises(KeyError):
        coordinator.run(plan, context)
