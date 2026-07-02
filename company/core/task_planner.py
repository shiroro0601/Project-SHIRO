from dataclasses import dataclass, field
from typing import List, Protocol

from company.core.task import Task


@dataclass
class PlannedTask:
    employee_role: str
    task: Task
    order: int

    def __post_init__(self) -> None:
        if self.order < 0:
            raise ValueError("order must be greater than or equal to 0.")


@dataclass
class TaskPlan:
    planned_tasks: List[PlannedTask] = field(default_factory=list)

    def add_task(self, planned_task: PlannedTask) -> None:
        self.planned_tasks.append(planned_task)

    def get_tasks(self) -> List[PlannedTask]:
        return sorted(self.planned_tasks, key=lambda planned_task: planned_task.order)


class TaskPlanner(Protocol):
    def create_plan(self, task: Task) -> TaskPlan:
        ...


class SequentialTaskPlanner:
    def create_plan(self, task: Task) -> TaskPlan:
        plan = TaskPlan()

        for order, employee_role in enumerate(["Researcher", "Writer", "Reviewer"]):
            plan.add_task(
                PlannedTask(
                    employee_role=employee_role,
                    task=task,
                    order=order,
                )
            )

        return plan
