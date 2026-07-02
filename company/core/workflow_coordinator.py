from typing import Dict

from company.core.employee import Employee
from company.core.task_context import TaskContext
from company.core.task_planner import TaskPlan


class EmployeeRegistry:
    def __init__(self):
        self._employees: Dict[str, Employee] = {}

    def register(self, employee: Employee) -> None:
        self._employees[employee.role] = employee

    def get(self, role_name: str) -> Employee:
        if role_name not in self._employees:
            raise KeyError(f"Employee role is not registered: {role_name}")

        return self._employees[role_name]


class WorkflowCoordinator:
    """
    TaskPlanに従ってEmployeeを順番に実行し、TaskContextを引き継ぐ調整層。

    WorkflowV2、CEO、Conversation、CompanyMemoryには依存せず、TaskContextだけを共有する。
    """

    def __init__(self, employee_registry: EmployeeRegistry):
        self.employee_registry = employee_registry

    def run(self, plan: TaskPlan, context: TaskContext) -> TaskContext:
        for planned_task in plan.get_tasks():
            employee = self.employee_registry.get(planned_task.employee_role)
            artifact = employee.execute_task(context.task)
            context.add_artifact(artifact)

        return context
