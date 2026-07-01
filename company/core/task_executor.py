from typing import Any, Dict

from company.core.task import Task


class TaskExecutor:
    """
    Project SHIRO Version1.0 TaskExecutor

    役割:
    - Taskの実行ライフサイクルを一箇所に集約する
    - 将来的なBrain、Retry、Memory、Logging、Provider、Cost、Prompt接続の入口にする
    - EmployeeがTask実行の詳細を直接持たなくてよい構造にする
    """

    def execute(self, task: Task) -> Task:
        task.start()

        try:
            output_data = self._execute_dummy_brain(task)
            task.complete(output_data)
            return task
        except Exception as e:
            task.fail(str(e))
            raise

    def _execute_dummy_brain(self, task: Task) -> Dict[str, Any]:
        """
        Brain V2接続前のダミー実行。

        現段階ではTask.input_dataを元に、Task.output_dataへ保存できる構造化データを返す。
        """
        return {
            "task_id": task.task_id,
            "task_type": task.task_type.value,
            "instruction": task.instruction,
            "input_data": task.input_data,
            "result": self._build_dummy_result(task),
        }

    def _build_dummy_result(self, task: Task) -> str:
        if task.input_data:
            return f"Dummy execution completed for {task.task_type.value} with input_data."

        return f"Dummy execution completed for {task.task_type.value}."
