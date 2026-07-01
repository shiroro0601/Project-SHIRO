from datetime import datetime

from company.core.task import Task, TaskType


class TaskFactory:
    """
    Project SHIRO Version1.0 TaskFactory

    役割:
    - Task IDを統一形式で生成する
    - Employeeが直接Taskを安全に作れるようにする
    - 将来的にTaskテンプレート、優先度、コスト制御を追加しやすくする
    """

    @staticmethod
    def create_task(
        task_type: TaskType,
        instruction: str,
        input_data: dict | None = None,
    ) -> Task:
        task_id = TaskFactory._generate_task_id(task_type)

        return Task(
            task_id=task_id,
            task_type=task_type,
            instruction=instruction,
            input_data=input_data or {},
        )

    @staticmethod
    def _generate_task_id(task_type: TaskType) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        return f"task_{task_type.value}_{timestamp}"