from typing import Any, Dict

from company.brain.provider import DummyProvider
from company.brain.provider_registry import ProviderRegistry
from company.core.task import Task


class BrainV2:
    """
    Project SHIRO Version1.0 Brain V2

    Taskを受け取り、Providerへ渡すための思考レイヤー。
    現段階では外部LLMへ接続せず、DummyProviderを標準Providerとして使う。
    """

    def __init__(self, provider=None, provider_name=None):
        if provider is not None:
            self.provider = provider
        elif provider_name is not None:
            self.provider = ProviderRegistry.create(provider_name)
        else:
            self.provider = DummyProvider()

    def ask(self, task: Task) -> Dict[str, Any]:
        return self.provider.generate(task)
