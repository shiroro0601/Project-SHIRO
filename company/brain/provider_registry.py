from company.brain.provider import (
    DummyProvider,
    LMStudioProvider,
    OllamaProvider,
    OpenAIProvider,
    OpenRouterProvider,
)


class ProviderRegistry:
    @staticmethod
    def create(provider_name: str):
        providers = {
            "dummy": DummyProvider,
            "openai": OpenAIProvider,
            "ollama": OllamaProvider,
            "lmstudio": LMStudioProvider,
            "openrouter": OpenRouterProvider,
        }

        normalized_name = provider_name.lower()

        if normalized_name not in providers:
            raise ValueError(f"Unknown provider: {provider_name}")

        return providers[normalized_name]()
