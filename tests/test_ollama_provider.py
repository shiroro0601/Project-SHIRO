import pytest

from company.brain.provider import OllamaProvider
from company.brain.provider_registry import ProviderRegistry
from company.core.task import TaskType
from company.core.task_factory import TaskFactory


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


def test_ollama_provider_generate_returns_response(monkeypatch):
    calls = {}

    def fake_post(url, json, timeout):
        calls["url"] = url
        calls["json"] = json
        calls["timeout"] = timeout
        return FakeResponse({"response": "Ollama response"})

    monkeypatch.setattr("company.brain.provider.requests.post", fake_post)

    provider = OllamaProvider(
        model="llama3",
        base_url="http://localhost:11434",
        timeout=10,
    )

    result = provider.generate("猫の意外な雑学")

    assert result == "Ollama response"
    assert calls["url"] == "http://localhost:11434/api/generate"
    assert calls["json"] == {
        "model": "llama3",
        "prompt": "猫の意外な雑学",
        "stream": False,
    }
    assert calls["timeout"] == 10


def test_ollama_provider_empty_prompt_raises_value_error():
    provider = OllamaProvider()

    with pytest.raises(ValueError, match="prompt must not be empty"):
        provider.generate("   ")


def test_ollama_provider_request_error_raises_runtime_error(monkeypatch):
    def fake_post(url, json, timeout):
        raise RuntimeError("connection refused")

    monkeypatch.setattr("company.brain.provider.requests.post", fake_post)

    provider = OllamaProvider()

    with pytest.raises(RuntimeError, match="OllamaProvider request failed"):
        provider.generate("猫の意外な雑学")


def test_ollama_provider_can_generate_from_task_for_brain_v2_compatibility(monkeypatch):
    def fake_post(url, json, timeout):
        return FakeResponse({"response": "Task response"})

    monkeypatch.setattr("company.brain.provider.requests.post", fake_post)
    task = TaskFactory.create_task(
        task_type=TaskType.PLANNING,
        instruction="企画を作成してください。",
        input_data={"theme": "猫の意外な雑学"},
    )

    result = OllamaProvider().generate(task)

    assert result["result"] == "Task response"
    assert result["provider"] == "ollama"
    assert result["task_type"] == "planning"
    assert result["instruction"] == "企画を作成してください。"
    assert result["input_data"] == {"theme": "猫の意外な雑学"}


def test_provider_registry_can_create_ollama_provider():
    provider = ProviderRegistry.create("ollama")

    assert isinstance(provider, OllamaProvider)
    assert provider.model == "llama3"
    assert provider.base_url == "http://localhost:11434"
    assert provider.timeout == 30
