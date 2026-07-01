from typing import Any, Dict

from company.core.task import Task


class BrainV2:
    """
    Project SHIRO Version1.0 Brain V2

    Taskを受け取り、将来Provider/LLMへ渡すための思考レイヤー。
    現段階では外部LLMへ接続せず、Task構造を保ったダミー応答を返す。
    """

    def ask(self, task: Task) -> Dict[str, Any]:
        return {
            "result": f"BrainV2 dummy response for {task.task_type.value}",
            "task_type": task.task_type.value,
            "instruction": task.instruction,
            "input_data": task.input_data,
        }
