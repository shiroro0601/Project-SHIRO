from typing import Any, Dict

from company.brain.provider import DummyProvider
from company.core.task import Task


class BrainV2:
    """
    Project SHIRO Version1.0 Brain V2

    Taskを受け取り、Providerへ渡すための思考レイヤー。
    現段階では外部LLMへ接続せず、DummyProviderを標準Providerとして使う。
    """

    def __init__(self, provider=None):
        self.provider = provider or DummyProvider()

    def ask(self, task: Task) -> Dict[str, Any]:
        return self.provider.generate(task)
