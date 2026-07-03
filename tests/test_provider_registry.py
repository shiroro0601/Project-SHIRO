import pytest

from company.brain.provider import (
    DummyProvider,
    LMStudioProvider,
    OllamaProvider,
    OpenAIProvider,
    OpenRouterProvider,
)
from company.brain.provider_registry import ProviderRegistry
from company.core.task import TaskType
from company.core.task_factory import TaskFactory


def test_provider_registry_creates_dummy_provider():
    assert isinstance(ProviderRegistry.create("dummy"), DummyProvider)


def test_provider_registry_creates_openai_provider():
    assert isinstance(ProviderRegistry.create("openai"), OpenAIProvider)


def test_provider_registry_creates_ollama_provider():
    assert isinstance(ProviderRegistry.create("ollama"), OllamaProvider)


def test_provider_registry_creates_lmstudio_provider():
    assert isinstance(ProviderRegistry.create("lmstudio"), LMStudioProvider)


def test_provider_registry_creates_openrouter_provider():
    assert isinstance(ProviderRegistry.create("openrouter"), OpenRouterProvider)


def test_provider_registry_unknown_provider_raises_value_error():
    with pytest.raises(ValueError, match="Unknown provider"):
        ProviderRegistry.create("unknown")


@pytest.mark.parametrize(
    ("provider_name", "message"),
    [
        ("openai", "OpenAIProvider is not implemented yet."),
        ("lmstudio", "LMStudioProvider is not implemented yet."),
        ("openrouter", "OpenRouterProvider is not implemented yet."),
    ],
)
def test_stub_provider_generate_raises_not_implemented_error(provider_name, message):
    task = TaskFactory.create_task(
        task_type=TaskType.GENERAL,
        instruction="汎用タスクを実行してください。",
    )
    provider = ProviderRegistry.create(provider_name)

    with pytest.raises(NotImplementedError, match=message):
        provider.generate(task)
