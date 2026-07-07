from main_v11_ai_company_demo import create_ai_company, run_demo


class FakeProvider:
    def __init__(self):
        self.prompts = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        if "YouTubeショート動画のリサーチャー" in prompt:
            return "Research result from provider"
        if "YouTubeショート動画の台本作家" in prompt:
            return "Script draft from provider"
        if "YouTubeショート動画の編集長" in prompt:
            return "Review result from provider"
        return "Unknown provider result"


def test_ai_company_demo_can_create_provider_powered_employees():
    provider = FakeProvider()
    registry = create_ai_company(provider)

    assert registry.get("Researcher").role == "Researcher"
    assert registry.get("Writer").role == "Writer"
    assert registry.get("Reviewer").role == "Reviewer"


def test_ai_company_demo_runs_researcher_writer_reviewer():
    provider = FakeProvider()

    result = run_demo(provider=provider)

    assert result["artifacts"] == [
        "Research result from provider",
        "Script draft from provider",
        "Review result from provider",
    ]


def test_ai_company_demo_adds_three_artifacts():
    provider = FakeProvider()

    result = run_demo(provider=provider)

    assert len(result["context"].get_artifacts()) == 3
    assert len(result["artifacts"]) == 3


def test_ai_company_demo_calls_provider_generate_for_each_role():
    provider = FakeProvider()

    run_demo(provider=provider)

    assert len(provider.prompts) == 3


def test_ai_company_demo_uses_role_specific_prompts_in_order():
    provider = FakeProvider()

    run_demo(provider=provider, theme="猫の意外な雑学")

    assert len(provider.prompts) == 3
    assert "YouTubeショート動画のリサーチャー" in provider.prompts[0]
    assert "テーマ" in provider.prompts[0]
    assert "猫の意外な雑学" in provider.prompts[0]
    assert "YouTubeショート動画の台本作家" in provider.prompts[1]
    assert "60秒以内" in provider.prompts[1]
    assert "猫の意外な雑学" in provider.prompts[1]
    assert "YouTubeショート動画の編集長" in provider.prompts[2]
    assert "合格" in provider.prompts[2]
    assert "修正必要" in provider.prompts[2]
    assert "猫の意外な雑学" in provider.prompts[2]
