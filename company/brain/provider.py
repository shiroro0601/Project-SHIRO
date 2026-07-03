from typing import Any, Dict, Union

from company.core.task import Task

try:
    import requests
except ImportError:
    class _UnavailableRequests:
        def post(self, *args, **kwargs):
            raise RuntimeError("requests is required for OllamaProvider.")

    requests = _UnavailableRequests()


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
    def __init__(
        self,
        model: str = "llama3",
        base_url: str = "http://localhost:11434",
        timeout: int = 30,
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def generate(self, prompt_or_task: Union[str, Task]) -> Union[str, Dict[str, Any]]:
        if isinstance(prompt_or_task, str):
            prompt = prompt_or_task.strip()
            if not prompt:
                raise ValueError("prompt must not be empty.")
            return self._generate_text(prompt)

        task = prompt_or_task
        prompt = self._build_prompt(task)
        response_text = self._generate_text(prompt)

        return {
            "result": response_text,
            "provider": "ollama",
            "task_type": task.task_type.value,
            "instruction": task.instruction,
            "input_data": task.input_data,
        }

    def _build_prompt(self, task: Task) -> str:
        parts = []
        if task.instruction:
            parts.append(task.instruction)
        if task.input_data:
            parts.append(f"Input: {task.input_data}")

        prompt = "\n".join(parts).strip()
        if not prompt:
            raise ValueError("prompt must not be empty.")
        return prompt

    def _generate_text(self, prompt: str) -> str:
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                },
                timeout=self.timeout,
            )
            if hasattr(response, "raise_for_status"):
                response.raise_for_status()
            data = response.json()
        except Exception as exc:
            raise RuntimeError(f"OllamaProvider request failed: {exc}") from exc

        if not isinstance(data, dict):
            raise RuntimeError("OllamaProvider response must be a JSON object.")

        return data.get("response", "")


class LMStudioProvider(BaseProvider):
    def generate(self, task: Task) -> Dict[str, Any]:
        raise NotImplementedError("LMStudioProvider is not implemented yet.")


class OpenRouterProvider(BaseProvider):
    def generate(self, task: Task) -> Dict[str, Any]:
        raise NotImplementedError("OpenRouterProvider is not implemented yet.")
