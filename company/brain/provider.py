from typing import Any, Dict

from company.core.task import Task


class BaseProvider:
    def generate(self, task: Task) -> Dict[str, Any]:
        raise NotImplementedError("Provider must implement generate(task).")


class DummyProvider(BaseProvider):
    def generate(self, task: Task) -> Dict[str, Any]:
        return {
            "result": f"DummyProvider response for {task.task_type.value}",
            "provider": "dummy",
            "task_type": task.task_type.value,
            "instruction": task.instruction,
            "input_data": task.input_data,
        }


class OpenAIProvider(BaseProvider):
    def generate(self, task: Task) -> Dict[str, Any]:
        raise NotImplementedError("OpenAIProvider is not implemented yet.")


class OllamaProvider(BaseProvider):
    def generate(self, task: Task) -> Dict[str, Any]:
        raise NotImplementedError("OllamaProvider is not implemented yet.")


class LMStudioProvider(BaseProvider):
    def generate(self, task: Task) -> Dict[str, Any]:
        raise NotImplementedError("LMStudioProvider is not implemented yet.")


class OpenRouterProvider(BaseProvider):
    def generate(self, task: Task) -> Dict[str, Any]:
        raise NotImplementedError("OpenRouterProvider is not implemented yet.")
