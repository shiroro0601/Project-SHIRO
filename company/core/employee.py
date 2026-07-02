from company.brain import Brain
from company.core.employee_role import DefaultEmployeeRole
from company.core.task import Task
from company.core.task_executor import TaskExecutor


class Employee:
    def __init__(
        self,
        name: str,
        role=None,
        brain=None,
        employee_role=None,
        task_executor: TaskExecutor | None = None,
    ):
        self.name = name
        self.employee_role = self._resolve_employee_role(role, employee_role)
        self.role = self._resolve_legacy_role_name(role)
        self.brain = brain or Brain(provider="dummy", model="shiro-local")
        self.task_executor = task_executor or TaskExecutor()

    def run(self, job):
        raise NotImplementedError("各社員クラスでrun(job)を実装してください。")

    def execute_task(self, task):
        prepared_task = self.employee_role.prepare(task)
        executable_task = prepared_task if prepared_task is not None else task
        role_result = self.employee_role.execute(executable_task)
        result = (
            self.task_executor.execute(role_result)
            if isinstance(role_result, Task)
            else role_result
        )
        if result is None:
            result = self.task_executor.execute(executable_task)
        finalized_result = self.employee_role.finalize(result)
        return finalized_result if finalized_result is not None else result

    def think(self, prompt: str) -> str:
        return self.brain.ask(role=self.role, prompt=prompt)

    def log(self, job, message: str):
        if hasattr(job, "log"):
            job.log(f"[{self.name}] {message}")

    def update_job(self, job, section: str, content):
        if hasattr(job, "update_section"):
            job.update_section(section, content)

    def _resolve_employee_role(self, role, employee_role):
        if employee_role is not None:
            return employee_role

        if self._looks_like_employee_role(role):
            return role

        return DefaultEmployeeRole()

    def _resolve_legacy_role_name(self, role) -> str:
        if self._looks_like_employee_role(role):
            return role.name

        return role or self.employee_role.name

    def _looks_like_employee_role(self, role) -> bool:
        return all(
            hasattr(role, attribute)
            for attribute in ("name", "prepare", "execute", "finalize")
        )
