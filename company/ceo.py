"""
Project SHIRO v0.8
CEOクラス
"""

from typing import Dict

from company.employee import Employee
from company.task import Task
from company.artifact import Artifact


class CEO(Employee):
    """
    社長
    社員へ仕事を振る役
    """

    def __init__(self):

        super().__init__(
            name="CEO",
            department="経営"
        )

        self.employees: Dict[str, Employee] = {}

    def add_employee(self, employee: Employee) -> None:
        """
        社員を登録
        """

        self.employees[employee.department] = employee

        self.log(
            f"{employee.department}『{employee.name}』を採用しました。"
        )

    def assign(self, department: str, task: Task) -> Artifact:
        """
        部署へ仕事を依頼
        """

        if department not in self.employees:
            raise ValueError(f"{department} 部が存在しません。")

        employee = self.employees[department]

        self.log(
            f"{department}へ仕事を依頼：{task.title}"
        )

        task.start()

        try:

            artifact = employee.run(task)

            task.complete()

            self.log(
                f"{department}が仕事を完了しました。"
            )

            return artifact

        except Exception:

            task.fail()
            raise

    def run(self, task: Task) -> Artifact:
        """
        CEO自身の仕事
        （今後実装）
        """
        raise NotImplementedError()