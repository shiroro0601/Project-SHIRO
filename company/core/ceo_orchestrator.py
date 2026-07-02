from dataclasses import dataclass
from typing import List

from company.core.employee import Employee


@dataclass
class CEOOrchestratorResult:
    results: list
    completed_count: int
    total_count: int


class CEOOrchestrator:
    """
    複数Employeeへ順番にTaskを渡すCEO層。

    Task生成、品質チェック、Retry、記憶保存は担当せず、社員の順番制御だけを担当する。
    """

    def __init__(self, employees: List[Employee]):
        if not employees:
            raise ValueError("employees must not be empty.")

        self.employees = employees

    def run(self, task) -> CEOOrchestratorResult:
        results = []

        for employee in self.employees:
            results.append(employee.execute_task(task))

        return CEOOrchestratorResult(
            results=results,
            completed_count=len(results),
            total_count=len(self.employees),
        )
