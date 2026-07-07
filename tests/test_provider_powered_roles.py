from company.core.employee_role import ResearchRole, ReviewerRole, WriterRole
from company.core.task import TaskType
from company.core.task_factory import TaskFactory


class FakeProvider:
    def __init__(self, response="generated text"):
        self.response = response
        self.prompts = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.response


def _task(input_data=None, instruction="猫の意外な雑学について作業してください。"):
    return TaskFactory.create_task(
        task_type=TaskType.GENERAL,
        instruction=instruction,
        input_data={"theme": "猫の意外な雑学"} if input_data is None else input_data,
    )


def test_research_role_without_provider_keeps_existing_behavior():
    role = ResearchRole()
    task = _task()

    role.prepare(task)
    result = role.execute(task)

    assert result == "Research result for: 猫の意外な雑学"


def test_writer_role_without_provider_keeps_existing_behavior():
    role = WriterRole()
    task = _task()

    role.prepare(task)
    result = role.execute(task)

    assert result == "Script draft for: 猫の意外な雑学"


def test_reviewer_role_without_provider_keeps_existing_behavior():
    role = ReviewerRole()
    task = _task()

    role.prepare(task)
    result = role.execute(task)

    assert result == "Review result: approved for 猫の意外な雑学"


def test_research_role_uses_provider_with_research_prompt():
    provider = FakeProvider(response="provider research result")
    role = ResearchRole(provider=provider)
    task = _task()

    role.prepare(task)
    result = role.execute(task)

    assert result == "provider research result"
    prompt = provider.prompts[0]
    assert "YouTubeショート動画のリサーチャー" in prompt
    assert "日本語" in prompt
    assert "5個" in prompt
    assert "雑学" in prompt
    assert "テーマ" in prompt
    assert "テーマから逸脱してはいけません" in prompt
    assert "別テーマを提案してはいけません" in prompt
    assert "出力形式" in prompt
    assert "猫の意外な雑学" in prompt


def test_writer_role_uses_provider_with_writer_prompt():
    provider = FakeProvider(response="provider script draft")
    role = WriterRole(provider=provider)
    task = _task(input_data={"topic": "犬の行動心理"})

    role.prepare(task)
    result = role.execute(task)

    assert result == "provider script draft"
    prompt = provider.prompts[0]
    assert "YouTubeショート動画の台本作家" in prompt
    assert "60秒以内" in prompt
    assert "冒頭の引き" in prompt
    assert "本編3点" in prompt
    assert "まとめ" in prompt
    assert "リサーチ結果だけを材料" in prompt
    assert "新しいテーマを作らない" in prompt
    assert "無関係な話題に移らない" in prompt
    assert "出力形式" in prompt
    assert "犬の行動心理" in prompt


def test_reviewer_role_uses_provider_with_reviewer_prompt():
    provider = FakeProvider(response="provider review result")
    role = ReviewerRole(provider=provider)
    task = _task(input_data={"title": "海の不思議"})

    role.prepare(task)
    result = role.execute(task)

    assert result == "provider review result"
    prompt = provider.prompts[0]
    assert "YouTubeショート動画の編集長" in prompt
    assert "合格" in prompt
    assert "修正必要" in prompt
    assert "改善点" in prompt
    assert "以下の台本だけをレビュー" in prompt
    assert "「内容がない」「不明」とは言わないでください" in prompt
    assert "出力形式" in prompt
    assert "海の不思議" in prompt


def test_provider_generate_result_becomes_execute_return_value():
    provider = FakeProvider(response="exact generated value")
    role = ResearchRole(provider=provider)
    task = _task()

    role.prepare(task)

    assert role.execute(task) == "exact generated value"
