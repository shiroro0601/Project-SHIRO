import pytest

from company.core.task import TaskType
from company.core.task_factory import TaskFactory
from company.core.task_planner import PlannedTask, SequentialTaskPlanner, TaskPlan


def _task():
    return TaskFactory.create_task(
        task_type=TaskType.GENERAL,
        instruction="Task planner test task",
        input_data={"theme": "test"},
    )


def test_planned_task_can_be_created():
    task = _task()

    planned_task = PlannedTask(
        employee_role="Researcher",
        task=task,
        order=0,
    )

    assert planned_task.employee_role == "Researcher"
    assert planned_task.task is task
    assert planned_task.order == 0


def test_planned_task_negative_order_raises_value_error():
    with pytest.raises(ValueError):
        PlannedTask(
            employee_role="Researcher",
            task=_task(),
            order=-1,
        )


def test_task_plan_adds_task():
    task = _task()
    planned_task = PlannedTask(
        employee_role="Writer",
        task=task,
        order=1,
    )
    plan = TaskPlan()

    plan.add_task(planned_task)

    assert plan.get_tasks() == [planned_task]


def test_task_plan_get_tasks_returns_ordered_tasks():
    task = _task()
    plan = TaskPlan()
    writer = PlannedTask(employee_role="Writer", task=task, order=1)
    reviewer = PlannedTask(employee_role="Reviewer", task=task, order=2)
    researcher = PlannedTask(employee_role="Researcher", task=task, order=0)

    plan.add_task(writer)
    plan.add_task(reviewer)
    plan.add_task(researcher)

    assert plan.get_tasks() == [researcher, writer, reviewer]


def test_task_plan_get_tasks_does_not_mutate_original_order():
    task = _task()
    plan = TaskPlan()
    writer = PlannedTask(employee_role="Writer", task=task, order=1)
    researcher = PlannedTask(employee_role="Researcher", task=task, order=0)

    plan.add_task(writer)
    plan.add_task(researcher)

    assert plan.planned_tasks == [writer, researcher]
    assert plan.get_tasks() == [researcher, writer]


def test_sequential_task_planner_creates_researcher_writer_reviewer_tasks():
    task = _task()
    planner = SequentialTaskPlanner()

    plan = planner.create_plan(task)
    planned_tasks = plan.get_tasks()

    assert [planned_task.employee_role for planned_task in planned_tasks] == [
        "Researcher",
        "Writer",
        "Reviewer",
    ]
    assert [planned_task.order for planned_task in planned_tasks] == [0, 1, 2]
    assert [planned_task.task for planned_task in planned_tasks] == [task, task, task]


def test_sequential_task_planner_returns_task_plan():
    plan = SequentialTaskPlanner().create_plan(_task())

    assert isinstance(plan, TaskPlan)
